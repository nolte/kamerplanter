# Spezifikation: REQ-053 - Grafische Garten- und Beetplanung

```yaml
ID: REQ-053
Titel: Grafische Garten- und Beetplanung (metrischer Gartenplan, Beetverwaltung, Pflanzplanung im Beet, Beetpflege und Pflegeprotokoll)
Kategorie: Infrastruktur & Planung
Fokus: Nutzpflanze (Outdoor, Gewächshaus, Hochbeet, Kübel); Zierpflanze mitgedacht
Technologie: Python 3.14+, FastAPI, ArangoDB, Celery, React 19, TypeScript 6, MUI 9, Redux Toolkit, WeasyPrint
Status: Entwurf
Priorität: Hoch
Version: 1.42 (#2857: Zelt-Hinweis zur Photoperiode zählt nur belegte Lichtdauern, sonst `tent.photoperiod_unknown`); 1.41 (#2913: Werkzeug „Text“ — freie Beschriftung als Planobjekt `text_label`; GP-UX-071 vollständig gebaut); 1.40 (#2913: Werkzeug „Pflanze setzen“ — eine Pflanze in einen freien Pflanzplatz; ein belegter Pflanzplatz lehnt eine zweite Einzelpflanze ab, V-25); 1.39 (#2913: Werkzeug „Bereich“ — Bereichs-Location zeichnen, Eltern der danach darin gezeichneten Beete); 1.38 (#2913: Werkzeug „Messen“, Werkzeug-Leiste aus einer Registry, Messen per Tastatur); 1.37 (#2888: Nachpflanzen warnt nicht mehr gegen die ausgefallene Pflanze selbst, Resthinweis nach Ausfallursache); 1.36 (#2898: eigene Position im Feldmodus, Opt-in, nie gespeichert); 1.35 (#2896: Staffeln eines Sukzessionsplans reservieren Slots, gestrichelt mit Datum); 1.34 (#2899: Beet-QR-Etikett mit Feldmodus-Deep-Link, Rücksprung nach dem Login); 1.33 (#2894: Sonnenauf-/-untergang im Kompass, Beetausrichtung aus Drehung und Nordwinkel); 1.32 (#2897: wiederkehrende Aufgaben aus Beetvorlagen per Opt-in beim Platzieren); 1.31 (#2862: Vereinzeln einer Zone mit Reihenabstand bei Band- und Reihensaat); 1.30 (#2890: Gartengrenze bzw. Grundriss im Editor zeichnen und bearbeiten, gesperrt nach dem Speichern); 1.29 (#2901: `as_of` an GP-API-001 für den Pflanzenstand eines vergangenen Tages); 1.28 (#2895/#2900: Unterlage im PDF-Export-Dialog; SVG mit title/desc je Objekt, getaggte PDFs); 1.27 (#2904: Auswahlgruppe auf dem Telefon einzeilig, Menü-Tooltips verdecken nichts mehr); 1.26 (#2886: Fokus bleibt bei nicht verfügbaren Editor-Knöpfen und beim Wandern in den Überlauf); 1.25 (#2891: „Beet räumen“ in der Beetansicht); 1.24 (#2854/#2903: direkter Düngungseintrag mit Produkt und Menge zählt in der Düngebilanz; Kopfdüngung im Düngeereignis als Dosis); 1.23 (#2892: Space+Drag schwenkt in jedem Werkzeug, Umschalt+Pfeil scrollt zehnfach); 1.22 (#2893: Slot-Raster im Beet-Rahmen beim Setzen und Ziehen von Slots, Rasterstufe des Plans); 1.21 (#2882/#2887: Seitenpanel-Inhalt an einer festen Baumposition, Panel-Tabs mit manueller Aktivierung); 1.20 (#2906: Pflanzenzustand zählt nur `died` als ausgefallen, `senesced` endet „historisch“); 1.19 (#2868 abgegrenzt: GP-UX-001 nennt nur die vier vorhandenen Werkzeuge, Bereich/Pflanze setzen/Messen/Text-Label werden GP-UX-071 (#2913), AC-2 mit TC-053-103 messbar); 1.18 (#2885: Seitenpanel ab md angedockt neben der Zeichenfläche statt Drawer darüber, Auswahl schwenkt in den sichtbaren Teil; GP-UX-069 und §17.3 Breakpoints, offener Punkt 6 entschieden); 1.17 (Abnahme Welle 10 und REQ-053-Abschluss, WP 10.15: Implementierungsstand, Matrix der Welle-10-Zeilen, §11.3 „ausgefallen“ nur `died`, offene Punkte der Arbeitsfläche, Restliste als Einzel-Issues); 1.16 (Welle 10, WP 10.1: Editor-Arbeitsfläche §17.3 mit GP-UX-063…070 und AC-1…AC-17, §32.6 Pkt. 1 beantwortet, §34 Welle 10 erweitert, Readiness-Review eingearbeitet); 1.15 (Abnahme Welle 9: Implementierungsstand, Matrix der Welle-9-Zeilen und UI-NFR-012-Kriterien, DSGVO-Nachzug, Sicherheitsnotiz SEC-003); 1.14 (Welle 9: GP-FR-165 und GP-FR-167 implementiert, §10.2 vollständig); 1.13 (Welle 9, WP 9.5: Stand Welle 9, UI-NFR-012 v2.3 nachgezogen, GP-API-070/071 Vorlagen-Austausch, `parcel_list` an GP-API-007); 1.12 (#2706: Bodenprofil aus Handeinträgen und offenen Analysen, je Feld gewinnt die neueste Beobachtung); 1.11 (Abnahme Welle 8: GP-API-063…069, Antworten aus #2643, Implementierungsstand und Matrix der Welle-8-Zeilen); 1.10 (Welle 8, WP 8.6: `ec_method`, `quantity_total` + `quantity_total_unit`, E-17 Variante A); 1.9 (Abnahme Welle 7: GP-API-057…062, Antworten aus #2466, Implementierungsstand und Matrix der SHOULD-Zeilen)
Datum: 2026-11-13
Tags: [garden-plan, bed, geometry, canvas, planting-layout, maintenance, care-log, irrigation-zone, mobile, mvp]
Abhängigkeit: REQ-002 v4.6 (Standort-Hierarchie Site → Location → Slot, LocationTypes, `adjacent_to`), REQ-013 v2.8 (Pflanzdurchlauf, `PlantingRunEntry.spacing_cm`, `run_at_location`), REQ-006 v3.5 (Task-Modell, `entity_type`/`entity_key`, `has_task`), REQ-022 v3.0 (Pflegeerinnerungen, `care_confirmations`), ADR-008 (einheitlicher Abschluss-Übergang), REQ-014 (`watering_events`), REQ-004 (Flächendosierung, Bodenanalyse-Felder), REQ-019 (Substratchargen, `filled_with`), REQ-028 (Mischkultur-Graph, Nachbarschafts-Check), REQ-001 v4.11 (Fruchtfolge-Kategorien, `rotation_after`, `row_spacing_cm`, `light_requirement`), REQ-007 (Ernte-Batches), REQ-018 (Aktorik, `irrigation_valve`), REQ-037 (ET0-Bewässerungsbedarf), REQ-034/REQ-052/NFR-013 (Fotos, Attachments), REQ-030 v1.13 (Zuständigkeitsgrenzen ADR-008), REQ-032 v1.2 (Druck/PDF, `LOCATION_OVERVIEW`), REQ-024 v1.37 (Mandant), REQ-049 v1.15 (Rollenvokabular), REQ-042 v1.3 (Modul-Sichtbarkeit, `garden_planner` registriert), REQ-025/NFR-011 (DSGVO), NFR-006 (Fehlerformat), NFR-016 (Migrationen), UI-NFR-001/002/003/012/019/022
Wird benötigt von: REQ-054 (Automatische Anbauplanung — liest Beete, Historie, `season_state`, schreibt geplante Runs mit Zeitfenster), REQ-032 (visueller Grundriss im Beetplan-Druck), REQ-028 §7.3 (Beetplan-Visualisierung), REQ-047 (Überwinterungsorte auf dem Plan), künftige Sonnen-/Schattenberechnung
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.42 | 2026-11-13 | **#2857 Teil A (§9.2a, V-23, W-016.6).** Der Photoperiode-Hinweis im Zelt wertet nur noch **belegte** Lichtdauern aus: Das Anforderungsprofil trägt die Herkunft `photoperiod_source` (REQ-003 v2.21: `sourced` aus einem Steckbrief oder im Profil-Editor eingetragen, `generated` aus der Phasenvorlage, `default` Rückfallwert, leer bei Altprofilen). Konfliktgruppen bilden nur `sourced`-Werte; alles andere zählt als unbekannt und führt zu `tent.photoperiod_unknown` (`info`) mit dem Schritt, die Lichtdauer im Phasenprofil einzutragen. Hanf bekommt seine Steckbrief-Lichtstunden über die Tabelle `steckbrief_phase_photoperiods` der Saatdaten als `sourced`; die übrigen Arten mit allgemeinen Phasen bleiben unbekannt, bis ein Wert im Editor gespeichert oder aus dem Steckbrief übernommen ist. Keine Migration; der Saatlauf stempelt beim Start. **Offen in #2857 (Teil B, wartet auf Migrationsnummern):** `PhotoperiodType.unspecified`, Ausschluss tagneutraler Pflanzen, Prüfung „Kurztagpflanze mit 18 h“. TC-REQ-053 v1.26 (TC-053-114). |
| 1.41 | 2026-11-13 | **#2913 (GP-UX-071, GP-UX-001, §17.3, §9.5, §20.4).** Achtes und letztes Werkzeug **Text**: ein Klick setzt den Ankerpunkt (rastet wie das Zeichnen), ein Dialog nimmt den Text, die Beschriftung entsteht als ungespeicherte Planänderung wie ein gezeichnetes Objekt. Sie ist ein Gartenobjekt der neuen Klasse `text_label` mit Rechteck-Geometrie (Ursprung = Anker, Länge = Texthöhe, Breite = Lauflänge, Drehung); ihr Text ist `label`: eine Zeile, 1–80 Zeichen, keine Steuer- und Bidi-Zeichen (422 `validation.invalid`). Keine Migration, keine neue Route. Eine Beschriftung zählt nirgends als Gegenstand: keine Höhe, kein Schatten, keine Aufgaben, kein Legendeneintrag, nicht in der Mini-Map. SVG/PDF drucken sie als maskierten Textknoten. Sie muss wie jedes Objekt innerhalb der Gartengrenze liegen (V-03). Tastaturpfad „Text hier setzen“ in der Leiste, unter md „Punkt setzen“ in der TouchBar. Damit sind alle vier Werkzeuge aus GP-UX-071 gebaut und die Obergrenze von acht Werkzeugen aus GP-UX-001 erreicht. TC-REQ-053 v1.25, UI-NFR-022 v1.27. |
| 1.40 | 2026-11-13 | **#2913 (GP-UX-071, GP-UX-001, §17.3, V-25).** Siebtes Werkzeug **Pflanze setzen**: ein Klick auf einen freien Pflanzplatz (Rolle `position`) öffnet einen Dialog mit Art und Sorte und legt genau eine Pflanze auf diesem Platz an (Betreiberannahme 2026-11-12: eine Pflanze je Klick, keine Reihen oder Flächen); die Pflanze entsteht sofort, der Plan bekommt keine zu speichernde Änderung. Ablehnungen (belegt, reserviert, harter Fruchtfolge-Block mit Verweis auf den Beet-Dialog, offline) stehen als Statusmeldung. Tastaturpfad über das Eigenschaftenpanel (Beet wählen, Pflanzplatz wählen). Das Werkzeug wird nur für Rollen mit Schreibrecht gerendert. Neu **V-25**: `POST /plant-instances` mit `slot_key` lehnt eine zweite Einzelpflanze auf einem belegten oder lebend reservierten Pflanzplatz mit 409 ab (`slot.occupied`, `slot.already_planned`), auch mit `skip_validation`; Reihen und Flächen bleiben bei `capacity_plants`. Prüfen-dann-Schreiben ohne Transaktion — gleichzeitige Anfragen können beide durchkommen. Verschieben (PUT/PATCH, MCP `SetPlantLocation`) prüft die Belegung weiterhin nicht. Offen in GP-UX-071: Text/Label. TC-REQ-053 v1.24, UI-NFR-022 v1.26. |
| 1.39 | 2026-11-13 | **#2913 (GP-UX-071, GP-UX-001, §17.3, §9.5).** Sechstes Werkzeug **Bereich**: eine Location ohne Beet-Eigenschaft (Garten, Terrasse, Balkon, Gewächshaus, eigene Typen; im Indoor-Plan Zimmer) als Rechteck oder Vieleck zeichnen, auch über „Mit Maßen hinzufügen“. Ein Bereich wird Eltern der Beete, die **danach** in ihm gezeichnet werden; was schon darin lag, behält seine Eltern und wandert beim Verschieben nicht mit — ein Umhängen gibt es nicht (Betreiberannahme 2026-11-12), ein Hinweis sagt das nach dem Zeichnen. Darstellung nach §9.5: helle Füllung, gepunkteter Rand, unter den Beeten (Trefferebene 3), in beiden Renderern und in SVG/PDF; vorhandene Gewächshäuser und Zimmer mit Geometrie erscheinen damit als Bereich. Lesemodell additiv: `locations[].is_area`, `area_type_keys`; keine Migration. Das Eigenschaftenpanel bietet für einen Bereich keine Beet-Aktionen; der Löschdialog nennt, was mitgelöscht wird, was bleibt, und dass stehende Pflanzen das Speichern ablehnen lassen (die frühere Aussage „löscht auch n Pflanzen“ war falsch, auch bei Beeten). Offen in GP-UX-071: Pflanze setzen, Text/Label. UI-NFR-022 v1.25. |
| 1.38 | 2026-11-12 | **#2913 (GP-UX-071, GP-UX-001, §17.3).** Fünftes Werkzeug **Messen**: Strecke oder Linienzug von Klick zu Klick, Länge je Abschnitt und Summe in der gewählten Einheit, rastet wie das Zeichnen ein, wird nie gespeichert; Enter oder Doppelklick beendet, Rücktaste nimmt den letzten Punkt, Esc löscht. Unter md über die TouchBar, ab md zusätzlich per Tastatur über „Punkt setzen“ und „Fertig“ in der Leiste (Fadenkreuz in der Planmitte, Pfeiltasten verschieben den Plan); das Ergebnis steht als Statustext (`aria-live`). Kurze Abschnittsbeschriftungen weichen der Summe. Die Leiste liest ihre Werkzeuge aus einer Registry (`editor/toolRegistry.ts`); Bereich, Pflanze setzen und Text/Label bleiben in GP-UX-071 offen. AC-2/TC-053-103: Überlauf-Einträge gelten als erreichbar, wenn sie durch Scrollen im Menü in den sichtbaren Teil kommen (der Fall war auf `develop` rot, weil er ungescrollte Positionen las). UI-NFR-022 v1.24 registriert `garden-plan-tool-<tool>` und die Mess-Kennungen. |
| 1.37 | 2026-11-12 | **#2888 (§11.3, GP-FR-131, GP-API-025).** Eine Nachpflanzung nennt die Pflanze, die sie ersetzt (`replant_of_plant_key`). Für diese eine Prüfung zählt die ersetzte Pflanze im Jahr ihres Ausfalls nicht als Vorkultur, wenn sie zu Beet und Mandant gehört, `died` ist und im laufenden Kalenderjahr endete; jeder andere Schlüssel wird ohne Fehler ignoriert. Resthinweis bei gleicher Familie aus `termination_cause`: Krankheit oder Schädling → Warnung mit „Trotzdem pflanzen“ und Begründung, ohne oder mit unbekannter Ursache → Hinweis, abiotisch oder mechanisch → keiner; nie eine Sperre. Andere Pflanzen, Vorjahre, Zeitstrahl und Fruchtfolge-Matrix unverändert. Das Datenmodell bodenbürtiger Ursachen wird mit REQ-054 H-10 geplant (Betreiberentscheid 2026-11-12). TC-053-111 umgekehrt. |
| 1.36 | 2026-11-12 | **#2898 (GP-UX-026).** Im Tab Karte des Feldmodus zeigt der Schalter „Meine Position“ (Opt-in nach dem REQ-002-Muster, je Besuch, nichts gemerkt) einen Punkt mit Genauigkeitskreis ≥ 3 m; Projektion relativ zu `Site.gps_coordinates` als Mitte des gezeichneten Plans, gedreht mit `north_angle_deg`. Die Position wird nie gesendet, gespeichert oder geloggt, die Karte schwenkt nie auf sie. §18-Statuszeile nachgezogen. |
| 1.35 | 2026-11-12 | **#2896 (GP-FR-074).** Jede Staffel, die `generate`/`generate-next` eines Sukzessionsplans erzeugt, reserviert freie Slots ihres Beets über `run_planned_at` (GP-FR-065, 409 bei Überlappung): die ersten freien nach `sequence`, bis die Kapazität `plants_per_batch` fasst; zu kleines Beet mit Slots → 422 `succession.not_enough_slots`, Beet ohne Slots wie bisher. Neues optionales Planfeld `batch_duration_days` (Standzeit je Staffel). Planänderung, Ende oder Löschen gibt die Reservierungen künftiger geplanter Staffeln frei. Der Plan zeigt reservierte leere Positionen gestrichelt mit `planned_from`. |
| 1.34 | 2026-11-12 | **#2899 (GP-UX-028, GP-FR-052; UI-NFR-014).** Die Beetansicht druckt ein Etikett mit QR-Code, der das Beet im Feldmodus öffnet (`/standorte/sites/{site}/plan?mode=field&bed={bed}`, ohne Token und Mandant); der Feldmodus öffnet das per `?bed=` genannte Beet. Nach dem Login führt `returnTo` zur aufgerufenen Seite zurück (nur gleiche Origin, root-relativ, auch nach Normalisierung). Die Pflanzen-Etiketten prüfen jetzt die Mandantenzugehörigkeit jeder Pflanze. Statuszeilen §10.1 und §18 nachgezogen. |
| 1.33 | 2026-11-12 | **#2894 (§9.3, GP-FR-016/017).** Mit `gps_coordinates` trägt das Plan-Lesemodell den heutigen Sonnenauf- und -untergang (Azimut und Ortszeit), der Kompass markiert beide. `Location.orientation` eines platzierten Beets ohne `aspect_deg` wird aus seiner Längsachse (`rotation_deg` + `north_angle_deg`) abgeleitet; Kreis und Quadrat behalten den manuellen Wert; gemeinsame Vektoren `bed_axis`. Ein Backfill für Bestandsbeete folgt nach den reservierten Migrationen v0109–v0111; bis dahin übernehmen sie den Wert bei der nächsten Bewegung. |
| 1.32 | 2026-11-12 | **#2897 (GP-FR-087, Betreiberentscheidung 2026-11-11).** Beim Platzieren einer Vorlage legt `place-template` mit `create_recurring_tasks` die wiederkehrenden Aufgaben der Vorlage direkt am neuen Beet an (Opt-in, Standard aus; keine Vorschläge, weil der Vorschlags-Erzeuger nach E-02 / ADR-008 Phase 2 fehlt). Erste Fälligkeit: Platziertag plus `days_offset` der Aufgabenvorlage, danach jährlich an diesem Tag – Aufgabenvorlagen tragen keinen Monatsanker. GP-FR-087, §12-Status, GP-API-062 und §32.4 Pkt. 9 nachgezogen. |
| 1.31 | 2026-11-12 | **#2862 (W-015, Agrobiologie-Review WP 10.9).** Vereinzeln einer Zone zählt mit Reihenabstand × Abstand in der Reihe, wenn ein Reihenabstand bekannt ist (Eingabe, sonst `row_spacing_cm` des Durchlauf-Eintrags, sonst unterer Wert aus `Species.row_spacing_cm`); sonst bleibt das gekennzeichnete Quadratraster. Keine agronomische Konstante im Code (E-10), keine Migration. Die Frage zur 500-Pflanzen-Grenze je Vorgang bleibt offen (#2862). |
| 1.30 | 2026-11-12 | **#2890 (UC-01, GP-FR-019/032, MUST).** Die Gartengrenze (indoor: der Grundriss) wird im Editor gezeichnet (Rechteck oder Polygon) und über Griffe bearbeitet; Einstieg im Überlauf „⋮“ (die Werkzeug-Leiste bleibt bei GP-UX-001). V-03 wird live von der Grenze aus geprüft, nie abgeschnitten. Nach dem Speichern ist die Grenze gesperrt (nicht auswählbar, keine Griffe), der Überlauf-Eintrag entsperrt sie; die Sperre ist Editor-Zustand. „Grundriss zeichnen“ im Indoor-Leerzustand startet das Werkzeug. TC-053-001 automatisiert. Statuszeilen UC-01, §9.8, §17, §28 nachgezogen. |
| 1.29 | 2026-11-12 | **#2901 (GP-API-001, SHOULD).** `GET /sites/{key}/plan?as_of=YYYY-MM-DD` liefert die Pflanzen, die an dem Tag standen (`planted_on <= as_of < removed_on`); die Struktur bleibt aktuell, `phase_key` bleibt leer (gespeichert ist nur die heutige Phase); ein Tag nach heute ist 422 `plan.as_of_in_future`. Der Jahr-Umschalter (GP-FR-077) nutzt es noch nicht. §21-Statuszeile nachgezogen. |
| 1.28 | 2026-11-12 | **#2895 (GP-FR-033) und #2900 (GP-NFR-029).** Der PDF-Export-Dialog bietet „Unterlage mitdrucken“ an (aus, nur bei vorhandener Unterlage, nicht auf dem Telefon). Jedes gezeichnete Objekt des Plan-SVG trägt `<title>` und `<desc>`, die Wurzel `role="graphics-document"`; alle Druck-PDFs sind getaggt (Strukturbaum, Titel, Sprache, Alternativtexte für Plan, Unterlage und QR-Code). Die Prüfung mit PAC/veraPDF steht aus. |
| 1.27 | 2026-11-12 | **#2904 (UI-Review Welle 10, GP-UX-066/069, AC-9/AC-15).** Unter md bleibt die Auswahlgruppe einzeilig (Ausrichten, Löschen); das Drehraster 15/45/90 steht dort als Einstellung im Überlauf „⋮“ (Einfachauswahl, Testids unverändert). Der Tooltip eines Menü-Knopfs erscheint weder über dem offenen Menü noch nach dem Schließen (Überlauf, Werkzeug-Untermenüs, Ausrichten, „⋯“ im Panel). §17.3-Statuszeile ohne #2904. |
| 1.26 | 2026-11-12 | **#2886 (UI-Review Welle 10, GP-NFR-070, WCAG 2.2 SC 2.4.3).** Nicht verfügbare Editor-Knöpfe (Speichern, Rückgängig/Wiederholen, Herauszoomen, Fertig, Punkt zurück, Ausrichten, Vorlagen-Aktionen) sind `aria-disabled` statt `disabled` und behalten den Fokus; wandert ein fokussiertes Element der Kopfleiste in den Überlauf, geht der Fokus auf „⋮“. §17.3-Statuszeile ohne #2886. |
| 1.25 | 2026-11-12 | **#2891: „Beet räumen“ in der Oberfläche (GP-FR-055, MUST).** Die Beetansicht (Tab Pflanzung) bietet Mitgliedern mit Schreibrecht „Beet räumen“: eine Beendigungsart für das ganze Beet (wie v1.5 (e), GP-ACC-040, TC-053-027), optionale Notiz, eine Bestätigung; nicht offline und nicht im Feldmodus (GP-UX-023). TC-053-027 automatisiert. Statuszeilen §10.1, §21, §28 und Welle 7 nachgezogen. |
| 1.24 | 2026-11-12 | **#2854 (Betreiberentscheidung 2026-11-11) und #2903.** §12: Ein direkter Pflegeeintrag „Düngen“ schreibt wie der Aufgabenabschluss ein Düngeereignis, wenn ein Produkt (Katalog oder Freitext) und eine Menge angegeben sind; ohne beides zählt er nicht in der Düngebilanz. Stornieren und Korrigieren ziehen es zurück; der kopierte Freitext-Produktname wird mit der Quellzeile geschwärzt (GP-FR-109, R-25). Absatz „Was in der Düngebilanz zählt“ neu. Das Düngeereignis einer Kopfdüngung zeigt Produkt, Material und Menge statt Volumen/EC/pH. |
| 1.23 | 2026-11-12 | **#2892: GP-FR-010 vollständig.** Gehaltene Leertaste auf der Zeichenfläche macht den Primärklick von Maus/Stift in jedem Werkzeug zum Schwenken (Werkzeug bleibt, Greif-Cursor, kein Seitenscrollen); in Textfeldern und auf Bedienelementen bleibt die Leertaste beim Element. Leertaste auf einem fokussierten Planobjekt wählt beim Loslassen (wie ein nativer Button), damit ein Space+Drag auf einem Objekt die Auswahl nicht zusammenfallen lässt. Umschalt+Pfeil scrollt um das Zehnfache. Statuszeilen GP-FR-010 und §28 nachgezogen. |
| 1.22 | 2026-11-12 | **#2893: Slot-Raster (GP-FR-154).** Die Messung zeigte, dass Slots im Editor nicht verschiebbar sind (GP-FR-068 ist der Weg); die vorbereitete Rahmen-Option des Editor-Snaps hatte deshalb keinen Aufrufer und ist entfernt. Betreiberentscheidung (a): Slots rasten dort ein, wo sie gesetzt und gezogen werden — freie Positionen im Pflanzdialog und „Position korrigieren“ — auf die Rasterstufe des Plans (`default_grid_m`, sonst Vorgabe des Standorttyps) im Beet-Rahmen; wie das Plan-Raster rastet das Slot-Raster immer ein, `Alt` setzt frei auf den Zentimeter. Statuszeilen GP-FR-012/154 und §28 nachgezogen. |
| 1.21 | 2026-11-11 | **#2882 und #2887 (UI-Review der Abnahme Welle 10).** Das Seitenpanel hat für beide Formen (angedockt ab md, Sheet darunter) eine einzige Position im Komponentenbaum; ein Wechsel über den Breakpoint ändert nur das Layout, offene Dialoge und getippte Werte bleiben erhalten (GP-UX-069, G-W10 b). GP-UX-068 / AC-5: Pfeiltasten bewegen den Fokus in der Tab-Leiste, aktiviert wird mit Eingabe- oder Leertaste bzw. Klick (WAI-ARIA-Tabs, manuelle Aktivierung); die Zonen laden erst beim bewussten Öffnen. §17.3-Statuszeile ohne #2882/#2887. |
| 1.20 | 2026-11-11 | **#2906: Zustandsrechner folgt §11.3.** Der Pflanzenzustand (GP-FR-192) ordnete `senesced` noch `failed` zu; jetzt gilt in Python und TypeScript nur `died` als ausgefallen, `senesced` landet wie `harvested`/`cancelled` in „historisch“. Gemeinsamer Vektor `plant-state-008` erwartet `historic`. §11.3 „ausgefallen“: Hinweis „der Zustandsrechner noch nicht“ durch den Stand ersetzt. Keine Migration. |
| 1.19 | 2026-11-11 | **#2868 abgegrenzt (Betreiberentscheidung 2026-11-11: „ABGRENZEN“).** GP-UX-001 listete acht Werkzeuge, gebaut sind vier; Bereich, Pflanze setzen, Messen und Text/Label waren nur im Code typisiert (`PlanTool`), ohne Logik und ohne Schaltfläche. Statt sie in Welle 10 nachzubauen, nennt GP-UX-001 jetzt genau die vorhandenen Werkzeuge der obersten Ebene (Auswahl, Hand/Pan, Beet ▸, Gartenobjekt ▸); die Obergrenze von acht Werkzeugen und zwei Ebenen bleibt. Die vier anderen stehen in der neuen Zeile **GP-UX-071** (SHOULD, Messen COULD, nicht MVP, #2913). Folgen: §17.3 „Werkzeug-Leiste“ und AC-2 beziehen sich auf die eingegrenzte Liste; AC-2 ist nicht mehr blockiert und wird von TC-053-103 bei 1024 × 768 gemessen (alle Werkzeuge mit Untermenü-Einträgen, alle Panel-Tabs, alle Überlauf-Einträge, kein horizontales Scrollen). Implementierungsstand §17, §17.3, §28 und Welle 10 korrigiert; Betreiberfragen Pkt. 1 und 7 als entschieden markiert. Im Code deklariert `PlanTool` nur noch die vier Werkzeuge. |
| 1.18 | 2026-11-11 | **#2885: kein Drawer mehr bei md (WCAG 2.2 SC 2.4.11).** Das UI-Review der Abnahme Welle 10 fand, dass der Drawer über der Zeichenfläche die Zoom-Steuerung und ein gerade ausgewähltes Objekt verdeckt. Ab md liegt das Seitenpanel jetzt wie ab lg angedockt **neben** der Zeichenfläche; sie gibt ihm die Breite ab, die Zoom-Stufen bleiben als Overlay auf ihr sichtbar. Öffnet eine Auswahl das Panel, behält der Plan seinen Einpass (WP 10.5), und der Viewport schwenkt waagerecht, bis das ausgewählte Objekt links vom Panel sichtbar ist — das gilt auch ab lg. Geändert: Tabelle der Breakpoints in §17.1 (Zeile md), §17.3 „Breakpoints“, GP-UX-069, offener Punkt „Drawer bei md“ und Punkt 6 der Betreiberfragen (#2884) als entschieden markiert. TC-053-102 misst das neue md-Layout. |
| 1.17 | 2026-11-11 | **Abnahme Welle 10 und REQ-053-Abschluss (WP 10.15, #2836).** (a) Implementierungsstand: WP 10.1–10.14 gemergt (#2850, #2855, #2861, #2863, #2865, #2867, #2870, #2872, #2874, #2875, #2877, #2878, #2880, #2881, #2883); Zeilen §9.8, §11.1–§11.3, §12, §17, §17.3, §25 und §28 nachgezogen, Zeile „Welle 10“ neu; zwei veraltete Aussagen korrigiert: das Glossar (GP-UX-011) ist seit #2622 vorhanden, `GET /plan` erfüllt GP-NFR-030 seit #2632/#2778. (b) Generierte Matrix `spec/e2e-testcases/GP-REQ-wave10-matrix.md` (`scripts/gp_acc_matrix.py`, `WAVE10_ROWS`/`WAVE10_AC_ROWS`/`WAVE10_DOMAIN_ROWS`): 34 Zeilen — 13 GP-Zeilen, 16 Kriterien der Arbeitsfläche (AC-11 ist mit v1.16 erfüllt und hat keine Zeile), 5 Befunde aus Anhang A 60–63 —, 33 mit Test, davon 7 mit benannter Teil-Lücke, und AC-2 ohne Test (blockiert durch #2868); Lücken in `GP-REQ-wave10-gaps.json`. (c) §11.3: „ausgefallen“ ist nur `termination_type = died`; `senesced` ist das natürliche Ende („abgeschlossen“), kein Ausfall — Folgekultur gehört zur Sukzession/Planung, nicht zum Nachpflanzen; ein vorzeitiges Seneszieren (Schossen, Hitze, Mangel) erfasst der Nutzer als `died` mit Ursache (agrobiologisches Review der Abnahme; der Code des Nachpflanz-Angebots, `planting/thinningLogic.ts`, folgt dem schon, der Zustandsrechner noch nicht: #2906). GP-ACC-040 bleibt (`senesced` beim Saisonende). (d) §17.3: neuer Absatz „Offene Punkte der Abnahme Welle 10“ (Breakpoints md = 768/lg = 1024 machen AC-2 zu einem lg-Kriterium; der Light-Modus-Hinweis senkt AC-1 auf 58,5 % bei 1366 × 768, ohne ihn 66,9 %; die Ebenen-Legende erscheint erst mit mindestens einer eingeschalteten Ebene) — als offene Fragen in #2884, die Kriterien sind unverändert. (e) Neuer §32.7 (Welle-10-Fragen aus #2884). (f) §34 Zeile 10: Stand der Abnahme; **Restliste** der offenen REQ-053-Zeilen als Einzel-Issues (#2885–#2906) bzw. als Liste der niedrigen Punkte im P-7-Bericht `.audits/prod-release/2026-11-11-req053-p7-wave10.md` — keine Welle 11. |
| 1.16 | 2026-11-10 | **Welle 10, WP 10.1 (#2822), Spec-Nachzug ohne Code.** (a) Neuer Abschnitt §17.3 „Editor-Arbeitsfläche“ nach der Betreiberentscheidung vom 2026-11-09 in #2820 (Vorschlag A Arbeitsfläche + Vorschlag C Beetliste als Tab, B entfällt): eine Kopfleiste, vertikale Werkzeug-Leiste mit Auswahlgruppe nur bei Auswahl, Zeichenfläche auf Viewport-Höhe mit Overlays, Seitenpanel mit Tabs Eigenschaften/Ansicht/Ebenen/Zonen (ohne Auswahl keine reservierte Breite), Tabs Plan · Liste · Beete mit `?tab=plan\|list\|beds` neben `?mode=`, Breakpoints ≥ lg angedockt, md Drawer, unter md `TouchBar` + Bottom Sheet; neue Zeilen GP-UX-063…070 und die Akzeptanzkriterien AC-1…AC-11 aus #2820. Präzisierungen gegenüber #2820: „Als Vorlage speichern“ steht im Überlauf, wird aber wie die Auswahlgruppe nur bei Auswahl gerendert (AC-4); „keine reservierte Breite“ gilt, solange der Nutzer das Panel nicht selbst geöffnet hat (AC-5); im Feldmodus wird `tab` ignoriert. (b) §17.1 auf die Arbeitsfläche umgestellt, §9.6, GP-NFR-023 und GP-NFR-025 verweisen auf §17.3; Implementierungsstand: neue Zeile §17.3 (nicht implementiert). (c) §32.6 Pkt. 1 beantwortet: Anhang A 60–63 gehören zu Welle 10 (Betreiberentscheidung 2026-11-09, #2759 Frage 1), keine Welle 11; Anhang A 60–63 und 84 tragen ihr Welle-10-Paket. (d) §34 Zeile „10“ auf den Welle-10-Umfang erweitert: WP 10.1–10.15 = #2822–#2836, Arbeitsfläche, Indoor-Grundriss, Domänen-Reste. (e) Readiness-Review eingearbeitet: GP-UX-052 und GP-UX-005 vermerken ihre Änderung ab Welle 10 selbst (Raster/Snap im Panel-Tab „Ansicht“, Zoom als Overlay, Export im Überlauf; Legende im Tab „Ebenen“); die Werkzeug-Leiste trägt genau die Werkzeuge aus GP-UX-001 („Verschieben“ aus #2820 = Hand/Pan, „Aus Vorlage“ und „Mit Maßen hinzufügen“ als Untermenü-Einträge); die Panelform folgt allein der Breite, der grobe Zeiger entscheidet nur über die `TouchBar`; Panel-Umschalter mit `aria-expanded`/`aria-controls`, Panel-Tabs nach dem WAI-ARIA-Muster „Tabs“, Ort und Zustandsregel des Panels (GP-UX-068); Verlagerungsreihenfolge der Kopfleiste und Belegung unter md (GP-UX-063); Verhältnis zu App-Shell und Seitenkopf (UI-NFR-005/017/021); „Als Vorlage speichern“ nur bei genau einem ausgewählten Beet; die zwei „Listen“ unterschieden; GP-UX-069 „ein Komponentenbaum“ als Review-Prüfpunkt statt Kriterium; GP-UX-070 mit UI-NFR-022 R-021 und Registrierung in §2.5.1 je WP; AC-2/3/4/5/9 präzisiert, neue AC-12…AC-17; AC-Einleitung als Abnahme der SHOULD-Zeilen 063…069 und der MUST-Zeile 070; Verweise auf den Implementierungsplan aus §17.3 entfernt. AC-9 verlangt Touch-Ziele ≥ 48 px nach UI-NFR-001 R-011, #2820 nannte 44 px. |
| 1.15 | 2026-11-09 | **Abnahme Welle 9 (WP 9.17, #2757).** (a) Implementierungsstand: WP 9.1–9.16 gemergt (#2786, #2787, #2789, #2791, #2792, #2793, #2796, #2797, #2799, #2802, #2803, #2808, #2811, #2812); §14, §18, §21, §23, §30, Welle 7/8/9 und §28.2 nachgezogen; GP-API-007 `parcel_list` und GP-API-070/071 sind gemountet. (b) Generierte Matrix `spec/e2e-testcases/GP-REQ-wave9-matrix.md`: 16 REQ-053-Zeilen und 35 UI-NFR-012-Kriterien der Welle, alle mit Test, vier Teil-Lücken in `GP-REQ-wave9-gaps.json` (GP-FR-025 Slot-Kopie und Überlappung der Kopie, UI-NFR-012 R-009 latenter API-Cache, R-020 Stammdaten, R-060 Kontolöschung auf anderem Gerät) — alle bei #2759. §30: GP-ACC-064 jetzt mit Test, 64 von 64 Kriterien belegt. (c) Reviews der Welle (Security, Datenschutz, Webview/CSP/SW, E2E-Ergebnisse): in diesem Stand behoben — Digest-Vergleich in konstanter Zeit an allen Stellen (SEC-002), `task_keys` der Batch-Routen ≤ 200 am Body (SEC-004), der Plan-Cache speichert weder `plan_updated_by_name` noch Beet-Notizen/-Beschreibungen (GDPR-004); als Notiz festgehalten: §32.6 Pkt. 16 (SEC-003). (d) §32.6 Pkt. 15 erledigt: REQ-025 v1.40 §10 (TTDSG-Zeilen, Einstufung mit offener Rechtsprüfung #2517), NFR-011 v1.46 §2.1 (R-41/R-42 mit bekannter Lücke), UI-NFR-012 v2.4 (R-056 b präzisiert). P-7-Bericht `.audits/prod-release/2026-11-09-req053-p7-wave9.md` (kein Deploy, E-07). |
| 1.13 | 2026-11-08 | **Welle 9, WP 9.5 (#2745), Spec-Nachzug ohne Code.** (a) §21.7: neue Zeilen GP-API-070 `GET /bed-templates/{key}/export` und GP-API-071 `POST /bed-templates/import` (Vorlagen-Austausch GP-FR-173, WP 9.9, #2749, noch nicht gemountet). (b) §21.1 GP-API-007: Parameter `parcel_list` (Zusatzseite Parzellenliste GP-FR-176) mit Zuweisung nur bei `include_assignment=true` (WP 9.10, #2750, noch nicht gemountet); Kennung = Beetname + laufende Nummer in Plan-Reihenfolge, kein Feld `bed_number` (§32.6 Pkt. 8). (c) §23.1 GP-FR-173/176 verweisen auf diese Zeilen. (d) §34 Welle 9: Stand 2026-11-08 — WP 9.1 (#2741), 9.2 (#2742), 9.3 (#2743) gemergt, WP 9.4 (#2744) in Arbeit; der Offline-Lesepfad läuft über IndexedDB, nicht über den Service-Worker-Cache, weil das Backend `Cache-Control: no-store` sendet (MT-044; Betreiberfrage §32.6 Pkt. 13). (e) Implementierungsstand: §18, §21, §23 nachgezogen, neue Zeile „Welle 9“; §28.2 Offline-Zeile auf den Stand gebracht. (f) GP-UX-024: Logout/Tenant-Wechsel leeren den Plan-Cache; für den Offline-Puffer gilt UI-NFR-012 R-056 (b)–(d). §30: GP-ACC-062…064 für GP-API-070/071 und `parcel_list` (geplant, als Lücke in `GP-ACC-gaps.json`); GP-API-071 nennt die Versionsgrenze wie GP-NFR-072. (g) Neuer §32.6: Platzhalter und offene Betreiberfragen der Welle 9, gespiegelt aus #2759, mit Pkt. 13 (`no-store`), Pkt. 14 (Lebensdauer des Schreibpuffers, 365 Tage) und Pkt. 15 (DSGVO-Nachzug REQ-025 §10 / NFR-011 §2.1). (h) UI-NFR-012 v2.3 übernimmt die SR-019-Regel als R-055/R-056, hält die Allowlist statt des Interceptors R-053 fest (R-057/R-058) und ersetzt die Abnahme „Lighthouse PWA-Score ≥ 90“ durch CDP-Kriterien. |
| 1.12 | 2026-11-07 | **Bodenprofil aus Handeinträgen und offenen Analysen, je Feld gewinnt die neueste Beobachtung (#2706, Betreiberstandard aus #2643, §32.5 Pkt. 11).** §15.1: Jedes Speichern, Stornieren (auch Rückgängig innerhalb von zehn Minuten und Rückgängig eines Aufgabenabschlusses), Korrigieren oder Ersetzen einer Bodenanalyse leitet die Messfelder des `soil_profile` in derselben Transaktion neu ab; es gibt keinen zweiten Schreibweg, und jede Ableitung schreibt das Beet (Schreibkonflikt statt stillem Überspringen). Je Messfeld konkurrieren der Handeintrag (serverseitig `hand_values`, `value = null` = von Hand geleert) und die neueste offene Analyse; der spätere Zeitpunkt gewinnt, Gleichstand geht an den Handeintrag. Ein Storno kehrt so zur neueren verbleibenden Beobachtung zurück. Regel für Altbestand ohne `hand_values` festgelegt. `PATCH /locations/{key}` legt nur Handeinträge für geänderte Messfelder an und führt dieselbe Ableitung in seiner Transaktion aus (gleichzeitige Ableitung: `409 WRITE_CONFLICT`); `last_analysis_at` und `hand_values` übernehmen PATCH und Plan-Import nie (`soil_profile: null` speichert `null`); ein mitgesendetes, abweichendes `last_analysis_at` ist `409 soil_profile.stale`. Ein vom Modell abgelehntes abgeleitetes Profil bricht die Transaktion ab (`422 soil_profile.derivation_invalid`). Der Verlauf (GP-API-066) trennt Serien nach Parameter, Methode und normalisierter Einheit (`unit` je Serie; `mS/cm` = `dS/m`, Groß-/Kleinschreibung und Leerzeichen egal; keine Umrechnung); ein Methodenwechsel wird je Analyse markiert. Mehrere Messungen eines Parameters in einer Analyse: die geringste `sample_depth_cm` gilt fürs Profil. Gelesen werden je Beet höchstens die 500 neuesten offenen Analysen. |
| 1.11 | 2026-11-07 | **Abnahme Welle 8 (WP 8.32, #2675).** (a) §21: Zeilen für die in Welle 8 gemounteten Routen — GP-API-063 `GET /sites/{key}/rotation-matrix`, GP-API-064 `GET /locations/{key}/succession-recommendation`, GP-API-065 `GET /locations/{key}/companion-edges`, GP-API-066 `GET /locations/{key}/soil-analyses`, GP-API-067 Beet-Fotos (`GET\|POST /locations/{key}/photos`, `PUT …/photos/cover`, `DELETE …/photos/{attachment_id}`), GP-API-068 `GET /locations?…&format=csv` (Beetliste als CSV mit Spaltenauswahl), GP-API-069 `POST /sites/{key}/beds/import-csv`; Pfade, Parameter, Grenzen und Fehlercodes aus den Routern gelesen. §8 nachgezählt (API 44 → 57). (b) **§32.5:** Betreiberantworten auf das Bündel #2643 (Fragen 1–9, 2026-11-03: Empfehlung je Frage übernommen) und die offenen Nachträge (Frage 10 Quellenregel, A–E aus WP 8.12/8.20, Profil-Rückrechnung #2706, Rechtsfragen Beet-Fotos, Vorgaben WP 8.8/8.9/8.25/8.26) eingearbeitet. (c) **Implementierungsstand** neu gemessen gegen `develop` 184bc9e3d: §10.1, §10.2, §11.4, §13, §15, §16, §19, §21, §23, §25, §27; neue Zeile „Welle 8“ mit der generierten Matrix `spec/e2e-testcases/GP-REQ-wave8-matrix.md` (37 Zeilen, 36 mit Test, davon 5 mit benannter Teil-Lücke; GP-NFR-072 ohne Test, WP 8.28 #2671 offen). (d) §34: Zeile Welle 8 mit Stand. Keine Verhaltensänderung im Code. |
| 1.10 (Nachtrag #2660) | 2026-11-06 | **Welle 8, WP 8.17 (#2660), Betreiberentscheidung #2643 Frage 3.** GP-API-040 gemountet: `POST /tasks/{key}/accept-suggestion` setzt `suggested = false` und leert `suggestion_reason` (das Feld gilt nur, solange `suggested`; der Erzeuger bleibt in `origin`/`source`), die Aufgabe bleibt offen; `POST /tasks/{key}/dismiss-suggestion` (Body `{reason?}`, ≤ 500 Zeichen) schließt als `skipped` (§12.1 „verworfen“) mit dem Grund in `completion_notes`, `suggested` bleibt `true`, kein `care_event`, keine Benachrichtigung. Beide nur für `suggested = true` (sonst 409 `task.not_a_suggestion`; Verwerfen eines geschlossenen Vorschlags 409 `task.suggestion_closed`), ab Gärtner, fremder Mandant 404; Prüfung und Schreiben in einer AQL-Anweisung. GP-FR-086: Abschnitt „Vorschläge“ im Pflege-Tab mit Grund und den Schaltflächen „Annehmen“/„Verwerfen“ (ersetzt „Jetzt erledigen“). **Kein Erzeuger** (E-02): der Abschnitt erscheint erst, wenn ADR-008 Phase 2 Vorschläge anlegt. Implementierungsstand §12 und §21 nachgezogen. |
| 1.10 (Nachtrag #2654) | 2026-11-06 | **Welle 8, WP 8.11 (#2654), E-17 Variante A im Code.** §15.3: neuer Eingang „Boden-Leitfähigkeit" und Flag **M5** `check_salt_content` („Salzgehalt prüfen"): Boden-`ec_ms_cm` über einem konfigurierten Grenzwert mit Quelle, nur bei gleicher `ec_method` (keine Umrechnung), nicht bei mineralischem Substrat; ändert keinen Zustand und keine Menge, ausgeliefert inert (Grenzwert `null`, R-001). Anzeige im Beetkopf als eigener Chip unabhängig vom Zustand. Im Code entfällt `_FEEDER_EC_FACTOR` (das EC-Ziel ist die Phasen-EC); die Stickstoffsammler-Warnung der Flächendosierung liest `Species.nitrogen_fixing` der gewählten Art (`species_key`, für den Mandanten lesbar, sonst 404), `demand_level` bleibt als veraltete Eingabe. |
| 1.10 | 2026-11-03 | **Welle 8, WP 8.6 (#2649).** (a) §15.1: `ec_method` am `soil_profile` und an der Messung (`ec_ms_cm` nur mit Methode, Vergleiche nur innerhalb einer Methode, keine Umrechnung; Review U-002); `target_ph` gilt je `ph_method` (U-003). (b) §15.2 GP-FR-123: `quantity_total` + `quantity_total_unit` (`g` bei `g_per_m2`, `l` bei `l_per_m2`, Rundung 3 Stellen) statt `quantity_total_g`, gemessen an `care_event_service._quantity_total` (P-002). (c) REQ-004 v3.9: Freiland-Düngetabelle auf `nutrient_demand` + `nitrogen_fixing`, Mengen als „Beispiel, unverifiziert“ (F-002, K-001). (d) §32.3: **E-17 entschieden, Variante A** (Betreiberantwort #2643 Frage 1, 2026-11-03): keine EC-Skalierung nach Zehrerstufe im Boden, Boden-EC nur Salz-Hinweis mit konfigurierbarer Schwelle (Default `null`), `_FEEDER_EC_FACTOR` entfällt. Quelle: `spec/analysis/agrobiology-req-053-wave8-ec.md`. *Nachtrag #2685 (2026-11-06):* Die Ausgangslage in §16.3 ist als historisch (vor M6) markiert. |
| 1.9 | 2026-10-31 | **Abnahme Welle 7 (WP 7.27, #2493).** (a) §21: Zeilen für die in Welle 7 gemounteten Routen — GP-API-057 `POST /sites/{key}/plan/new-season`, GP-API-058 `GET /sites/{key}/plan/snapshots`, GP-API-059 `POST /sites/{key}/plan/snapshots/{audit_key}/restore`, GP-API-060 `PUT\|DELETE /sites/{key}/plan/underlay`, GP-API-061 Vorlagen-Katalog (`GET\|POST /bed-templates`, `PATCH\|DELETE /bed-templates/{key}`), GP-API-062 `POST /sites/{key}/plan/place-template` mit dem gemessenen Body `{template_key, origin, rotation_deg, expected_revision}`; GP-API-053 nennt den Body `{volume_liters, allocation: by_area\|equal, performed_at?, summary?}` und die Antwort; die Parameter `scope`/`keys` (GP-API-004), `target`/`offset_m` (GP-API-005) und `underlay`/`bed_list` (GP-API-007) stehen jetzt in ihren Zeilen. (b) **§32.4:** Betreiberantworten vom 2026-10-19 auf die Platzhalter der Welle 7 (#2466) und die drei Fragen aus WP 7.1 eingearbeitet. Abweichung vom Wortlaut der Antwort zu Frage (3) „keine Zonen-Quote“: seit #2525 hält eine Site höchstens 500 Zonen (`irrigation_zone.quota_exceeded`, GP-NFR-017), weil ein wiederholter `merge`-Import die Zonen der Datei jedes Mal neu anlegt und der Plan-Lesepfad sonst unbegrenzt wüchse. (c) GP-FR-081: der Weg `for_each_plant` schreibt keine `task_cloned_from`-Kante und übernimmt `trigger_phase` und `recurrence_end_date` nicht (bekannte Grenze). (d) GP-API-005 und GP-NFR-017: ein wiederholter `merge`-Import legt die Zonen der Datei erneut an (eine Zone der Datei hat keine stabile Identität). (e) **Implementierungsstand** neu gemessen gegen `develop` 156dc4d99: §9.4 auf „teilweise“ korrigiert (`Ctrl/Cmd+D` ohne Tastenbelegung, ein dupliziertes Beet ohne Slots), §9.7 nach #2490 (PR #2600), §14 (`by_demand`, „Regen — übersprungen“, Felder der Wasserquelle im Editor), §21, §28; neue Zeile „Welle 7, SHOULD-Zeilen“ mit der generierten Matrix `spec/e2e-testcases/GP-REQ-wave7-matrix.md` (`scripts/gp_acc_matrix.py`). Keine Verhaltensänderung im Code. |
| 1.8 | 2026-10-31 | **GP-ACC-054 und GP-ACC-055 geschlossen (#2544).** (a) GP-FR-070: `POST /planting-runs/mixed-culture` prüft vor jeder Berechnung und jedem Schreiben, dass die `row_assignment`-Mengen der Einträge paarweise disjunkt sind; eine Überschneidung antwortet `422 layout.row_assignment_overlap`, `details[0].conflicts` nennt die Paare (`runs`: Positionen im Body, `rows`: gemeinsame Reihen, `rows_total`), gekappt auf 20 Paare zu je 50 Reihen; `pairs_total` und `truncated` sagen, was fehlt. Nur Einträge mit Reihen-Anordnung (`grid`, `rows`, `triangular`) und `row_assignment` zählen mit; `zone`, `free` und Einträge ohne Anordnung belegen keine Reihen. Reihenindizes sind 0-basiert (Beispiele in GP-FR-070, §20.6 und GP-ACC-054 darauf umgestellt). **Bekannte Grenze:** der Index bezieht sich auf das Reihenraster des Eintrags (`row_spacing_cm`, `row_direction`, Randabstände); zwei Einträge mit verschiedenen Rastern können trotz disjunkter Indizes Pflanzen an dieselbe Stelle setzen. Der Pflanzdialog legt alle Einträge auf ein gemeinsames Raster; die API prüft nur die Indizes. Gemessen: ein Run trägt genau einen Entry (`monoculture`/`clone`), mehrere Entries mit Reihen gibt es nur über diesen Endpunkt — „ein Run mit zwei Entries" in GP-ACC-054 ist dort umgesetzt (ein Run je Art). (b) GP-FR-137 „je Beet einschaltbar": neues Feld `Location.rotation_enabled: bool \| null` (additiv, `null` = Standard des Typs, keine Migration). Vorrang: `rotation_exempt` → aus; sonst `rotation_enabled = true` → an, `false` → aus (`rotation.not_applicable.disabled`, neu); sonst Typ (`planter`/`tent`/`shelf` aus). `PATCH /locations/{key}` nimmt `rotation_enabled` und `rotation_exempt` (bisher über keine Route schreibbar); beide `true` nach der Änderung → `422 patch.rotation_exempt_and_enabled` (geprüft nur, wenn der PATCH eines der beiden Felder sendet). Die Prüfung je Pflanzplatz (`POST /plant-instances` mit `slot_key`, `POST /planting-runs/{key}/create-plants`, `POST /plant-instances/slots/{slot_key}/validate-planting`) folgt demselben Schalter: ein ausgeschaltetes Beet weist keine Pflanzung mit `ROTATION_VIOLATION` ab (D-09). Der Import weist ein Beet mit beiden `true` mit dem Befund `import.rotation_exempt_and_enabled` ab; beide Felder sind dort strikte JSON-Booleans. Beide Felder in der JSON-Sicherung (`schema_version "1"`, additiv) und im Art.-15-Export. Abweichung zu §15.1: `rotation_exempt` liegt im Code an der Location, nicht am `soil_profile`; der Schalter liegt daneben. (c) §30: 61 von 61 Kriterien mit Test belegt. |
| 1.7 | 2026-10-30 | **Spec-Drift-Durchgang (WP 6.4, #2448):** neuer Abschnitt „Implementierungsstand" vor §1, gemessen gegen `develop` 1738dbc19 (gemountete Routen, Domänen- und Frontend-Code, Nachweis je Zeile über die gemergten PRs) — 34 Zeilen: 6 `implementiert`, 25 `teilweise`, 3 `nicht implementiert`. Offene MUST-Punkte laut Messung: Gartengrenze und Beet räumen nur über die API, Space+Drag (GP-FR-010), Slot-Raster (GP-FR-154), inerter Frost-Grund des Pflanzenzustands (§11.4), Glossar (GP-UX-011), GP-ACC-054/055, GP-NFR-030. **GP-API-056** (§21.2) trägt die in #2425 Punkt 4 bestätigten Endpunkte `PUT\|DELETE /slots/{key}/adjacent/{other_key}` nach (Betreiberentscheidung 2026-10-19). §8 auf den gezählten Stand (API 42 → 44, ACC 57 → 61). Keine Anforderung geändert. |
| 1.6 (Nachtrag #2512) | 2026-10-30 | **`frost_exposed` in Sicherung und PATCH-Abgleich (#2512, Betreiberentscheidung 2026-10-19 zu #2503 Option a und #2466 Punkt 12):** (a) Die JSON-Sicherung trägt `frost_exposed` je Location (additiv innerhalb `schema_version "1"`, GP-FR-140); der Import übernimmt den Wert der Datei, sobald der Schlüssel im Eintrag steht (explizites `null` = vom Standorttyp erben), und leitet ihn nur für eine ältere Datei ohne den Schlüssel wie bisher aus `microclimate.frost_risk` ab (`high` → `true`, `low` → `false`, sonst erben). Ein migriertes Beet `false`/`normal` übersteht damit die Wiederherstellung aus seiner eigenen Sicherung (#2503 Kante 2); `frost_exposed` steht auch im Art.-15/20-Export (GP-FR-147). (b) `PATCH /locations/{key}` bei einer **Änderung** des Risikos: `high` setzt `true`, `low` setzt `false`, `unknown` hebt die Übersteuerung auf; `normal` hebt nur ein gespeichertes `true` auf und lässt ein erzwungenes `false` (und `null`) stehen. Ein unverändertes Risiko berührt das Feld weiter nie. Folge (#2503 Kante 1): `low` → `normal` behält `false`; `normal` → `high` → `normal` endet bei `null`, weil `high` das `false` durch `true` ersetzt und das Feld keine Vorgeschichte hält. (c) Rollout P-2: ein Dev-Cluster, auf dem der erste Entwurf von v0098 lief, behält `false`/`low`-Zeilen (als `conflicts` gelistet) und meldet `migration_checksum_drift` für 0098. |
| 1.6 (Nachtrag #2542) | 2026-10-30 | **Import-/Restore-Härtung (#2542, Security-Review #2541, Gruppe `2026-10-29-plan-input-hardening`):** GP-NFR-055 — je Site höchstens die 20 neuesten `import_snapshot`-Zeilen; der `replace`-Import und die Wiederherstellung entfernen die älteren in derselben Transaktion, andere Zeilen von `garden_plan_audit` bleiben. Die Listen `locations`, `garden_objects` (je ≤ 500) und `slots` (≤ 8 000) einer Importdatei werden vor jeder Verweisauflösung begrenzt (422 `plan.quota_exceeded`, auch im `dry_run`); der Export bleibt unbegrenzt, weil ein über die Standort-API angelegter Standort nicht gegen die Plan-Quote zählt. GP-NFR-052 (e): die CSP des SVG-Downloads ist `default-src 'none'` ohne `style-src 'unsafe-inline'` — die Engine schreibt weder `style`-Element noch `style`-Attribut. |
| 1.6 (Nachtrag #2528) | 2026-10-29 | **Vorlage löschen gibt die Beete frei (#2528, Gruppe `2026-10-29-delete-cascades`):** §20.12 — `delete_template` entfernt `template_key` an den platzierten Beeten in derselben Transaktion (eigene Vorlage: Beete des Mandanten; Systemvorlage: alle Mandanten); Import behandelt `template_key`/`soil_profile.substrate_key` als Herkunftsverweise (REQ-056 v1.7); v0102 bereinigt verwaiste Schlüssel. |
| 1.6 (Nachtrag #2513) | 2026-10-29 | **Standort löschen kaskadiert (#2513, Gruppe `2026-10-29-delete-cascades`):** `DELETE /sites/{key}` läuft als eine Stream-Transaktion, entfernt die Struktur des Standorts (Beete inkl. verschachtelter, Slots, Gartenobjekte, Bewässerungszonen, Saisonzustände, Wetterprognosen/Klimanormalen/Wetterquellen, Bewässerungsbedarfe) und schneidet jede aus den Graph-Definitionen abgeleitete Kante an einem entfernten Knoten; `care_events` und bestehende `garden_plan_audit`-Zeilen bleiben als Historie (GP-FR-101, SR-011); eine Audit-Zeile `op=delete, entity=site` wird in derselben Transaktion geschrieben (§20.13). Neu **V-24** `site.has_active_plants` (409, §22.2) und **GP-ACC-061**. Fremd gestempelte Zeilen (`tenant_key` ≠ Mandant des Standorts) werden nie entfernt; `*_key`-Felder anderer Anforderungen (Sensoren, Tasks, Pflanzläufe, …) bleiben stehen, nur ihre Kanten fallen (Folge-Issue #2556: Delete-seitiger Kaskaden-Guard). |
| 1.6 (Nachtrag WP 3.9) | 2026-10-19 | **Umsetzung der Standortmerkmale (#2399), Festlegungen:** (a) `Location.site_conditions` ist der eingebettete Werttyp aus §10.2 in voller Form (`sun_profile`, `microclimate`, `wind_exposure`, `slope_deg`, `aspect_deg`, `access_sides`, `flags`), alles optional, Standard unbekannt; `PATCH /locations/{key}` nimmt ihn (die gesendeten Schlüssel werden in den gespeicherten Wert gemischt, `sun_profile` und `microclimate` je Schlüssel, Listen ersetzt; ein unbekannter Schlüssel ist ein 422; explizites `null` leert ihn), Antwort, Plan-Export und -Import tragen ihn. Die Oberfläche bietet im MVP nur die Sonnen-Kacheln (GP-FR-157); `sun_window`-Chips (GP-FR-158), Laubschatten (159) und die übrigen Felder bleiben SHOULD ohne Oberfläche. (b) **Migration v0098** kopiert `frost_exposed` nach `microclimate.frost_risk` (`true` → `high` wie in §10.2, `false` → `normal` (Betreiberentscheidung 2026-10-19, #2454 Punkt 1; `normal` hebt eine Übersteuerung nur bei einer **Änderung** auf; Import und Rückänderung entschieden in #2512, siehe Nachtrag #2512), `null` bleibt unberührt); sie ist additiv: `frost_exposed` bleibt das Feld, das die Winterleser lesen (`frost_exposure_resolver`, Saison-Automatik), und `PUT`/`PATCH /locations` sowie der Plan-Import halten beide Felder im Gleichschritt (nur eine **Änderung** zählt; `high` setzt `true`, `low` setzt `false`, `normal`/`unknown` heben die Übersteuerung auf, der Standorttyp entscheidet dann wieder; seit Nachtrag #2512 hebt `normal` nur ein `true` auf, und der Import übernimmt `frost_exposed` aus der Datei). Die Umstellung der Leser und das Entfernen des Alt-Felds sind eigener Schritt. (c) `site_fit_calculator.assess` liefert zusätzlich zum Wert einen Grundcode (`match`, `too_sunny`, `too_shady`, `tolerated`, `tolerance_unknown`, `bed_unknown`, `requirement_unknown`); die gemeinsamen Vektoren (`operation: site_fit`, 23 Fälle, eine Zelle der Matrix je Fall) liegen in `garden-plan-vectors.json`. GP-ACC-053 ist der Nachweis (GP-ACC-050 betrifft den Pflanzenzustand). (d) Die Stapel-Zuweisung läuft über die Editor-Operation `update_fields` (ein Rückgängig-Schritt, gesperrte Beete bleiben unverändert), es gibt keine neue Route. (e) `SpeciesResponse` führt `light_requirement`, `shade_tolerance` und `row_spacing_cm`, die Felder, die der Pflanzdialog liest. |
| 1.6 (Nachtrag WP 3.4) | 2026-10-19 | **Umsetzung des Beet-Validators (#2394), Festlegungen:** (a) `POST /locations/{key}/validate-planting` nimmt `{species_key, slot_key?, rotation_window_years?}` (Fenster 1–8, Standard 3) und antwortet **immer 200** mit Hinweisen: `severity` ∈ `OK \| INFO \| WARNING \| CRITICAL`, `code`, Grund, `years_since`, `pause_years`, `pause_source` ∈ `species \| family \| default`. Stärkestufe: höchstens die halbe Anbaupause verstrichen → `CRITICAL`, danach bis zum Ende der Pause `WARNING`; keine Aufzeichnung in der Rückschau → `INFO` „nicht prüfbar“ (kein stilles Bestehen, REQ-054 H-01). Mit `slot_key` zählen die Nachbarn dieses Slots (`adjacent_to`, WP 3.3), ohne die Spezies im ganzen Beet (Stufe `INFO`). (b) Pflanzen zählen für jedes Jahr, in dem sie standen; Gründüngung zählt mit ihrer Familie; ein Brachejahr (`plan_role = fallow`) belegt das Beet ohne Familie. (c) `rotation_reset_at` liegt am `soil_profile` des Beetes (§15.1); die Historie davor zählt nicht. (d) Aus für `planter`/`tent`/`shelf` und `rotation_exempt` (`rotation_applicable: false`, GP-FR-137); ein Schalter „je Beet einschalten“ ist noch nicht modelliert. (e) `GET /locations/{key}/rotation` listet jedes Jahr des Rückblicks, neueste zuerst, mit Familie, `nutrient_demand` (Spezies, sonst Familie; `null` bei Gründüngung/Brache) und `plan_role`. (f) `POST …/history/backfill` schreibt `care_event(planting, trigger = backfill)` mit dem neuen Server-Feld `rotation_entry {year, season?, family_key?, species_key?, plan_role}` (§20.10); `performed_at` = Saisonmitte (Frühjahr 15.4., Hauptkultur/ohne 1.7., Herbst 15.9.); V-11 entfällt für Backfill — die Grenze ist das Kalenderjahr `heute − 10 … heute − 1` (422 `backfill.year_out_of_range`), weil der älteste Jahrgang mitten im Jahr über 3 650 Tage zurückliegen kann. `DELETE …/history/backfill/{care_event_key}`: Autor oder Leitung, `void_reason = backfill_error`. |
| 1.6 | 2026-10-18 | **Folgeentscheidungen vom 2026-10-18 (E-16, E-17, #2411) und Umsetzung des Abschluss-Übergangs (WP 4.3, #2413).** E-16: `performed_by`-Filter von GP-API-034 rollenabhängig (Betrachter/Gärtner nur auf sich selbst, Leitung und `management`-Scope auf jedes Mitglied; SR-020, D-22 revidiert); das Pflegeprotokoll ist **kein** PflSchG-§11-Nachweis (`treatment_applications` bleibt der Nachweis, §13.2); Freitexte gelöschter Mitglieder bleiben in geteilten Mandanten stehen wie bei `plant_diary_entries` (GP-NFR-055); ein neu gesetzter RRULE leert `recurrence_rule_unconvertible` (§12.2). E-17: EC-Skalierung und `nutrient_demand_level` gehören in Welle 8 (Bodenanalyse/Düngung, mit agrobiologischer Prüfung), nicht in diese Version (§15, §16.3). Abschluss-Übergang (GP-FR-083/088/149, GP-API-031/032): Bettbezug, Fachdokumente je Kategorie, Batch-Vertrag (404 für den ganzen Batch), Rückgängig als `reopen` mit `undo` — §12.3, §21.5. |
| 1.5 | 2026-10-18 | **Betreiberentscheidungen vom 2026-10-18 (E-12…E-15, §32.3).** #2333: Beet-Rahmen ±1 000 m (V-01, §9.2), Plan-Rahmen bleibt 0…1 000 m; Polygon-Pivot = erster Punkt (§20.1); negatives `rotation_deg` abgelehnt, Werte die auf 360,000 runden wrappen auf 0,0; GP-NFR-012 bleibt unverändert (Property-Tests mit Hypothesis). #2349: GP-NFR-031/§25.2 Budget „groß" ≈ 1 MB unkomprimiert, Pflanzen serverseitig paginiert bzw. per `include=` nachladbar; GP-NFR-013 nennt die 1-MiB-Body-Grenze (413 `body_too_large`) statt 2 MB/422. #2346: §12.2 M5 parkt nicht konvertierbare Rules nach `recurrence_rule_unconvertible` statt den Start zu verweigern. #2371: Steckbrief-Datenregeln (§16.3, §10.2). Bestätigt: `spacing_cm`/`row_spacing_cm` 5–1 500 cm (Code `MAX_SPACING_CM = 1_500.0`; Issue #2391 nannte 1 000 irrtümlich). |
| 1.5 (Nachtrag WP 3.2) | 2026-10-18 | **Umsetzung der Reservierung (#2392), Festlegungen:** (a) `Slot.capacity_plants` bleibt für `position` 1–20; für `row`/`zone` ist es die Pflanzenzahl, die das Layout fasst (bis 100 000, GP-FR-064) — ein Zonen-Layout über 20 Pflanzen bleibt **ein** Slot statt in 20er-Stücke zerlegt zu werden. (b) V-08: Zeitfenster sind **geschlossene** Datumsintervalle (der `planned_until`-Tag ist noch belegt); ein offenes Ende überlappt jeden späteren Beginn. (c) `PlantingRun.source`-Allowlist: `manual`, `plan_editor`, `succession`, `allocation`, `season_copy`, `field_mode`, `crop_planner`. (d) Ein Run mit Reservierungen behält sein `planned_start_date` (422 `run.reserved_window_fixed`); verschieben = freigeben und neu planen. (e) `POST /locations/{key}/clear` setzt `termination_type` auf alle stehenden Pflanzen; `cancelled` beendet die Runs als `cancelled`, alle anderen Arten als `completed`; `harvested_batch` wird in diesem Paket nicht ausgewertet (Erntebuchung = REQ-007). (f) Quick-Planting: nur `grid`/`rows`/`triangular`, Pflanzen über die Beetkapazität hinaus werden ohne Position erfasst (`layout.capacity_exceeded`). |
| 1.4 (Nachtrag) | 2026-10-16 | **Spec-Readiness-Review eingearbeitet** (4 Critical, 11 Warning, 10 Suggestion; Entscheidungen getroffen): `spacing_cm`/`row_spacing_cm` überall 5–1 500 cm (REQ-013, REQ-001 mitgezogen); M6: `demand_level = green_manure` → `plan_role = green_manure`, `nutrient_demand = null` (GP-FR-139, REQ-002); `sun_exposure`-Schwellen in §29 konfigurierbar statt fest; `row_assignment` mit **einer** Semantik (`list[int]` am Entry, GP-FR-060/070, §20.6); `Species.row_spacing_cm` ist Range-String (GP-FR-061, REQ-001); `shade_tolerance = null` → `marginal` „Toleranz unbekannt" (GP-FR-160, REQ-001); GP-ACC-017/GP-API-016 auf `edge_margin_along_cm`/`edge_margin_across_cm`; Maßstabsstufen in GP-API-007/REQ-032 = GP-FR-142; Rückblick GP-FR-103/GP-API-039 `max(rotation_pause_years, 5)`, Obergrenze 10; GP-NFR-062 `ConsentGuard` statt Middleware; §28.2 Offline (E-06) und GP-FR-086 (ADR-008 Phase 2) präzisiert; §28.3 vervollständigt; fünf neue Akzeptanzkriterien GP-ACC-053…057 (§8: 57 ACC); GP-NFR-071 als Tabellenzeile (§8: 61 NFR); `GP-DATA`-Präfix (ohne Anforderungen) und der Geister-Verweis „033b" in GP-FR-033 gestrichen; Pins in der Kopfzeile angehoben; §34 Welle 0 und Anhang A (4, 5, 55, 77, 78) als erledigt markiert; `entity_type`-Allowlist identisch mit REQ-006; Konflikt-Dialog-Wortlaut einheitlich (GP-UX-017, GP-ACC-011, UI-NFR-022); Kurzzusätze zu unbelegten Faktoren (O-17) in GP-FR-015/060/061/130/157. |
| 1.4 | 2026-10-15 | **Implementierungsstart** — Betreiberentscheidungen E-01…E-11 (§32.2, Plan `.audits/plans/req-053-garden-bed-planning-implementation.md`). Gegen den Code gemessen (v0087, #2107/MT-010): `tenant_key` wurde von `locations`/`slots` bewusst **entfernt**, die Site ist der einzige Eigentümer (`domain/services/location_ownership.py`). **SR-022/D-18 revidiert:** kein Stempeln, keine Indizes `locations/slots(tenant_key)`, `garden_objects` folgen dem Location-Muster (nur `site_key`); GP-ACC-046 prüft jetzt das Site-Anker-Prädikat; Issue 6f entfällt (§20.4, §20.13, §20.14, §22.3, R-09, §33). **ADR-008** wird Accepted mit Phase 3 **nur für den Task-Abschluss** (§12.2, O-05); M5 schrumpft, weil `recurrence_rule` im Code bereits RRULE ist — nur Alt-Cron-Strings und der croniter-Fallback (GP-NFR-015). **O-16 entschieden:** `Species.shade_tolerance` bleibt Toleranz, neues `Species.light_requirement` als Anspruch, `site_fit` im MVP (GP-FR-061/160, §32.1). **O-21 revidiert:** GeoJSON **WON'T** (GP-FR-018/146, §8, §28.2). **Offline:** Welle 9 baut die UI-NFR-012-Basis (GP-UX-024, §34). `Task.entity_type` bleibt String mit Service-Allowlist (§20.9). M4 Backfill → Welle 8. |
| 1.3 | 2026-10-11 | **Editor-Interaktion, Standortmerkmale, Import/Export** nach zwei neuen Reviews (`spec/analysis/frontend-design-review-req-053-v1.3.md`, `outdoor-garden-planner-review-req-053-v1.3.md`). Neu: **§9.7 Interaktionsregeln** (Auswahl/Hit-Priorität, Touch-Gesten und Zeichnen ohne Maus, Zoom-Definition in px/m und LOD, Eltern-Kind-Verhalten, Snap-Priorität, Undo-Granularität, Fehlbedienungsschutz, Tastatur/WCAG 2.1.4, Fokusmodell, Labels, Leerzustände, Live-Validierung, Export-/Import-UI); **§10.2 Standortmerkmale des Beets** (Sonnenprofil, Mikroklima, Wind, Hang, Erreichbarkeit, Eignungs-Ampel `site_fit` gegen `Species.shade_tolerance`); **§23.1 Import/Export-Erweiterungen** (Vorjahres-Kopie, Teil-Export, CSV-Import, Vorlagen-Austausch, Spaltenauswahl). Widersprüche bereinigt (Long-Press, Pfeiltasten, Redo, Beschriftungs-Zoom, „2 s destruktiv", Doppelklick, GP-NFR-028). **Betreiberentscheidungen O-16…O-22 (§32.1)**: `deep_shade` ergänzt, `replace`-Import + Snapshot im MVP, Hintergrund-Unterlage SHOULD, Saison-Kopie in REQ-053, GeoJSON bleibt COULD, Schwellenprüfung später, Indoor-Grundriss (§9.8) SHOULD und nicht MVP. Neu **§11.4 Pflanzeninfo als Mouseover und grafische Pflanzenzustände** (GP-FR-190…192, GP-UX-058…062, GP-API-054). Roadmap (§34), Anhang A (Issues 69–86) und Zählung (§8) nachgezogen; `TC-REQ-053.md` auf 44 Testfälle erweitert (TC-053-031…044). |
| 1.2b | 2026-10-04 | **Pre-Merge-Review (PR #2091, 10 Findings):** Migrationsnummern v0072–v0077 waren auf `develop` bereits vergeben → logische Platzhalter M1…M6 (GP-NFR-015); bbox-Beispiele in §20.3/§21.3 auf die Rotationskonvention korrigiert; GP-ACC-015 nutzt `retired` statt des mit W-014 entfallenen `fallow`-Status; Rückgängig im Feldmodus braucht Void auf eigene Ereignisse ≤ 10 min (GP-API-037); Nacherfassung der Vorjahre bekommt einen Datenpfad GP-API-042 (V-11-Ausnahme serverseitig); `trigger`-Enum in GP-FR-100 vervollständigt; CSV-Pfad vereinheitlicht; GP-ACC-028/GP-FR-133 auf `nutrient_demand`/`plan_role` umgestellt. Nicht übernommen: die Behauptung „TaskCategory hat 18 Werte" — `common/enums.py` hat 16. |
| 1.2a | 2026-10-04 | Querverweis: §29 verweist für die automatische Anbauplanung auf das neue **REQ-054**; „Wird benötigt von" ergänzt. Keine inhaltliche Änderung. |
| 1.2 | 2026-10-04 | **Drei Reviews eingearbeitet** (`spec/analysis/agrobiology-review-req-053.md`, `outdoor-garden-planner-review-req-053.md`, `security-review-req-053.md`) mit Betreiberentscheidungen: **O-07 revidiert** (K-001) — Zehrerstufe (3 Werte) und `nitrogen_fixing` (Bool) getrennt, `PlanRole` für den Rotationsplan (§16.3); **`tenant_key` auf Location und Slot** in M1 (SR-022, §20.13, §22.3); **Fruchtfolge- und Mischkultur-Hinweis sowie Vorjahresanzeige in den MVP** (F-12, GP-FR-131/132 → MUST); **Plan-Revision nur für Struktur** — Slot-Korrekturen und Quick-Planting laufen außerhalb (F-09, D-06); Retention `care_events` 5 Jahre (SR-005, NFR-011); `performed_by`-Filter für alle Rollen (SR-020); **Slot-Reservierung mit Zeitfenster** und UC „Beet räumen" (F-01/F-02); **Beetstatus = Lebenszyklus, Saisonzustand abgeleitet** (W-014). Dazu: Bodenmodell neu (K-002/K-003: `soil_texture`, `growing_medium_kind`, `conditions[]`, Messwerte mit Methode/Einheit), Anbaupausen je Familie (K-004), Layout-Semantik präzisiert (W-002/W-003: `grid`, `triangular`, Rand quer/längs, Reihenrichtung, Kapazität mit Reihenabstand), Steckbrief-Felder statt Duplikat (W-001), Pflegekatalog erweitert (W-006/F-03), Tasks an Kompost/Wasserquelle (W-008), Zeltregeln (W-016), Schattenfelder vorbereitet (§29), Security: Batch-Rollenprüfung je Op (SR-001), Referenzauflösung GP-NFR-058 (SR-002/003), Quoten (SR-004), Redaktion GP-FR-109 (SR-006), Kaskade/Export (SR-007/008), `trigger` serverseitig (SR-009), Matrix bereinigt (SR-010), Pflicht-Audit (SR-011), Komplexitäts-/Zeitbudget (SR-012), Prüfreihenfolge (SR-013), HA-Entität (SR-014), `url_fetcher`/SVG-Allowlist (SR-015), CSV (SR-016), Rate-Limits (SR-017), Import (SR-018), Sentry/Cache (SR-019). Feldmodus: Sofortspeichern, Schnellprotokoll-Chips, Rückgängig-Snackbar, Stepper als Standard (F-13/F-16/F-18). MoSCoW/MVP-Widersprüche bereinigt (F-06). 11 neue Akzeptanzkriterien (GP-ACC-039…049). |
| 1.1 | 2026-10-04 | **Alle offenen Punkte entschieden** (Betreiber, §32). Folgenreichste Entscheidung O-01: **ein Positionsmodell für Zelt und Beet** — `Slot.geometry` gilt für alle Slots, `Slot.position` (Rasterzelle) wird in Welle 1 per Migration in Geometrie überführt und entfernt (§9.2a, §20.5); damit entfallen der Indoor-Feature-Flag V-18 und die Scope-Einschränkung für Indoor-Sites (§2.3, O-08). O-02: `Location.dimensions` wird in Welle 1 entfernt, nicht gespiegelt (§20.8). O-05: ADR-008 wird in Welle 0 auf Accepted gehoben, RRULE kanonisch, bestehende Cron-Regeln werden migriert (§12.2). O-07: REQ-053 legt das gemeinsame Zehrer-Enum fest (§16.3, GP-FR-138) und ändert REQ-001/REQ-002 mit. O-13: Durchfluss manuell mit optionaler HA-Überschreibung und Provenienz (GP-FR-114). Übrige Punkte wie empfohlen. Roadmap Welle 0/1 und Issue-Kandidaten angepasst. |
| 1.0 | 2026-10-04 | Erstfassung. Fasst die in REQ-002 §1 („Visuelle Beetplanung") nur als Business-Case angelegte Gartenplanung zu einer eigenen, implementierbaren Anforderung zusammen: metrisches Geometriemodell auf Site/Location/Slot (§7, §20), neue Collections `garden_objects`, `care_events`, `irrigation_zones` (§20), Plan-Batch-API mit optimistischer Nebenläufigkeit (§21), Rendering-Entscheidung SVG-in-React mit austauschbarer Renderer-Grenze (§19), Feldmodus für die mobile Nutzung im Garten (§18), MVP-Abgrenzung (§28) und 30 Akzeptanzkriterien (§30). Die Vorgabe aus dem Auftrag (Go-Backend, Vue.js, Tailwind) widerspricht dem verbindlichen Stack (`spec/stack.md`: FastAPI, React 19, MUI 9) und wurde **nicht** übernommen — siehe §3.2. |

---

## Implementierungsstand

Gemessen am 2026-10-30 gegen `develop` 1738dbc19 (v1.7): Router und gemountete Routen (`app.routes` des importierten Backends), Domänen- und Frontend-Code. Die Nachweise sind die gemergten Pull Requests (Squash-Commits auf `develop`), gefunden über `git log -- <Pfade>`; Aussagen aus der Versionshistorie oder dem Implementierungsplan sind nur übernommen, wo der Code sie bestätigt. **Status:** `implementiert` — der Abschnitt ist im Code vollständig vorhanden, bekannte offene Punkte sind höchstens Folge-Issues ohne fehlendes Verhalten; `teilweise` — ein Teil fehlt, die Anmerkung nennt ihn; `nicht implementiert` — kein Verhalten im Code. Offen sind außerdem die Abnahmepakete WP 6.1 (#2445), WP 7.24–7.28 (#2490–#2494). **Nachmessung v1.9 (2026-10-31, `develop` 156dc4d99, WP 7.27):** WP 6.1 (#2546), WP 7.24 (#2600), WP 7.25 (#2599) und WP 7.26 (#2602) sind gemergt; offen bleibt WP 7.28 (#2494). Die Zeilen §9.4, §9.7, §14, §21 und §28 sind nachgezogen, die Zeile „Welle 7, SHOULD-Zeilen“ ist neu. **Nachmessung v1.11 (2026-11-07, `develop` 184bc9e3d, WP 8.32):** Welle 8 ist bis auf WP 8.28 (#2671, GP-NFR-072) und die Abnahme gemergt; die Zeilen §10.1, §10.2, §11.4, §13, §15, §16, §19, §21, §23, §25 und §27 sind nachgezogen, die Zeile „Welle 8“ ist neu. **Nachmessung v1.17 (2026-11-11, `develop` 48b87efa8, WP 10.15):** Welle 10 ist gemergt; die Zeilen §9.8, §11.1–§11.3, §12, §17, §17.3, §18, §21, §24, §25 und §28 sind nachgezogen, die Zeile „Welle 10“ ist neu; jede offene Zeile nennt ihr Rest-Issue. Pfade relativ zu `src/backend/app/` bzw. `src/frontend/src/features/gardenPlanner/`.

| Bereich | Status | Was fehlt / Anmerkung | Nachweis |
|---------|--------|-----------------------|----------|
| §7, §20 Datenmodell (Geometrie, `Site.plan`, Location-/Slot-Geometrie, `garden_objects`, `care_events`, `irrigation_zones`, `bed_templates`, M1–M6) | implementiert | `Location.dimensions` und `Slot.position` entfernt (O-01/O-02). | #2332, #2334, #2336, #2339, #2341, #2347, #2348, #2410, #2403, #2507, #2527 |
| §9.1, §9.2, §9.2a Plan-Modell, Maße, Raster, Zoom (GP-FR-001–009, 011, 013, 014, 150) | implementiert | — | #2376, #2377, #2380, #2382, #2389 |
| GP-FR-010 Pan | implementiert | Mittelklick und Space+Drag (`useEditorTools.ts`: gehaltene Leertaste auf der Zeichenfläche macht den Primärklick von Maus/Stift in jedem Werkzeug zum Pan, Werkzeug im Store unverändert, Greif-Cursor; Leertaste in Textfeldern und auf Bedienelementen bleibt deren, `keyTargets.ts`) sowie Zwei-Finger-Pan; Shift+Pfeil scrollt ohne verschiebbare Auswahl um das Zehnfache (`useEditorKeyboard.ts`, `COARSE`). Leertaste auf einem fokussierten Planobjekt wählt es beim Loslassen, sofern sie nicht zum Pan diente (#2892). | #2380, #2383, #2385 |
| UC-01 sowie der Grenzanteil von GP-FR-019/032, GP-API-002 Gartengrenze in der Oberfläche | implementiert | Seit #2890: Der Eintrag „Gartengrenze zeichnen“ im Überlauf „⋮“ (Indoor: „Grundriss zeichnen“) startet den Grenz-Modus — eine planweite Handlung, kein Werkzeug der obersten Ebene (GP-UX-001, §17.3); unter md ist er über denselben Überlauf und die `TouchBar` („Punkt setzen“, „Fertig“) erreichbar. Gezeichnet wird ein Rechteck oder Vieleck mit den Zeichenschritten der Beete (`editor/tools/drawMachine.ts`, Ziel `boundary`), danach trägt die Grenze Griffe wie ein Beet (Ecken, Kanten, Drehen, Punkte verschieben/einfügen/löschen; `editor/tools/boundaryMachine.ts`). Jede Änderung ist eine `set_boundary`-Operation im Batch, ein Rückgängig-Schritt, der Nordwinkel bleibt erhalten. GP-FR-032: Die gespeicherte Grenze ist gesperrt — nicht auswählbar, ohne Griffe; „Gartengrenze entsperren und bearbeiten“ im Überlauf entsperrt sie, „Sperren“, Esc oder das Speichern sperren sie wieder. Die Sperre ist ein Zustand des Editors, kein gespeichertes Feld (`Site.plan` hat kein `locked`). V-03 von der Grenze aus (Spiegel von V-19): Eine Grenze, die Beete oder Gartenobjekte draußen ließe, wird beim Ziehen rot gezeichnet und nicht übernommen (Hinweis, kein Abschneiden); ein Server-Fund `boundary.shrinks_below_objects` erscheint in der Speichermeldung. Der Indoor-Leerzustand „Grundriss zeichnen“ startet den Modus direkt. Der Garten-Leerzustand bietet weiterhin nur „Erstes Beet anlegen“ (#2617, GP-UX-049: genau eine Handlung); die Grenze zeichnet man dort danach über den Überlauf. | Backend #2353; #2890 |
| §9.3 Orientierung (GP-FR-015–017) | teilweise | Nordwinkel und Kompass (GP-FR-015). **GP-FR-016** (#2894): Hat die Site `gps_coordinates`, trägt das Plan-Lesemodell `sun_directions` (Azimut und Ortszeit von Sonnenauf- und -untergang am heutigen Tag der Site, `Site.timezone`; `domain/calculators/sun_calculator.py` `calculate_sun_directions`, astral), der Kompass markiert beide auf dem Ring und nennt sie in einer Beschriftung (`editor/Compass.tsx`); ohne GPS und bei Polartag/-nacht nichts, keine Verschattung (§29). **GP-FR-017** (#2894): Ohne `aspect_deg` wird `Location.orientation` eines platzierten Beets aus der **Längsachse** abgeleitet — Rechteck entlang der längeren Seite (`length_m` > `width_m` → `+y`), Polygon nach der Bounding-Box seiner Punkte im eigenen Rahmen, Kreis und Quadrat ohne Achse (manueller Wert bleibt); die Achse, gedreht um `rotation_deg` und gelesen gegen `north_angle_deg`, wird auf die Halbdrehung [0, 180) gefaltet und nach ihrem Ende zwischen Nord und Südost benannt (`north` = Nord–Süd-Achse; `orientation_calculator.bed_axis`, TS-Port `model/bedOrientation.ts` gegen `garden-plan-vectors.json` Operation `bed_axis`). `aspect_deg` behält Vorrang (GP-FR-168). Geschrieben von Plan-Batch (Beete, die er anlegt, verschiebt oder dreht, und alle Beete bei geändertem Nordwinkel), `PATCH /locations` bei geändertem Hang, Import; `PUT /locations` schreibt den Wert eines Beets mit Längsachse nicht. Das Seitenpanel zeigt die Längsachse live (nur lesend). **Lücke:** Bestandsbeete ohne Hang erhalten den abgeleiteten Wert erst beim nächsten Verschieben, Drehen oder Ändern des Nordwinkels — eine Backfill-Migration ist offen, weil v0109–v0111 für den Datenschutzplan reserviert sind (`spec/privacy/09-migrations-and-backfills.md`, M-1 lückenlos). | #2382, #2894 |
| §9.4 Objektmanipulation (GP-FR-019–028, 151–153, 155, 156) | teilweise | Zeichnen, Auswahl, Griffe, Löschdialog mit Kinderzahl, Duplizieren über Panel und Kontextmenü inkl. Mehrfach-Duplizieren, Undo/Redo, Kontextmenü, Panel, Sperren vorhanden. Die Taste `Ctrl/Cmd+D` dupliziert seit WP 9.14 (`useEditorShortcuts.ts`). **Fehlt (MUST-Teil von GP-FR-025):** Ein dupliziertes Beet bekommt keine Slots, weil die abschließende Batch-Op-Liste kein `create_slot` hat (`editor/tools/duplicate.ts`; §32.4 Pkt. 8: bleibt so). | #2380, #2385, #2386, #2532, #2591 |
| GP-FR-012, GP-FR-154 Snap | implementiert | Raster- und Objekt-Snap im Editor vorhanden. Slots rasten im Beet-Rahmen ein (Anker (0, 0), mit dem Beet gedreht): im Pflanzdialog beim Setzen und Ziehen freier Positionen und in „Position korrigieren" beim Ziehen des Markers, mit der Rasterstufe des Gartenplans (`default_grid_m`, sonst der Vorgabe des Standorttyps); wie das Plan-Raster im Editor rastet das Slot-Raster immer ein, die Pixel-Toleranz gilt nur für Ecken und Kanten; `Alt` setzt frei auf den Zentimeter (`planting/LayoutCanvas.tsx`, `snapPointToGrid` in `editor/tools/snap.ts`). Die Pfeiltasten in „Position korrigieren" rasten nicht ein; einen Snap-Marker zeichnen die Pflanz-Ansichten nicht. Im Editor sind Slots nicht verschiebbar — der Weg dafür ist GP-FR-068 („Position korrigieren"). | #2382, #2532, #2591, #2893 |
| GP-FR-029, GP-FR-031 Ausrichten/Verteilen, Ebenen | implementiert | Ebenen-Registry mit Zonen, „zuletzt gegossen", Unterlage, Sonne/Feuchte/Frost, Pflanzenzustand. | #2532, #2533, #2540, #2570, #2576 |
| GP-FR-033 Hintergrund-Unterlage | implementiert | Hochladen, Zwei-Punkt-Eichung und Ebene im Editor vorhanden; die PDF-Unterlage bietet der Export-Dialog als Opt-in „Unterlage mitdrucken“ — standardmäßig aus, nur bei einer gespeicherten Unterlage und nicht auf dem Handy; gewählt sendet er `underlay=true` an `GET /print/garden-plan/{site_key}` (`io/ExportDialog.tsx`, `io/ioApi.ts`, #2895). Folgepunkte #2545. | #2540, #2895 |
| GP-FR-034 Messwerkzeug (COULD) | nicht implementiert | — | — |
| §9.7 Interaktionsregeln (GP-UX-032–057, GP-NFR-065–070) | implementiert | Label am Pol der Unzugänglichkeit (Python-Referenz `label_anchor_calculator`, TS-Port gegen `garden-plan-vectors.json`), Kürzen mit „…“, bei Überlappung gewinnt das größere Objekt, Maße außerhalb über der Kante an den Griffen vorbei, „Zum Bearbeiten heranzoomen“ (GP-UX-047/048, GP-NFR-067; #2490). Bekannte Grenzen aus #2600: das PDF wendet die Überlappungsregel nicht an; Zaun-/Hecken-Beschriftungen unterscheiden sich zwischen Editor und PDF; ein großes Beet verdrängt die Namen der Beete darin (ein Bereich wie ein Gewächshaus seit #2913 im Editor nicht mehr, §9.5); TC-053-040 läuft nur auf Komponentenebene, nicht als E2E. | #2380, #2383, #2385, #2386, #2443, #2600 |
| §9.8 Indoor-Grundriss (GP-FR-180–183) | implementiert | Seit Welle 10: Eigenschaften von `window`/`door`/`furniture`/`lamp` sowie `trellis` und `off_site` im Tab „Eigenschaften“, Objekt-Legende im Tab „Ebenen“ (180; `editor/objectProps/*`, `planting/ObjectLegend.tsx`, WP 10.6); Fensterorientierung aus Wandsegment und Nordwinkel mit Vorschlag „Aus Fenster vorschlagen“ für das `sun_window` im Umkreis (Standard 1,5 m je Site), nie ohne Bestätigung (181; `domain/calculators/window_orientation.py`, TS-Port `model/windowOrientation.ts` gegen `garden-plan-vectors.json`, `editor/WindowSunSuggestion.tsx`, WP 10.7); Site-Typ im Plan-DTO, Indoor-Leerzustand, Wetter-/Frost-/Windmerkmale ausgeblendet, Raster 5 cm (182, WP 10.8); Pflanzplätze über `supports_layout` (Zelt, Regal), Tab und Liste „Pflanzplätze“ (183). Den Wohnungsumriss zeichnet seit #2890 „Grundriss zeichnen“ als Grenze des Plans. **Grenzen:** ein JSON-Import ohne `plan`-Block legt den Plan mit 10 cm an (Repository-Fallback); die Zuordnung Himmelsrichtung → `sun_window` ist eine Modellierungskonvention, die drei-Quellen-Recherche des Reviews ist offen (WP 10.7); keine Lichtberechnung aus `lamp` (gewollt). | #2347, #2385, #2874, #2875, #2877 |
| §10.1 Beetfelder (GP-FR-040–055) | teilweise | Vorhanden: `is_bed`, Beetansicht, Beetliste mit Filter „Meine Beete", Statuswechsel, Vorlagen und Standardgrößen; seit WP 8.18/8.19 Fotos am Beet mit Titelbild, Galerie-Tab und Feldmodus-Foto „an Beet oder Pflanze" (GP-FR-051; `domain/services/location_photo_service.py`, `bed/BedPhotosTab.tsx`, `bed/BedCoverPhoto.tsx`, GP-API-067). Beet räumen (GP-FR-055, MUST) in der Oberfläche seit #2891: Knopf „Beet räumen“ im Tab Bepflanzung, solange Pflanzen im Beet stehen (ab Gärtner, gesperrt offline und auf zwischengespeichertem Stand); der Dialog nennt die betroffenen Pflanzen und Durchläufe, erklärt die Folgen, fragt eine Beendigungsart für das ganze Beet (Standard `harvested`, Festlegung v1.5 Nachtrag WP 3.2 (e)) und ruft `POST /locations/{key}/clear` (#2418) einmal auf (`bed/BedClearDialog.tsx`, E2E TC-053-027); im Feldmodus nicht angeboten (GP-UX-023). Seit #2899 das Beet-QR-Etikett (GP-FR-052 mit GP-UX-028): „Etikett drucken“ in der Beetansicht (`components/print/LocationLabelDialog.tsx`), PDF über den Druckpfad der Pflanzen-Etiketten (`GET /t/{slug}/print/location-label/{location_key}`, Vorlage `location_label.html`, Mandantenanker an der Site); der QR-Code trägt `{APP_BASE_URL}/standorte/sites/{site_key}/plan?mode=field&bed={location_key}`, für eine Location ohne `is_bed` die Standortseite. Der Link nennt keinen Mandanten: Wer in mehreren Mandanten ist und einen anderen aktiv hat, erhält die 404 der Site. Fehlt: Teilen/Zusammenlegen (GP-FR-054, COULD, keine Route). Folgepunkte der Fotos: #2715 (Härtung), Rechtsfragen §32.5 Pkt. 12. | #2341, #2402, #2418, #2527, #2532, #2717, #2891 |
| §10.2 Standortmerkmale (GP-FR-157–169) | implementiert | Vorhanden: Sonnenkacheln und `site_fit` (157, 160), `sun_window`/Laubschatten (158, 159), Karten-Ebenen (169); seit Welle 8: `site_fit` mit Frost, Wind und Drainage (161; `domain/calculators/site_fit_calculator.py` `assess_axes`, TS-Port `model/siteFit.ts` gegen `garden-plan-vectors.json`), beetgenaue Frost-Frühwarnung (162; `tasks/frost_forecast_tasks.py` nennt die Beete aus `domain/engines/bed_frost_engine.py` `named_frost_beds`: `high` immer, `low` nie), Mikroklima/Wind/Hang/Zugangsseiten im Panel und die Feldmodus-Chips „Feucht/Normal/Trocken“ und „Windig“ (162, 163, GP-UX-057; `bed/SiteConditionsFields.tsx`), Sonnenklassen- und Erreichbarkeits-Schwellen je Site (164; `domain/models/site.py` `SunClassThresholds`, `ReachThresholds`), Hinweis `bed.reach_too_wide` (166; `domain/calculators/reach_calculator.py`, `model/reach.ts`), `orientation` aus `aspect_deg` (168; `domain/calculators/orientation_calculator.py`). **Grenzen:** der Erreichbarkeits-Hinweis kennt den Zugang nur aus `access_sides`, nicht aus angrenzenden Wegen (#2703); Hang/Exposition erben nicht vom Site-Wert (§32.5 Pkt. 4, die Site hat kein `terrain`); die Frühwarnung nennt jede Location mit `frost_risk = high`, nicht nur Beete (§32.5 Nachtrag D). Seit Welle 9: `flags` `root_competition`/`allelopathy_risk` als Auswahl ohne Berechnung (165; `bed/SiteConditionsFields.tsx`) und `nearest_water_source_m` (167): Luftlinie von der Beetkante zur nächsten Wasserquelle des Gartens (Kante-zu-Kante, 0 bei Überlappung; Quellen mit `off_site` zählen nicht), vom Server berechnet und an drei Stellen derselbe Wert: Beet-Summary (GP-API-012, nur für Beete), Beetliste (GP-API-011 liefert das Feld, sobald Beete gelistet werden; die Spalte erscheint, sobald ein Beet einen Wert hat) und wählbare CSV-Spalte. Die Quellen liest eine nach Klasse und `off_site` gefilterte Abfrage (`domain/calculators/geometry_distance.py` mit `is_water_source`; TS-Port `model/geometryDistance.ts` gegen `garden-plan-vectors.json`, noch ohne Konsument in der Oberfläche — dieselbe Primitive nutzt später #2703). | #2457, #2537, #2570, #2586, #2689, #2692, #2698, #2707, #2751, #2752 |
| §11.1–§11.3 Pflanzplanung (GP-FR-060–073, 077) | implementiert | Layout, Vorschau, Reservierung, Pflanzdialog, Positionskorrektur und Mischkultur in einer Transaktion vorhanden; sich überschneidende `row_assignment` der Mischkultur werden mit `422 layout.row_assignment_overlap` abgewiesen (GP-ACC-054, v1.8). Bekannte Grenze (GP-FR-070): geprüft werden die Reihenindizes je Eintrag, nicht die Positionen; Einträge mit verschiedenem Reihenraster können sich trotz disjunkter Indizes überlagern (der Pflanzdialog nutzt ein gemeinsames Raster). Seit Welle 10 (WP 10.9, Anhang A 60, W-015): Aussaat über `PUT /slots/{key}/sowing`, Zustand „gesät“ in Pflanzenzuständen und Pflanzliste, „Vereinzeln“ erzeugt die Pflanzen in der vom Server berechneten Anzahl (ohne Abstand fragt der Dialog, kein Standard, E-10), „Nachpflanzen“ am ausgefallenen Slot (nur `died`, §11.3). **Grenzen:** Reihen und Zonen werden auf der Zeichenfläche nicht gezeichnet und SVG/PDF zeigen gesäte Slots nicht; beim Nachpflanzen zählt die ersetzte ausgefallene Pflanze seit #2888 nicht mehr als Vorkultur (Resthinweis aus `termination_cause`, §11.3), offen bleibt dort das Datenmodell bodenbürtiger Ursachen; der Zustandsrechner führt `senesced` noch als `failed` (#2906). Seit #2862 zählt eine Zone mit Reihenabstand als Fläche ÷ (Reihenabstand × Abstand in der Reihe); der Reihenabstand kommt aus der Anfrage, sonst vom `PlantingRunEntry.row_spacing_cm`, sonst als unterer Wert aus `Species.row_spacing_cm` (Quelle im Dialog genannt, E-10). Ohne Reihenabstand (Breitsaat) bleibt das als Schätzung gekennzeichnete Quadratraster. Offen bleibt, ob Zonen über der Grenze von 500 Pflanzen je Vorgang Einzelpflanzen oder einen Sollbestand erhalten (#2862). | #2401, #2418, #2452, #2531, #2587, #2544, #2863 |
| GP-FR-074 Sukzession reserviert Slots | implementiert | Gemessen 2026-11-12 (#2896). Jede Staffel, die `POST /succession-plans/{key}/generate` bzw. `…/generate-next` für ein Beet mit Slots erzeugt und deren Saattag nicht vorbei ist, reserviert ihre Slots über `run_planned_at` (GP-FR-065) — derselbe Schreibweg wie `plan-slots` (`PlantingReservationService.reserve_slots`), V-08 vor und in der Transaktion, 409 `slot.already_planned`. Zeitfenster: `planned_from` = Saattag, `planned_until` aus dem neuen Planfeld `batch_duration_days` (Standzeit je Staffel, von Hand; leer = offenes Ende). Gewählt werden die ersten freien Slots des Beets in `sequence`-Reihenfolge, bis ihre Kapazität `plants_per_batch` fasst; alle Staffeln eines Aufrufs werden vor dem ersten Schreiben gewählt. Ein Beet, dessen Positionen zusammen weniger als eine Staffel fassen: 422 `succession.not_enough_slots`; ein Beet ohne Slots reserviert nichts. Eine Planänderung an Zeitplan, Beet, Staffelgröße oder Standzeit, ein beendeter und ein gelöschter Plan geben die Reservierungen der noch geplanten, nicht fälligen Staffeln frei; die Runs bleiben. `GET /sites/{key}/plan` liefert je Slot `planned_from` (erster Tag einer laufenden Reservierung); SVG- und Konva-Renderer zeichnen die leere Position gestrichelt mit dem Datum. Code: `domain/services/succession_plan_service.py`, `domain/services/planting_reservation_service.py` (`pick_batch_slots`), `domain/engines/slot_reservation_engine.py` (`pick_free_slots`), `renderer/SvgPlanRenderer.tsx`, `renderer/konvaDraw.ts`. | #2896 |
| GP-FR-075, 076, 078 Zone auflösen, Reihe als Linie, Saison kopieren | nicht implementiert | COULD; „Neue Saison aus Vorjahr" (GP-FR-171) legt Slots an, keine geplanten Runs. Restliste im P-7-Bericht der Welle 10. | — |
| §11.4 Pflanzeninfo und Pflanzenzustände (GP-FR-190–192, GP-API-054) | implementiert | Hover-Info, Zustandskanäle, Badge, Legende und PDF-Legende vorhanden. Der Grund „Frost" ist seit WP 8.20 lebendig: `frost_risk_of` (`domain/services/plant_state_inputs.py:20`) = Beet `frost_risk = high` **und** für die Site ist im Horizont Frost vorhergesagt (gespeicherte Prognosen, derselbe Ausdruck wie die Frühwarnung); der Grund erscheint ab dem ersten Tag des Horizonts (`frost_forecast_horizon_days`, §32.5 Nachtrag E). | #2456, #2576, #2689 |
| §12 Beetpflege (GP-FR-080–091) | teilweise | Tasks an Beeten, „für jede Pflanze", Abschluss-Übergang, Pflege-Tab, Gießdienst-Batch vorhanden. Vorschläge (GP-FR-086) mit „Annehmen"/„Verwerfen" geliefert, GP-API-040 gemountet (WP 8.17), aber **ohne Erzeuger**: kein Code legt `suggested = true` an (E-02, ADR-008 Phase 2), der Abschnitt bleibt in einer laufenden Installation deshalb verborgen. Seit Welle 10: Aufgaben an `compost`/`water_source`/`storage` im Tab „Eigenschaften“ (R-7.2, W-008, WP 10.10), eine Bodenverbesserung über „Pflege protokollieren“ schreibt dasselbe `feeding_event` wie der Aufgabenabschluss (W-007, WP 10.12), ein direkter `feeding`-Eintrag mit Produkt und Menge ebenso (#2854, §12.1). Seit #2897: Aufgaben aus Beetvorlagen (GP-FR-087) — `place-template` mit dem Opt-in `create_recurring_tasks` legt je Aufgabenvorlage eine jährlich wiederkehrende Aufgabe am neuen Beet an (Betreiberentscheidung 2026-11-11). Fehlt: Saison-Checklisten (GP-FR-091, COULD). | #2419, #2427, #2437, #2510, #2519, #2660, #2855, #2878, #2897 |
| §13 Pflegehistorie (GP-FR-100–109, 149) | teilweise | Append-only mit Supersede/Void/Redaktion, Historie-Tab, Zeitstrahl, Nacherfassung, Rückgängig im Feldmodus vorhanden. Seit Welle 8: CSV-Export (GP-FR-104; `GET /care-events?format=csv`, gemeinsames Modul `common/csv_export.py`, Schaltfläche am Historie-Tab und auf der Seite „Historie aller Beete“), Backfill M4 (GP-FR-105; `migrations/versions/v0104_care_events_backfill.py` mit der Abbildung `domain/engines/care_event_backfill_mapper.py`), täglicher Konsistenz-Job (GP-FR-105; `tasks/care_events_consistency.py`, Beat 05:10 UTC, Fenster `care_events_consistency_window_days` = 7) und `care_confirmations` → `care_event(trigger = reminder)` in derselben Transaktion (GP-FR-106; `domain/services/care_reminder_service.py`). Fehlt: Auswertungen (GP-FR-108, COULD). | #2403, #2440, #2453, #2501, #2691, #2695, #2696, #2699 |
| §14 Bewässerung (GP-FR-110–119) | teilweise | Zonen, Zuordnung, Status, Gießrunde (`by_area`/`equal`/`by_demand`, als verteilt gekennzeichnet), „Regen — übersprungen“ (ein `rainfall`-Ereignis ohne Menge je Beet, offene Gieß-Tasks bleiben offen, geht nicht in die Wasserbilanz — §32.6 Pkt. 11; Route `POST /irrigation-zones/{key}/rain-skipped` ohne eigene GP-API-Zeile), Bedarf, Verbrauch, Quellenkapazität, Felder der Wasserquelle im Eigenschaften-Panel (GP-FR-111), Konflikthinweis Zonentyp ↔ Beet, Ebene „zuletzt gegossen“ vorhanden; je Site höchstens 500 Zonen (#2525). Aktor- und HA-Durchfluss-Bindung nur über die API (der Zonen-Editor bietet nur den manuellen Durchfluss). **Fehlt:** „Jetzt bewässern“ (GP-FR-115), HA-Export der Zone (116), Bodenfeuchte-Sensor (118). | #2507, #2521, #2525, #2533, #2590, #2811 |
| §15 Boden und Substrat (GP-FR-120–127) | teilweise | Bodenprofil und Beet-Substrat (120, 121) vorhanden. Seit Welle 8: eine Bodenanalyse schreibt ihre neuesten Werte mit Methode ins Profil, `GET /locations/{key}/soil-analyses` liefert die Serien je Methode samt Hinweis „Kalkung wahrscheinlich sinnvoll“ (nur Text; GP-API-066, `domain/services/soil_analysis_service.py`), der Boden-Tab erfasst Analysen und zeigt den Verlauf pH/EC/Humus je Methode (122; `bed/SoilAnalysisDialog.tsx`, `bed/SoilAnalysisChart.tsx`); der Pflegedialog dosiert pro m² aus dem Produktdatenblatt mit Gesamtmenge (123; `care/areaDose.ts`, serverseitig `quantity_total`) und bietet die Bodenverbesserungs-Materialien (124); der Nährstoff-Hinweis `ok \| check \| likely_deficit \| insufficient_data` steht im Beetkopf (125; `domain/engines/nutrient_hint_engine.py`), ebenso der Salz-Hinweis M5 (`domain/engines/soil_salinity_hint.py`, E-17 Variante A). **Ausgeliefert inert:** alle Schwellen des Nährstoff- und des Salz-Hinweises sind `null` (keine Quelle, R-001…R-012, §32.5 Pkt. 9/10) — jedes Beet antwortet `insufficient_data`; Aktivierung ist eine Code-Konstante (`DEFAULT_CONFIG`, `DEFAULT_SALINITY_CONFIG`), kein Setting. Seit #2706: Storno/Korrektur einer Analyse rechnet das Profil in derselben Transaktion neu (§15.1, §32.5 Pkt. 11), Serien je Einheit getrennt. Offen: Mulchstatus und Nährstoffplan je Beet (126, 127, COULD). | #2402, #2701, #2730, #2731, #2733, #2737 |
| §16 Fruchtfolge und Mischkultur (GP-FR-130–139) | teilweise | Nachbarschaft aus Geometrie und manuelle Kanten (GP-API-056), Beet-Validator, Hinweise im Pflanzdialog, `NutrientDemand`-Split vorhanden. Seit Welle 8: Folgekultur-Empfehlung unter dem Zeitstrahl (133; `domain/engines/succession_recommendation_engine.py`, GP-API-064, `history/SuccessionRecommendationPanel.tsx`), Ebene „Mischkultur“ (134; `domain/services/companion_overlay_service.py` über dieselbe Engine wie der Pflanzdialog, GP-API-065, `renderer/CompanionOverlay.tsx`), Rotationsmatrix je Site (135; `domain/services/rotation_matrix_service.py` über dieselbe Zusammenführung wie GP-API-039, GP-API-063, `history/RotationMatrixPage.tsx`) und der Schalter „Fruchtfolge für dieses Beet“ im Boden-Tab (137; `bed/RotationSwitch.tsx`, über `PATCH /locations/{key}`). **Grenze:** die Rotationsmatrix hat keine Zukunftsspalten (kein Speicher für `CropRotationPlan`, §32.5 Nachtrag A). Fehlt: Problempflanzen (136, COULD), beetübergreifende Nachbarschaft und `adjacency_factor` je Location (#2425 Punkt 5). | #2348, #2428, #2440, #2452, #2544, #2690, #2693, #2697, #2710 |
| §17 UX/UI (GP-UX-001–017) | teilweise | Werkzeugleiste, Speichern-Status, Auto-Save, Legende, Info-Blase und Mini-Map vorhanden; Glossar-Erklärungen der Fachbegriffe (GP-UX-011) seit #2622 (`glossary/PlannerGlossary.tsx`, Hinweise im Pflanzdialog). GP-UX-001 seit v1.19 auf die vier vorhandenen Werkzeuge eingegrenzt (Auswahl, Hand, Beet, Gartenobjekt; #2868); aus GP-UX-071 sind alle vier Werkzeuge gebaut — Messen, Bereich, Pflanze setzen und Text (#2913; `editor/toolRegistry.ts`, Ziel `area` in `editor/tools/drawMachine.ts`, Typauswahl `editor/useAreaTypes.ts`, Klickmaschine `editor/tools/plantMachine.ts` mit Dialog `planting/PlantSlotDialog.tsx`, Klickmaschine `editor/tools/textMachine.ts` mit Dialog `editor/TextLabelDialog.tsx` und der Objektklasse `text_label`); die Leiste hat damit acht Werkzeuge, die Obergrenze von GP-UX-001. Gartengrenze zeichnen/bearbeiten ist ein Eintrag im Überlauf, kein Werkzeug der Leiste (#2890). | #2380, #2386, #2456, #2532, #2591, #2622 |
| §17.3 Editor-Arbeitsfläche (GP-UX-063–070, AC-1…AC-17) | teilweise | Seit Welle 10 (WP 10.2–10.5): Tabs Plan · Liste · Beete mit `?tab=` (`routes/GardenPlanRoute.tsx`, `routes/planTab.ts`), eine Kopfleiste mit Überlauf in fester Reihenfolge (`editor/EditorHeaderBar.tsx`, `useHeaderOverflow.ts`; Stufe 5 „kompakter Speicher-Status“ seit #2881), vertikale Werkzeug-Leiste mit Auswahlgruppe (`editor/EditorToolbar.tsx`), Zeichenfläche auf Viewport-Höhe mit Overlays (`editor/EditorWorkspace.tsx`, `ZoomOverlay.tsx`), Seitenpanel mit Tabs und Zustandsregel (`editor/SidePanel.tsx`, `sidePanelState.ts`). E2E TC-053-098…108 (gemessen: Zeichenfläche 66,9 % bei 1366 × 768). **Offen:** Messbedingungen von AC-1/AC-2/AC-6 in #2884; Befund des UI-Reviews #2905 (Dezimaltrennzeichen). Telefon seit #2904: Die Auswahlgruppe der angedockten Leiste ist eine Zeile ohne Umbruch (Ausrichten, Löschen), das Drehraster steht unter md im Überlauf „⋮“ (Einträge `garden-plan-angle-<Schritt>`); der Tooltip eines Menü-Knopfs erscheint weder über dem offenen Menü noch nach dessen Schließen (`editor/MenuTriggerTooltip.tsx`). Fokuserhalt seit #2886: Speichern, Rückgängig/Wiederholen, Herauszoomen und „Fertig“ sind im nicht verfügbaren Zustand `aria-disabled` und behalten den Fokus (`editor/unavailable.ts`); ein fokussiertes Kopfleisten-Element, das in den Überlauf wandert, gibt den Fokus an „⋮“ ab (`useHeaderFocusRescue` in `useHeaderOverflow.ts`). Hinweis-, Notiz- und Info-Zeilen (`garden-plan-draw-hint`, `garden-plan-notice`, `garden-plan-info`) stehen weiter als Zeilen über der Zeichenfläche. | #2865, #2867, #2870, #2872, #2880, #2881, #2886, #2904 |
| §18 Feldmodus (GP-UX-020–031) | teilweise | Listen-Einstieg, Beet-Sheet, Schnellprotokoll, Stepper, Quick-Planting vorhanden. Seit Welle 9 Offline (GP-UX-024): Lesen von Plan, Site-Liste, Beetliste, Beet-Summary und Beetblatt aus IndexedDB mit Banner „Stand von hh:mm“ (WP 9.2) und Puffer für Erledigt/Notiz/Foto (≤ 500 je Nutzer, FIFO-Sync, Konflikt-Dialog Behalten/Verwerfen, Rückfrage beim Abmelden; WP 9.4); Geometrie und die übrigen Chips bleiben online-only (`features/gardenPlanner/offline/`). Seit #2899 öffnet `?mode=field&bed=<key>` das Beetblatt des genannten Beets (Beet-QR, 028); ein Beet, das die Site nicht hat, meldet ein Hinweis; ohne Session führt der Login mit `returnTo` zurück (UI-NFR-014 R-009–R-011, `utils/loginReturn.ts`). GPS-Hilfe (GP-UX-026, SHOULD) seit #2898: Schalter „Meine Position“ im Tab Karte, nach dem REQ-002-Muster (Browser wird erst nach dem Einschalten gefragt, ohne Geolocation-API kein Schalter, ohne sicheren Kontext gesperrt mit Begründung, verweigert/Timeout/nicht ermittelbar als Hinweis); die Wahl wird nicht gemerkt. Ein Punkt mit Genauigkeitskreis (≥ 3 m, sonst Gerätegenauigkeit) folgt dem Gerät per `watchPosition`, solange Schalter an, Karte offen und Browser-Tab sichtbar ist. Projektion lokal äquirektangulär relativ zu `Site.gps_coordinates`, das als Mitte der Gartengrenze gilt, gedreht mit `north_angle_deg` über denselben Konverter wie der Kompass (`model/ownPosition.ts`). Hinweis statt Punkt ohne Site-GPS, bei verweigerter Freigabe, außerhalb des Ausschnitts und weiter als 500 m vom Plan; die Karte schwenkt nie auf die Position, weil der Kartenausschnitt auf dem Gerät gemerkt wird. Die Position bleibt Komponentenzustand: kein Request, kein Speicher, kein Log (`field/useOwnPosition.ts`, `field/OwnPosition.tsx`). | #2418, #2501, #2537, #2587, #2789, #2792, #2898 |
| §19 Technische Architektur (GP-NFR-001–017, 058) | implementiert | Slice, Renderer-Grenze, Stream-Transaktion, Quoten, Referenzauflösung vorhanden; `adjacency_recompute` und seit WP 8.2 `care_events_consistency` (GP-NFR-016) laufen als Celery-Tasks; M4 als v0104 (GP-NFR-015, WP 8.1). | #2332, #2353, #2376, #2377, #2428, #2691, #2695 |
| §21 API | teilweise | 59 von 59 GP-API-Zeilen sind gemountet. Zuletzt gemountet: seit v1.15 (Welle 9) GP-API-070/071 (Vorlagen-Austausch, #2799) und der Parameter `parcel_list` an GP-API-007 (#2803); ohne eigene Zeile die Route „Regen — übersprungen“ `POST /irrigation-zones/{key}/rain-skipped` (GP-FR-117, #2811) und `client_event_id` an GP-API-031/032 und den Foto-Uploads (WP 9.3, #2787); seit v1.11 GP-API-063…069 für Rotationsmatrix, Folgekultur, Mischkultur-Kanten, Bodenanalysen, Beet-Fotos, Beetliste als CSV und CSV-Import; seit v1.9 GP-API-057…062 für Neue Saison, Snapshot-Liste, Wiederherstellen, Unterlage, Vorlagen-Katalog und `place-template`; GP-API-040 `POST /tasks/{key}/accept-suggestion`, `…/dismiss-suggestion` seit WP 8.17, ohne Erzeuger von Vorschlägen. Seit #2901 trägt GP-API-001 `as_of`: die Pflanzen, die an dem Tag standen (`planted_on <= as_of < removed_on`, offenes `removed_on` zählt als stehend), ohne `phase_key` (gespeichert ist nur die heutige Phase) und mit dem daraus abgeleiteten `season_state`; Beete, Objekte, Grenze, Stellplätze, Task-Zähler und Zonen bleiben aktuell; ein Tag nach heute (UTC) ist `422 plan.as_of_in_future`. Der Jahr-Umschalter (GP-FR-077) ruft `as_of` noch nicht auf. `format=csv` an GP-API-034 seit WP 8.4. Seit Welle 10 ohne eigene GP-API-Zeile: `PUT /slots/{key}/sowing` und die Vereinzel-Route (WP 10.9, #2863), `tent_hints` in der Location-Summary (WP 10.11, #2861). Die Parameter `scope`/`keys` (GP-API-004), `target`/`offset_m` (GP-API-005) und `underlay`/`bed_list` (GP-API-007) stehen seit v1.9 in ihren Zeilen. Ohne Aufruf aus der Oberfläche (nur API): GP-API-008 (Plan-Audit), GP-API-021/022 (geplante Belegung), GP-API-056; `underlay=true` an GP-API-007 bietet der Export-Dialog nicht an. Docstring der DELETE-Route von GP-API-056 behauptet eine Neuableitung, die nicht stattfindet. GP-API-055 steht in der Zonen-Tabelle §21.6 mit vier statt drei Spalten. `POST /tasks` mit `for_each_plant` (GP-FR-081) antwortet mit einer Liste, das Schema ist deshalb `TaskResponse \| list[TaskResponse]` (OpenAPI-Union). | #2901, #2787, #2799, #2803, #2811, #2353, #2360, #2401, #2418, #2428, #2436, #2440, #2444, #2453, #2456, #2474, #2475, #2480, #2482, #2485, #2507, #2521, #2527, #2531, #2539, #2540, #2548, #2660, #2690, #2697, #2699, #2701, #2710, #2717, #2725, #2763 |
| §22 Validierung (V-01…V-24) | teilweise | Regeln im Service und im Client (GP-UX-053); `Infinity` in einer Geometrie ergibt 500 statt 422 (#2529). | #2334, #2353, #2559, #2583 |
| §23, §23.1 Import und Export (GP-FR-140–148, 170–176) | teilweise | JSON-Sicherung, PDF, SVG, Import mit `dry_run`/Snapshot, Wiederherstellen, Teil-Export, Zielwahl und Versatz, Neue Saison, Art.-15-Export vorhanden; seit Welle 8 CSV-Export der Historie (GP-FR-104) und der Beetliste mit Spaltenauswahl und Excel-Variante (145, 175; `domain/engines/bed_list_csv_engine.py`, GP-API-068, Option im Export-Dialog) und der CSV-Beetlisten-Import mit Prüfbericht im Import-Assistenten (174; `domain/services/bed_csv_import_service.py`, `common/csv_import.py`, GP-API-069, `io/BedCsvImportPanel.tsx`). Seit Welle 9: PNG clientseitig in 1×/2×/4×, Wasserzeichen optional und standardmäßig aus (144; `io/pngExport.ts`, nicht auf dem Telefon), Vorlagen-Austausch als JSON ohne Mandanten-Keys (173; GP-API-070/071, `domain/models/bed_template_exchange.py`), Parzellenliste als PDF-Zusatzseite mit Zuweisung nur per Opt-in (176; `parcel_list` an GP-API-007). Seit WP 8.28 nimmt der Import die aktuelle und die vorige `schema_version` an (GP-NFR-072). | #2436, #2444, #2539, #2548, #2583, #2586, #2699, #2725, #2763, #2782, #2796, #2799, #2803 |
| §24 Accessibility (GP-NFR-020–029) | implementiert | Listenansicht, Tastatur, Live-Region, Skip-Links, axe; GP-NFR-029 (SHOULD): jedes gezeichnete Objekt des SVG (Beet, Gartenobjekt, Pflanzplatz, Pflanze, Plangrenze) trägt `<title>` (Klasse und Name) und `<desc>` (Status, Fläche bzw. Länge, Höhe, Art, Pflanzenzahl, Phase, Zustand) in der Exportsprache, die Wurzel `role="graphics-document"` (`domain/engines/plan_svg_engine.py`); jedes Druck-PDF ist ein Tagged PDF (WeasyPrint `pdf_tags`: Strukturbaum in Dokumentreihenfolge, `/MarkInfo`, Titel, Sprache), Plan und Unterlage haben einen Alternativtext (`domain/engines/print_engine.py`, #2900). Eine Prüfung mit einem PDF-Accessibility-Checker (PAC, veraPDF) steht aus; die Kultur eines Beets nennt die `<desc>` nicht, weil das Lesemodell nur Art-Schlüssel trägt. | #2383, #2429, #2509, #2900 |
| §25 Performance (GP-NFR-030–040, 071) | teilweise | GP-NFR-030 seit #2632 (schlankeres Lesemodell) und #2778 (eingefrorener Start-Heap, `common/gc_policy.py`) erfüllt: lokal 40 Läufe p95 262 ms (Standard) bzw. 175 ms (eingefroren), der Integrationstest `test_get_plan_on_the_large_class_meets_the_spec_p95_of_300_ms` läuft ohne `xfail` (vorher gemessen 0,82 s, #2526); der Wert gilt für einen Prozess nach dem Start unter der Freeze-Regel. Lighthouse misst die Plan-Route ohne Backend (Hinweis in `lighthouserc.json`). Das INP-Messprofil (GP-NFR-071) läuft seit WP 8.29 als E2E (`tests/e2e/test_req053_inp_profile.py`, Auswahl, Drag-Start, Zoom, Pinch, Feldmodus mit CPU 4×); die Grenzen INP ≤ 200 ms und Pinch ≤ 33 ms sind **advisory** (Warnung, kein Fehlschlag). | #2520, #2694 |
| §26 Sicherheit (GP-NFR-050–057) | implementiert | Mandanten-Negativtests je Endpunkt, ZAP-Negativtests, Import-/Restore-Härtung; offene Folge-Issues #2545, #2569. | #2373, #2541, #2583 |
| §27 Observability (GP-NFR-060–064) | implementiert | Logs und Metriken vorhanden; der Konsistenz-Job meldet Laufzeit und Trefferzahl als Structlog-Event, zählt `care_events_consistency_backfilled_total{source}` und warnt ab 101 Treffern je Lauf (GP-NFR-063; `domain/services/care_event_consistency_service.py`, `ALERT_THRESHOLD = 100`). | #2353, #2428, #2695 |
| §28 MVP (MUST, „MVP = ja“) | teilweise | Offene MUST-Punkte (Stand v1.17, je mit Rest-Issue): Slot-Kopie beim Duplizieren (GP-FR-025, Betreiberfrage in #2759). Erledigt seit v1.11: `Ctrl/Cmd+D` (WP 9.14), Frost-Grund (WP 8.20), Glossar (#2622), GP-NFR-030 (#2778), Slot-Raster (GP-FR-154, #2893), Space+Drag und Shift-Faktor (GP-FR-010, #2892), Beet räumen in der Oberfläche (GP-FR-055, #2891), Gartengrenze in der Oberfläche (UC-01, GP-FR-019/032, #2890). GP-ACC-054/055 sind seit v1.8 belegt; die Label-Platzierung (GP-UX-047) ist seit #2600 umgesetzt. | siehe Zeilen oben |
| §30 Akzeptanzkriterien | teilweise | 64 von 64 Kriterien mit Test belegt (generierte Matrix `spec/e2e-testcases/GP-ACC-matrix.md`, `GP-ACC-gaps.json` leer seit der Abnahme Welle 9); ob ein Test ein Kriterium vollständig beweist, bleibt eine Review-Frage. Status „teilweise“, weil offene MUST-Reste aus §28 kein GP-ACC tragen. | #2546, #2544, #2757 |
| Welle 7, SHOULD-Zeilen (GP-FR/GP-API/GP-UX, §34) | teilweise | Generierte Matrix `spec/e2e-testcases/GP-REQ-wave7-matrix.md` (`scripts/gp_acc_matrix.py`, Guard `tests/unit/guards/test_req053_acceptance_matrix.py`): 37 Zeilen, alle mit mindestens einem Test, seit Welle 9 (#2811) nur noch eine mit benannter Teil-Lücke in `GP-REQ-wave7-gaps.json` — GP-FR-025 (Slot-Kopie beim Duplizieren, Entscheidung bei #2759); GP-FR-111 und GP-FR-117 sind geschlossen, TC-053-047 ist automatisiert (#2812), TC-053-027 (Beet räumen) seit #2891 (`tests/e2e/test_req053_planting.py`). Ob ein Test eine Zeile vollständig beweist, bleibt eine Review-Frage. | #2491, #2492, #2493, #2599, #2602, #2811, #2812 |
| Welle 8 (GP-FR/GP-API/GP-UX/GP-NFR, §34) | teilweise | Generierte Matrix `spec/e2e-testcases/GP-REQ-wave8-matrix.md` (`scripts/gp_acc_matrix.py`, Guard `tests/unit/guards/test_req053_acceptance_matrix.py`): 37 Zeilen, alle mit mindestens einem Test (GP-NFR-072 seit WP 8.28, #2782), vier davon mit benannter Teil-Lücke in `GP-REQ-wave8-gaps.json` — GP-FR-086 (kein Erzeuger von Vorschlägen), GP-FR-125 (alle Schwellen `null`, inert), GP-FR-135 (keine Zukunftsspalten), GP-FR-168 (kein Erben vom Site-Hang). Nicht automatisiert: TC-053-066 (Nährstoff-Hinweis mit Schwelle — die Schwellen sind Code-Konstanten; Regeltabelle im Unit-Test belegt). Reviews je Paket: §32.5 Pkt. 16. Ob ein Test eine Zeile vollständig beweist, bleibt eine Review-Frage. | #2768, #2675 |
| Welle 9 (§34, UI-NFR-012 v2.4) | implementiert | WP 9.1–9.16 gemergt: ein Workbox-Service-Worker unter `/sw.js` mit übernommenem Web Push, App-Shell-Precache, API-`GET`-Allowlist im Namensraum `kp:{user_key}:{tenant_key}`, Leerung bei Logout und Tenant-Wechsel, Kill-Switch `PWA_CACHING_ENABLED`, nginx `no-store` für `/sw.js` und `/manifest.json`, CSP `worker-src`/`manifest-src 'self'` (9.1); Offline-Lesen aus IndexedDB `kp-plan-cache` (9.2); `client_event_id`-Idempotenz mit Migration `v0106` (9.3); Schreibpuffer `kp-write-queue` für Erledigt/Notiz/Foto (9.4); Renderer-Messung D-01 (9.6) und `KonvaPlanRenderer` ab 3 000 Objekten als eigener Lazy-Chunk ≤ 200 KB gzip (9.7); PNG (9.8); Vorlagen-Austausch (9.9); Parzellenliste (9.10); Standort-Flags (9.11); `nearest_water_source_m` (9.12); „Regen — übersprungen“ und `by_demand` (9.13); `Ctrl/Cmd+D` und Felder der Wasserquelle (9.14); E2E TC-053-084…097 und TC-053-047 (9.15/9.16). **Abnahme (WP 9.17):** generierte Matrix `spec/e2e-testcases/GP-REQ-wave9-matrix.md` (Guard `tests/unit/guards/test_req053_acceptance_matrix.py`) — 16 REQ-053-Zeilen und 35 UI-NFR-012-Kriterien, alle mit Test, vier Teil-Lücken in `GP-REQ-wave9-gaps.json` (GP-FR-025, R-009, R-020, R-060; alle bei #2759). Der API-Cache des Service Workers bleibt latent, weil das Backend `Cache-Control: no-store` sendet (MT-044, §32.6 Pkt. 13). Sicherheitsnotiz: §32.6 Pkt. 16. P-7: `.audits/prod-release/2026-11-09-req053-p7-wave9.md` (kein Deploy, E-07). | #2786, #2787, #2789, #2791, #2792, #2793, #2796, #2797, #2799, #2802, #2803, #2808, #2811, #2812, #2757 |
| Welle 10 (§34: Arbeitsfläche, Indoor-Grundriss, Domänen-Reste) | teilweise | WP 10.1–10.14 gemergt (#2850, #2855, #2861, #2863, #2865, #2867, #2870, #2872, #2874, #2875, #2877, #2878, #2880, #2881, #2883); Migration `v0108_location_tent_fields` (WP 10.11, additiv). **Abnahme (WP 10.15):** generierte Matrix `spec/e2e-testcases/GP-REQ-wave10-matrix.md` (Guard `tests/unit/guards/test_req053_acceptance_matrix.py`) — 34 Zeilen (GP-UX-063…070, GP-FR-180…183, GP-UX-049 Welle-10-Teil, AC-1…AC-17 ohne AC-11, W-005/007/008/015/016), seit v1.19 alle 34 mit Test, davon 5 mit benannter Teil-Lücke (GP-UX-049, AC-1, AC-6 bei #2884; W-015 bei #2888; W-016 bei #2889); `GP-REQ-wave10-gaps.json`. E2E TC-053-098…115. Restliste: §34 Zeile 10. P-7: `.audits/prod-release/2026-11-11-req053-p7-wave10.md` (kein Deploy, E-07). | #2850, #2855, #2861, #2863, #2865, #2867, #2870, #2872, #2874, #2875, #2877, #2878, #2880, #2881, #2883, #2836 |

---

## Inhalt

Implementierungsstand (vor §1) · 1. Executive Summary · 2. Ziel und Scope · 3. Ausgangssituation · 4. Benutzergruppen · 5. Personas · 6. Use Cases · 7. Fachliches Domänenmodell · 8. Funktionale Anforderungen (Übersicht) · 9. Grafischer Garteneditor · 10. Beetverwaltung · 11. Pflanzplanung · 12. Beetpflege · 13. Pflegehistorie · 14. Bewässerung · 15. Boden/Nährstoffe · 16. Fruchtfolge/Mischkultur · 17. UX/UI (17.3 Editor-Arbeitsfläche) · 18. Mobile Nutzung · 19. Technische Architektur · 20. Datenmodell · 21. API · 22. Validierung · 23. Import/Export (23.1 Erweiterungen) · 24. Accessibility · 25. Performance · 26. Sicherheit · 27. Observability · 28. MVP · 29. Future Features · 30. Akzeptanzkriterien · 31. Risiken · 32. Offene Fragen · 33. Entscheidungsvorlagen · 34. Implementierungs-Roadmap · Anhang A: GitHub-Issue-Kandidaten

**ID-Schema dieses Dokuments.** Anforderungen tragen das Präfix `GP-` (Garden Planner), damit sie nicht mit den Repository-weiten Dokument-IDs kollidieren (`spec/nfr/NFR-012` ist ein Dokument, `GP-NFR-012` eine Anforderung in diesem Dokument):

| Präfix | Bedeutung | Beispiel |
|--------|-----------|----------|
| `GP-FR-nnn` | Functional Requirement | GP-FR-010 |
| `GP-NFR-nnn` | Non-Functional Requirement | GP-NFR-003 |
| `GP-UX-nnn` | UX Requirement | GP-UX-007 |
| `GP-API-nnn` | API Requirement | GP-API-002 |
| `GP-ACC-nnn` | Acceptance Criterion | GP-ACC-012 |

Prioritäten nach MoSCoW: **MUST** (MVP-Pflicht), **SHOULD** (erste Folgeversion), **COULD** (bei Gelegenheit), **WON'T** (bewusst nicht in diesem Vorhaben). Die Spalte „MVP" in den Tabellen bedeutet: Teil des in §28 abgegrenzten MVP.

---

## 1. Executive Summary

Kamerplanter kennt heute Standorte als **Baum** (Site → Location → Slot), nicht als **Fläche**. Ein Beet ist eine Location vom Typ `bed` mit einer Quadratmeterzahl (`area_m2`) und einem undokumentierten Maß-Tupel (`dimensions`); ein Pflanzplatz ist ein Slot mit einer Integer-Rasterposition `(row, col)`. Wo ein Beet im Garten liegt, wie es geschnitten ist, was daneben steht und wo im Beet die einzelne Pflanze wächst, weiß das System nicht. Genau das braucht die Zielgruppe der Freiland- und Gemeinschaftsgärtner (ZG-002, ZG-004), die ihre Saison am Schreibtisch plant und mit dem Smartphone im Beet steht.

Diese Anforderung erweitert das vorhandene Standortmodell um ein **metrisches Geometriemodell** (Meter, nicht Pixel) und stellt darauf einen **grafischen Gartenplan** bereit, in dem Gartenflächen, Beete, Wege, Gebäude, Bäume, Gewächshäuser und Wasserquellen maßstäblich gezeichnet, verschoben, gedreht und skaliert werden. Beete werden darin mit dem bestehenden Pflanzdurchlauf-Modell (REQ-013) bepflanzt: Pflanzabstand und Reihenabstand erzeugen Pflanzpositionen, die als Slots persistiert und als Pflanzen auf dem Plan dargestellt werden. Pflegeaufgaben hängen am Beet und an der Pflanze (REQ-006, REQ-022) und münden in ein **einheitliches, revisionssicheres Pflegeprotokoll** (`care_events`), das die heute auf vier Collections verteilten Pflegeereignisse an einem Ort nachvollziehbar macht.

Drei Grundsätze tragen den Entwurf: **Das Domänenmodell führt, das Canvas folgt** (die Rendering-Bibliothek ist hinter einer Renderer-Grenze austauschbar, §19.4); **reale Maße sind die persistente Wahrheit** (Pixel entstehen erst beim Zeichnen, §9.2); **keine Parallelarchitektur** (Garten = Site, Beet = Location, Pflanzposition = Slot, Pflegeaufgabe = Task — es werden nur drei neue Collections eingeführt, §7.1).

Der MVP (§28) umfasst: Gartenfläche und Beete zeichnen und bearbeiten, metrisches Raster mit Snap, Speichern über eine transaktionale Batch-API mit Konfliktschutz, Pflanzdurchläufe auf Beeten mit automatischer Positionsberechnung, Pflanzendarstellung, Pflegeaufgaben am Beet mit Erledigung und Historie, PDF-Export mit Maßstab und ein mobiler **Feldmodus**. Bewässerungszonen, Boden-Historie, Fruchtfolge-/Mischkultur-Overlays, GeoJSON und Sonnen-/Schattenberechnung sind spezifiziert, aber bewusst nachgelagert (§28.3, §29).

---

## 2. Ziel und Scope

### 2.1 Ziel

Der Nutzer bildet seine reale Gartenanlage **maßstäblich oder zumindest metrisch plausibel** ab und nutzt diese Abbildung als Oberfläche für das fachliche Gartenmodell: Beete anlegen, bepflanzen, pflegen, dokumentieren, auswerten. Die Grafik ist ein **Zugang** zum Modell, kein eigenständiger Zeicheneditor.

### 2.2 Im Scope

- Metrisches Geometriemodell für Site (Gartengrenze), Location (Beete, Bereiche, Gewächshäuser) und Slot (Pflanzpositionen im Beet) sowie nicht bepflanzbare Gartenobjekte (Weg, Rasen, Gebäude, Baum, Strauch, Mauer/Zaun, Wasserquelle, Kompost, Lager, Sonstiges).
- Webbasierter Editor mit Zoom, Pan, Auswahl, Mehrfachauswahl, Verschieben, Drehen, Skalieren, Polygon-Punktbearbeitung, Duplizieren, Löschen, Raster, Snap, Undo/Redo, Tastaturbedienung, Touch.
- Beetverwaltung mit Beettypen, Vorlagen, Bodenprofil, Status, Bepflanzungsübersicht (geplant / aktiv / historisch).
- Pflanzplanung im Beet über PlantingRuns: Pflanzabstand, Reihenabstand, Pflanztiefe, Reihen, Zonen, freie Positionen, automatische Positionsberechnung, Korrektur der tatsächlichen Position.
- Beetpflege: Aufgabenkatalog, einmalige/wiederkehrende/vorgeschlagene Aufgaben, Erledigung, einheitliches Pflegeprotokoll.
- Bewässerungszonen als fachliches Modell (Integration mit REQ-018-Aktorik vorbereitet).
- Boden/Substrat-Bezug des Beets; Fruchtfolge- und Mischkultur-Anbindung als fachliche Anforderung.
- API-first (REST/OpenAPI), ArangoDB-Persistenz, Import/Export (JSON-Sicherung, PDF, SVG, PNG, CSV; GeoJSON gestrichen — O-21 revidiert in v1.4).
- Responsive Nutzung inkl. Feldmodus für Smartphone/Tablet im Garten.

### 2.3 Nicht im Scope

- Ein allgemeiner CAD-/GIS-Editor (keine Layer-Verwaltung jenseits der fachlichen Objektklassen, keine Höhenmodelle, kein Georeferenzieren von Luftbildern im MVP).
- Ein zweites Positionsmodell für Indoor: Growzelte, Regale und Beete laufen auf **demselben** Slot-Geometriemodell (§9.2a, Entscheidung O-01). Ebenen-Stapel eines Regals und Topfgrößen-Raster bleiben außerhalb; ein Zelt ist eine Location mit Rechteck-Geometrie und Punkt-Slots. **Ab v1.3** gibt es zusätzlich einen Wohnungs-/Raum-Grundriss mit denselben Zeichenfunktionen wie der Garten (§9.8, SHOULD, O-22).
- Automatische Bewässerungssteuerung (REQ-018 bleibt zuständig; hier nur Zonen-Modell und Verknüpfung).
- Sonnen-/Schattenberechnung, KI-Pflanzplanung, Ertragsplanung (§29).
- Änderungen am Tenant-, Rollen- oder Rechtemodell (REQ-024/REQ-049 gelten unverändert).

### 2.4 Abgrenzung zu bestehenden Dokumenten

| Dokument | Liefert | Verhältnis zu REQ-053 |
|----------|---------|-----------------------|
| **REQ-002** | Site/Location/Slot, LocationTypes, `adjacent_to`, `bed_*`-Felder im Business Case | **Bleibt Quelle der Hierarchie.** REQ-053 ergänzt `geometry` und `soil_profile` auf Location, `geometry` auf Slot, `plan` auf Site und löst die `bed_*`-Felder in das Geometriemodell auf (§20.8). |
| **REQ-013** | PlantingRun, Entry mit `spacing_cm`, `run_at_location`, Batch-Erzeugung mit `assign_to_slots` | **Bleibt Quelle des Durchlaufs.** REQ-053 ergänzt `row_spacing_cm`, `depth_cm`/`depth_kind`, `layout_strategy` am Entry und ein Layout-Verfahren, das Slots mit Geometrie erzeugt (§11). |
| **REQ-006 / REQ-022 / ADR-008** | Task-Modell, Erinnerungen, Abschluss-Übergang | **Bleiben Quelle der Aufgabe.** REQ-053 ergänzt Kategorien und macht `entity_type = location` zur ersten Klasse; der Abschluss-Übergang schreibt zusätzlich einen `care_event` (§12, §13). |
| **REQ-014 / REQ-004 / REQ-010** | `watering_events`, `feeding_events`, `treatment_applications` | **Bleiben Quelle der Fachdaten.** `care_events` referenziert sie, dupliziert sie nicht (§13.2). |
| **REQ-028 / REQ-001** | Mischkultur-Graph, Fruchtfolge-Validator (slot-basiert) | REQ-053 leitet `adjacent_to` aus Slot-Geometrie ab und liefert die Beet-Ebene für den Validator (§16). |
| **REQ-032** | `LOCATION_OVERVIEW`-Druck, „tabellarisch oder visueller Grundriss" | REQ-053 liefert den visuellen Grundriss (§23). |
| **REQ-018 / REQ-037** | Aktoren inkl. `irrigation_valve`, ET0-Bedarf je Run | REQ-053 führt `irrigation_zones` ein, die Aktoren und Bedarf bündeln (§14). |

---

## 3. Ausgangssituation

### 3.1 Was heute existiert (gemessen am Code, Stand 2026-10-04)

| Bereich | Befund | Quelle |
|---------|--------|--------|
| Hierarchie | `Site` → `Location` (rekursiv, `parent_location_key`, `depth`, `path`) → `Slot`; Edges `contains`, `has_slot`, `placed_in` | `src/backend/app/domain/models/site.py:41-156`, `data_access/arango/collections.py` |
| Site-Maße | `total_area_m2`, `gps_coordinates`, `timezone`, Frostdaten, `water_config` (Wasser**qualität**, keine Infrastruktur) | `site.py:105-156` |
| Location-Maße | `area_m2` (Pflicht), `dimensions: tuple[float,float,float] = (0,0,0)` ohne dokumentierte Semantik/Einheit, `orientation` nur `north/south/east/west`, `irrigation_system` (Enum), `tank_key`, `frost_exposed` | `site.py:65-102`, `common/enums.py:375,458` |
| Slot | `slot_id` (`TENT01_A1`), `position: tuple[int,int]` (Rasterzelle), `capacity_plants` 1–20, `currently_occupied` | `site.py:41-62` |
| LocationTypes | 10 Seeds: `garden`, `greenhouse`, `building`, `room`, `balcony`, `terrace`, `tent`, `bed`, `shelf`, `container`; nutzerdefinierbar | REQ-002 §2, `src/backend/app/migrations/seed_location_types.py` |
| Pflanzdurchlauf | `PlantingRun` (`planned/active/harvesting/completed/cancelled`), `PlantingRunEntry.spacing_cm` (5–300), `assign_to_slots` bei Batch-Erzeugung; **keine** geplante Position | `domain/models/planting_run.py:18-45` |
| Pflanze | `PlantInstance` mit `site_key/location_key/slot_key`, `planted_on`, `removed_on`, `termination_type`, `photo_refs`; kein Statusfeld | `domain/models/plant_instance.py:8` |
| Aufgaben | `Task` mit `entity_type/entity_key`, `category` (16 Werte inkl. `watering`, `pest_control`, `monitoring`, `cleaning`), `recurrence_rule`, `photo_refs`, Audit-Edge; `has_task` erlaubt bereits `locations` als Quelle | `domain/models/task.py:128`, `collections.py` |
| Pflegeprotokoll | **verteilt**: `watering_logs`, `watering_events`, `feeding_events`, `care_confirmations`, `treatment_applications`, Task-Completion — kein gemeinsamer Ort für was/wann/wer/warum/Produkt/Menge/Ergebnis | §3 Backend-Befund |
| Fruchtfolge/Mischkultur | `CropRotationValidator.validate_planting(slot_key, species_key, *, tenant_key)`, `CompanionPlantingEngine` über `adjacent_to`; **kein** API-Endpunkt, der `adjacent_to` setzt | `domain/engines/crop_rotation_validator.py:33`, `graph_repository.py:206` |
| Bewässerung | `irrigation_demands` (ET0, je Site+Run); Aktoren mit `irrigation_valve`/`pump` an Locations; **keine** Zone | `domain/models/irrigation_demand.py`, `actuator.py:114` |
| Boden | REQ-004 nennt `soil_type`, `soil_ph`, `soil_analysis_date`, aber **kein Träger-Entity**; Substrat nur je Slot (`filled_with`) | REQ-004 §1, REQ-019 |
| Druck | WeasyPrint + Jinja2, `PrintEngine.render_pdf`, Endpunkte `/print/*`; kein SVG, kein CSV-Export für Standorte | `domain/engines/print_engine.py:132` |
| Nebenläufigkeit | Kein `version`/ETag auf CRUD-Ressourcen; `_rev`-Prüfung nur an der Tagebuch-Lease (409 `conflict.concurrent_update`) | `plant_diary_repository.py:292`, `common/exceptions.py` |
| Batch-Muster | `BatchResponse{succeeded, failed}` (Teilerfolg) bei Tasks; keine Transaktion | `api/v1/tasks/schemas.py:349` |
| Frontend | React 19, MUI 9, Redux Toolkit (Slices + Thunks, **kein** RTK Query), `react-grid-layout` (Dashboard), `recharts`; **keine** Canvas-/SVG-/Gesten-Lib, **kein** Undo/Redo, **kein** Offline-Cache; Bundle-Budget 400 KB gzip (Ziel 300, Ist 343) | `src/frontend/package.json`, `bundle-budget.json`, `DashboardEditGrid.tsx:31` |
| Standort-UI | Baum (`SimpleTreeView`), Slot-Tabelle; keine 2D-Darstellung | `src/frontend/src/pages/standorte/` |
| Routing | Flache Routen `standorte/sites/:key` …; Tenant-Präfix setzt der `tenantClient` (`/t/{slug}`) | `src/api/client.ts:316` |
| Mobil | Kiosk-Theme mit Touch-Zielen 64/72 px; keine Pinch/Pan-Gesten | `src/kiosk/kioskTheme.ts:14` |

### 3.2 Korrektur der Vorgabe aus dem Auftrag

Der Auftrag nennt als Zielarchitektur „Go Backend, Vue.js, Tailwind". **Das trifft auf Kamerplanter nicht zu.** Verbindlich sind `spec/stack.md` und NFR-001: Python 3.14 / FastAPI / Celery, ArangoDB + TimescaleDB + Valkey, React 19 / TypeScript 6 / MUI 9 / Redux Toolkit, Vite, Kubernetes/Helm. Vue erscheint in `stack.md` nur als verworfene Alternative. Die übrigen Vorgaben (API-first, versionierte DTOs, OpenAPI, Containerisierung, Kubernetes, responsive, englische Quelltexte, Garten-/Boden-orientiertes UI, Pflanzen/Pflanzdurchläufe/Phasen als zentrale Objekte) gelten unverändert und werden hier eingelöst. Wo der Auftrag „Vue-Komponenten" sagt, ist „React-Komponenten" zu lesen.

### 3.3 Was fehlt (Lückenliste)

1. Räumliche Lage und Form von Locations und Slots (Geometrie in Metern).
2. Nicht bepflanzbare Gartenobjekte (Weg, Gebäude, Baum, Wasserquelle …).
3. Plan-Orientierung (Nordwinkel) und Maßstab.
4. Ein Editor samt Zustandsverwaltung (Undo/Redo, Konfliktschutz).
5. Geplante Pflanzpositionen vor dem Anlegen der Pflanzen.
6. Beet-Bodenprofil als Träger für REQ-004-Felder.
7. Einheitliches Pflegeprotokoll auf Beet-Ebene.
8. Bewässerungszonen.
9. Automatische Ableitung von `adjacent_to` aus Positionen.
10. Visueller Grundriss im Druck (REQ-032 §2.5).

---

## 4. Benutzergruppen

| Gruppe | Zielgruppen-Dokument | Bezug zur Gartenplanung |
|--------|---------------------|-------------------------|
| Freiland-/Gemüsegärtner | `spec/target-audiences/ZG-002_Freilandgaertner.md` | Primär. 1–5 Beete, 10–100 m², Winterplanung am Desktop, Gartenarbeit mit Tablet/Smartphone. Beetplanung dort als „kritisch" markiert. |
| Gemeinschaftsgarten (Leitung + Mitglied) | `ZG-004_Gemeinschaftsgarten.md` | Primär. Viele Parzellen, Gießdienst, Lesezugriff für Beobachter, Zuweisung von Beeten an Mitglieder (`location_assignments`, Koordination, keine Schreibgrenze — REQ-049 §3.5). |
| Gewächshaus-Betrieb | `ZG-005`, `UZG-005` | Sekundär. Tische/Beete im Gewächshaus, Zonen, Bewässerung. |
| Marktgärtner | `UZG-002` | Sekundär. Reihenkulturen, Sukzession, Flächenertrag. |
| Bildungseinrichtungen | `UZG-003` | Sekundär. Schulgarten, viele Lesende, wenige Schreibende. |
| Casual-Hobby-Nutzer | `UZG-001` | Tertiär. Balkon/Terrasse mit Kübeln; profitiert vom Plan nur, wenn er in Minuten entsteht (Vorlagen, §10.4). |
| Cannabis-Indoor-Grower | `ZG-001` | Zelt/Regal laufen auf demselben Geometriemodell (§9.2a); Wohnungs-Grundriss §9.8 (SHOULD). |

---

## 5. Personas

Die Personas sind den bestehenden Zielgruppen-Dokumenten entnommen und um den Planungsbezug ergänzt.

**Sabine, 52, Lehrerin (ZG-002).** 60 m² Gemüsegarten hinter dem Haus, fünf Beete, Kompost, samenfeste Sorten. Plant im Januar am Laptop: Welches Beet bekommt dieses Jahr die Starkzehrer? Sie zeichnet die Beete einmal nach Maß (3,0 × 1,2 m), weil sie wissen will, wie viele Tomaten bei 60 cm Abstand hineinpassen. Im Mai steht sie mit dem Handy im Beet, trägt ein, dass Beet 3 gemulcht ist, und korrigiert, dass die Zucchini doch am Rand gelandet ist.

**Tom, 42, Sozialarbeiter (ZG-004, Leitung).** Gemeinschaftsgarten mit 30 Parzellen in einem Hinterhof. Braucht den Gesamtplan, um Parzellen zuzuweisen, den Gießdienst nach Zonen zu organisieren und neuen Mitgliedern zu zeigen, wo ihre Parzelle liegt. Zeichnet Wege, Wasserhähne, Komposthaufen und den Geräteschuppen ein, damit der Plan auch als Orientierung dient. Will den Plan als PDF am Gartentor aushängen.

**Aisha, 28, Studentin (ZG-004, Mitglied).** Erste eigene Parzelle, keine Erfahrung. Öffnet auf dem Smartphone ihre Parzelle, sieht die offenen Aufgaben dieser Woche, hakt „Gießen" ab und fotografiert einen Schädlingsverdacht. Sie bearbeitet die Geometrie nie; sie braucht große Schaltflächen und wenig Auswahl.

**Jonas, 35, Gärtnermeister (UZG-005).** Zwei Folientunnel mit je vier Beetreihen, Tropfbewässerung in sechs Zonen. Pflanzt in Reihen mit festem Reihen- und Pflanzabstand, nutzt Sukzession, will Zonen an Home-Assistant-Ventile koppeln. Für ihn zählt die Reihenlogik, nicht die Freihandpositionierung.

---

## 6. Use Cases

| ID | Use Case | Akteur | Vorbedingung | Hauptablauf (kurz) | Ergebnis | MVP |
|----|----------|--------|--------------|--------------------|----------|-----|
| UC-01 | Garten anlegen und Fläche definieren | Gärtner | Site mit `type ∈ {outdoor, greenhouse, balcony}` existiert oder wird angelegt | Plan öffnen → Gartengrenze als Rechteck oder Polygon zeichnen → Nordrichtung setzen → speichern | `Site.plan` mit `boundary`, `north_angle_deg`, `plan_revision = 1` | ja |
| UC-02 | Beet zeichnen | Gärtner | UC-01 | Werkzeug „Beet" → Rechteck/Kreis/Polygon ziehen → Name, Beettyp → speichern | Location `location_type = bed`, `geometry`, `area_m2` berechnet | ja |
| UC-03 | Beet verschieben/drehen/skalieren | Gärtner | UC-02 | Auswahl → Griff ziehen oder Eigenschaftenpanel-Werte → speichern | Geometrie aktualisiert, Slots folgen (beet-lokal) | ja |
| UC-04 | Gartenobjekt platzieren | Gärtner | UC-01 | Werkzeug (Weg, Baum, Gebäude, Wasserquelle …) → zeichnen → speichern | `garden_objects`-Dokument | ja (Teilmenge, §9.5) |
| UC-05 | Beet bepflanzen (Durchlauf) | Gärtner | UC-02, Spezies vorhanden | Beet wählen → „Bepflanzen" → Spezies/Sorte, Menge, Pflanzabstand, Reihenabstand, Layout → Vorschau → Durchlauf anlegen | `PlantingRun` (`planned`), Entries, Slots mit Geometrie, `run_planned_at`-Edges | ja |
| UC-06 | Geplante Pflanzung ausführen | Gärtner | UC-05 | Durchlauf starten → Pflanzen erzeugen (REQ-013 `create-plants`) | `PlantInstance` je Slot, `placed_in`, Run `active` | ja |
| UC-07 | Pflanzposition korrigieren | Gärtner | UC-06 | Pflanze auf Plan wählen → verschieben (Desktop: Drag; Mobil: Long-Press + Drag oder Koordinaten) | `Slot.geometry` aktualisiert, Audit | ja |
| UC-08 | Pflegeaufgabe am Beet anlegen | Gärtner | UC-02 | Beet → „Aufgabe" → Kategorie, Fälligkeit, Wiederholung | `Task` mit `entity_type = location` | ja |
| UC-09 | Pflegeaufgabe im Garten erledigen | Mitglied | UC-08, Mobilgerät | Feldmodus → Beet antippen → Aufgabe → „Erledigt" → optional Notiz, Produkt, Menge, Foto | Task `completed`, `care_event` geschrieben | ja |
| UC-10 | Pflegehistorie einsehen | Alle Rollen | Ereignisse vorhanden | Beet → Tab „Historie" → Filter Zeitraum/Kategorie | Chronologische Liste aus `care_events` + Pflanzungen | ja |
| UC-11 | Plan drucken | Alle Rollen | UC-01 | „Drucken" → Format, Maßstab → PDF | Maßstäbliches PDF mit Maßstabsleiste, Nordpfeil, Legende | ja |
| UC-12 | Plan sichern/wiederherstellen | Leitung | UC-01 | Export JSON → später Import in dieselbe oder andere Site | Vollständige Wiederherstellung der Geometrien | ja (Export), SHOULD (Import) |
| UC-13 | Bewässerungszone definieren | Gärtner | UC-02, UC-04 (Wasserquelle) | Zone anlegen → Beete zuordnen → Typ, Quelle, optional Aktor | `irrigation_zones`, `Location.irrigation_zone_key` | nein (SHOULD) |
| UC-14 | Bodenprofil pflegen | Gärtner | UC-02 | Beet → „Boden" → Bodenart, pH, Humus, Drainage; Analyse als Ereignis | `Location.soil_profile`, `care_event(category = soil_analysis)` | teilweise (Profil ja, Analyse-Ereignis SHOULD) |
| UC-15 | Fruchtfolge-/Mischkultur-Hinweis beim Bepflanzen | Gärtner | UC-05, Graphdaten | Bei Spezieswahl: Validator läuft über Beet-Slots → Warnung mit Grund | Hinweis im Dialog, kein Blocker | nein (SHOULD) |
| UC-16 | Beet aus Vorlage anlegen | Gärtner | Vorlagen vorhanden | Werkzeug „Vorlage" → Hochbeet 2 × 1 m → platzieren | Location + ggf. Reihen-Slots | nein (SHOULD) |
| UC-17 | Mehrere Objekte gruppieren und gemeinsam verschieben | Gärtner | ≥ 2 Objekte | Mehrfachauswahl → Verschieben | Batch-Update | ja (Mehrfachauswahl), Gruppen-Persistenz WON'T |

---

## 7. Fachliches Domänenmodell

### 7.1 Zuordnung der geforderten Objekte

Die im Auftrag genannten Objekte werden nicht 1:1 als Entitäten eingeführt, sondern auf das bestehende Modell abgebildet. Entscheidend: **drei neue Collections** (`garden_objects`, `care_events`, `irrigation_zones`), alles andere sind additive Felder und Edges.

| Gefordertes Objekt | Abbildung | Begründung |
|--------------------|-----------|------------|
| Garden | **`Site`** (bestehend) mit neuem eingebetteten `plan` (Grenze, Nordwinkel, Revision) | Der Garten ist bereits die Wurzel der Hierarchie; GPS, Klimazone, Frostdaten, Saison-Zustand hängen daran. |
| GardenArea | **`Location`** (bestehend) mit `geometry`; `location_type` z. B. `garden`, `greenhouse`, `terrace`, nutzerdefiniert „Nutzgarten", „Vorgarten" | Rekursive Locations decken Bereiche ab; ein Bereich kann Beete enthalten (`contains`). |
| Bed | **`Location`** (bestehend) mit `location_type = bed` (Bodenbeet) bzw. neuen Seeds `raised_bed`, `planter`, `greenhouse_bed`, `cold_frame`; `geometry`, `soil_profile`, `bed_status` | REQ-002 sieht `bed_type` vor; als LocationType ist es filterbar, ikonisierbar und nutzererweiterbar. |
| PlantingArea | **`Slot`** (bestehend) mit `geometry` (Punkt oder Polygon, beet-lokal) und `slot_role ∈ {position, zone, row}` | Slot ist bereits das Ziel von `placed_in`; `capacity_plants` erlaubt Zonen mit mehreren Pflanzen. |
| Path, Lawn, Greenhouse*, Tree, Shrub, Building, Wall/Fence, WaterSource, IrrigationArea*, CompostArea, StorageArea, OtherGardenObject | **`GardenObject`** (neu, Collection `garden_objects`) mit `object_type`-Enum | Nicht bepflanzbare Objekte brauchen keine Slots, keine Tasks-Kaskade, keine Fruchtfolge. Eine Collection mit Typ-Enum statt zehn Collections. (*Gewächshaus ist, wenn darin gepflanzt wird, eine Location vom Typ `greenhouse`; als reine Kulisse ein GardenObject `greenhouse_shell` — §7.3. *IrrigationArea ist keine Geometrie, sondern eine Zone, §14.) |
| Plant | **`PlantInstance`** (bestehend) | unverändert; Position ergibt sich aus dem Slot |
| PlantingRun | **`PlantingRun`** + **`PlantingRunEntry`** (bestehend) mit zusätzlichen Layout-Feldern | §11 |
| MaintenanceTask | **`Task`** (bestehend) | `entity_type = location` ist über `has_task` bereits zulässig; Kategorien werden ergänzt |
| MaintenanceEvent | **`CareEvent`** (neu, Collection `care_events`) | Einheitliches, revisionssicheres Protokoll; referenziert die Fachereignisse (§13) |
| Tree/Shrub als **Pflanze** | Wenn ein Baum gepflegt werden soll (Obstbaum): `PlantInstance` in einem eigenen Slot einer Location (`location_type = orchard` o. ä.); als Kulisse: `GardenObject(object_type = tree)` | Beides ist zulässig; §7.3 definiert die Regel |

### 7.2 Beziehungen

```
Site ──contains──▶ Location ──contains──▶ Location (Beet) ──has_slot──▶ Slot
 │                                            │                          ▲
 │ has_garden_object                          │ run_at_location          │ placed_in
 ▼                                            ▼                          │
GardenObject                             PlantingRun ──run_contains──▶ PlantInstance
                                              │
                                              └─run_planned_at──▶ Slot   (geplante Belegung)

Location (Beet) ──has_task──▶ Task ──task_logged_as──▶ CareEvent ──care_event_at──▶ Location
PlantInstance  ──has_task──▶ Task                       CareEvent ──care_event_for──▶ PlantInstance (0..n)
                                                        CareEvent ──care_event_source──▶ watering_events | feeding_events | treatment_applications | harvest_batches

IrrigationZone ──zone_covers──▶ Location (Beet)      IrrigationZone ──zone_supplied_by──▶ GardenObject(water_source)
IrrigationZone ──zone_actuated_by──▶ Actuator         Site ──has_irrigation_zone──▶ IrrigationZone
Slot ──adjacent_to──▶ Slot   (ab REQ-053 aus Geometrie abgeleitet, §16.2)
```

Die geforderten Ketten lauten damit:

- **Garden → GardenArea → Bed → PlantingArea → PlantingRun → Plant** = `Site → Location → Location(bed) → Slot ← run_planned_at ← PlantingRun → run_contains → PlantInstance → placed_in → Slot`
- **Bed → MaintenanceTask → MaintenanceEvent** = `Location(bed) → has_task → Task → task_logged_as → CareEvent`

Vorhandene Fremdschlüssel-Felder (`site_key`, `location_key`, `slot_key`, `parent_location_key`) bleiben parallel zu den Edges bestehen (heutiges Doppelmuster, Backend-Befund §2). Neue Beziehungen folgen demselben Muster: Feld für den 1:1-Elternbezug, Edge für Graph-Traversalen.

### 7.3 Regeln für Objektklassen

| Regel | Inhalt |
|-------|--------|
| R-7.1 | Ein Objekt ist eine **Location**, wenn darin gepflanzt, gemessen oder gepflegt wird (Slots, Sensoren, Tasks, Aktoren hängen daran). Sonst ist es ein **GardenObject**. |
| R-7.2 | Ein GardenObject hat keine Slots und keine Pflanzen. Pflegeaufgaben sind nur für `compost`, `water_source` und `storage` zulässig (Kompost umsetzen, Regentonne winterfest machen, Schuppen aufräumen — W-008): `Task.entity_type = garden_object`, Edge `has_task` wird um `garden_objects` erweitert. `water_source` kann Ziel von `zone_supplied_by` sein. |
| R-7.3 | Ein Gewächshaus, in dem Beete liegen, ist eine Location (`greenhouse`), die Beet-Locations enthält. Die Hülle wird aus der Location-Geometrie gezeichnet; ein zusätzliches GardenObject ist nicht nötig. |
| R-7.4 | Ein Baum oder Strauch, der gepflegt und geerntet wird, ist eine PlantInstance in einem Slot einer Location (z. B. `orchard`, `hedge`). Für die reine Darstellung (Nachbars Baum, Zierstrauch ohne Pflege) ist er ein GardenObject (`tree`, `shrub`) mit Kronenradius. |
| R-7.5 | Beete sind Blatt-Locations in der Planungssemantik: Ein Beet enthält keine weiteren Locations. Unterteilungen innerhalb des Beets sind Slots (`slot_role = zone` oder `row`). |
| R-7.6 | Eine Umwandlung GardenObject ↔ Location ist eine fachliche Neuanlage (kein Typwechsel), weil Edges und Tasks sonst verwaisen. Die UI bietet „als Beet neu anlegen" mit Übernahme der Geometrie. |

### 7.4 Zustandsmodell des Beets

**Lebenszyklus** (`Location.bed_status`, nur für Beet-Typen; entschieden W-014):

```
planned ──▶ active ──▶ retired ──▶ active   (Reaktivierung nach Umbau)
   └──────────────────▶ retired             (nie angelegt)
```

| Status | Bedeutung | Auswirkung |
|--------|-----------|------------|
| `planned` | Gezeichnet, noch nicht angelegt | Keine aktiven Pflanzungen erlaubt; geplante Runs ja |
| `active` | In Nutzung | Standard |
| `retired` | Aufgelöst | Keine neuen Runs; Historie bleibt; auf dem Plan ausgeblendet, über Historie-Filter sichtbar; Reaktivierung durch Leitung |

**Saisonzustand** (`season_state`, **abgeleitet**, nie gesetzt) — was auf dem Beet gerade geschieht:

| Zustand | Ableitung |
|---------|-----------|
| `empty` | kein aktiver Run, keine Pflanze mit `removed_on = null` |
| `planted` | mindestens ein aktiver Run mit `plan_role = main_crop` |
| `green_manure` | aktiver Run mit `plan_role = green_manure` (Gründüngung **ist eine Pflanzung**; ihre Familie zählt in der Fruchtfolge, §16) |
| `fallow` | `empty` und das Beet wurde in der laufenden Saison bewusst nicht bepflanzt (`CropRotationPlan`-Eintrag mit `plan_role = fallow` für das Jahr) |
| `winter_covered` | letztes `care_event(category = covering)` ohne nachfolgendes `uncovering` |

Die Fruchtfolge (§16) liest `season_state` je Jahr; „Brache" und „Gründüngung" werden damit korrekt getrennt gezählt (Senf als Gründüngung ist ein Brassicaceae-Wirt und zählt als Kohlfamilie).

Pflanzungen haben keinen eigenen Statusfeld — ihr Zustand leitet sich ab (§11.3).

## 8. Funktionale Anforderungen (Übersicht)

Die funktionalen Anforderungen sind in §9–§16 thematisch gegliedert. Diese Tabelle ist der Index; die Nummern sind dort wiederzufinden.

| Bereich | IDs | MUST | SHOULD | COULD | WON'T |
|---------|-----|------|--------|-------|-------|
| Garteneditor inkl. Indoor-Grundriss (§9) | GP-FR-001 … 034, 150 … 156, 180 … 183 | 34 | 7 | 2 | 2 |
| Beetverwaltung und Standortmerkmale (§10) | GP-FR-040 … 055, 157 … 169 | 11 | 12 | 6 | 0 |
| Pflanzplanung, Pflanzeninfo und -zustände (§11) | GP-FR-060 … 078, 190 … 192 | 17 | 1 | 4 | 0 |
| Beetpflege (§12) | GP-FR-080 … 091 | 9 | 2 | 1 | 0 |
| Pflegehistorie (§13) | GP-FR-100 … 109, 149 | 7 | 3 | 1 | 0 |
| Bewässerung (§14) | GP-FR-110 … 119 | 0 | 7 | 3 | 0 |
| Boden/Nährstoffe (§15) | GP-FR-120 … 127 | 2 | 4 | 2 | 0 |
| Fruchtfolge/Mischkultur (§16) | GP-FR-130 … 139 | 6 | 3 | 1 | 0 |
| Import/Export (§23) | GP-FR-140 … 148, 170 … 176 | 5 | 8 | 2 | 1 |
| **Summe** | 163 FR · 61 NFR · 58 UX · 57 API · 61 ACC | **91** | **47** | **22** | **3** |

Stand v1.4, aus den Anforderungstabellen gezählt (nur `GP-FR`-Zeilen je Abschnitt; NFR/UX/API/ACC als Gesamtzahl). v1.4: GP-FR-018 und GP-FR-146 (GeoJSON) von COULD nach WON'T. Nachtrag 2026-10-16 (Spec-Readiness-Review): GP-NFR-071 als Tabellenzeile in §25.2 (NFR 60 → 61), fünf neue Akzeptanzkriterien GP-ACC-053…057 (ACC 52 → 57). v1.7 (gezählt): API 42 → 44 (GP-API-055 aus #2463 war nicht nachgezählt, GP-API-056 neu), ACC 57 → 61 (GP-ACC-058…061 aus v1.5 und dem Nachtrag #2513). v1.11 (gezählt): API 44 → 57 (GP-API-057…062 aus v1.9 und GP-API-063…069 aus v1.11 waren nicht nachgezählt).

---

## 9. Grafischer Garteneditor

### 9.1 Grundsatz: Darstellung ≠ Datenmodell

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-001 | MUST | Der Editor arbeitet ausschließlich auf dem fachlichen Plan-Modell (§20): jede Interaktion erzeugt eine **Plan-Operation** (z. B. `move_object`, `set_geometry`, `create_location`), die lokal auf das Modell angewandt, gerendert und über die Batch-API (§21.3) persistiert wird. Die Rendering-Bibliothek hält keinen eigenen Zustand, der nicht aus dem Modell rekonstruierbar ist. | ja |
| GP-FR-002 | MUST | Jede persistierte Geometrie ist in **Metern** definiert (§9.2). Pixelwerte entstehen ausschließlich in der Transformation Modell → Viewport und werden nie gespeichert. | ja |
| GP-FR-003 | MUST | Der Editor rendert aus dem Modell deterministisch: dieselben Daten ergeben bei gleichem Viewport dieselbe Darstellung (Voraussetzung für Snapshot-Tests und PDF-Gleichheit). | ja |

### 9.2 Koordinatensystem, Maße, Raster

**Koordinatenrahmen.** Es gibt zwei Rahmen:

1. **Plan-Rahmen (Site):** Ursprung ist die linke untere Ecke der Gartengrenzen-Bounding-Box beim ersten Speichern; `+x` nach rechts, `+y` nach oben (mathematisch, nicht Bildschirm). Einheit Meter, Dezimalgenauigkeit 3 Nachkommastellen (= Millimeter). Locations und GardenObjects liegen in diesem Rahmen; zulässig sind Koordinaten 0…1 000 m je Achse.
2. **Beet-Rahmen (Location):** Ursprung ist der Ankerpunkt (`origin`) der Beet-Geometrie, Achsen folgen der Beet-Rotation. Slots liegen in diesem Rahmen. **Wertebereich (E-12):** Koordinaten im Beet-Rahmen sind auf ±1 000 m je Achse begrenzt (Vorzeichen erlaubt, weil Punkte links/unterhalb des Ankers liegen können); der Plan-Rahmen bleibt 0…1 000 m. **Folge:** Wird ein Beet verschoben oder gedreht, bleiben seine Slot-Geometrien unverändert gültig — ein Beet mit 40 Pflanzpositionen zu verschieben ist ein Update eines Dokuments, nicht von 41.

Die Transformation Beet-Rahmen → Plan-Rahmen ist `p_plan = origin + R(rotation_deg) · p_bed`. Der Nordwinkel (§9.3) wirkt nur auf die Darstellung des Kompasses und auf spätere Sonnenberechnungen, nie auf die gespeicherten Koordinaten.

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-004 | MUST | Längen werden in Metern gespeichert (`float`, gerundet auf 0,001 m). Die UI zeigt wahlweise Meter mit zwei Nachkommastellen oder Zentimeter; die Einstellung ist nutzerbezogen (localStorage, wie `module_visibility`) und ändert die gespeicherten Werte nicht. | ja |
| GP-FR-005 | MUST | Eine Geometrie ist eine der Formen aus §20.1 — Flächen: `rect` (origin, width_m, length_m, rotation_deg), `circle` (origin = Mittelpunkt, radius_m), `polygon` (points[], rotation_deg = 0, geschlossen, ≥ 3 Punkte, einfach — keine Selbstüberschneidung); Linienobjekte (Zaun, Mauer, Wegachse): `polyline` (points[], width_m); Positionen (Slots, Punktobjekte): `point`. | ja |
| GP-FR-006 | MUST | `area_m2` wird für `rect`, `circle`, `polygon` serverseitig berechnet (Shoelace für Polygon) und in `Location.area_m2` geschrieben, sobald eine Geometrie vorliegt. Ohne Geometrie bleibt `area_m2` manuell pflegbar (Bestandsverhalten). Die Berechnung ist in einem reinen Modul (`domain/calculators/geometry_calculator.py`) ohne I/O. | ja |
| GP-FR-007 | MUST | Jedes Objekt besitzt eine serverseitig berechnete **Bounding Box** (`bbox: [min_x, min_y, max_x, max_y]` im Plan-Rahmen, nach Rotation), die für Containment-Prüfung, Viewport-Culling und die Mini-Map verwendet wird. | ja |
| GP-FR-008 | MUST | Rotation wird in Grad gespeichert (`rotation_deg`, 0 ≤ r < 360, gegen den Uhrzeigersinn, bezogen auf `+x`). Negative Werte lehnt die API ab (`geometry.invalid`, E-12); Werte, die auf 3 Nachkommastellen zu 360,000 runden, wrappen auf 0,0. Die UI bietet Drehgriff, Eingabefeld und Schritte 15°/45°/90°. | ja |
| GP-FR-009 | MUST | Zoom: stufenlos per Mausrad/Pinch, feste Stufen (25 %, 50 %, 100 %, 200 %, 400 %; Definition und Grenzen GP-FR-150) per Schaltfläche/Tastatur, „An Fläche anpassen". Ein Maßstabsbalken (1 m / 5 m / 10 m je nach Zoom) ist immer sichtbar. | ja |
| GP-FR-010 | MUST | Pan: Mittelklick/Space+Drag/Zwei-Finger-Pan; Tastatur: Pfeile scrollen, Shift+Pfeile scrollen um das Zehnfache — **nur wenn kein Objekt ausgewählt ist**; bei Auswahl verschieben die Pfeile das Objekt (GP-UX-044). | ja |
| GP-FR-011 | MUST | Raster: Standardgrößen **1 cm, 5 cm, 10 cm, 25 cm, 50 cm, 1 m**. Standardwert 10 cm. Das Raster ist ein-/ausschaltbar (Schalter + Taste `G`); die Rasterlinien werden nur gezeichnet, wenn ihr Bildschirmabstand ≥ 8 px ist (sonst nächstgrößere Stufe), das Snap-Raster bleibt unabhängig davon aktiv. | ja |
| GP-FR-012 | MUST | Snap-to-Grid gilt für Verschieben, Zeichnen und Griffe; es ist mit gehaltener `Alt`-Taste bzw. per Schalter temporär abschaltbar. Zusätzlich SHOULD: Snap an Kanten/Ecken benachbarter Objekte (Toleranz 10 px). | ja (Grid), SHOULD (Objekt-Snap) |
| GP-FR-013 | MUST | Der Plan-Rahmen erlaubt Längen bis 1 000 m je Achse (Streuobstwiese, Gemeinschaftsgarten). Darüber lehnt die API ab (§22). | ja |
| GP-FR-014 | MUST | Maßangaben am Objekt: Bei Auswahl und während des Zeichnens/Skalierens werden Breite, Länge (bzw. Radius) und Fläche als Beschriftung am Objekt angezeigt. | ja |

### 9.2a Ein Positionsmodell für Zelt und Beet (O-01)

Die Betreiberentscheidung lautet: **keine Sonderbehandlung** — ein Growzelt und ein Beet werden mit denselben Koordinaten betrieben. Was das konkret bedeutet:

| Aspekt | Vorher (REQ-002) | Ab REQ-053 |
|--------|------------------|------------|
| Positionsangabe eines Slots | `position: (row, col)` als Rasterzelle ohne Einheit; Zelt-Raster implizit | `geometry` im Beet-/Zelt-lokalen Rahmen in Metern — für Zelte, Regale, Beete, Kübel gleich |
| Zelt-Darstellung | Tabelle (`LocationDetailPage`) | dieselbe Beetansicht (§9.6): Zelt = Location mit `rect`-Geometrie (z. B. 1,2 × 1,2 m), Töpfe = Punkt-Slots; Pflanzen-Marker, Tasks, Historie identisch |
| Raster | nur im Zelt gedacht | Snap-Raster ist eine Editor-Einstellung (§9.2) und für alle Locations gleich; wer ein 4 × 4-Topfraster will, nutzt `compute_layout(grid, spacing = Topfdurchmesser)` (§11.2) |
| Nachbarschaft (`adjacent_to`) | manuell, nur programmatisch | aus Geometrie abgeleitet (GP-FR-130) — auch im Zelt, womit die Mischkultur-Engine erstmals indoor Nachbarn kennt |
| Site-Typen | Plan nur outdoor/greenhouse/balcony | Plan für **alle** `SiteType`s; `V-18` entfällt; Indoor-Sites bekommen Grenze = Raumgrundriss oder bleiben ohne `boundary` (dann gilt nur Containment in der Location) |
| Bestandsdaten | — | Migration M1 leitet für jeden Slot ohne `geometry` einen Punkt aus `position` ab: `origin = (col × pitch, row × pitch)` mit `pitch` = `location.pitch_m` (neu, Standard 0,30 m — ein 11-l-Topf), `geometry_source = migrated_grid`. `Slot.position` wird danach **entfernt** (keine Spiegelung; Sortierungen nutzen `row_index`/`sequence`, die die Migration ebenfalls füllt). |
| Layout-Fähigkeit | nur Beete | `LocationType.supports_layout = true` für `is_bed`-Typen **und** `tent`, `shelf` (W-016.1); Bepflanzen-Dialog, `compute_layout` und Run-Layout hängen daran, nicht an `is_bed` |
| Topfvolumen | nur `planter.volume_liters` am Beet | `Slot.container_volume_l` (optional) — im Zelt begrenzt das Topfvolumen die Pflanze, nicht der Abstand; der Dialog prüft gegen `Species.recommended_container_volume_l`/`min_container_depth_cm` (Schema vorhanden) und warnt (W-016.5) |
| Licht (SHOULD, nicht MVP) | — | `Location.lighting {lamp_height_cm, canopy_distance_cm, fixture_geometry?}` als Vorbereitung für PPFD-Verteilung; Randabstand im Zelt ist frei konfigurierbar, weil `spacing/2` dort keine Lichtbasis hat (W-016.2/3) |
| Etagen | — | **Eine Ebene = eine Location** (Kind von `shelf`/`tent`) mit eigener Lampe, Klima und Photoperiode; 2D-Geometrie bildet keine Stapel ab (W-016.4) |
| Photoperiode (SHOULD) | — | Validierungshinweis `tent.photoperiod_conflict`, wenn Pflanzen verschiedener Photoperiode-Phasen in derselben Zelt-Location stehen (W-016.6); nur belegte Lichtdauern (`photoperiod_source = sourced`) bilden Gruppen, alles andere zählt als unbekannt (#2857, siehe unten) |
| Nachbarschaftsfaktor | Site-weit | `adjacency_factor` pro Location überschreibbar (SCROG-Überlappung, W-016.8) |
| Fruchtfolge | — | Für `tent`, `shelf`, `planter` standardmäßig aus (GP-FR-137) |

**Photoperiode-Hinweis — nur belegte Lichtdauern zählen (#2857).** Der Hinweis liest die Lichtdauer aus dem
Anforderungsprofil der aktuellen Phase jeder Pflanze (REQ-003 `photoperiod_hours`) samt ihrer Herkunft
(`photoperiod_source`). Konfliktgruppen bilden **nur** Lichtdauern mit Herkunft `sourced` (aus einem Steckbrief oder
im Profil-Editor eingetragen). Eine Lichtdauer aus der Phasenvorlage des Generators (`generated`), der Rückfallwert
(`default`), ein Profil ohne Herkunft (vor #2857 gespeichert) und eine Pflanze ohne Profil zählen gleich: als
**unbekannt**. Daraus folgt:

- Zwei oder mehr Gruppen belegter Lichtdauern, mindestens 1 h auseinander → `tent.photoperiod_conflict` (`warning`);
  unbekannte Pflanzen werden am Konflikt mitgezählt und benannt (höchstens fünf Namen).
- Sonst mindestens zwei beteiligte Pflanzen, davon mindestens eine unbekannt → `tent.photoperiod_unknown` (`info`);
  der Text sagt, dass nur ein Standard- oder Vorlagenwert vorliegt, und nennt den Schritt: die Lichtdauer im
  Phasenprofil der Art eintragen.
- Eine belegte und eine unbekannte Pflanze sind nie ein Konflikt, nur `unknown`.
- Toleranz (1 h), Ausschluss junger Phasen und die Bedingung „eigener Lichtplan“ (Zelt; Regal-Ebene mit eigener
  Lampe) bleiben unverändert.

Der Teil, der am Photoperiodentyp hängt, bleibt in #2857 offen, bis eine Datenmigration möglich ist: ein Wert
`unspecified` für `PhotoperiodType` (heute steht `day_neutral` als Vorgabe auch für nie klassifizierte Arten), der
Ausschluss tagneutraler Pflanzen aus dem Konflikt und die Prüfung „Kurztagpflanze mit 18 h“. Bis dahin nehmen
tagneutrale Pflanzen am Vergleich teil.

Abgenommen wird der Editor weiterhin primär mit Outdoor-Szenarien (§30), aber die E2E-Grundlinie (Issue 23) enthält **ein Zelt-Szenario** (Location `tent`, 9 Punkt-Slots im 3 × 3-Raster, Pflanze verschieben), damit die Gleichbehandlung nachweisbar ist (GP-ACC-036).

### 9.3 Orientierung

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-015 | MUST | `Site.plan.north_angle_deg` (0–359,9) definiert, wohin **geografisch** Norden auf dem Plan zeigt: Kompass-Azimut **im Uhrzeigersinn**, 0 = `+y` ist Norden, 90 = `+x` ist Norden (abweichend von `rotation_deg`, das mathematisch gegen den Uhrzeigersinn läuft — beide Konventionen sind im Code mit benannten Konvertern zu trennen). Standard 0. Die UI beschriftet „geografisch Nord"; ein Handy-Kompass liefert magnetisch Nord (Missweisung Deutschland ≈ +4° Ost, WMM2025), der Wert wird daher nie automatisch übernommen. Ein Kompass-Widget im Editor zeigt N/O/S/W und lässt den Winkel durch Drehen oder Eingabe setzen. | ja |
| GP-FR-016 | SHOULD | Ist `Site.gps_coordinates` gesetzt, zeigt das Kompass-Widget zusätzlich die Richtung von Sonnenauf- und -untergang am heutigen Tag (`sun_calculator`, REQ-002). Keine Verschattungsberechnung (§29). | nein |
| GP-FR-017 | SHOULD | `Location.orientation` (8 Werte seit WP 8.24; bei gesetztem `aspect_deg` nach GP-FR-168 abgeleitet) und das in REQ-002 vorgesehene `bed_orientation` werden, wenn eine Geometrie vorliegt, aus `rotation_deg` + `north_angle_deg` **abgeleitet** und nur noch angezeigt, nicht mehr manuell gepflegt. Ohne Geometrie bleibt die manuelle Pflege. | nein |
| GP-FR-018 | WON'T | ~~Beim Export (GeoJSON, §23) wird aus `gps_coordinates` + `north_angle_deg` eine affine Transformation Plan → WGS84 berechnet.~~ Gestrichen mit GP-FR-146 (O-21 revidiert, v1.4): WGS84-Koordinaten sind der Wohnort, ein zweites Koordinatensystem ohne Nutzer, der es verlangt. | — |

### 9.4 Objektmanipulation

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-019 | MUST | Zeichnen: Rechteck (Drag), Kreis (Drag vom Mittelpunkt), Polygon (Klick je Punkt, Doppelklick/Enter schließt, Esc bricht ab), Polylinie (wie Polygon, offen). | ja |
| GP-FR-020 | MUST | Auswahl: Klick; Mehrfachauswahl per Shift+Klick und Rahmen-Auswahl (Drag auf leerer Fläche im Auswahlwerkzeug); `Ctrl/Cmd+A` wählt alle sichtbaren Objekte der aktiven Ebene. | ja |
| GP-FR-021 | MUST | Verschieben per Drag oder Pfeiltasten (1 Rasterschritt; Shift = 10 Schritte); Mehrfachauswahl verschiebt gemeinsam. | ja |
| GP-FR-022 | MUST | Skalieren über 8 Griffe (Rect) bzw. Radiusgriff (Circle); Shift hält das Seitenverhältnis. Polygon-Skalierung über die Bounding-Box-Griffe (SHOULD). | ja (rect/circle), SHOULD (polygon) |
| GP-FR-023 | MUST | Polygon-Punkte: Punkt ziehen, Punkt hinzufügen (Mitten-Handle „+“ auf der Kante; Schaltfläche „Punkt einfügen“), Punkt löschen (Entf bzw. Schaltfläche „Punkt löschen“ bei selektiertem Punkt, min. 3 Punkte bleiben); Doppelklick ist **nicht** belegt (GP-UX-040). Touch-Entsprechungen: GP-UX-036…038. | ja |
| GP-FR-024 | MUST | Löschen (Entf/Backspace, Kontextmenü, Panel). Beete mit aktiven Pflanzen oder offenen Tasks verlangen eine Bestätigung mit Nennung der Anzahl; die API verweigert das Löschen eines Beets mit `removed_on = null`-Pflanzen (409, §22). | ja |
| GP-FR-025 | MUST | Duplizieren (`Ctrl/Cmd+D`): kopiert Geometrie und Stammfelder mit Versatz um einen Rasterschritt; bei Beeten werden Slots mitkopiert, Pflanzen und Tasks nicht. **Mehrfach duplizieren** (SHOULD, F-10): Anzahl, Richtung, Abstand und Namensschema (`Parzelle {n}`) für Gemeinschaftsgärten mit 30 Parzellen. | ja (einfach), SHOULD (mehrfach) |
| GP-FR-026 | MUST | Undo/Redo (`Ctrl/Cmd+Z`; Redo `Ctrl/Cmd+Shift+Z` **und** `Ctrl+Y`) als clientseitiger Operationsstapel (mind. 50 Schritte, Granularität GP-FR-155) über alle Plan-Operationen; nach erfolgreichem Speichern bleibt der Stapel erhalten, bei Konflikt (409) wird er geleert und der Nutzer informiert. | ja |
| GP-FR-027 | MUST | Kontextmenü (Rechtsklick bzw. Long-Press **nur mit Maus/Stift**; auf Touch über die Schaltfläche „⋯“ im Panel/Sheet, GP-UX-040) mit Bearbeiten, Duplizieren, Löschen, „Bepflanzen" (Beet), „Aufgabe anlegen", „In Vordergrund/Hintergrund" (z-Order). | ja |
| GP-FR-028 | MUST | Eigenschaftenpanel (Desktop: rechte Seitenleiste; Mobil: Bottom Sheet) zeigt für das ausgewählte Objekt Name, Typ, Position (x, y), Maße, Rotation, Fläche und typspezifische Felder; Werte sind direkt editierbar (Tastatur-Alternative zum Drag, UI-NFR-002 R-024). | ja |
| GP-FR-029 | SHOULD | Ausrichten/Verteilen für Mehrfachauswahl (links/rechts/oben/unten/zentriert, gleichmäßig verteilen). | nein |
| GP-FR-030 | WON'T | Persistente Gruppen (Gruppenobjekt mit eigenem Dokument). Begründung: Die Hierarchie Location → Location leistet fachliches Gruppieren bereits; ein rein grafisches Gruppenobjekt erzeugt ein zweites Containment-Modell. Mehrfachauswahl deckt den Bedienfall ab. | — |
| GP-FR-031 | MUST | Ebenen-Sichtbarkeit: Schalter für Raster, Pflanzen, Beschriftungen (MVP) sowie Gartenobjekte, Beete, Zonen, „zuletzt gegossen" (SHOULD). Die Sichtbarkeit ist nutzerbezogen (localStorage). | ja |
| GP-FR-032 | MUST | Sperren eines Objekts gegen versehentliches Verschieben (`locked: true`, persistiert, Schloss-Symbol). Gartengrenze ist nach dem ersten Speichern standardmäßig gesperrt. | ja |
| GP-FR-033 | SHOULD | Hintergrundbild (Foto/Skizze/Luftbild) als **Unterlage zum Abzeichnen** mit Zwei-Punkt-Eichung (zwei Punkte + bekannte Distanz → Maßstab) und Deckkraft. Nur Darstellung, nie Datenquelle, nicht im Export (GP-FR-140) und nicht im PDF, außer ausdrücklich gewählt; Dateigröße begrenzt (Quote GP-NFR-017), Lagerung als Attachment (NFR-013); Luftbilder können Wohnort verraten → §26. Georeferenzierung/Kacheln bleiben COULD (kein eigener Eintrag, §29). *(O-19 entschieden 2026-10-11.)* | nein |
| GP-FR-034 | COULD | Messwerkzeug (Abstand zwischen zwei Punkten, Fläche eines temporären Polygons). | nein |

### 9.5 Objektklassen und ihre Darstellung

| Objekt | Entität | Geometrieformen | Pflichtfelder | Darstellung | MVP |
|--------|---------|-----------------|---------------|-------------|-----|
| Gartengrenze | `Site.plan.boundary` | rect, polygon | — | gestrichelte Außenlinie, gesperrt | ja |
| Bereich (GardenArea) | Location (`garden`, `terrace`, `balcony`, `greenhouse`, eigene; im Indoor-Plan `room`) | rect, polygon | name, location_type | leichte Füllung, gepunkteter Umriss, Name; liegt unter Beeten und Wegen (Hit-Klasse „Bereich“, GP-UX-032); bei Überlappung weicht sein Name den Namen der Beete darin (Ausnahme zu GP-UX-047). Bereich ist jede Location, deren Typ weder `is_bed` noch `supports_layout` trägt (Lesemodell `is_area`, Plan-Feld `area_type_keys`) — auch ein schon vorhandenes Gewächshaus oder Zimmer; Zelt und Regal (`supports_layout`) bleiben Pflanzplätze. | ja |
| Beet | Location (`bed`, `raised_bed`, `planter`, `greenhouse_bed`, `cold_frame`) | rect, circle, polygon | name, location_type | typabhängige Füllung (Boden braun, Hochbeet mit Rand), Name, Status-Badge | ja |
| Weg | GardenObject `path` | polyline, polygon | — | grau, Breite | ja |
| Rasen | GardenObject `lawn` | rect, polygon | — | hellgrün | SHOULD |
| Baum | GardenObject `tree` | circle (Kronenradius) | — | Kronenkreis mit Stammpunkt; Props `species_label?`, `height_m?`, `crown_base_height_m?`, `foliage ∈ {deciduous, evergreen}?` (Schattenvorbereitung, §29) | ja |
| Strauch/Hecke | GardenObject `shrub` | circle, polyline (Hecke, width_m) | — | dunkelgrün | SHOULD |
| Gebäude | GardenObject `building` | rect, polygon | — | dunkelgrau, Name; Props `height_m?` (Traufhöhe), `ridge_height_m?` | ja |
| Mauer/Zaun | GardenObject `wall`, `fence` | polyline | — | dicke Linie / Linie mit Pfosten; Props `height_m?`, `opacity ∈ {opaque, semi, open}?` | ja (fence), SHOULD (wall) |
| Rankhilfe/Spalier | GardenObject `trellis` | polyline | — | gestrichelte Linie mit Pfosten; Props `height_m`; wird im Bepflanzen-Dialog angeboten, wenn `Species.support_required` (W-005) | SHOULD |
| Wasserquelle | GardenObject `water_source` | point (circle r = 0,25 m fest) | `water_source_kind ∈ {tap, rain_barrel, well, pond, cistern, hose_reel}` | Tropfen-Icon | ja |
| Kompost | GardenObject `compost` | rect, circle | — | Icon | SHOULD |
| Lager/Schuppen | GardenObject `storage` | rect | — | Icon | SHOULD |
| Sonstiges | GardenObject `other` | alle | `label` | neutral, Label | ja |
| Beschriftung (Text) | GardenObject `text_label` (GP-UX-071, #2913) | rect (die Textbox: `origin` = Ankerpunkt links unten, `length_m` = Texthöhe, `width_m` = Lauflänge, `rotation_deg` = Drehung) | `label` = der Text: eine Zeile, 1–80 Zeichen nach dem Trimmen, kein Zeilenumbruch, kein Steuer- oder Bidi-Formatzeichen (serverseitig geprüft, 422) | nur der Text, mittig in der Box, so groß wie die Box es erlaubt (Schrift = 0,8 × Höhe, kleiner, wenn der Text sonst über die Breite liefe — Editor und PDF dieselbe Regel); der Rahmen nur ausgewählt (gestrichelt); kein Icon, kein Namensetikett, keine Maßangabe. Kein physisches Objekt: keine Höhe, kein Schatten, keine Aufgaben, kein Legendeneintrag, nicht in der Mini-Map, nicht im Untermenü „Gartenobjekt“ und nicht in „Mit Maßen hinzufügen“; kein Eltern-Bereich (hängt frei auf dem Plan, Containment gegen die Gartengrenze wie jedes Objekt, V-03) | SHOULD |
| Pflanzposition/Zone/Reihe | Slot | point, polygon, polyline (row) | slot_id | Punkt mit Pflanzen-Icon; Zone als Schraffur; Reihe als Linie mit Punkten | ja |
| Pflanze | PlantInstance (über Slot) | — | — | Icon/Initiale der Spezies, Phasenfarbe (UI-NFR-016), Status-Ring | ja |

Gewächshaus-Darstellung: Eine Location `greenhouse` wird mit Glasrand gezeichnet; darin liegende Beet-Locations werden normal gezeichnet. Ein GardenObject `greenhouse_shell` ist **nicht** vorgesehen (R-7.3).

**Objekte außerhalb der Gartengrenze:** `GardenObject.off_site = true` (Nachbars Haus, Baum am Zaun) nimmt das Objekt von der Containment-Prüfung V-03 aus; es wird als Kulisse gezeichnet (grau, nicht editierbar in der Fläche) und steht für die Schattenberechnung (§29) zur Verfügung.

### 9.6 Ansichten

| Ansicht | Inhalt | Route | MVP |
|---------|--------|-------|-----|
| **Gartenübersicht** | Gesamter Plan mit allen Objektklassen, Legende, Mini-Map (ab Site-Ausdehnung > 4× Viewport), Werkzeugleiste; seit v1.16 Arbeitsfläche mit den Tabs Plan · Liste · Beete (§17.3) | `standorte/sites/:key/plan` (`?tab=plan\|list\|beds`, GP-UX-064) | ja |
| **Beetansicht** | Ein Beet im Beet-Rahmen, Slots/Reihen/Zonen, Pflanzen, Maße; Tabs: Pflanzung · Pflege · Boden · Historie | `standorte/locations/:key/plan` (Tabs über `useTabUrl`) | ja |
| **Pflanzansicht** | Pflanzen eines Beets als Marker mit Phase, Name, Alter; Klick → Pflanzen-Detail (bestehende Seite) | Tab „Pflanzung" der Beetansicht | ja |
| **Pflegeansicht** | Offene/fällige Tasks des Beets und seiner Pflanzen; Erledigen inline | Tab „Pflege" | ja |
| **Historie** | Vergangene Pflanzungen (Zeitstrahl nach Jahr/Saison) und `care_events` | Tab „Historie" | ja |
| **Feldmodus** | Reduzierte Gartenübersicht für Mobilgeräte (§18) | `standorte/sites/:key/plan?mode=field` | ja |

Die Mini-Map ist nur sinnvoll, wenn der Plan größer als der Viewport ist; sie ist daher bedingt (Schwelle oben), nicht permanent.

### 9.7 Interaktionsregeln (v1.3)

Diese Regeln präzisieren §9.4 und §17. Wo sie einer älteren Zeile widersprechen, gilt §9.7 (die Zeilen sind entsprechend angepasst). Alle Zeilen: MUST, MVP ja, sofern nicht anders angegeben. Quelle der Befunde: `spec/analysis/frontend-design-review-req-053-v1.3.md`.

**Auswahl und Fokus**

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-UX-032 | MUST | **Hit-Priorität** bei überlappenden Objekten, von oben nach unten: Pflanze/Slot-Marker → Beet/Gartenobjekt → Weg → Bereich → Gartengrenze. Innerhalb einer Klasse gilt die z-Order, danach die kleinere Fläche. Gesperrte Objekte (GP-FR-032) sind trefferbar, aber nicht verschiebbar. | ja |
| GP-UX-033 | MUST | **Stapelauswahl:** Wiederholter Klick/Tipp auf dieselbe Stelle (Alt+Klick auf Desktop) wählt das nächste Objekt darunter; das Panel/Sheet zeigt „Objekte an dieser Stelle (n)" als Liste. SHOULD (MVP nein): Objektbaum-Panel mit Mehrfachauswahl. | ja |
| GP-UX-034 | MUST | **Dichte Pflanzen auf Touch:** Ist der Bildschirmabstand benachbarter Marker kleiner als das Zielmaß (48 px, Feldmodus 64 px), öffnet ein Tipp die Liste „Pflanzen in der Nähe" (Bottom Sheet, Einträge ≥ 64 px, Spezies + Slot-Nummer) — Pflanzen werden nie per Direkttreffer „geraten". | ja |
| GP-UX-035 | MUST | Im Feldmodus „Vorherige/Nächste Pflanze" (Reihenfolge der Reihen) als Einstieg in den Positions-Stepper (§18.1 Schritt 9). | ja |
| GP-NFR-065 | MUST | `PlanRenderer.hitTestAll` (siehe GP-NFR-009) liefert den vollständigen Stapel; `hitTest` ist dessen erstes Element. | ja |
| GP-UX-037 | MUST | **Mehrfachauswahl auf Touch:** Umschalter „Mehrfachauswahl“ in der Werkzeugleiste (jeder Tipp fügt hinzu/entfernt), „Alle auswählen“ im Menü. **Rahmenauswahl** wählt nur Objekte, die **vollständig** im Rahmen liegen; gesperrte Objekte, die Gartengrenze und (außer bei aktiver Ebene) Slots/Pflanzen sind ausgenommen. Rahmenauswahl auf Touch nur im Mehrfachauswahl-Modus (sonst Pan). | ja |

**Zeichnen, Gesten, Tastatur**

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-UX-036 | MUST | **Zeichenmodus auf Touch:** Aktionsleiste „Punkt setzen · Rückgängig · Fertig · Abbrechen“ (je ≥ 48 px). Rechteck: Drag oder Tipp–Tipp (zwei Ecken); Kreis: Mittelpunkt, dann Radius. Im Zeichenwerkzeug gilt **kein** Long-Press-Zwang. Snap-Umschalter als Schaltfläche (ersetzt `Alt`, GP-FR-012). | ja |
| GP-UX-038 | MUST | **Polygonpunkte ohne Tastatur:** Punkt wählen → Schaltflächen „Punkt löschen“ und „Punkt einfügen“ (Kantenmitte); ersetzt Doppelklick/Entf auf Touch. | ja |
| GP-UX-040 | MUST | **Verbindliche Gestentabelle (Touch):** Tipp = auswählen + Sheet (Info-Blase nur Hover/Desktop); Long-Press 500 ms (Fortschrittsring, `navigator.vibrate` wo verfügbar) = Verschiebe-Griff; Kontextmenü über „⋯“ im Sheet; Details nur über die Schaltfläche „Details öffnen“. Auf Maus/Stift: Rechtsklick/Long-Press = Kontextmenü, Doppelklick = Details. Kein Doppelklick-Shortcut auf Polygonkanten (GP-FR-023). | ja |
| GP-NFR-066 | MUST | `touch-action: none` nur auf der Zeichenfläche, `-webkit-touch-callout: none`, `user-select: none` und Unterdrückung des `contextmenu`-Ereignisses auf Touch dort (keine Lupe/Callout beim Long-Press). | ja |
| GP-UX-041 | SHOULD | Phantom-Touch-Filter (nasse Finger): weitere Pointer innerhalb 50 ms und Kontaktflächen über Schwellwert ignorieren. | ja |
| GP-UX-044 | MUST | Pfeile verschieben das ausgewählte Objekt, sonst scrollen sie (GP-FR-010); die Statuszeile nennt den aktiven Modus. Ohne Raster: 1 cm (Shift 10 cm). Redo: `Ctrl/Cmd+Shift+Z` und `Ctrl+Y`. | ja |
| GP-UX-045 | MUST | Einzeltasten-Shortcuts (`G`, `R`, `+`, `-`, `?`) sind nur aktiv, wenn die Zeichenfläche den Fokus hat, und in den Einstellungen abschaltbar (WCAG 2.1.4). | ja |
| GP-UX-046 | MUST | **„Hinzufügen mit Maßen“:** Dialog (Typ, Form, Breite × Länge bzw. Radius, Position, Rotation; Polygon per Punktliste; optional Abstand zu einem Referenzobjekt wie Haus/Zaun) als Tastatur- und Touch-Alternative zum Zeichnen; Platzierung danach per Drag oder Panel. Ersetzt für die Anlage nicht die Zeichenwerkzeuge. | ja |

**Maßstab, Darstellung, Raster**

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-150 | MUST | **Zoom ist `px_per_m`:** 100 % = 100 px/m (bei devicePixelRatio 1). Mindestzoom = „An Fläche anpassen“, Höchstzoom so, dass 1 cm ≥ 8 px. Die festen Stufen aus GP-FR-009 gelten relativ dazu und werden bei großen Plänen (> 100 m) durch den Mindestzoom begrenzt. | ja |
| GP-NFR-067 | MUST | **LOD-Tabelle (ersetzt „Marker ab 50 %, Beschriftung ab 100 %“):** Beetname ab ≥ 60 px Bildschirmbreite des Beets; Gartenobjekt-Icons ab ≥ 24 px; Pflanzen-Marker ab ≥ 10 px Markerabstand, darunter Cluster mit Zähler je Beet; Maßangaben nur bei Auswahl. Schrift bildschirmkonstant (12 px, Feldmodus ≥ 16 px), skaliert nicht mit dem Zoom. | ja |
| GP-UX-047 | MUST | **Label-Platzierung:** Name in der Objektmitte (Polygon: Pol der Unzugänglichkeit), mit „…“ gekürzt; unter 60 px Breite entfällt das Label zugunsten des Typ-Icons; bei Überlappung gewinnt das größere Objekt. Maßangaben stehen außerhalb über der Kante und weichen Griffen aus. PDF: bei Platzmangel Nummer + Beetliste auf Seite 2 (SHOULD, MVP nein). | ja |
| GP-UX-048 | MUST | **Griffe an kleinen Objekten:** sichtbar 12–16 px, Hit-Area 48 px. Objekt < 3 × 48 px Bildschirmgröße → nur vier Eckgriffe; < 2 × 48 px → keine Griffe, stattdessen „Zum Bearbeiten heranzoomen“ (Auto-Zoom) und Panel-Eingabe. Trefferpriorität: Verschiebefläche → Kantengriff → Eckgriff; Rotationsgriff ≥ 32 px außerhalb der Kante. | ja |
| GP-FR-154 | MUST | **Snap-Reihenfolge:** Objekt-Eckpunkt → Objekt-Kante → Raster. Slots snappen auf das Beet-lokale (gedrehte) Raster, Beete/Objekte auf das Plan-Raster. Toleranz 10 px (Maus), 24 px (Touch/Stift). Sichtbare Hilfslinie + Marker; Rasterstufe in der Kopfzeile. Winkel-Snap immer an (außer `Alt`). Objekt-Snap bleibt SHOULD (MVP nein), ist aber Teil der Reihenfolge. | ja |

**Eltern-Kind, Undo, Schutz**

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-151 | MUST | **Bereich verschieben/drehen** bewegt alle enthaltenen Locations und GardenObjects mit (eine Plan-Operation je Kind im Batch, ein Undo-Schritt). | ja |
| GP-FR-152 | MUST | **Beet mit Slots skalieren:** Dialog mit Vorschau „Positionen mitskalieren“ oder „Positionen beibehalten“; Slots außerhalb der neuen Form werden rot markiert und blockieren „Übernehmen“ (V-Regeln unverändert). | ja |
| GP-FR-153 | MUST | **Löschdialog** nennt die Zahl betroffener Kinder (Beete, Objekte, Slots, Pflanzen, Tasks); Kaskade ist explizit, nie implizit. | ja |
| GP-UX-043 | MUST | Bestätigung bei jedem Löschen eines Objekts mit Kindern und bei Mehrfachauswahl ≥ 3 Objekten, mit Zählung; Fokus startet auf „Abbrechen“, Bestätigen-Button ≥ 64 px im Feldmodus. | ja |
| GP-FR-155 | MUST | **Undo-Granularität:** ein Undo-Schritt = eine Nutzeraktion (ganzer Drag, Rahmen-Skalierung, Panel-Feld nach `blur`/Enter, Mehrfachauswahl-Move, „n-mal duplizieren“, Entsperren). Undo einer noch ungespeicherten Operation entfernt sie aus `pending`; nach dem Speichern erzeugt Undo eine Gegenoperation (wieder Dirty). Undo/Redo-Schaltflächen auch auf sm/xs; Tooltip nennt die Aktion. Das Löschen eines Beets mit Pflanzen ist nach dem Speichern nicht undo-bar (im Dialog genannt). | ja |
| GP-FR-156 | MUST | **Gesperrte Objekte** sind von Rahmenauswahl, „Alle auswählen“, Pfeiltasten und Panel-Eingabe ausgenommen; Schloss-Symbol mit Tooltip „Entsperren“. | ja |

**Fokus und Screenreader**

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-NFR-068 | MUST | **Roving-Tabindex:** Die Zeichenfläche ist **ein** Tab-Stopp (`role="group"`, `aria-roledescription="Gartenplan"`); innerhalb navigieren Pfeile/Tab zwischen den Objekten der aktuellen Ebene, Enter betritt ein Beet (Pflanzenebene), Esc geht zurück. Auswahl per `aria-selected`. Ersetzt „jedes Objekt `tabindex=0`“ (GP-NFR-020). | ja |
| GP-NFR-069 | MUST | Fokusziele hängen am Modell, nicht am gerenderten Ausschnitt: Culling entfernt kein Fokusziel; fokussierte Objekte außerhalb des Viewports scrollen hinein. | ja |
| GP-NFR-070 | MUST | Skip-Links „Zur Objektliste“ / „Zum Eigenschaftenpanel“; nach Dialog, Löschen und Undo wandert der Fokus auf ein Nachbarobjekt, nie auf `body`. Live-Region meldet nur das Endergebnis einer Aktion, nicht jede Zwischenposition. | ja |

**Dialoge, Leerzustände, Validierung**

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-UX-049 | MUST | **Leerzustände** je mit beschreibendem Text und genau einer Handlung: leeres Beet („Dieses Beet ist leer. [Bepflanzen]“), Plan ohne Grenze, Feldmodus-Liste ohne Beete („Noch keine Beete. [Planungsmodus]“ — die Liste zeigt stets alle Beete nach Zuweisung und Fälligkeit sortiert, GP-UX-030; „nichts fällig“ ist daher kein Leerzustand, jede Zeile nennt ihre nächste Fälligkeit), leere Historie (gefiltert: [Filter zurücksetzen]; Beet-Historie: [Was stand hier?]; die mandantenweite Historie ist lesend und bietet ungefiltert keine Handlung — Pflege wird am Beet protokolliert), keine Pflegeaufgaben („Hier ist nichts zu tun. [Neue Aufgabe]“), Offline ohne Cache, Ladefehler, leere Objektsuche. Braucht die Handlung Schreibrechte, sieht `viewer` nur den Text. Skeleton beim Laden (UI-NFR-003). | ja |
| GP-UX-050 | MUST | **Export-Dialog** (Menü „Exportieren“ in der Kopfzeile, auf xs im Überlauf): Format, Seitengröße, Maßstab (automatisch, überschreibbar), Ebenen, Option „Zuweisungen anzeigen“ (Standard aus, Hinweis SR-024), Vorschau, Fortschritt und Fehler nach UI-NFR-004. Auf xs nur JSON/PDF mit Standardoptionen. | ja |
| GP-UX-051 | SHOULD | **Import-Assistent** in drei Schritten: Datei wählen → Prüfbericht (`dry_run`: Zähler, Warnungen, `dropped_references[]`, Quotenverletzungen) → Modus; `replace` verlangt die Eingabe des Site-Namens und nennt den Pflicht-Snapshot (SR-011). Import/Export sind im Feldmodus ausgeblendet (mit Begründung im Menü). | nein |
| GP-UX-052 | MUST | **Kopfzeile/Sheet unter md:** Speichern-Status und Undo/Redo bleiben sichtbar, Raster, Zoom-Stufen und Exportieren liegen im „⋯“-Überlauf (Einträge ≥ 48 px) (ab Welle 10: Raster und Snap im Panel-Tab „Ansicht“, Zoom als Overlay, Exportieren bleibt im Überlauf — GP-UX-069; Undo/Redo bleiben sichtbar, unter md in der `TouchBar` — GP-UX-063). Werkzeuge tragen unter md eine Textbeschriftung (Tooltips gibt es auf Touch nicht). Bei Auswahl pannt der Viewport, sodass das Objekt oberhalb des Sheets sichtbar bleibt; das Sheet ist nicht modal, schließbar per Schaltfläche; Zahlenfelder `inputmode="decimal"`, Sheet-Höhe folgt `visualViewport`. | ja |
| GP-UX-053 | SHOULD | **Live-Validierung im Client** (Containment, einfaches Polygon, Slot-Überlappung) mit dem Frontend-Port der Calculators (§19.1) während Zeichnen/Drag: roter Rand + Hinweis im Panel, Loslassen im ungültigen Zustand = Snap-Back mit Meldung. Der Server bleibt maßgeblich (GP-UX-017). | ja |
| GP-UX-054 | SHOULD | Panelfelder tragen Achsen-/Drehrichtungssymbole („x →, y ↑“, Drehpfeil) und bei Slots den Bezugsrahmen „in Beet-Koordinaten“ (mathematische Rotation vs. Kompass-Nordwinkel, GP-FR-015). | ja |
| GP-UX-055 | COULD | Feldmodus: Plan wahlweise an der Blickrichtung ausrichten (nur flüchtiger Gerätezustand, vgl. GP-UX-026). | nein |
| GP-UX-056 | SHOULD | Kiosk (UI-NFR-019): nur Feldmodus lesend + Schnellprotokoll; Editier- und Export-Funktionen ausgeblendet. | nein |

**Messprofile.** GP-NFR-071 (SHOULD, MVP nein; Tabellenzeile in §25.2): INP ≤ 200 ms für Auswahl, Drag-Start und Zoom; Pinch-Zoom-Frametime ≤ 33 ms auf Smartphone; Low-End-Android-Profil (CPU 4× gedrosselt) für den Feldmodus. Ergänzt GP-NFR-033/-034.


### 9.8 Indoor-/Wohnungs-Grundriss (v1.3, O-22 entschieden: SHOULD, nicht MVP)

Wer Zimmerpflanzen, Fensterbänke, Regale und Zelte in der Wohnung hält, soll **dieselben Zeichen- und Planungsfunktionen** nutzen wie im Garten. Grundlage ist bereits entschieden (O-01, O-08): ein Positionsmodell für alle Site-Typen, `V-18` entfällt. Neu ist nur, was einem Wohnungsplan fehlt. Entschieden (O-22, 2026-10-11): SHOULD, nicht MVP; die Zeilen gelten für den **Indoor-Plan**, die Editor-Regeln aus §9.7 gelten unverändert mit.

| Aspekt | Regelung |
|--------|----------|
| Raum | Location `room` (Seed vorhanden) mit `rect`/`polygon`-Geometrie; die Site-Grenze ist der Wohnungsumriss (GP-FR-005, `boundary`). Etagen: **eine Etage = eine Site-Ebene** wird nicht eingeführt; mehrere Etagen sind mehrere Sites oder verschachtelte `building`-Locations (keine 3D-Stapelung, wie bei Regalen, W-016.4). |
| Neue Objektklassen | GardenObject `window` (polyline/Linie in der Wand, Props `sill_height_m?`, `glazing ∈ {single, double, unknown}?`, `orientation` abgeleitet aus Wand + `north_angle_deg`), `door` (Linie, Props `swing`), `furniture` (rect; Fensterbank, Regal-Standfläche, Tisch), `lamp` (Punkt/rect, Props `kind ∈ {grow_light, ceiling, floor}`, `height_m`, `ppfd_ref?` — Vorbereitung für Lichtverteilung, keine Berechnung). `wall` (bestehend) bildet Innenwände. |
| Pflanzplatz | Topf/Kübel = Slot (Punktgeometrie) oder `planter`-Location auf Fensterbank/Regal (`shelf` ist kein Beet, O-09, trägt aber `planter`). Gleiche Bepflanzen-, Aufgaben- und Historienfunktionen wie im Garten. |
| Licht | Fenster liefert dem Raum eine **Lichtrichtung**: `sun_profile.sun_window` und `sun_exposure` der Locations am Fenster lassen sich aus Fensterorientierung vorbelegen (Vorschlag, manuell überschreibbar; Verschattung durch Gebäude/Bäume draußen bleibt §29). Künstliches Licht über `lamp` + `Location.lighting` (§9.2a). |
| Zeichnen | Dieselben Werkzeuge (Rechteck/Polygon/Polylinie), Raster, Snap, Zwei-Punkt-Eichung der Hintergrund-Unterlage (GP-FR-033: **Foto oder Skizze des Grundrisses als Vorlage**) und „Hinzufügen mit Maßen“ (GP-UX-046) — die Unterlage ist hier der wichtigste Einstieg. Raster-Standard Indoor 5 cm. |
| Export/Import | Wie §23 (PDF/SVG/JSON); „Neue Saison aus Vorjahr“ (GP-FR-171) gilt auch hier. |

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-180 | SHOULD | Indoor-Objektklassen `window`, `door`, `furniture`, `lamp` (Tabelle oben) mit Darstellung, Eigenschaftenpanel und Legende; Aufnahme in das Untermenü „Gartenobjekt“ des Werkzeugs (umbenannt in „Objekt“, GP-UX-001 bleibt bei ≤ 8 Werkzeugen). | nein |
| GP-FR-181 | SHOULD | Fenster tragen eine aus Wandrichtung und Nordwinkel abgeleitete Himmelsrichtung; Locations in einem Radius (konfigurierbar, Standard 1,5 m) können `sun_profile` daraus vorbelegen lassen — nie automatisch überschreiben. | nein |
| GP-FR-182 | SHOULD | Indoor-Plan ist über Route und Modul wie der Gartenplan erreichbar (`standorte/sites/:key/plan`); Leerzustand erklärt „Zeichne die Umrisse deiner Wohnung oder lade ein Foto als Vorlage“ (GP-UX-049). Für `SiteType` indoor sind Wetter-, Frost- und Windmerkmale (§10.2) ausgeblendet. | nein |
| GP-FR-183 | COULD | Räume als Hierarchie: Wohnung → Raum → Fensterbank/Regal → Topf; Beetliste (GP-FR-042) heißt Indoor „Pflanzplätze“. | nein |

---

## 10. Beetverwaltung

### 10.1 Beetfelder

| Feld | Quelle | Neu? | Bemerkung |
|------|--------|------|-----------|
| Name, Beschreibung | `Location.name`, `description` (neu) | `description` neu | |
| Geometrie, Fläche | `Location.geometry`, `area_m2` | `geometry` neu | §9.2 |
| Bodenart, Füllmedium, Bodenzustand | `Location.soil_profile.{soil_texture, growing_medium_kind, conditions[]}` | neu | §15 |
| Standort (Lage im Garten) | `geometry.origin`, Elternbereich | — | |
| Sonneneinstrahlung | `Location.sun_exposure ∈ {full_sun, partial_shade, shade, deep_shade, unknown}` | neu | manuell; später aus Berechnung vorbelegbar (§29) |
| Bewässerungszone, -typ | `Location.irrigation_zone_key`, `irrigation_system` (bestehend) | `irrigation_zone_key` neu | §14 |
| Notizen | `Location.notes` | neu | Freitext, Markdown-frei |
| Status | `Location.bed_status` (Lebenszyklus) + abgeleiteter `season_state` | neu | §7.4 |
| Aktive/historische/geplante Pflanzungen | abgeleitet | — | §7.4 |

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-040 | MUST | Ein Beet ist eine Location, deren `location_type` als Beettyp markiert ist (`LocationType.is_bed = true`, neu). Seeds: `bed` (Bodenbeet, bestehend), `raised_bed` (Hochbeet), `planter` (Pflanzkübel/Topf-Gruppe — ersetzt fachlich den Seed `container`, der bestehen bleibt), `greenhouse_bed` (Gewächshausbeet), `cold_frame` (Frühbeet). **Nicht** `is_bed`: `shelf` (Tisch/Regal trägt Kübel, die selbst `planter` sind — O-09), `tent`, `room`, `garden`, `greenhouse`, `building`, `balcony`, `terrace`. Nutzer können weitere Beettypen anlegen (REQ-002). | ja |
| GP-FR-041 | MUST | Beet-Detailseite mit den Tabs aus §9.6; die bestehende `LocationDetailPage` erhält den Tab „Plan" (Beetansicht) und verlinkt zur Gartenübersicht. | ja |
| GP-FR-042 | MUST | Beetliste je Site (bestehende Tabellenlogik, UI-NFR-010) mit Spalten Name, Typ, Fläche, Status, aktive Pflanzen, offene Aufgaben, nächste Fälligkeit; Klick auf eine Zeile hebt das Beet auf dem Plan hervor. | ja |
| GP-FR-043 | SHOULD | Höhe: Für `raised_bed` und `planter` wird `height_m` (0,1–1,5) im Anlegedialog angeboten und aus der Vorlage vorbelegt; **kein Pflichtfeld** (F-06). Für `planter` zusätzlich `volume_liters` (abgeleitet aus Geometrie × Höhe, überschreibbar). Pflanzen mit `min_container_depth_cm` > `height_m × 100` lösen einen Hinweis aus (H-005). | ja |
| GP-FR-044 | SHOULD | **Beetvorlagen** (`bed_templates`, tenant-scoped, plus globale System-Vorlagen): Name, Beettyp, Standardgeometrie (rect 2,0 × 1,0; 1,2 × 2,4 Hochbeet; Kübel Ø 0,4 m …), Höhe, Standard-Reihenlayout (`row_spacing_cm`), Bodenprofil-Vorgabe. „Aus Vorlage platzieren" erzeugt eine Location mit Kopie der Felder. | nein |
| GP-FR-045 | SHOULD | Standardgrößen als Schnellwahl im Zeichendialog (1 × 1, 2 × 1, 3 × 1,2, 4 × 1,2 m; Hochbeet 2 × 1 × 0,8 m; Kübel Ø 0,3/0,4/0,5 m). | nein |
| GP-FR-046 | MUST | Beetstatus-Wechsel nach §7.4 mit Begründungspflicht bei `retired`; der Wechsel schreibt einen `care_event(category = bed_status_change)`. | ja |
| GP-FR-047 | MUST | Beet-Zusammenfassung (Kopf der Beetansicht): Fläche, Typ, Status, Bodenart, Sonneneinstrahlung, aktive Pflanzen (Anzahl, Spezies), offene Aufgaben, letzte Pflege, nächste Fälligkeit. | ja |
| GP-FR-048 | MUST | Pflanzkübel sind beweglich (REQ-002 „mobile Positionierung"): Ein `planter` darf auch dann verschoben werden, wenn Pflanzen darin stehen — ohne Bestätigung, weil die Pflanzen mitwandern (beet-lokaler Rahmen). Für Bodenbeete mit Pflanzen fragt die UI nach (Plan-Korrektur vs. physische Verlegung). | ja |
| GP-FR-049 | COULD | Beet archivieren mit Ausblendung aus Listen (`retired` + Filter „Archivierte anzeigen"). | nein |
| GP-FR-050 | MUST | Beete einem Mitglied zuweisen (bestehendes `location_assignments`, REQ-024/REQ-049 §3.5): Zuweisung ist im Panel sichtbar und als Filter „Meine Beete" nutzbar; sie ist **keine** Schreibgrenze. | ja |
| GP-FR-051 | SHOULD | Fotos am Beet (`Location.photo_refs`, `cover_photo_ref`, Attachment-Kategorie `location`) über das Galerie-Muster aus REQ-034; Erfassung über REQ-052 Profil `gallery`. | nein |
| GP-FR-052 | COULD | Beet-QR-Etikett (bestehender `plant_label`-Pfad, Vorlage `location_label`) mit Deep-Link in den Feldmodus. | nein |
| GP-FR-053 | MUST | Beet umbenennen ändert nur `name`; `slot_id` und alle Keys bleiben unverändert (Historie hängt per `placed_in` an Slots, F-07). | ja |
| GP-FR-054 | COULD | Beet teilen / zusammenlegen (`POST /locations/{key}/split`, `POST /locations/merge`): Slots werden anhand ihrer Geometrie dem neuen Beet zugeordnet, Historie folgt dem Slot; Tasks am Beet werden dem Nutzer zur Zuordnung vorgelegt. | nein |
| GP-FR-055 | MUST | **Beet räumen / Saisonende** (F-02): Aktion „Beet räumen" beendet alle aktiven Runs des Beets in einem Schritt (je Pflanze `removed_on`, `termination_type` wählbar: `harvested`, `senesced`, `died`, `cancelled`), schreibt einen `care_event(category = clearing)` und gibt die Slots frei. Slots abgeschlossener Runs bleiben als Historie erhalten (`archived_at` gesetzt) und blockieren weder V-06 noch V-08 (nur aktive und geplante Slots zählen). Der nächste Run im Beet darf dieselben Positionen neu belegen oder neue erzeugen. | ja |

### 10.2 Standortmerkmale des Beets (v1.3)

`sun_exposure` mit fünf Werten (§10.1) reicht für die Pflanzenwahl nicht: Ein Beet mit Morgensonne ist für Salat etwas anderes als eines mit Nachmittagssonne, ein Beet unter einem Obstbaum ist im April sonnig und im Juli schattig. Alle Felder sind **optional, Standard `unknown`**, manuell erfassbar und zwingen den Bepflanzen-Dialog zu nichts. Quelle der Befunde: `spec/analysis/outdoor-garden-planner-review-req-053-v1.3.md`. Fachliche Zahlen wurden am 2026-10-15 geprüft (O-17/E-10, `spec/analysis/agrobiology-thresholds-req-053.md`, Quelle je Wert); was dort als `unverified` steht, bleibt konfigurierbar und so markiert.

**Datenregel Reihenabstände (E-15):** Obst-Reihenabstände aus dem Erwerbsobstbau werden für den Hausgarten nicht übernommen; `row_spacing_cm` bleibt `null`, solange keine Hausgarten-Quelle vorliegt.

```yaml
Location.site_conditions:                     # neu, eingebetteter Werttyp
  sun_profile:
    sun_window: morning | midday | afternoon | all_day | mixed | unknown
    direct_sun_hours_summer: float | null     # optional, manuell oder berechnet
    foliage_shade_in_summer: bool             # Laubschatten: Frühjahr sonnig, Sommer schattig
    source: manual | computed                 # §29, bestehendes sun_exposure_source
  microclimate:
    frost_risk: low | normal | high | unknown
    cold_air_pocket: bool
    heat_retention: none | wall | building | unknown
  wind_exposure: sheltered | normal | exposed | unknown
  slope_deg: float | null                     # optional, sonst Site.plan.terrain geerbt
  aspect_deg: float | null
  access_sides: list[N|E|S|W]                 # optional, Zugangsseiten für die Pflege
  flags: list[root_competition | allelopathy_risk]   # Wurzeldruck/Gehölzkonkurrenz
```

`Location.sun_exposure` bleibt als **Grobwert** erhalten (aus `sun_profile` abgeleitet, wenn `computed`; sonst manuell). Das bestehende `frost_exposed` (Bool, §20.3) wird durch `microclimate.frost_risk` ersetzt und migriert (`true` → `high`, `false` → `normal`, Nachtrag WP 3.9 und #2512).

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-157 | MUST | **Sonne/Schatten als Kachelauswahl** mit Icon + Text (nicht Dropdown): ☀ Volle Sonne · ⛅ Halbschatten · ☁ Schatten · ● Tiefschatten · ? Unbekannt (Standard). Jede Kachel trägt einen Hilfetext mit Definition („Volle Sonne: mehr als 6 Stunden direktes Sonnenlicht an einem Sommertag“, „Halbschatten: 3–6 Stunden“, „Schatten: 2–3 Stunden“, „Tiefschatten: weniger als 2 Stunden“, „Unbekannt: noch nicht erfasst“; Glossar UI-NFR-011; Schwellen konfigurierbar, GP-FR-164). Eingabeort: Anlegedialog, Eigenschaftenpanel/Beet-Sheet, Beet-Zusammenfassung (GP-FR-047); im Feldmodus lesend, Ändern über „Bearbeiten“; Kacheln ≥ 64 px. **Stapel-Zuweisung:** „Sonne für alle gewählten Beete setzen“ (30 Parzellen). `deep_shade` ist ergänzt, damit die Skala zu `Species.shade_tolerance` passt (O-16 entschieden). | ja |
| GP-FR-158 | SHOULD | **Sonnenprofil:** `sun_window` als Chip-Auswahl „Morgen / Mittag / Nachmittag / ganztägig“ (Stundenzahl optional, kein Zählen nötig); Eingabe auch im Feldmodus als Beet-Sheet mit 3–4 Chips (GP-UX-057). | nein |
| GP-FR-159 | SHOULD | **Laubschatten:** Schalter „Laubschatten im Sommer“ (`foliage_shade_in_summer`) belegt die Saisonwerte vor (Frühjahr sonnig, Sommer schattig); die Berechnung bleibt §29. | nein |
| GP-FR-160 | MUST | **Eignungs-Ampel `site_fit`** im Bepflanzen-Dialog (§11): Beetmerkmal gegen Anspruch der Art, Werte `ok / marginal / poor / unknown`, Begründung im Klartext („Beet: Halbschatten — Tomate braucht Vollsonne“). **Nicht blockierend**, analog zu Fruchtfolge-/Mischkultur-Hinweisen. `unknown` auf einer Seite ergibt keinen Hinweis. Grundlage (O-16 entschieden, E-05): **Anspruch** `Species.light_requirement ∈ {full_sun, partial_shade, shade}` (neu, REQ-001) gegen `Location.sun_exposure`; **Toleranz** `Species.shade_tolerance` (bestehend, vier Stufen) weitet die Gelb-Zone. Mapping (reine Funktion `site_fit_calculator.compute(sun_exposure, light_requirement, shade_tolerance) → ok \| marginal \| poor \| unknown`, Python + TS-Port gegen gemeinsame Vektoren, §19.6): `ok`, wenn `sun_exposure` genau der Anspruchsstufe entspricht; **schattiger als der Anspruch:** `marginal` bei genau einer Stufe Abstand, wenn `shade_tolerance` diese Stufe deckt, sonst `poor`; ist `shade_tolerance = null` (nicht belegt) und das Beet genau eine Stufe schattiger, ebenfalls `marginal` mit der Begründung „Toleranz unbekannt" (kein stiller `poor`); `poor` ab zwei Stufen; **sonniger als der Anspruch** (Waldmeister auf dem Vollsonnenbeet — Verbrennung, Trockenstress): `marginal` bei genau einer Stufe, `poor` ab zwei Stufen; `unknown`, wenn eine Seite fehlt. Stufenfolge `full_sun > partial_shade > shade > deep_shade`. Die Testvektoren (§19.6) enthalten je einen Fall pro Zelle dieser Matrix, einschließlich der sonnigen Seite. Der Baustein ist generisch (`site_suitability`: Beetmerkmal ↔ Artanspruch) und wird von REQ-054 als Kriterium wiederverwendet. | ja |
| GP-FR-161 | SHOULD | `site_fit` berücksichtigt zusätzlich `microclimate.frost_risk` ↔ Frostempfindlichkeit/Winterhärte, `wind_exposure` ↔ `Species.support_required` und `soil_profile.drainage` ↔ `waterlogging_tolerance`. | nein |
| GP-FR-162 | SHOULD | **Mikroklima/Frostrisiko** (`microclimate`): manuell; `frost_risk` fließt in die Frost-Frühwarnung (REQ-046/REQ-392) **beetgenau** statt gartenweit ein. Ableitung der Senke aus `Site.plan.terrain` bleibt §29. | nein |
| GP-FR-163 | SHOULD | `wind_exposure` manuell; später Ableitung aus `Site.plan.prevailing_wind_deg` und Hindernissen (`fence`/`wall`/`shrub` mit `height_m`/`opacity`) — jetzt nur das Feld, kein Algorithmus. | nein |
| GP-FR-164 | SHOULD | Schwellen und Referenzdatum der Sonnenklassen (H-006) sind **Konfiguration** am Tenant/Site, nicht fest; Standard (geprüft O-17, RHS-Definition): `full_sun` > 6 h, `partial_shade` 3–6 h, `shade` 2–3 h, `deep_shade` < 2 h direkter Sonne an einem Hochsommertag (Referenz 21. Juni, statt Äquinoktium). | nein |
| GP-FR-165 | COULD | `flags` `root_competition`, `allelopathy_risk` (z. B. unter Walnuss/Birke) als Auswahl; keine Berechnung. | nein |
| GP-FR-166 | SHOULD | **Erreichbarkeit:** Hinweis `bed.reach_too_wide`, wenn die kürzeste Seite die konfigurierbare Schwelle übersteigt und kein Weg angrenzt; nur Hinweis, nie Fehler. Ein Gartenobjekt `path` macht eine Beetseite erreichbar, wenn seine Kante höchstens 0,3 m von dieser Beetkante entfernt ist (Kante zu Kante; je Site konfigurierbar als `reach_thresholds.path_access_max_distance_m`, 0–1 m; Betreiberentscheidung 2026-11-09, #2703); Wege an zwei gegenüberliegenden Seiten quer zur Beetbreite ergeben beidseitigen Zugang, der stärkere Zugang aus `access_sides` und Wegen gilt. Richtwerte 1,2 m bei beidseitigem, 0,6 m bei einseitigem Zugang sind **bestätigt** (OSU/ISU Extension, MKUEM RLP 2019 — O-17). Optional `access_sides` manuell. | nein |
| GP-FR-167 | COULD | Abgeleitet, nur lesend: `nearest_water_source_m` (Luftlinie im Plan-Rahmen) als optionale Spalte der Beetliste (GP-FR-042). | nein |
| GP-FR-168 | COULD | Hang pro Beet (`slope_deg`/`aspect_deg`, vom Site-Wert geerbt, überschreibbar); `orientation` wird bei gesetztem `aspect_deg` abgeleitet (GP-FR-017, Abgleich mit §20.8). | nein |
| GP-FR-169 | SHOULD | **Karten-Ebenen** „Sonne“, „Feuchte/Drainage“, „Frostrisiko“ (Muster + Icon, nie nur Farbe; Schalter wie GP-FR-031); GP-FR-047 (Beet-Zusammenfassung) zeigt zusätzlich Drainage und Wasserregime. | nein |
| GP-UX-057 | SHOULD | Beet-Sheet im Feldmodus mit Kurzbefragung: Chips „Sonne: Morgen/Mittag/Nachmittag/ganztägig“, „Feucht/Normal/Trocken“, „Windig“; passt zu GP-UX-029. Kein Formular mit acht Feldern je Beet. | nein |

---

## 11. Pflanzplanung innerhalb eines Beetes

### 11.1 Ablauf

1. Beet wählen → „Bepflanzen". Der Dialog zeigt **Fruchtfolge-Hinweis** (letzte Familie im Beet, Jahre seit demselben Anbau, Anbaupause der gewählten Familie) und **Mischkultur-Hinweis** zu bereits geplanten/aktiven Nachbarn (GP-FR-131/132, MVP).
2. Spezies/Sorte wählen (bestehende Stammdaten, Favoriten zuerst); Anzahl **oder** „so viele wie passen". Angezeigt werden Endhöhe/-breite und ob eine Rankhilfe nötig ist (`mature_height_cm`, `mature_width_cm`, `support_required` aus dem Steckbrief, W-001/W-005).
3. Layout wählen: `grid` (quadratisch, `row_spacing = spacing`), `rows` (Reihen mit eigenem Reihenabstand), `triangular` (versetzt; `row_spacing` ist **abgeleitet** = spacing × 0,866, nicht editierbar; der Dialog zeigt die berechnete Mehrzahl statt „~15 %"), `zone` (eine Fläche mit Kapazität, Standard für Direktsaat), `free` (manuell gesetzte Positionen; Standard für Gehölze).
4. Abstände: Pflanzabstand `spacing_cm`, Reihenabstand `row_spacing_cm` (nur `rows`), Reihenrichtung `row_direction ∈ {along_length, along_width}`, Randabstand längs/quer (`edge_margin_along_cm` = spacing/2, `edge_margin_across_cm` = row_spacing/2 als Standard), Tiefe mit `depth_kind ∈ {sowing, planting}`; bei Direktsaat zusätzlich `sowing_spacing_cm` und `thinning_to_cm`. Vorbelegung: Steckbrief (`Species.spacing_cm`, `row_spacing_cm`), sonst „zuletzt verwendet" für diese Spezies im Tenant (F-11), sonst leer mit Hinweis.
5. Vorschau auf dem Beet; Pflanzen verschieben/entfernen; bei mehreren Entries: Zonen oder **alternierende Reihen** zuweisen (Möhre/Zwiebel — GP-FR-070 Reihenzuweisung ist MVP, Zonen-Mischkultur SHOULD).
6. Durchlauf anlegen (`PlantingRun.status = planned`, `plan_role = main_crop | green_manure`) → Slots mit Geometrie werden erzeugt, `run_planned_at`-Edges mit **Zeitfenster** gesetzt (GP-FR-065).
7. Später: Durchlauf starten → Pflanzen erzeugen (REQ-013 `create-plants`, `assign_to_slots` nutzt die geplanten Slots). Direktsaat in `zone`/`row`-Slots erzeugt **keine** Pflanze je Samen, sondern den Zustand `sown`; Pflanzen entstehen nach dem Vereinzeln (`thinning`) oder bleiben als Zonen-Bestand (§11.3).

### 11.2 Anforderungen

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-060 | MUST | `PlantingRunEntry` erhält `row_spacing_cm` (5–1 500), `row_direction ∈ {along_length, along_width}`, `edge_margin_along_cm`/`edge_margin_across_cm` (0–200, Standard spacing/2 bzw. row_spacing/2 — der Randabstand spacing/2 ist Konvention, fachlich unbelegt (O-17), konfigurierbar), `depth_cm` (0–100) mit `depth_kind ∈ {sowing, planting}`, `sowing_spacing_cm`/`thinning_to_cm` (optional, Direktsaat), `layout_strategy ∈ {grid, rows, triangular, zone, free}`, `placement_hint`, `row_assignment: list[int] \| null` (Reihenindizes, **ab 0 gezählt**, die dieser Entry bei alternierenden Reihen belegt, GP-FR-070; `null` bei Monokultur); `spacing_cm` bleibt, Obergrenze wird auf **1 500 cm** angehoben (Gehölze, Streuobst — W-004; O-17: Hochstamm-Kirsche/Walnuss 12–15 m, RLP-Förderung „mindestens 15 m"). Semantik: `grid` setzt `row_spacing = spacing`; `triangular` leitet `row_spacing = spacing × 0,866` ab (W-002). | ja |
| GP-FR-061 | MUST | Vorbelegung aus dem Steckbrief nutzt die **vorhandenen** Schemafelder `Species.spacing_cm` (Range-String, numerisch geparst: unterer Wert), `mature_height_cm`, `mature_width_cm`, `support_required`, `sowing_depth_cm`, `recommended_container_volume_l`, `min_container_depth_cm` (`species.schema.yaml:150–174, 347`); **neu** nur `row_spacing_cm` (O-11, W-001 — kein `spacing_cm_default`-Duplikat) und `light_requirement` (E-05, für GP-FR-160). Die Steckbrief-Vorlage erhält die Abschnitte „Pflanzabstand und Reihenabstand" und „Lichtbedarf", `plant-info-to-seed-yaml` extrahiert sie, `seed-data-validator` prüft 5–1 500 cm bzw. das Enum. **Werte nur mit Quelle** (E-10): fehlt eine belastbare Quelle, bleibt das Feld `null` und steht in der Lückenliste — kein stiller Default. Gemessen 2026-10-15: `Species.spacing_cm`, `mature_height_cm`, `mature_width_cm` sind Range-Strings (`species.py:384–386`); **`Species.row_spacing_cm` ist ebenfalls ein Range-String** (Schema-Entscheidung, REQ-001 v4.11) und läuft durch denselben Parser „unterer Wert", der Teil von Welle 1 ist. Fehlt der Wert, gilt „zuletzt verwendet" (F-11), sonst leer mit Hinweis — kein stiller Default. `compute_layout` warnt, wenn `spacing_cm < mature_width_cm × 0,7` (Faktor 0,7 unverifiziert, konfigurierbar). | ja |
| GP-FR-062 | MUST | **Layout-Berechnung** ist eine reine Funktion `compute_layout(bed_geometry, entry_layout, max_count?) → LayoutResult{slots, count, capacity_max, warnings}` in `domain/calculators/planting_layout_calculator.py`; sie liefert Punkte im Beet-Rahmen, die vollständig innerhalb der Beetgeometrie **minus Randabstand als Inset** liegen (Distanz zur Polygonkante, nicht nur Point-in-Polygon — W-002). **Obergrenze (SR-004):** Vorab-Schätzung `Fläche ÷ (spacing × row_spacing)`; ergibt sie > 2 000 Positionen, bricht die Funktion mit 422 `layout.too_many_positions {estimated}` ab, bevor sie Punkte erzeugt. | ja |
| GP-FR-063 | MUST | Die Berechnung ist über `POST …/locations/{key}/planting-layout/preview` abrufbar (ohne Persistenz) und wird vom Dialog für die Live-Vorschau genutzt; derselbe Algorithmus läuft im Frontend (TypeScript-Port mit identischen Testvektoren, §19.6) für verzögerungsfreie Vorschau — die Server-Antwort ist bei Abweichung maßgeblich. | ja |
| GP-FR-064 | MUST | Das Ergebnis der Planung wird als **Slots** persistiert: `slot_role = position` (ein Punkt, `capacity_plants = 1`), `row` (Polylinie mit `capacity_plants = n`), `zone` (Polygon mit `capacity_plants = n`). Die `slot_id` folgt dem bestehenden Format `LOCATION_NNN` (z. B. `BEET03_R2P05`). | ja |
| GP-FR-065 | MUST | **Geplante Pflanzung mit Zeitfenster** (F-01): Edge `run_planned_at` (planting_runs → slots) mit `entry_key`, `planned_species_key`, `sequence`, `planned_from` (= `run.planned_start_date`), `planned_until` (= geplantes Ende aus Kulturdauer des Steckbriefs oder manuell; `null` = offen). Ein Slot darf für mehrere Runs reserviert sein, solange sich die Zeitfenster **nicht überlappen** (Nachkultur: Feldsalat nach Tomate im selben Slot). Konflikt → 409 `slot.already_planned {conflicting_run_key, overlap_from, overlap_until}`. Aktive Pflanzen (`placed_in`, `removed_on = null`) blockieren jede Reservierung, deren `planned_from` vor dem erwarteten Ende des aktuellen Runs liegt (Hinweis, Reservierung mit `planned_from` danach ist erlaubt). | ja |
| GP-FR-066 | MUST | **Tatsächliche Pflanzung:** `create-plants` (REQ-013) nutzt bei `assign_to_slots = true` die `run_planned_at`-Slots in `sequence`-Reihenfolge; überzählige geplante Slots bleiben reserviert, bis der Run `completed`/`cancelled` wird oder der Nutzer sie freigibt. | ja |
| GP-FR-067 | MUST | Pflanzen auf dem Plan: Jede `PlantInstance` mit `placed_in` wird am Slot-Zentrum gezeichnet; bei `slot_role = zone` werden Pflanzen gleichmäßig in der Zone verteilt (nur Darstellung, keine persistierte Einzelposition). | ja |
| GP-FR-068 | MUST | **Einzelne Pflanze verschieben** = Slot-Geometrie ändern (`slot_role = position`), weil Slot und Pflanze 1:1 sind. Die UI nennt das „Position korrigieren"; die Änderung wird als `care_event(category = position_corrected)` protokolliert. Pflanzen in Zonen haben keine Einzelposition und sind nicht verschiebbar (Hinweis in der UI). | ja |
| GP-FR-069 | MUST | Verschieben in ein **anderes Beet** ist kein Drag, sondern die bestehende Umsetzen-Logik (Task `transplant`, REQ-006) — der Plan bietet dafür „Umpflanzen nach …" im Kontextmenü. | ja |
| GP-FR-070 | MUST | **Mischkultur im Beet:** Mehrere Entries verschiedener Spezies werden auf **alternierende Reihen** verteilt (**eine** Semantik: am Entry `row_assignment: list[int]` = Reihenindizes (0-basiert: die erste Reihe ist `0`), die dieser Entry belegt, z. B. Entry 1 `[0, 2, 4]`, Entry 2 `[1, 3]`; die Mengen der Entries eines Runs sind disjunkt, jeder Slot einer Reihe trägt den `entry_key` seines Entries; MVP — F-11, REQ-013 §2) oder auf disjunkte Zonen (`slot_role = zone`, SHOULD); der Dialog zeigt die Kompatibilität der gewählten Spezies (REQ-028 `check_compatibility`). | ja (Reihen), SHOULD (Zonen) |
| GP-FR-071 | COULD | **Begleit-/Randbepflanzung:** Ein Entry kann `placement_hint ∈ {interior, edge, corner}` tragen; `edge` erzeugt Positionen entlang der Beetkante mit `spacing_cm`. | nein |
| GP-FR-072 | MUST | **Freie Positionen** (`layout_strategy = free`): Der Nutzer setzt Punkte per Klick/Tipp; Mindestabstand = `spacing_cm` wird als Hinweis (gelber Ring), nicht als Blocker durchgesetzt. | ja |
| GP-FR-073 | MUST | Pflanzenanzahl: Bei „so viele wie passen" liefert `compute_layout` die Maximalzahl (gedeckelt durch GP-FR-062); der Nutzer kann sie reduzieren. Die Kapazitätsanzeige nimmt die **Anzahl aus `compute_layout`**, nicht aus der Fläche (Randeffekte kleiner Beete). `slot_capacity_calculator.calculate_plants_per_m2` wird auf `(spacing_cm, row_spacing_cm=None, strategy)` erweitert — heute rechnet sie 1/spacing² und ignoriert den Reihenabstand (Tomate 60 × 80: 2,08/m² statt 2,78; W-003, nachgemessen `slot_capacity_calculator.py:32`). Für `triangular` gilt 1/(spacing² × 0,866). | ja |
| GP-FR-074 | SHOULD | Sukzessionspläne (REQ-013 `succession_plans`) reservieren Slots je Charge; der Plan zeigt reservierte, noch leere Positionen gestrichelt mit Datum. | nein |
| GP-FR-075 | COULD | Pflanzen einer Zone nachträglich in Einzelpositionen „auflösen" (Zone → n Positionen). | nein |
| GP-FR-076 | COULD | Reihen als bearbeitbare Linie: Reihe verschieben verschiebt alle Positionen der Reihe. | nein |
| GP-FR-077 | MUST | **Vorjahr am Beet** (F-08): Die Info-Blase (GP-UX-006) und der Beetkopf zeigen „Vorjahr: {Familie/Spezies}" aus GP-API-039; ein Jahr-Umschalter in der Planansicht (`?year=`) färbt Beete nach der Familie des gewählten Jahres. | ja |
| GP-FR-078 | COULD | „Saison kopieren": Runs eines Jahres als geplante Runs des Folgejahres duplizieren (ohne Pflanzen), mit Fruchtfolge-Warnungen je Beet. | nein |

### 11.3 Zustände einer Pflanzung (verbindliche Begriffe)

| Begriff | Definition | Darstellung |
|---------|------------|-------------|
| **geplant** | `run_planned_at`-Edge mit Zeitfenster existiert, keine `PlantInstance` im Slot | gestricheltes Icon, Spezies-Initiale, `planned_from` |
| **gesät** (W-015) | `zone`/`row`-Slot mit `sown_at` gesetzt, noch keine Pflanzen (Direktsaat, vor dem Auflaufen/Vereinzeln) | Saatreihen-Muster, Datum |
| **tatsächlich** | `PlantInstance` mit `placed_in`, `removed_on = null` | volles Icon, Phasenfarbe |
| **in Ernte** (W-015) | Pflanze steht, mindestens ein `harvest_batch` referenziert sie (`harvest_type = partial/continuous`) | Icon mit Erntesymbol |
| **geerntet** | `termination_type = harvested`, `removed_on` gesetzt | nur in Historie |
| **ausgefallen** (W-015) | `termination_type = died` mit `termination_cause`; Slot ist frei für Nachpflanzung. *(v1.17: bis v1.16 stand hier `∈ {died, senesced}`.)* `senesced` ist das natürliche Ende einer Kultur und kein Ausfall: die Pflanze ist **abgeschlossen** (Zustand „historisch“), eine Folgekultur gehört zur Sukzession bzw. Planung (§16, GP-FR-133), nicht zum Nachpflanzen. Seneszieren vor der Zeit (Schossen, Hitze, Mangel) erfasst der Nutzer als `died` mit Ursache. Grund: agrobiologisches Review der Abnahme Welle 10 (WP 10.15); das Nachpflanz-Angebot folgt dem (`planting/thinningLogic.ts`, `REPLANT_TERMINATIONS`), der Zustandsrechner (GP-FR-192) seit #2906 ebenfalls (`FAILED_TERMINATIONS = {died}`, Vektor `plant-state-008`). **Nachpflanzen und Fruchtfolge (#2888):** Eine Nachpflanzung nennt die Pflanze, die sie ersetzt (`replant_of_plant_key` an GP-API-025). Für genau diese Prüfung zählt die ersetzte Pflanze im Jahr ihres Ausfalls nicht als Vorkultur, sofern sie zu diesem Beet und Tenant gehört, `termination_type = died` hat und im laufenden Kalenderjahr (UTC) und nach `rotation_reset_at` endete; sonst wird die Angabe ohne Fehler ignoriert (kein Hinweis auf fremde Pflanzen). Andere Pflanzen des Beets, Vorjahre (auch Vorjahre derselben mehrjährigen Pflanze), Nacherfassungen sowie Zeitstrahl und Rotationsmatrix bleiben unverändert. Wird dieselbe Familie nachgepflanzt, bleibt ein Resthinweis aus der `termination_cause` der ersetzten Pflanze: `disease`/`pest` → `rotation.replant_after_biotic_failure` (`WARNING`, „Trotzdem pflanzen“ mit Grund wie bei jedem überstimmbaren Fruchtfolge-Hinweis); keine Ursache oder `unknown` → `rotation.replant_cause_unknown` (`INFO`, kein Grund nötig); `frost`, `heat`, `drought`, `waterlogging`, `neglect`, `mechanical` → kein Hinweis. Nie `CRITICAL`, nie ein Blocker (D-09). Offen bleibt das Datenmodell bodenbürtiger Ursachen (Ursachenklasse, Persistenz des Erregers, Wirtskreise, Saisondefinition, Substrat); es wird mit REQ-054 H-10 (`soil_hazards[]`, `soil_persistence_years`) geplant, nicht in REQ-053 (Betreiberentscheid 2026-11-12, #2888). | Historie; Nachpflanz-Vorschlag am Slot |
| **historisch** | `removed_on != null` (jede Ursache) | Historie/Zeitstrahl |

### 11.4 Pflanzeninfo beim Überfahren und grafische Pflanzenzustände (v1.3)

Zu **jeder Pflanze** auf dem Plan sollen die wichtigsten Informationen beim Überfahren (Hover; auf Touch per Tipp, GP-UX-040) erscheinen, und ihr **Zustand** soll am Marker ohne Öffnen ablesbar sein. Die Seite „Pflanzen-Detail“ bleibt die ausführliche Ansicht; der Plan zeigt nur, was für die Entscheidung „muss ich hier etwas tun?“ nötig ist.

**Inhalt der Pflanzen-Info (GP-FR-190):** Sie ist bewusst kurz (ein Blick, max. acht Zeilen) und nur mit den Angaben gefüllt, die vorliegen; Leeres entfällt.

| Zeile | Inhalt | Quelle |
|-------|--------|--------|
| Kopf | Foto-Vorschau (Titelbild, falls vorhanden), Artname (Anzeigename, darunter wissenschaftlich), Sorte, `instance_id` | `PlantInstance`, Species/Cultivar, Attachments |
| Phase | Phasenname mit Phasenfarbe und Fortschritt „{aktuell} d / {typisch} d“ (UI-NFR-016 R-014); nächste Phase mit voraussichtlichem Datum, falls berechenbar | REQ-003, `current_phase_key` |
| Alter | „gepflanzt am {Datum} · {n} Tage“; bei Direktsaat „gesät am …“ | `planted_on`, `sown_at` |
| Position | Beet · Reihe/Slot (z. B. „Hochbeet 3 · Reihe 2, Pos. 5“) | `slot_key` |
| Pflege | letzte Pflege je Kategorie (zuletzt gegossen, zuletzt gedüngt) und **nächste fällige Aufgabe** mit Datum; überfällige hervorgehoben | `care_events`, `tasks` |
| Handlungsbedarf | die Gründe des Aufmerksamkeits-Badges im Klartext (GP-UX-060), z. B. „2 Aufgaben überfällig“, „Befund: Blattläuse (offen)“ | `plant_state_calculator` |
| Ernte | Erntefenster („erntereif ab …“) und bisher geerntete Menge, falls `harvest_batches` vorliegen | REQ-007 |
| Hinweis | Mischkultur-/Standorthinweis am Platz (`site_fit`, GP-FR-132), falls nicht `ok` | §10.2, §16 |

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-190 | MUST | **Pflanzen-Info als Mouseover:** Hover über einen Pflanzen-Marker (Desktop), Fokus per Tastatur (Pfeile im betretenen Beet, GP-NFR-068) und Tipp (Touch → Sheet, GP-UX-040) zeigen die Pflanzen-Info der Tabelle oben. Ergänzt GP-UX-006 (Objekte) um die Pflanzenebene. Unter dem LOD-Schwellwert (GP-NFR-067) zeigt der Cluster statt dessen die Zusammenfassung „{n} Pflanzen · {m} mit Handlungsbedarf“. | ja |
| GP-FR-191 | MUST | **Keine Abfrage pro Hover:** Die Pflanzen-Info und der Zustand (GP-FR-192) kommen gebündelt mit den Plandaten des sichtbaren Beets (`GET …/locations/{key}/plant-states`, GP-API-054; eine Anfrage je Beet statt je Pflanze). Das Überfahren rendert ausschließlich aus dem lokalen Zustand. Aktualisierung nach jeder Plan-/Pflege-Aktion und bei Rückkehr in den Vordergrund; im Feldmodus offline der zuletzt geladene Stand mit Zeitstempel (GP-UX-024). | ja |
| GP-FR-192 | MUST | **Pflanzenzustand als reine Funktion:** `plant_state_calculator.compute(plant, phase, tasks, care_events, findings, now) → PlantVisualState{lifecycle, phase_key, phase_progress, attention[], harvest_ready}` im Domain-Layer ohne I/O; derselbe Algorithmus läuft als Frontend-Port (§19.6), damit Plan, Tooltip, PDF und Feldmodus nie abweichen. `lifecycle ∈ {planned, sown, active, harvesting, failed, historic}` entspricht §11.3; `attention[]` ist die nach GP-UX-060 sortierte Liste der Handlungsgründe. | ja |
| GP-UX-058 | MUST | **Hover-Verhalten:** Erscheint nach 300 ms Verweilzeit, verschwindet mit Esc oder beim Verlassen von Marker **und** Blase; die Blase ist hoverbar und bleibt sichtbar, bis der Zeiger sie verlässt (WCAG 1.4.13). Während Drag, Zeichnen und Zoom/Pan erscheint keine Blase. Der Inhalt ist auch per Tastaturfokus und Screenreader erreichbar (`aria-describedby`, derselbe Text). Die Blase verdeckt den Marker nicht (Platzierung mit Kollisionsvermeidung, GP-UX-047). Ein Klick/Tipp auf „Details“ öffnet die Pflanzen-Detailseite. | ja |
| GP-UX-059 | MUST | **Grafische Zustandskanäle am Marker** (ein Marker kombiniert höchstens diese vier Kanäle, Farbe ist nie der einzige Träger, GP-UX-015): siehe Tabelle unten. | ja |
| GP-UX-060 | MUST | **Aufmerksamkeits-Badge:** Pro Marker wird höchstens **ein** Badge gezeichnet, gewählt nach Priorität *Problem/Befund > Frostgefahr > überfällige Aufgabe > Wasserbedarf > erntereif*; alle weiteren Gründe stehen in der Pflanzen-Info. Cluster zeigen die Zahl der Pflanzen mit Badge und die höchste Priorität. | ja |
| GP-UX-061 | SHOULD | Ebene „Pflanzenzustand“ (Schalter in GP-FR-031) und Filter „nur Pflanzen mit Handlungsbedarf“; Legende (GP-UX-005) und PDF-Legende erklären alle Kanäle und Badges. | nein |
| GP-UX-062 | MUST | **Barrierefreiheit der Zustände:** jeder Marker hat ein `aria-label` mit Art, Phase und Handlungsbedarf („Tomate, Blüte, 2 Aufgaben überfällig“); Kontrast der Zustandskanäle ≥ 3:1 in Light und Dark (GP-UX-016); Formen unterscheiden sich auch in Graustufen und für Farbfehlsichtige. | ja |
| GP-NFR-073 | SHOULD | Berechnung des Zustands für 5 000 Pflanzen ≤ 50 ms im Client; Blase erscheint ≤ 100 ms nach Verweilzeit. | ja |
| GP-API-054 | MUST | `GET /t/{slug}/locations/{key}/plant-states` → Liste `{plant_key, slot_key, species/cultivar-Anzeige, instance_id, planted_on, phase{key,name,elapsed_d,typical_d,next_phase_eta?}, last_care{watering?, feeding?}, next_task?, attention[], harvest{ready_from?, harvested_total?}, cover_photo_ref?}`; nur Felder der Pflanzen-Info (keine Notizen, keine Nutzernamen, SR-006/SR-020); Rolle: alle Mitglieder. | alle Rollen |

**Zustandskanäle (GP-UX-059):**

| Kanal | Bedeutet | Darstellung |
|-------|----------|-------------|
| Ring-Farbe | Wachstumsphase | Phasenfarbpalette UI-NFR-016 R-006; Dormanz blaugrau (R-004); bei Zoom ≥ Detailstufe zusätzlich Ringsegment als Phasenfortschritt (R-014) |
| Ring-Stil | Lebenszyklus (§11.3) | `planned` gestrichelt, 40 % Deckkraft, Datum; `sown` Saatpunkt-Muster; `active` durchgezogen; `harvesting` Ring mit Erntesymbol; `failed` graues Kreuz auf leerem Slot mit „Nachpflanzen“ (Jahres-/Historienansicht) |
| Füllung | Art | Icon bzw. Initiale der Spezies (GP-UX-015) |
| Badge (oben rechts) | Handlungsbedarf (GP-UX-060) | Problem/Befund: Warndreieck; Frostgefahr: Schneeflocke; überfällig: roter Punkt mit „!“; Wasserbedarf: Tropfen; erntereif: Haken/Korb |

*Datenverfügbarkeit.* Problem/Befund setzt Gesundheitsbeurteilung bzw. IPM (REQ-010, REQ-044) voraus und erscheint nur bei aktivem Modul; Frostgefahr nutzt `microclimate.frost_risk` (GP-FR-162) und die Frost-Frühwarnung (REQ-392/REQ-046); Wasserbedarf nutzt `irrigation_demands` (REQ-037). Fehlt eine Quelle, entfällt der Grund ohne Fehlermeldung.

---

## 12. Beetpflege

### 12.1 Aufgabenkatalog

Die geforderten Pflegearten werden auf `TaskCategory` abgebildet. Bestehende Werte bleiben; neue sind markiert. Die Zuordnung Kategorie → Fachereignis legt fest, welche Fachdaten bei Erledigung abgefragt werden (§12.3).

| Pflegeart | `TaskCategory` | Neu? | Fachereignis bei Erledigung |
|-----------|----------------|------|-----------------------------|
| Gießen | `watering` | nein (Code) | `watering_events` (Menge, Quelle) |
| Düngen | `feeding` | nein | `feeding_events` (Produkt, Menge; Flächendosierung g/m² oder L/m² nach REQ-004); ein direkter Eintrag über „Pflege protokollieren“ schreibt dasselbe `feeding_event`, wenn Produkt und Menge angegeben sind (#2854) |
| Mulchen | `mulching` | **neu** | `care_event` (Material, Menge, Schichtdicke) |
| Unkraut entfernen | `weeding` | **neu** | `care_event` |
| Boden lockern | `soil_loosening` | **neu** | `care_event` |
| Aussaat | `sowing` | **neu** | `care_event` + optional Run-Start |
| Pikieren | `pricking_out` | **neu** | `care_event` |
| Umpflanzen | `transplant` | nein | bestehende Umsetzen-Logik + `care_event` |
| Anbinden | `training` | nein | `care_event` |
| Ausgeizen | `ausgeizen` | nein (Enum-Wert bleibt — Umbenennung wäre ein Enum-Retirement; Anzeigename „Ausgeizen/Seitentriebe entfernen") | `care_event` |
| Rückschnitt | `pruning` | nein | `care_event` |
| Schädlingskontrolle | `pest_control` / `ipm` | nein | `treatment_applications` (REQ-010) bei Behandlung, sonst `care_event(observation)` |
| Krankheitskontrolle | `monitoring` | nein | `care_event(observation)` |
| Ernte | `harvest` | nein | `harvest_batches` (REQ-007) |
| Bodenverbesserung | `soil_amendment` | **neu** | `care_event` (Material, Menge); Materialien mit Nährstoffwirkung (`compost`, `manure`, `horn_shavings`) schreiben **zusätzlich** ein `feeding_event` mit Flächendosierung, damit die Düngebilanz (GP-FR-125) sie sieht (W-007) |
| Kompost hinzufügen | `soil_amendment` mit `material = compost` | — | `care_event` |
| Kalkung | `liming` | **neu** | `care_event` (Produkt, g/m², Kalkart `calcium_carbonate \| dolomite \| quicklime`); gilt für Bodenbeete — `ph_adjustment` ist Gießwasser/Nährlösung (Kübel, Hydro, Zelt); pH-Absenkung im Boden = `soil_amendment` mit `sulfur` (W-007) |
| pH-Anpassung | `ph_adjustment` | **neu** | `care_event` (Produkt, Zielwert, Messwert) |
| EC-/Nährstoffkontrolle | `ec_check` | **neu** | `care_event(measurement)` |
| Spülen/Flush | `flush` | **neu** | `watering_events` mit `is_flush = true` (neu); nur für Locations mit `growing_medium_kind ≠ native_soil` angeboten (W-007) |
| Vereinzeln/Ausdünnen | `thinning` | **neu** | `care_event` (+ erzeugt Pflanzen aus `sown`-Zonen, §11.3) |
| Anhäufeln | `hilling` | **neu** | `care_event` |
| Umbrechen/Einarbeiten | `tillage` | **neu** | `care_event` (Gründüngung einarbeiten beendet den `green_manure`-Run) |
| Gründüngung einsäen | `sowing` mit Run `plan_role = green_manure` | — | Run + `care_event` |
| Abdecken / Abdeckung entfernen | `covering` / `uncovering` | **neu** | `care_event` (Material: `fleece`, `net`, `foil`, `frost_cover`); bestimmt `season_state = winter_covered` |
| Lüften (Gewächshaus/Frühbeet) | `ventilating` | **neu** | `care_event` |
| Beet räumen | `clearing` | **neu** | `care_event` (GP-FR-055) |
| Bodenanalyse | `soil_analysis` | **neu** | `care_event(measurements)` (§15) |
| Niederschlag erfassen | `rainfall` | **neu** | `care_event(quantity, unit = l_per_m2)` — Eingang der Wasserbilanz (GP-FR-113) |
| Handbestäubung | `pollinating` | **neu** | `care_event` |
| Fruchtausdünnen/Entlauben | `pruning` mit `pruning_kind ∈ {fruit_thinning, defoliation, shaping}` | — | `care_event` |

Die bestehenden Kategorien `care_reminder`, `seasonal`, `phenological`, `observation`, `maintenance`, `cleaning` bleiben erhalten.

**Was in der Düngebilanz zählt (GP-FR-125, #2854):** die `feeding_events`. Ein direkter Eintrag über „Pflege protokollieren“ (`POST /care-events`) schreibt mit demselben Baustein wie der Aufgabenabschluss eins, und zwar

- bei `feeding` mit Produkt (Katalogdünger oder Freitext-Name) **und** Menge > 0. Ein direkter `feeding`-Eintrag ohne Produkt oder ohne Menge sagt „gedüngt“, aber nicht womit und wie viel: Er bleibt der Protokolleintrag allein und trägt nichts zur Düngebilanz bei. Der Aufgabenabschluss schreibt das `feeding_event` weiterhin schon bei angegebener Menge;
- bei `soil_amendment` mit Nährstoffmaterial (`compost`, `manure`, `horn_shavings`) und Menge (W-007).

Stornieren oder Korrigieren eines direkten Eintrags nimmt sein `feeding_event` in derselben Transaktion zurück; eine Korrektur, die weiter eine Gabe nennt, schreibt eins für die korrigierte Menge. Direkte Einträge `watering` und `harvest` bleiben der Protokolleintrag allein; ihre Fachdokumente entstehen über die eigenen Formulare oder den Aufgabenabschluss. Das Düngeformular nach REQ-004 bleibt der Weg für Fertigation mit EC-/pH- und Ablaufwerten.

**Kontextabhängige Anzeige:** Der Erledigen-/Protokoll-Dialog bietet nur Kategorien an, die zum Beet passen: `flush`, `ec_check`, `ph_adjustment` nur für `growing_medium_kind ≠ native_soil`; `ventilating` nur in `greenhouse`/`cold_frame`/`tent`; `hilling`, `tillage`, `liming` nur für Bodenbeete (F-03).

### 12.2 Aufgabenarten

| Art | Abbildung | Quelle |
|-----|-----------|--------|
| einmalig | `Task` ohne `recurrence_rule` | REQ-006 |
| wiederkehrend | `Task.recurrence_rule` — kanonisch **RRULE** (RFC 5545, ADR-008 Grenze 1). **Entschieden (O-05, präzisiert E-02 v1.4):** ADR-008 wird in Welle 0 auf *Accepted* gehoben; **Phase 3 (ein Abschluss-Übergang) wird in Welle 4 nur für den Task-Abschluss umgesetzt** (`complete_task`, `tasks/batch/status`, `reopen`); die Kadenz-Vorschübe außerhalb der `RecurrenceEngine` bleiben ein eigener ADR-008-Strang. Gemessen am Code (2026-10-15): `recurrence_engine.py:51` parst bereits RRULE und hält einen croniter-Fallback für Alt-Cron-Strings (`:57`). Migration `M5_recurrence_cron_to_rrule` konvertiert daher nur **gespeicherte** Cron-Regeln (`0 8 * * 1` → `FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;BYMINUTE=0`), **parkt nicht konvertierbare Ausdrücke (E-14, #2346):** der Originalwert wandert nach `recurrence_rule_unconvertible`, `recurrence_rule` wird `null`, der Dry-Run-Report listet **jede** geparkte Regel, die Migrationskette hält wegen einer einzelnen Regel nicht an; setzt der Besitzer später eine neue RRULE, wird `recurrence_rule_unconvertible` am Task geleert (kein API-Feld, keine Benachrichtigung; E-16); der Fallback wird entfernt; REQ-006 wird auf RRULE umgestellt. Die API nimmt ab dann nur RRULE an (422 `recurrence.rrule_required`). | ADR-008 |
| geplant | `Task.status = pending` mit `due_date` in der Zukunft | REQ-006 |
| automatisch vorgeschlagen | `Task.origin = system`, `source` nennt den Erzeuger (`care_reminder_engine`, `irrigation_demand`, `season_engine`); vorgeschlagene Tasks sind `pending` mit Kennzeichen `suggested = true` (neu) und können angenommen (→ `suggested = false`) oder verworfen (`skipped`) werden | REQ-022, REQ-037, REQ-047 |
| tatsächlich ausgeführt | `care_event` (§13) | neu |

### 12.3 Anforderungen

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-080 | MUST | Tasks können an ein Beet (`entity_type = location`) gebunden werden; die bestehende `has_task`-Edge (`locations → tasks`) wird dafür genutzt. Die Task-Liste (`/tasks/queue`) erhält den Filter `location_key` (inkl. untergeordneter Locations). `entity_type = garden_object` ist für `compost`, `water_source`, `storage` zulässig (R-7.2). | ja |
| GP-FR-081 | MUST | Beim Anlegen einer Beet-Aufgabe kann der Nutzer wählen: „für das Beet" (eine Task) oder „für jede Pflanze im Beet" (n Tasks mit `task_cloned_from`, bestehende Clone-Logik). `POST /tasks` mit `for_each_plant` legt für „jede Pflanze" nur die n Pflanzen-Tasks an, in einer Transaktion und ohne Beet-Task (Grenzen wie beim Fan-Out: höchstens 200 Pflanzen, keine Pflege-Erinnerung, keine Wiederholung; Beet ohne Pflanzen legt nichts an); der Aufgaben-Dialog nutzt diesen Weg statt Anlegen + `/fan-out` (#2462). **Ausnahme vom `task_cloned_from`-Satz:** der Weg `for_each_plant` legt die Pflanzen-Tasks als Kopien der Beschreibung an, ohne Beet-Task und daher ohne `task_cloned_from`-Kante; `trigger_phase` und `recurrence_end_date` werden dabei nicht übernommen und nicht abgewiesen (bekannte Grenze, v1.9; ob ein 422 richtiger wäre, ist eine Betreiberfrage). Die Antwort ist eine Liste (OpenAPI-Union `TaskResponse \| list[TaskResponse]`). | ja |
| GP-FR-082 | MUST | `TaskCategory` wird um die in §12.1 markierten Werte erweitert; die Migration ist additiv (Enum-Erweiterung, keine Umbenennung — Memory „Enum-Retirement → Startup-Crash" beachten). | ja |
| GP-FR-083 | MUST | **Erledigen** läuft ausschließlich über den einen Abschluss-Übergang (ADR-008 Grenze 4: `POST /tasks/{key}/complete`). Der Übergang schreibt nach erfolgreichem Status-Wechsel **atomar** einen `care_event` mit `task_key`, Kategorie, `performed_by`, `performed_at`, Notiz, Fotos und — je nach Kategorie — dem Fachereignis-Bezug (§12.1). Atomar = ArangoDB-Stream-Transaktion über `tasks`, `care_events`, Fachcollection, Edges. **Umsetzung (WP 4.3):** Ein Task gehört zum Pflegeprotokoll, wenn er an ein Beet (`entity_type = location`) oder an eine Pflanze in einem Beet (`plant_instance` mit `location_key`) gebunden ist; Pflege-Erinnerungen (`category = care_reminder`) behalten ihren eigenen Strang (GP-FR-106). Fachdokumente: `watering_events` (Menge in l, ml oder `l_per_m2`; Pflanzen = `plant_keys` oder alle Pflanzen des Beetes), `feeding_events` (Gabe mit Menge; trockene Gaben `g`/`kg`/`g_per_m2` ohne Volumen; auch bei `soil_amendment` mit Nährstoffmaterial), `harvest_batches` (nach Karenz-Prüfung, Gewicht in g/kg). `treatment_applications` schreibt der Abschluss **nicht**: der PflSchG-Nachweis bleibt der IPM-Endpunkt mit Resistenz- und Karenzprüfung (§13.2). Ohne Bettbezug schließt der Übergang den Task allein; Pflegefelder ohne Bettbezug sind 422 `task.no_bed_context`. Wiederholung, abhängige Tasks und Benachrichtigung folgen nach dem Commit (eigener ADR-008-Strang). | ja |
| GP-FR-084 | MUST | Der Erledigen-Dialog fragt je Kategorie nur die relevanten Felder (Gießen: Liter/Quelle; Düngen: Produkt/Menge/Einheit; Mulchen: Material/Dicke; sonst: Notiz). Alle Felder außer dem Zeitpunkt sind optional — ein Tipp auf „Erledigt" ohne Eingaben ist zulässig (Feldmodus). | ja |
| GP-FR-085 | MUST | Rückdatieren: `performed_at` darf in der Vergangenheit liegen (max. 365 Tage), nie in der Zukunft (§22). | ja |
| GP-FR-086 | SHOULD | Vorgeschlagene Aufgaben (`suggested = true`) erscheinen im Beet-Pflege-Tab in einem eigenen Abschnitt „Vorschläge" mit Grund (`source`, z. B. „ET0-Bedarf 4,2 L/m² seit 3 Tagen") und zwei Schaltflächen: Annehmen, Verwerfen. | nein |
| GP-FR-087 | SHOULD | Wiederkehrende Beet-Aufgaben aus Vorlage: Beettyp-Vorlagen (GP-FR-044) können einen Satz wiederkehrender Tasks mitbringen (z. B. Hochbeet: jährlich „Erde nachfüllen" im März). **Entschieden (Betreiberentscheidung 2026-11-11, #2897):** Das Platzieren legt die Aufgaben **direkt** an, nicht als Vorschläge (GP-FR-086 hat keinen Erzeuger, E-02), und nur auf ein **Opt-in beim Platzieren** (Kontrollkästchen „Wiederkehrende Aufgaben anlegen“, Standard aus; GP-API-062 `create_recurring_tasks`). **Umgesetzt (#2897):** je Schlüssel aus `recurring_task_templates` eine offene Aufgabe am neuen Beet (`entity_type = location`, `origin = user`, `template_key` mit `instance_of`-Kante), aus der Aufgabenvorlage über denselben Baustein wie ein Workflow-Lauf; erste Fälligkeit = Tag des Platzierens + `days_offset` der Aufgabenvorlage, Wiederholung als RRULE `FREQ=YEARLY;BYMONTH=m;BYMONTHDAY=t` auf diesen Kalendertag (ADR-008 Grenze 1; der 29. Februar wird auf den 28. gelegt). Eine Aufgabenvorlage trägt keine eigene Kadenz, daher ist „jährlich“ die Kadenz; ein Monatsanker je Aufgabenvorlage (REQ-006 `trigger_month`) ist nicht umgesetzt. Jeder Schlüssel wird vor dem Schreiben des Beets aufgelöst — eigene oder globale Aufgabenvorlage, sonst 422 `reference.not_found` auf `recurring_task_templates[i]`, nichts wird geschrieben. Die Aufgaben entstehen nach der Plan-Transaktion in **einer** eigenen Transaktion (alle oder keine); scheitert sie, bleibt das Beet stehen und die Antwort meldet `recurring_tasks_failed = true`. | nein |
| GP-FR-088 | MUST | Mehrere Aufgaben desselben Typs auf mehreren Beeten in einem Schritt erledigen (Gießdienst: „alle Beete der Zone gegossen") — nutzt `POST /tasks/batch/status` erweitert um die Fachfelder; erzeugt je Task einen `care_event`. Höchstens 200 Tasks; ein unbekannter oder fremder Schlüssel ist 404 für den **ganzen** Batch (nichts wird geschrieben); nicht abschließbare Tasks (falscher Status, fehlendes Pflichtfoto) stehen in `failed`, der Rest läuft in **einer** Transaktion. | ja |
| GP-FR-089 | MUST | Aufgaben auf dem Plan als Badge am Beet (Anzahl offen/überfällig) mit Farbcodierung nach Priorität; Klick öffnet den Pflege-Tab. | ja |
| GP-FR-090 | MUST | Pflegeaufgaben ohne Task direkt protokollieren („Ich habe gerade gemulcht"): `POST /care-events` ohne `task_key` (§13). Im Feldmodus als **Schnellprotokoll** mit sechs Chips: Gegossen · Geerntet · Gesät · Gejätet/Gemulcht · Gepflanzt · Notiz (F-03, GP-UX-029). | ja |
| GP-FR-091 | COULD | Aufgaben-Checklisten je Beettyp als Saisonvorlage (Frühjahr/Sommer/Herbst/Winter). | nein |

---

## 13. Pflegehistorie

### 13.1 Zweck

Heute verteilt sich „was wurde gemacht" auf `watering_events`, `feeding_events`, `care_confirmations`, `treatment_applications`, `harvest_batches` und Task-Completion-Felder. Es gibt keinen Ort, an dem **warum**, **Ergebnis** und **betroffene Pflanzen** über alle Pflegearten hinweg stehen, und keine Lesesicht pro Beet. `care_events` ist dieser Ort.

### 13.2 Entscheidung: eigene Collection, nicht nur Projektion

| Option | Vorteil | Nachteil |
|--------|---------|----------|
| A: AQL-Union über die Fachcollections (reine Lesesicht) | keine neue Collection | `why`, `observed_outcome`, Beet-Bezug und Pflegearten ohne Fachcollection (Mulchen, Jäten …) haben keinen Platz; Revision nicht möglich |
| **B: `care_events` als Protokoll mit Referenz auf die Fachcollection** (gewählt) | ein Ort für alle Pflegearten; Revision; Beet-Bezug; Auswertbarkeit | zweite Schreibstelle — gelöst durch die Atomarität im Abschluss-Übergang (GP-FR-083) und einen Konsistenz-Job (GP-FR-105) |
| C: Fachcollections abschaffen und alles in `care_events` | ein Modell | Bruch mit REQ-004/014/010 und laufendem Code; nicht gerechtfertigt |

Die Fachcollections bleiben **Quelle der Fachdaten** (Liter, ml/L, Wirkstoff). `care_events` hält das **Protokoll** (Kontext, Verantwortung, Ergebnis) und zeigt auf die Fachdaten.

**Abgrenzung (E-16, #2411):** Das Pflegeprotokoll ist ausdrücklich **keine** Rechtsquelle und **kein** Nachweis nach PflSchG § 11. Der Nachweis einer Pflanzenschutzmaßnahme bleibt `treatment_applications` (REQ-010; Aufbewahrung NFR-011, Karenz- und Resistenzprüfung im IPM-Dienst). Eine `pest_control`-/`ipm`-Zeile im Protokoll ist die betriebliche Notiz derselben Maßnahme; sie ersetzt den Nachweis nicht und kann ihn nicht erzeugen.

### 13.3 Anforderungen

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-100 | MUST | Jeder `care_event` beantwortet: **was** (`category`, `summary`), **wann** (`performed_at`), **wer** (`performed_by_user_key` aus dem Token; für ein anderes Mitglied `performed_for_user_key` per Auswahl; für Dritte `performed_by_label` ≤ 80 Zeichen mit UI-Hinweis „keine vollständigen Namen" — SR-006), **wo** (`location_key`, `site_key`), **warum** (`reason` Freitext + `trigger ∈ {task, reminder, suggestion, manual, observation, backfill, system}` — Client nur `manual`/`observation`, §20.10), **Produkt** (`product_ref` → `fertilizers`/Freitext `product_label`), **Menge** (`quantity`, `unit ∈ {l, ml, g, kg, l_per_m2, g_per_m2, cm, pieces}`), **betroffene Pflanzen** (`plant_keys[]`, leer = ganzes Beet), **Ergebnis** (`observed_outcome` Freitext, `outcome_rating ∈ {positive, neutral, negative, unknown}`), **Belege** (`photo_refs[]`). | ja |
| GP-FR-101 | MUST | **Revisionssicherheit:** `care_events` sind append-only. Eine Korrektur erzeugt einen neuen Eintrag mit `supersedes_key` auf den alten; der alte erhält `superseded_by_key` und bleibt lesbar (Filter „Korrekturen anzeigen"). Beim Supersede wird `performed_by_user_key` vom Vorgänger übernommen, der Korrigierende steht in `created_by`; ein korrigiertes `performed_at` unterliegt V-11 (SR-009). Storno nur als `voided_at`, `voided_by`, `void_reason`. Physisch löscht nur die DSGVO-Kaskade (REQ-025). In der UI heißt Supersede „Bearbeiten"; `position_corrected`-Einträge sind in der Historie standardmäßig ausgeblendet (F-13). | ja |
| GP-FR-102 | MUST | Historie-Tab des Beets: chronologische Liste (neueste zuerst) aus `care_events` **und** Pflanzungsereignissen (Run gestartet/abgeschlossen, Pflanze gesetzt/entfernt, abgeleitet aus `plant_instances`/`planting_runs`), Filter nach Kategorie, Zeitraum, Pflanze, Person; Paginierung ab 50 Einträgen (UI-NFR-003 R-018). | ja |
| GP-FR-103 | MUST | Pflanzungs-Zeitstrahl: Je Jahr/Saison, welche Spezies (Familie farbcodiert) im Beet standen — Grundlage für den Fruchtfolge-Blick (§16). Rückblick mindestens `max(rotation_pause_years der beteiligten Familien, 5)` Jahre, Obergrenze 10 (REQ-002: 3–5; Anbaupausen je Familie K-004); dieser Wert ist der Query-Default `years` von GP-API-039. | ja |
| GP-FR-104 | SHOULD | Export der Historie eines Beets als CSV über GP-API-034 (`GET /care-events?location_key={key}&format=csv`) mit den Feldern aus GP-FR-100 in flacher Form; **CSV-Härtung (SR-016):** Zellen, die mit `=`, `+`, `-`, `@`, Tab oder CR beginnen, werden mit `'` präfixiert; UTF-8 mit BOM, RFC-4180-Quoting; `performed_by` als Anzeigename; ≤ 50 000 Zeilen. | nein |
| GP-FR-105 | SHOULD | Konsistenz-Job (Celery, täglich): findet Fachereignisse (`watering_events`, `feeding_events`, `treatment_applications`, `harvest_batches`) ohne `care_event`-Referenz und erzeugt nachträglich Protokolleinträge mit `trigger = backfill`; Rückwärts-Migration beim Einführen (§34). | nein |
| GP-FR-106 | SHOULD | `care_confirmations` (REQ-022) erzeugen ebenfalls einen `care_event` (`trigger = reminder`), damit Zimmerpflanzen- und Beetpflege in derselben Historie erscheinen. | nein |
| GP-FR-107 | MUST | Die Historie ist mandantenweit filterbar unter `GET /care-events` (alle Beete), mit denselben Filtern; Standard-Zeitraum 90 Tage. | ja |
| GP-FR-108 | COULD | Auswertungen: Gießmenge je Beet und Monat, Düngegaben je m² und Saison, Zeit zwischen Pflanzung und erster Ernte — als Tabellen im Historie-Tab; Grafiken (recharts) nach dataviz-Regeln. | nein |
| GP-FR-109 | MUST | **Redaktion (SR-006, Art. 16/17):** Die Leitung und die DSGVO-Kaskade können die Freitextfelder (`summary`, `reason`, `observed_outcome`, `product_label`, `performed_by_label`) und `photo_refs` eines `care_event` **und aller Vorgänger seiner Supersede-Kette** durch `[redacted]` ersetzen; dabei werden `redacted_at`, `redacted_by`, `redaction_reason` gesetzt und die referenzierten Attachments gelöscht. Redaktion ist neben Supersede und Void die einzige erlaubte Mutation und wird in `garden_plan_audit` protokolliert. Endpunkt GP-API-041. | ja |
| GP-FR-149 | MUST | **Rückgängig im Feldmodus** (F-13): Nach „Erledigt" oder einem Schnellprotokoll-Chip erscheint 8 s eine Snackbar „Rückgängig"; sie storniert den Task-Abschluss (`reopen`) und das `care_event` (`void` mit `void_reason = undo`) in einer Transaktion: `POST /tasks/{key}/reopen` mit `{"undo": true}`; es gilt dasselbe Prädikat wie bei GP-API-037 (Autor ≤ 10 min, sonst Leitung; sonst 403 und nichts ändert sich). Dieselbe Transaktion entfernt das Fachdokument samt Edges, das der Abschluss geschrieben hat (Gieß-/Düngeereignis, Erntecharge) — es würde sonst eine zurückgenommene Handlung weiterzählen; eine Erntecharge mit Folgesätzen (Bewertung, Ertrag, Nacherntecharge) blockiert das Rückgängig (409 `task.undo_blocked`). Wird ein ohne `undo` wieder geöffneter Task erneut erledigt, ersetzt die neue Zeile die alte (`void_reason = reopened`, Fachdokument entfernt), wenn ihr Autor oder die Leitung erneut erledigt — bei jedem anderen kommt eine Zeile hinzu und die Leitung kann die alte stornieren; eine Erntecharge mit Folgesätzen blockiert den Ersatz (409 `task.undo_blocked`). | ja |

---

## 14. Bewässerung

### 14.1 Modell

Eine **Bewässerungszone** (`irrigation_zones`, tenant-scoped, Site-Ebene) bündelt Beete, die gemeinsam bewässert werden — manuell (Gießdienst-Runde), per Tropfschlauch an einem Ventil oder per Sprinkler. Sie ist der Anker für Bedarf, letzten/nächsten Vorgang, Verbrauch und — später — für den Aktor.

```
IrrigationZone {
  name, site_key, tenant_key,
  irrigation_type ∈ {manual, drip, sprinkler, soaker_hose, sub_irrigation},
  water_source_key → garden_objects(water_source) | null,
  actuator_key → actuators(irrigation_valve|pump) | null,   // REQ-018
  flow_rate_l_per_min | null, flow_rate_source ∈ {manual, ha_entity}, flow_rate_ha_entity_id | null,   // O-13
  schedule_hint (Freitext) ,
  color (Darstellung)
}
Location.irrigation_zone_key → irrigation_zones | null
```

Verhältnis zu Bestehendem: `Location.irrigation_system` (Enum, bestehend) bleibt als Eigenschaft des Beets („wie wird hier bewässert"); die Zone ist die Gruppierung. Fehlt eine Zone, gilt das Beet als manuell bewässert. `Site.water_config` (Wasser**qualität**) bleibt unberührt; die **Wasserquelle als Objekt** ist das GardenObject `water_source`.

### 14.2 Anforderungen

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-110 | SHOULD | Zonen anlegen/bearbeiten/löschen je Site; Beete per Mehrfachauswahl auf dem Plan einer Zone zuordnen; die Zone wird als farbiger Umriss/Schraffur über ihren Beeten dargestellt (Ebene „Zonen"). | nein |
| GP-FR-111 | SHOULD | `water_source`-Objekt mit `water_source_kind` (§9.5) und optional `capacity_liters` (Regentonne, Zisterne) und `last_refilled_at`. | nein |
| GP-FR-112 | SHOULD | **Letzter Vorgang:** je Zone und je Beet abgeleitet aus dem jüngsten `care_event(category = watering)` bzw. `watering_events` mit `slot_keys` im Beet. **Nächster geplanter Vorgang:** jüngster offener Task `watering` am Beet/den Beeten der Zone. | nein |
| GP-FR-113 | SHOULD | **Bedarf:** REQ-037 berechnet `irrigation_demands` je Site und Run; die Zone aggregiert `net_demand_mm × bepflanzte Fläche` (REQ-037 `irrigated_area`; bei Mischbeeten Flächenanteil je Entry) ihrer Beete zu Litern, geteilt durch `application_efficiency` (Brutto). Für `planter`/`raised_bed`/`tent` wird die Einzelgabe durch nutzbare Wasserkapazität × Substratvolumen gedeckelt (W-017). `rainfall`-Ereignisse (§12.1) gehen als effektiver Niederschlag ein. Anzeige im Zonen-Panel und als Vorschlags-Task (GP-FR-086). | nein |
| GP-FR-114 | SHOULD | **Verbrauch:** Summe `volume_liters` aus `watering_events` je Zone und Zeitraum; bei Aktor-Zonen zusätzlich `flow_rate_l_per_min × Laufzeit` aus `control_events` (REQ-018). **Durchfluss-Quelle (O-13):** manuell (`flow_rate_l_per_min`, `flow_rate_source = manual`) oder HA-Entität (`flow_rate_ha_entity_id`, `flow_rate_source = ha_entity`), die bei Wert ≤ 24 h alt den manuellen überschreibt; Provenienz am Verbrauchswert (`consumption_source ∈ {manual_log, actuator_runtime_manual_rate, actuator_runtime_ha_rate}`). **Validierung (SR-014):** `flow_rate_ha_entity_id` passt auf `^sensor\.[a-z0-9_]{1,64}$`, muss zu den dem Tenant **freigegebenen** Entitäten gehören (`tenant_ha_entity_grants`, sonst 422 — Modell A nach #2112: eine HA-Instanz je Installation, der Tenant bindet nur freigegebene Entitäten; Entitätslisten brauchen den Scope `technical`) und `device_class ∈ {water, volume_flow_rate}` tragen; setzen darf nur die Zusatzberechtigung **Technik**; der Rohzustand der Entität geht nie an den Client, nur der abgeleitete Liter-Wert; Abruf ausschließlich über den bestehenden HA-Adapter mit SSRF-Guard. **Wirkungsgrad (W-017):** `application_efficiency` je `irrigation_type` (Tropf 0,88, Sprinkler 0,75, manuell 0,8 — überschreibbar; O-17: Howell 2003 Tropf 70–95 % Designwert 88 %, Beregnung 70–90 %); Laufzeit = Brutto-Liter / Durchfluss. | nein |
| GP-FR-115 | COULD | Aktor-Kopplung: Zone → `actuator_key`; „Jetzt bewässern (n Minuten)" ruft den bestehenden `POST /actuators/{key}/command` (REQ-018) auf; der Plan zeigt den Aktorzustand am Ventil-Symbol. | nein |
| GP-FR-116 | COULD | Home-Assistant-Export der Zone als Entität (`ha_publish`, bestehend): Bedarf (L), letzter Vorgang, nächster Vorgang als Sensoren; Ventil als Switch — Vertrag im HA-Dokument (`ha-integration-requirements-engineer`). | nein |
| GP-FR-117 | SHOULD | Gießdienst-Runde (ZG-004): Alle Beete einer Zone in einem Schritt als gegossen protokollieren (GP-FR-088) mit Gesamtmenge, die anteilig nach Beetfläche verteilt wird (Kennzeichnung `allocation = by_area`, alternativ `by_demand`); in Auswertungen (GP-FR-108) werden verteilte Werte nie als gemessen dargestellt. Gießrunde mit Übergabenotiz und „Regen — übersprungen" (F-05). | nein |
| GP-FR-118 | COULD | Bodenfeuchte-Sensor (REQ-005) einer Zone/einem Beet zuordnen; Anzeige des letzten Werts am Beet. | nein |
| GP-FR-119 | SHOULD | Konfliktregel `IrrigationZone.irrigation_type` vs. `Location.irrigation_system`: Die Zone gewinnt für Bedarf/Verbrauch; weicht das Beet ab, zeigt die UI einen Hinweis. Kapazität einer `water_source` (`capacity_liters`) wird gegen den Tagesbedarf der versorgten Zonen geprüft (Hinweis „Regentonne reicht für n Tage"). | nein |

---

## 15. Boden und Substrat

### 15.1 Modell (K-002/K-003 eingearbeitet)

REQ-004 benennt Bodenanalyse-Felder ohne Träger; REQ-019 ordnet Substratchargen nur Slots zu. Für Beete ist die **Location** der richtige Träger. Bodenart (Korngröße), Füllmedium und Zustand sind **drei getrennte Achsen**:

```
Location.soil_profile {
  growing_medium_kind ∈ {native_soil, raised_bed_mix, potting_mix, mineral_substrate, other},
  soil_texture ∈ {sand, loamy_sand, sandy_loam, loam, silt_loam, clay_loam, clay, unknown},   // Korngröße; Hobby-Erfassung über 4 Klassen + Fingerprobe-Hilfe
  stone_content_class ∈ {none, few, many, unknown},
  substrate_key → substrates | null,            // REQ-019, für raised_bed_mix/potting_mix
  substrate_batch_key → substrate_batches | null,
  ph | null, ph_method ∈ {cacl2, h2o, probe_unknown} | null,
  ec_ms_cm | null, ec_method ∈ {saturated_paste, ratio_1_2, ratio_1_5, sensor, unknown} | null,   // Pflicht, sobald ec_ms_cm gesetzt ist
  humus_percent | null, caco3_percent | null,
  drainage ∈ {poor, moderate, good, unknown},
  site_water_regime ∈ {dry, fresh, moist, wet, unknown},   // Standortansprache (nicht Sensorzustand, H-002)
  conditions: list[ConditionFlag] ⊆ {compacted, depleted, waterlogged, crusting, stony},
  target_ph | null,                              // abgeleitet aus soil_texture (Sand 5,5–6,5, Lehm 6,0–7,0, Ton 6,5–7,5; überschreibbar)
  established_on | null,                        // Anlage-/Befülldatum (Hochbeet-Erstjahr, W-012)
  rotation_reset_at | null,                     // Substratwechsel setzt Fruchtfolge-Historie zurück
  rotation_exempt: bool = false,                 // Dauerkultur (Spargel, Beerensträucher, W-013)
  mulch_factor | null,                           // 0,5–1,0 Verdunstungsmodifikator (W-011)
  last_analysis_at | null,
  notes
}
```

`needs_lime` ist **kein** Feld, sondern wird aus `ph`, `ph_method`, `soil_texture` und `target_ph` abgeleitet (Anzeige „Kalkbedarf wahrscheinlich"). Messwerte werden **als Ereignis** erfasst (`care_event(category = soil_analysis)`) mit je Messwert `{value, unit, extraction_method ∈ {cal, ammonium_acetate, saturated_paste, quick_test, sensor}, sample_depth_cm, source ∈ {lab, test_kit, sensor}}`; Einheiten für Boden sind `mg_per_100g` (P, K, Mg nach CAL, Gehaltsklassen A–E) und `kg_n_per_ha` (Nmin), für Nährlösung/Substrat `mg_per_l` (W-009). Das Profil hält nur den letzten Stand (`ph`, `ec_ms_cm`, `humus_percent`, `caco3_percent`, `last_analysis_at`).

**Herkunft der Profilfelder und Rückrechnung (#2706):** Messfelder sind `ph` mit `ph_method`, `ec_ms_cm` mit `ec_method`, `humus_percent` und `caco3_percent`; alle übrigen Felder (Achsen, `drainage`, `site_water_regime`, `conditions`, Substrat, `target_ph`, `established_on`, `rotation_reset_at`, `notes` …) pflegt der Mensch, und keine Analyse berührt sie. Nach jedem Speichern, Stornieren (auch Rückgängig innerhalb von zehn Minuten und Rückgängig eines Aufgabenabschlusses), Korrigieren oder Ersetzen einer Bodenanalyse leitet das System die Messfelder in derselben Transaktion neu ab (sie deklariert `locations` und liest `sites`; geschrieben wird nur ein Beet, dessen Standort dem Mandanten gehört, und zwar bei jeder Ableitung, auch ohne Änderung — so stoßen zwei gleichzeitige Ableitungen desselben Beetes auf einen Schreibkonflikt, statt dass eine still auf einem veralteten Stand endet). **Je Feld gewinnt die neueste Beobachtung:** Kandidaten sind der Handeintrag des Feldes (serverseitig in `hand_values` je Feld mit `{value, method, at}`; `value = null` heißt „von Hand geleert“) und die neueste offene (weder stornierte noch ersetzte) Analyse, die den Parameter in der Profileinheit gemessen hat. Gewinnt der spätere Zeitpunkt (Handeintrag: `at`, Analyse: `performed_at`); bei Gleichstand gewinnt der Handeintrag. Ohne Kandidat ist das Feld leer. Folgen: Eine später nachgetragene ältere Analyse füllt nur ein Feld, für das nichts Neueres vorliegt. Wird eine Analyse storniert, gilt wieder die neuere der verbleibenden Beobachtungen — ein Handwert, den eine neuere Analyse überholt hatte, kehrt zurück, nicht die ältere Analyse, die er ersetzt hatte. Ein von Hand geleertes Feld bleibt leer, bis eine Analyse kommt, die nach dem Leeren durchgeführt wurde. Die Zeitpunkte gelten je Feld. `last_analysis_at` ist das `performed_at` der neuesten Analyse, deren Wert gewonnen hat. Eine Korrektur, die einen Parameter weglässt, nimmt ihren Wert heraus; eine Korrektur auf ein früheres Datum setzt `last_analysis_at` zurück. `PATCH /locations/{key}` schreibt keine abgeleiteten Felder selbst: Es legt für jedes Messfeld, dessen (Wert, Methode) vom gespeicherten wirksamen Wert abweicht, einen Handeintrag mit dem aktuellen Zeitpunkt an (unveränderte Felder erhalten keinen), übernimmt die übrigen Bodenfelder wie gesendet und führt in **derselben Transaktion** dieselbe Ableitung aus wie jede Analyse — eine gleichzeitige Ableitung desselben Beetes führt so zu `409 WRITE_CONFLICT`, statt überschrieben zu werden. **Vorbedingung:** Sendet der Body `soil_profile.last_analysis_at` mit und weicht er vom in der Transaktion gelesenen ab, antwortet die API `409 soil_profile.stale` (eine Maske, die vor einer neuen Analyse geöffnet wurde, würde sonst den alten pH als Handänderung speichern und die neue Analyse dauerhaft verdrängen); ohne das Feld keine Prüfung. Die Oberfläche sendet das gelesene Profil zurück und zeigt bei 409 einen eigenen Hinweis. `last_analysis_at` und `hand_values` sind **serverseitig**: PATCH und Plan-Import übernehmen sie nie (der Import setzt sie leer); `soil_profile: null` speichert `null`. **Altbestand** (Profil ohne `hand_values`): Ein vorhandener Messwert, der genau einem Wert entspricht, den irgendeine Analyse des Beetes (auch eine stornierte oder ersetzte) gemessen hat, gilt als Analysewert; jeder andere wird zum Handeintrag mit dem frühestmöglichen Zeitpunkt (jede offene Analyse, die das Feld misst, löst ihn ab; sonst bleibt er). Die erste Ableitung schreibt `hand_values`; ein PATCH auf ein solches Profil leitet es zuerst nach dieser Regel ab und legt selbst nie Einträge für unveränderte Werte an. Lehnt das Modell ein abgeleitetes Profil ab, bricht die auslösende Transaktion ab (`422 soil_profile.derivation_invalid` mit dem Feldnamen, ohne Werte). Mehrere Messungen eines Parameters in einer Analyse: fürs Profil gilt die geringste `sample_depth_cm` (ohne Tiefe zuletzt). Gelesen werden je Beet höchstens die 500 neuesten **offenen** Bodenanalysen (über den Index `tenant_key, location_key, performed_at`, die Kategorie wird vor dem Sortieren gefiltert); die stornierten und ersetzten liest nur die Altbestands-Regel, getrennt und ebenso auf 500 begrenzt. Wird eine Grenze erreicht, protokolliert das System eine Warnung. Der Verlauf trennt Serien nach Parameter, Methode **und normalisierter Einheit** (Leerzeichen und Groß-/Kleinschreibung zählen nicht, `dS/m` = `mS/cm`); gemeldet wird `pH`, `mS/cm` oder `%`, eine andere Einheit in der Schreibweise ihrer ältesten Messung. Werte verschiedener Einheiten werden nie in eine Serie gelegt oder umgerechnet.

**Messmethode bei pH und EC (U-002/U-003):** Ein Leitfähigkeitswert ist nur mit seiner Extraktionsmethode lesbar: Salzschwellen gelten für den Sättigungsextrakt (ECe), Hobbywerte sind meist 1:2, 1:5 oder Sondenwerte, und eine verlustfreie Umrechnung gibt es nicht (sie hängt von der Textur ab). Deshalb trägt das Bodenprofil `ec_method`, die Messung am `care_event(category = soil_analysis)` trägt sie ebenfalls (`ec_method` neben `extraction_method`, gleiche Werteliste wie am Profil), und `ec_ms_cm` ohne `ec_method` wird mit 422 abgelehnt (vorhandene Profile mit `ec_ms_cm` und ohne Methode erhalten bei der Umsetzung `ec_method = unknown`; `unknown` ist mit nichts vergleichbar, auch nicht mit sich selbst über Messungen hinweg). **Vergleiche (Verlauf, Schwellwert-Hinweise) gelten nur innerhalb einer Methode; das System rechnet nie zwischen Methoden um.** Entsprechend gilt der aus `soil_texture` abgeleitete `target_ph` nur für die Methode, für die der Bereich belegt ist; bei `ph_method = probe_unknown` oder einer anderen Methode entfällt der Kalkbedarf-Hinweis, statt `ph` und `target_ph` unterschiedlicher Methoden zu vergleichen. Die Zahlenbereiche für `target_ph` (Sand/Lehm/Ton oben) sind unverifiziert (Recherchepunkt R-008 des Reviews `spec/analysis/agrobiology-req-053-wave8-ec.md`) und gelten bis dahin als Anzeigevorbelegung, nicht als Grundlage einer Empfehlung (E-10).

### 15.2 Anforderungen

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-120 | MUST | `soil_profile` am Beet pflegbar (Tab „Boden"); `growing_medium_kind`, `soil_texture` (mit Fingerprobe-Hilfe), `drainage`, `site_water_regime`, `conditions[]` als Auswahl, Rest optional. | ja |
| GP-FR-121 | MUST | Beet-Substrat: für `raised_bed`/`planter` kann ein `substrate_key` (REQ-019) gewählt werden; `ph`/`ec_ms` werden aus `Substrate.ph_base`/`ec_base_ms` vorbelegt. Die Slot-Ebene (`filled_with`) bleibt für Indoor/Hydro; Beet-Slots erben das Beet-Substrat, wenn sie keins haben. | ja |
| GP-FR-122 | SHOULD | Bodenanalyse als Ereignis (§15.1) mit Verlaufsdiagramm pH/EC/Humus im Boden-Tab. | nein |
| GP-FR-123 | SHOULD | **Flächendosierung** (REQ-004 `application_rate_g_per_m2`/`l_per_m2`): Der Düngen-Dialog am Beet rechnet g/m² × `area_m2` in die Gesamtmenge um und schreibt beides in den `care_event`: `quantity` und `unit` (`g_per_m2` oder `l_per_m2`) sowie `quantity_total` und `quantity_total_unit` (`g` bzw. `l`); die Gesamtmenge ist `quantity × area_m2`, gerundet auf 3 Nachkommastellen, und entfällt (`null`) bei anderen Einheiten oder `area_m2 ≤ 0` (Stand im Code: `CareEventService._quantity_total`). Es gibt kein Feld `quantity_total_g`. | nein |
| GP-FR-124 | SHOULD | Bodenverbesserungen (Kompost, Mulch, Kalk, Sand, Gründüngung) als `care_event(category ∈ {soil_amendment, mulching, liming})` mit `material ∈ {compost, manure, horn_shavings, lime, sulfur, rock_dust, wood_ash, sand, perlite, biochar, straw_mulch, bark_mulch, grass_clippings, coffee_grounds, green_manure, other}` und Menge. | nein |
| GP-FR-125 | SHOULD | Nährstoff-Hinweis am Beet (W-010): aus `nutrient_demand` der aktuellen Spezies (REQ-001), Vorfrucht (`nitrogen_fixing`-Flag), letzter Düngung/Bodenverbesserung mit Nährstoffwirkung und Gehaltsklassen der Bodenanalyse eine Einschätzung `ok \| check \| likely_deficit \| insufficient_data` mit `confidence` und Begründungstext; beschriftet als „Düngebedarf wahrscheinlich", nie als Messwert. Regelwerk in einem reinen Engine-Modul (Regeltabelle §15.3); Rindenmulch zählt als N-bindend. | nein |
| GP-FR-126 | COULD | Mulchschicht-Status (`mulched_at`, `mulch_material`, `mulch_depth_cm`) im Profil, aus dem letzten Mulch-Ereignis abgeleitet. | nein |
| GP-FR-127 | COULD | Verknüpfung mit `substrate_ec_adapter` / Nährstoffplänen (REQ-004): Nährstoffplan für ein Beet (statt je Pflanze) mit Flächenbezug. | nein |

### 15.3 Regeltabelle Nährstoff-Hinweis (GP-FR-125, WP 8.10)

Referenzimplementierung: `src/backend/app/domain/engines/nutrient_hint_engine.py` (rein, ohne Datenbank); die Eingänge sammelt `nutrient_hint_service.py`, ausgeliefert wird das Ergebnis als `nutrient_hint` in `GET /locations/{key}/summary` (nur für Beete, sonst `null`). Es gibt keine eigene Route und keine TypeScript-Portierung: Die Oberfläche zeigt nur den Zustand und die Begründungscodes an. Agrarbiologie-Review vom 2026-11-06: PASS für den inerten Stand, Änderungen 1–10 eingearbeitet.

**Grundsatz (E-10).** Jede agronomische Schwelle ist Konfiguration (`NutrientHintConfig`) und wirkt nur mit Wert **und** `source`. Die Recherche WP 8.5 (`spec/analysis/agrobiology-req-053-wave8-ec.md`, Addendum) hat keine dieser Schwellen geschlossen. Deshalb sind alle Schwellen ausgeliefert `null`, und jedes Beet erhält `insufficient_data` mit dem Code `thresholds_without_source`. Die qualitativen Flags (Vorfrucht- und stehende Leguminose, Rindenmulch) erscheinen als Begründungscodes. Sie tragen nie eine Menge und erzeugen allein keinen Zustand.

**Dokumentierte Ausnahme (M3).** Die Regel „P oder K in Klasse D/E" ist die einzige qualitative Regel, die ausgeliefert aktiv ist, abweichend von „Hinweis nur mit `source`, Default aus" (Addendum WP 8.5). Begründung: Sie hebt keinen Zustand an und empfiehlt nichts, sie hält nur Kompost und P-Dünger zurück (die vorsichtige Richtung). Ihre Quelle ist R-006 (Bayerische Gartenakademie/LWG, Merkblatt 2202, 12/2020; Hessisches Landeslabor, Erläuterungen zur Bodenuntersuchung, 2024); die Antwort nennt sie in `withheld_source`.

**Eingänge.**

| Eingang | Herkunft | Regel |
|---|---|---|
| Zehrerstufe | `Species.nutrient_demand` jeder Art, die mit aktiver Pflanze im Beet steht (`BedCounters.species_keys`), nur für den Mandanten lesbare Arten | Kein Ersatz durch `BotanicalFamily.typical_nutrient_demand`, kein stiller Default. Gemischtes Beet: die stärkste angegebene Stufe |
| Vorfrucht `nitrogen_fixing` | Fruchtfolge-Historie des Beets (`bed_rotation_entries`): das neueste Jahr vor dem aktuellen mit einem Eintrag `main_crop` oder `green_manure` (Brache zählt nicht), ohne die Arten, die jetzt im Beet stehen; `Species.nitrogen_fixing`, bei `null` das Flag der Familie | Nur qualitatives Flag, keine N-Menge („Bleibt null" Nr. 6, R-015) |
| Stehende Leguminose | eine jetzt im Beet stehende Art mit `nitrogen_fixing` (Art, sonst Familie), z. B. eine mehrjährige Leguminose | Eigenes Flag `standing_nitrogen_fixer`, keine N-Menge (R-015) |
| Letzte N-Gabe | neuester `care_event` `feeding` oder `soil_amendment` mit `material ∈ {manure, horn_shavings}`, nicht storniert, nicht ersetzt, höchstens `read_window_days` (Standard 365) zurück | **Kompost zählt nicht** (R-005: kein N-Lieferant); W-007 bleibt unverändert (Kompost schreibt weiter ein `feeding_event` für die Düngebilanz). Ein `feeding` zählt unabhängig vom Produkt, also auch eine reine K-Düngung, bis der Pflegeeintrag ein N-Feld trägt. Älter oder nicht erfasst gilt als „nicht erfasst", nicht als „nicht gedüngt" |
| N-bindender Mulch | neuester `care_event` `mulching` mit `material = bark_mulch`, höchstens `read_window_days` zurück | Zählt, wenn er nach der letzten N-Gabe liegt oder keine erfasst ist |
| Gehaltsklassen P, K | neueste `soil_analysis`-Messung je Parameter mit `source = lab` **und** `extraction_method = cal` und `content_class`; bis zu 20 Analysen ohne Zeitfenster | Eine Klasse aus einer anderen Extraktion zählt weder für R2 noch für M3. Mg bleibt außen vor (CaCl2, R-007). Nie eine eigene Klassenzuweisung aus Zahlen. Wie lange eine Analyse gilt, ist offen (R-016) |
| Füllung | `soil_profile.growing_medium_kind` | `mineral_substrate` folgt REQ-004-A (Nährlösung), nicht dieser Regel |
| Boden-Leitfähigkeit | `soil_profile.ec_ms_cm` mit `soil_profile.ec_method` (§15.1) | Nur für M5 (Salz-Grenzwert-Hinweis, E-17 Variante A), nie ein EC-Ziel und nie eine Menge; verglichen wird nur innerhalb derselben `ec_method`, keine Umrechnung (U-002) |

**Vorbedingungen** (erste zutreffende gewinnt, Ergebnis immer `insufficient_data`, `confidence = low`):

| Nr. | Bedingung | Code |
|---|---|---|
| V1 | `growing_medium_kind = mineral_substrate` | `substrate_bed` |
| V2a | keine Pflanze im Beet | `no_current_crop` |
| V2b | Pflanzen stehen, aber keine ihrer Arten ist für den Mandanten lesbar | `species_not_readable` |
| V3 | keine lesbare Art im Beet hat eine gespeicherte Zehrerstufe | `demand_unknown` |
| V4 | keine Regel R1/R2 mit Quelle greift | `thresholds_without_source` |

**Regeln** (nur mit Quelle; der schwerste Zustand gewinnt, Rangfolge `likely_deficit` > `check` > `ok`):

| Nr. | Eingang → Zustand | Code | Schwelle (Konfiguration) | Wert / `source` heute |
|---|---|---|---|---|
| R1a | Tage seit letzter N-Gabe > `likely_deficit_after_days[Stufe]` → `likely_deficit` | `feeding_overdue` | `likely_deficit_after_days` je Zehrerstufe | `null` / `null` (R-013) |
| R1b | sonst Tage > `check_after_days[Stufe]` → `check` | `feeding_due` | `check_after_days` je Zehrerstufe | `null` / `null` (R-013) |
| R1c | sonst (eine R1-Schwelle der Stufe aktiv) → `ok` | `fed_recently` | wie R1a/R1b | — |
| R1d | keine N-Gabe erfasst, eine R1-Schwelle der Stufe aktiv → höchstens `check` | `no_feeding_recorded` | wie R1a/R1b | — |
| R2a | Laborklasse P oder K in `low_content_classes` → `likely_deficit` | `p_class_low` / `k_class_low` | `low_content_classes`: Klassenmenge plus `source`, `lab`, `year`, `region` (Bundesland); ohne eine der vier Angaben inaktiv | `null` / `null` (R-006 deckt nur D/E; R-007: Klassengrenzen je Labor, Jahr und Land verschieden) |
| R2b | Laborklassen vorhanden, keine niedrig → `ok` | `content_classes_sufficient` | wie R2a | — |

Grenzfall: Ein Wert genau auf der Schwelle gilt noch nicht als überschritten (`>`).

**Konfigurationsprüfung.** `NutrientHintConfig` lehnt beim Anlegen ab (Fehler), wenn eine aktive R1-Schwelle nicht in `0 < Wert ≤ read_window_days` liegt; sonst läse eine Gabe knapp hinter dem Lesefenster als „nicht erfasst", obwohl sie noch innerhalb der Schwelle liegt. `read_window_days` muss positiv sein. Ob R1 in Kalendertagen oder in Tagen der Vegetationszeit zu messen ist, ist offen (R-017); bis dahin Kalendertage.

**Modifikatoren und Flags** (immer als Code, auch bei `insufficient_data`):

| Nr. | Bedingung | Wirkung | Code | Schwelle / `source` heute |
|---|---|---|---|---|
| M1 | Vorfrucht fixiert Stickstoff | Flag. Senkt nur mit aktivem `nitrogen_fixer_relief` ein `likely_deficit`, das allein auf R1a beruht, auf `check` (nie ein Laborbefund-Defizit) | `preceding_nitrogen_fixer` | `nitrogen_fixer_relief`: aus / `null` (R-015) |
| M1b | Stehende Art fixiert Stickstoff | Nur Flag, ändert keinen Zustand | `standing_nitrogen_fixer` | — |
| M2 | Rindenmulch nach der letzten N-Gabe | Flag („Rindenmulch kann Stickstoff binden"). Hebt nur mit aktivem `bark_mulch_binding` ein `ok`, das allein aus R1 stammt, auf `check`; ein `ok` aus R2 nie. Keine Bindungsmenge | `bark_mulch_n_binding` | `bark_mulch_binding`: aus / `null` („Bleibt null" Nr. 12, R-014) |
| M3 | Laborklasse (CAL) P oder K in D oder E | `compost_and_p_withheld = true`, `withheld_source` = R-006. Kompost dient bei hohen P/K-Gehalten nicht der Nährstoffversorgung; als Bodenverbesserung bleibt er möglich. Der Hinweis verweist nie auf Kompost oder P-Dünger und nennt grundsätzlich kein Mittel und keine Menge | `p_or_k_class_high` | aktiv, Quelle R-006 (siehe Ausnahme oben) |
| M4 | Nicht jede Art im Beet hat eine Zehrerstufe | Flag, `confidence = low` | `demand_partly_unknown` | — |
| M5 | Boden-`ec_ms_cm` > `soil_salinity.threshold_ms_cm`, gemessen mit genau der `soil_salinity.ec_method`, für die der Grenzwert gilt; nicht bei `mineral_substrate` | Flag „Salzgehalt prüfen" (E-17 Variante A). Ändert **keinen** Zustand, keine `confidence`, keine `sources[]` und nie eine Menge: Der Zustand beschreibt die Nährstoffversorgung, ein hoher Salzgehalt ist kein Versorgungsbefund. Der Grenzwert genau auf dem Wert gilt nicht als überschritten. `unknown` ist als Methode des Grenzwerts nicht zulässig. Referenz: `src/backend/app/domain/engines/soil_salinity_hint.py` | `check_salt_content` | `soil_salinity`: `null` / Methode `null` / `null` (R-001, #2643 Frage 10) |

**Konservativer Fall P = E, K = A.** Die Rückhaltung gilt, sobald P **oder** K in D/E liegt. Bei P in E und K in A meldet R2 (mit Quelle) das K-Defizit (`k_class_low`), M3 hält trotzdem Kompost und P zurück: Kompost brächte weiteren Phosphor ein (R-005, R-006). Ob Kompost bei Klasse A/B für P/K sinnvoll ist, bleibt offen (R-018).

**`confidence`.** `low` bei `insufficient_data`, bei `no_feeding_recorded`, bei `demand_partly_unknown` oder wenn M1/M2 den Zustand geändert haben. `high`, wenn eine Laborklasse (R2) den Zustand bestimmt. Sonst `medium`.

**Antwort.** `state`, `confidence`, `reasons[]` (Codes, entscheidende zuerst, dann Flags), `compost_and_p_withheld`, `withheld_source` (Quelle von M3, sonst `null`), `sources[]` (die `source` jeder Schwelle, die den Zustand bestimmt hat; bei R2 mit Labor, Jahr und Land; leer bei `insufficient_data`). Nie eine Zahl.

**Anzeige (Beetkopf).** `likely_deficit` → Chip „Düngebedarf wahrscheinlich", `check` → Chip „Düngung prüfen", jeweils mit den Begründungstexten und dem Satz „Eine Düngemenge nennt die App nicht." `ok` und `insufficient_data` zeigen nichts. Ausnahme M5: Trägt der Hinweis `check_salt_content`, zeigt der Beetkopf unabhängig vom Zustand einen eigenen Chip „Salzgehalt prüfen" mit dem Begründungstext; in der Begründungsliste des Nährstoff-Chips erscheint der Code dann nicht noch einmal. Damit bleibt der Beetkopf ohne Hinweis, bis eine Schwelle eine Quelle hat (bekannte Inert-Gefahr, Plan §3 Welle 8; die Gegenprobe mit aktivierter Testschwelle steht in `tests/unit/domain/engines/test_nutrient_hint_engine.py`).

**Offene Recherchepunkte** (aus dem Review vom 2026-11-06, Fortsetzung der Liste R-001…R-012 in `spec/analysis/agrobiology-req-053-wave8-ec.md`; keine Zahl, bis je Punkt drei Quellen vorliegen, E-10):

| Nr. | Frage | Betrifft |
|---|---|---|
| R-013 | Düngeintervall in Tagen je Zehrerstufe | R1a/R1b |
| R-014 | N-Immobilisierung durch Rindenmulch (ob und wann ein `ok` zu `check` werden soll) | M2 |
| R-015 | Rest-N einer Leguminosen-Vorfrucht und mehrjähriger Leguminosen | M1, M1b |
| R-016 | Gültigkeitsdauer einer Bodenanalyse (ab welchem Alter eine Laborklasse nicht mehr zählt) | R2, M3 |
| R-017 | Vegetationszeit gegen Kalendertage als Maß für R1 | R1, Konfigurationsprüfung |
| R-018 | P/K-Beitrag von Kompost bei Klasse A/B | M3, R2 |

---

## 16. Fruchtfolge und Mischkultur

### 16.1 Vorhandene Grundlage

- `CropRotationValidator.validate_planting(slot_key, species_key, rotation_window_years, *, tenant_key)` prüft **je Slot** die Familienhistorie der letzten 3 Jahre über `placed_in`.
- `CompanionPlantingEngine.check_compatibility(...)` prüft **Nachbarn** über `adjacent_to` (slots → slots, `distance_cm`); die Kante wird heute nur programmatisch gesetzt, es gibt keinen Endpunkt.
- Graph: `compatible_with`, `incompatible_with`, `family_compatible_with`, `family_incompatible_with`, `rotation_after`, `shares_pest_risk` (global, Plattform-Admin).
- `CropRotationPlan` (REQ-002) mit `demand_level` je Jahr/Saison; `SuccessionPlan` (REQ-013).

### 16.2 Anforderungen

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-130 | MUST | **Nachbarschaft aus Geometrie:** Nach jeder Slot-Geometrieänderung in einem Beet leitet der Service `adjacent_to`-Kanten neu ab: zwei Slots sind benachbart, wenn der Abstand ihrer Zentren ≤ `adjacency_factor × max(spacing_a, row_spacing_a, spacing_b, row_spacing_b)` ist (Standard 1,5 — Diagonale √2 eingeschlossen, übernächster Dreiecksnachbar 1,73 ausgeschlossen; der `adjacency_factor` 1,5 ist geometrisch konsistent, agronomisch unbelegt (O-17), konfigurierbar; **mit Reihenabstand**, sonst wären alternierende Reihen wirkungslos — W-018); `distance_cm` wird gesetzt. Bei bekanntem `mature_width_cm` beider Arten gilt stattdessen der Interaktionsradius `(w_a + w_b)/2 × f` mit `f = 1,2` für krautige Arten (unverified) und `f = 2,0` für `Species.growth_habit ∈ {tree, shrub}` (vorhandenes Schemafeld; es gibt kein `growth_form`) (O-17: Wurzelreichweite 2–3 × Kronenradius, Gilman 1988/UF-IFAS), beide als Konfiguration am Tenant. Ab 200 Punkt-Slots je Beet werden Nachbarschaften nur noch **zwischen Zonen/Reihen** abgeleitet (Kantenlimit). Manuell gesetzte Kanten (`source = manual`) bleiben; sie werden über einen eigenen Endpunkt mit Site-Gleichheitsprüfung beider Enden gesetzt (SR-021). Der Celery-Job erhält nur `location_key` und löst Site/Tenant selbst auf. Beetübergreifend (Beetkanten ≤ 50 cm) ist SHOULD. | ja (beetintern) |
| GP-FR-131 | MUST | **Fruchtfolge auf Beet-Ebene** (F-12, MVP): `validate_planting_in_location(location_key, species_key, *, tenant_key)` führt die Historie aller Slots des Beets zusammen (ab `rotation_reset_at`, nicht für `rotation_exempt`); Ergebnis je Familie: letzte Spezies, Jahre seit demselben Anbau, **Anbaupause** aus `BotanicalFamily.rotation_pause_years` (neu, Default je Familie — geprüft O-17: Brassicaceae 4, Solanaceae 4, Apiaceae 4, Amaryllidaceae 4, Cucurbitaceae 4, Asteraceae 3, Amaranthaceae 3, **Fabaceae 6** (Erbsenmüdigkeit), Poaceae `null`; Spezies-Override `Species.rotation_pause_years`, z. B. *Phaseolus vulgaris* 4; Fallback `rotation_window_years`, Obergrenze auf 8 angehoben — K-004. Sperrfristen nach Befall (Kohlhernie ≥ 7 J., Kartoffelnematoden 15–20 J.) überschreiten 8 und gehören nicht hierher, sondern in `soil_hazards`/`soil_persistence_years` (REQ-054 H-10)) und `severity` mit Grund (z. B. „Kohlhernie-Risiko: Brassicaceae vor 2 Jahren"). Gründüngung zählt mit ihrer Familie. Mischbeete: jede Familie des Jahres zählt. Nachpflanzung eines ausgefallenen Slots: optional `replant_of_plant_key`; die ersetzte, in diesem Kalenderjahr eingegangene Pflanze (`died`) dieses Beets zählt für diese Prüfung im Ausfalljahr nicht als Vorkultur, dieselbe Familie erhält einen Resthinweis aus `termination_cause` (`disease`/`pest` `WARNING`, ohne/`unknown` `INFO`, abiotisch keiner; Regel und offene Punkte §11.3 „ausgefallen“, #2888). Vorjahre können nacherfasst werden: MVP-Dialog „Was stand hier {Jahr}?" am Beet schreibt über GP-API-042 (Rotationsmatrix editierbar, GP-FR-135, ist SHOULD). | ja |
| GP-FR-132 | MUST | Im Bepflanzen-Dialog (§11.1 Schritt 1) erscheinen Fruchtfolge-Warnung und Mischkultur-Hinweis (zu bereits geplanten/aktiven Nachbarn im Beet über `adjacent_to`) **als Hinweis mit Stärkestufe, nicht als Blocker** (D-09); „Trotzdem pflanzen" speichert den Grund am Run (`rotation_override_reason`). Das Beet trägt auf dem Plan ein Badge, wenn eine aktive Pflanzung einen Fruchtfolge-Hinweis hat. Für `planter`/`tent`/`shelf` standardmäßig aus (GP-FR-137). | ja |
| GP-FR-133 | SHOULD | **Folgekultur-Empfehlung:** aus `rotation_after` (REQ-001) und dem `NutrientDemand`/`PlanRole`-Zyklus (Starkzehrer → Mittelzehrer → Schwachzehrer → Gründüngung/Brache, §16.3) eine Liste geeigneter Familien/Spezies für das nächste Jahr, angezeigt im Historie-Tab unter dem Zeitstrahl. | nein |
| GP-FR-134 | SHOULD | **Mischkultur-Overlay** (REQ-028 §7.3): Ebene auf dem Plan, die zwischen benachbarten Pflanzen grüne (kompatibel), rote (inkompatibel) und graue (unbekannt) Verbindungen zeichnet; Hover/Tipp zeigt Grund und Score. Nur für sichtbare Beete, max. 500 Kanten je Viewport (Culling). | nein |
| GP-FR-135 | SHOULD | **Rotationsmatrix** (REQ-002 §1 „Beet × Jahr") als Tabelle je Site: Zeilen Beete, Spalten Jahre, Zellen **Liste** der Familien je Saison (Vor-/Haupt-/Nachkultur, W-013) farbcodiert nach `nutrient_demand`; Datenquelle `care_events`/`plant_instances`, Zukunftsspalten aus `CropRotationPlan`. | nein |
| GP-FR-136 | COULD | Problematische Pflanzen je Beet: Spezies, deren Familie in den letzten `rotation_window_years` im Beet stand oder die mit aktiven Nachbarn inkompatibel sind — als Negativliste im Bepflanzen-Dialog ausgegraut mit Grund. | nein |
| GP-FR-137 | MUST | Fruchtfolge für `planter`, `tent`, `shelf` standardmäßig aus (Substratwechsel ersetzt die Rotation, REQ-001) und für `rotation_exempt`-Beete (Dauerkulturen) aus; je Beet einschaltbar. | ja |

### 16.3 Zehrerstufe, Stickstofffixierung und Planrolle (O-07, revidiert nach K-001)

*Ausgangslage vor Migration M6 (historisch, Stand v1.4; seit E-17 Variante A liest außer M6 kein Code mehr `nutrient_demand_level`):* Es existierten drei Enums für dieselbe Sache und ein Merkmal steckte im falschen Enum: `Species.nutrient_demand_level` (`heavy_feeder|medium_feeder|light_feeder|nitrogen_fixer`), `BotanicalFamily.typical_nutrient_demand` (`light|medium|heavy`) plus `BotanicalFamily.nitrogen_fixing` (Bool), `CropRotationPlan.demand_level` (`…|green_manure|fallow`). `nitrogen_fixer` ist **keine** Zehrerstufe — eine Erbse ist Schwachzehrer *und* N-Fixierer (K-001). REQ-053 legt daher **drei getrennte Begriffe** fest, die REQ-001 und REQ-002 übernehmen:

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-FR-138 | MUST | **`NutrientDemand`** = `heavy_feeder \| medium_feeder \| light_feeder` an Spezies (`Species.nutrient_demand`, Pflicht bei Nutzpflanzen, mit `source`/`confidence` — H-004) und Familie (`BotanicalFamily.typical_nutrient_demand`). **`nitrogen_fixing: bool`** an Spezies (neu) und Familie (vorhanden). **`PlanRole`** = `main_crop \| green_manure \| fallow` am `PlantingRun` (`plan_role`, Standard `main_crop`) und am `CropRotationPlan` (ersetzt `demand_level`; `fallow` ist dort der einzige Wert ohne Run). Pydantic-Validatoren: `fallow` nie an Spezies/Familie/Run; `green_manure` am Run verlangt `Species.green_manure_suitable = true`. | ja (Welle 1) |
| GP-FR-139 | MUST | Migration `M6_nutrient_demand_split`: `Species.nutrient_demand_level = nitrogen_fixer` → `nitrogen_fixing = true` und `nutrient_demand` aus dem Steckbrief (Pflichtfeld in `plant_info.schema.yaml`; fehlt der Wert, bleibt `nutrient_demand = null` und der Dry-Run-Report listet die Spezies — **kein** stiller Default); `BotanicalFamily.typical_nutrient_demand` `light→light_feeder`, `medium→medium_feeder`, `heavy→heavy_feeder`; `CropRotationPlan.demand_level` → `nutrient_demand` + `plan_role`: `heavy_feeder/medium_feeder/light_feeder` → `nutrient_demand` = Wert, `plan_role = main_crop`; `green_manure` → `plan_role = green_manure`, `nutrient_demand = null` (eine Gründüngung hat keine eigene Zehrerstufe); `fallow` → `plan_role = fallow`, `nutrient_demand = null` (GP-ACC-037, REQ-002 §2). Schemas `_defs.schema.yaml:51`, `species.schema.yaml`, `plant_info.schema.yaml`, `botanical_families.schema.yaml:31` und Seeds werden umgestellt; `seed-data-validator` prüft danach. REQ-001 §2 und REQ-002 §2 erhalten eine Changelog-Zeile mit Verweis auf GP-FR-138. | ja (Welle 1) |

**Steckbrief-Datenregeln (E-15, #2371):** Die Quellenlage entscheidet. Wo `nutrient_demand` quellenbelegt ist, schlägt es das ältere `nutrient_demand_level` (Konflikte, etwa Mentha/Ocimum/Raphanus, stehen in der Lückendatei). `rotation_pause_years` der Familie wird nur gefüllt, wo eine Quelle es trägt (Fabaceae: Art-Spanne 3–5, Familienwert 3); nicht definierte Familien bleiben `null` und stehen in der Lückendatei. Schwach belegte Werte bleiben mit `confidence: low`.

Die Rotationslogik (Starkzehrer → Mittelzehrer → Schwachzehrer → Gründüngung/Brache) in GP-FR-131/133/135 arbeitet auf `NutrientDemand` + `PlanRole`; die N-Gutschrift einer Leguminosen-Vorfrucht kommt aus `nitrogen_fixing`.

## 17. UX/UI

### 17.1 Layout

Seit v1.16 gilt für den Planungsmodus der Gartenübersicht die Editor-Arbeitsfläche aus §17.3 (Welle 10); die Tabelle fasst sie je Breakpoint zusammen, maßgeblich sind die Zeilen GP-UX-063…070. Bis zur Umsetzung in Welle 10 zeigt der Editor noch das ältere Layout (Implementierungsstand).

| Breakpoint (UI-NFR-001) | Layout |
|-------------------------|--------|
| ≥ lg (Laptop, Monitor) | Vierteilig nach §17.3: eine Editor-Kopfleiste (Zurück, Undo/Redo, Speichern-Status, Tabs Plan · Liste · Beete, Panel-Umschalter, Überlauf), links die vertikale Werkzeug-Leiste, in der Mitte die Zeichenfläche auf Viewport-Höhe, rechts das Seitenpanel mit Tabs (angedockt, nimmt nur geöffnet Breite ein). Seitentitel und Brotkrumen bleiben in der App-Shell; die Editor-Kopfleiste ersetzt die Aktions-Zone des Seitenkopfs nach UI-NFR-021 (§17.3). |
| md (Tablet quer, kleiner Laptop) | Wie ≥ lg: Das Seitenpanel liegt angedockt neben der Zeichenfläche, nicht darüber (§17.3, GP-UX-069, #2885). |
| sm (Tablet hochkant) | Werkzeug-Leiste wird die `TouchBar` (§9.7), das Panel ein Bottom Sheet (halb/voll), die Zeichenfläche füllt den Rest (§17.3, GP-UX-069). |
| xs (Smartphone) | Feldmodus als Standard (§18); Editiermodus erreichbar über „Bearbeiten", mit reduzierten Werkzeugen (Verschieben, Position korrigieren, Eigenschaften) — Zeichnen neuer Polygone auf xs ist zulässig, aber nicht abgenommen (O-10, entschieden). |

### 17.2 Anforderungen

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-UX-001 | MUST | Die Werkzeugleiste zeigt höchstens 8 Werkzeuge auf oberster Ebene (seit v1.19: Auswahl, Hand/Pan, Beet ▸ Untermenü, Gartenobjekt ▸ Untermenü — die Werkzeuge, die es gibt; #2868; dazu aus GP-UX-071 Bereich ▸ Untermenü vor Beet, Pflanze setzen nach Gartenobjekt, Messen und Text, #2913 — acht Werkzeuge, die Obergrenze ist erreicht); seltene Objekte liegen im Untermenü. Ein weiteres Werkzeug der obersten Ebene setzt voraus, dass ein anderes in ein Untermenü wandert. Max. 2 Ebenen (UI-NFR-019 R-019 sinngemäß). | ja |
| GP-UX-002 | MUST | Jeder Cursor-Modus ist sichtbar (Cursor-Form + aktives Werkzeug hervorgehoben) und per Esc verlassbar. | ja |
| GP-UX-003 | MUST | Speichern-Status in der Kopfzeile: „Gespeichert", „Ungespeicherte Änderungen (n)", „Speichert…", „Konflikt" — kein Auto-Save im **Planungsmodus**; expliziter Speichern-Button + `Ctrl/Cmd+S`; Verlassen mit ungespeicherten Änderungen fragt nach (Guard-Dialog, bestehendes Muster, Memory #1689 beachten). Im **Feldmodus** gibt es keinen Dirty-Zustand: jede Aktion (Erledigt, Notiz, Foto, Position korrigieren, Gepflanzt) wird sofort gesendet (F-16). | ja |
| GP-UX-004 | SHOULD | Auto-Save nach 2 s Inaktivität als nutzerbezogene Option; bei Konflikt wird Auto-Save pausiert. | nein |
| GP-UX-005 | MUST | Legende (ein-/ausblendbar) mit allen auf dem Plan vorkommenden Objektklassen und Phasenfarben; Legende ist Teil des PDF. (Ab Welle 10 steht die Legende im Panel-Tab „Ebenen“ und bleibt dort ein-/ausblendbar — GP-UX-068.) | ja |
| GP-UX-006 | MUST | Hover (Desktop) / Tipp (Touch) auf ein Objekt zeigt eine Info-Blase: Name, Typ, Maße, bei Beeten aktive Pflanzen, offene Aufgaben, **Vorjahr** (GP-FR-077) und zuletzt gegossen; Doppelklick/zweiter Tipp öffnet die Detailseite. **Für Pflanzen-Marker gilt GP-FR-190 (§11.4).** | ja |
| GP-UX-007 | MUST | Drag & Drop mit Vorschau (Geisterobjekt), Snap-Markierung (Hilfslinie), Abbruch per Esc; während des Drags werden Position und Maß live angezeigt (GP-FR-014). | ja |
| GP-UX-008 | MUST | Touch: Ein-Finger-Drag auf Objekt = Verschieben nur nach **Long-Press 500 ms mit sichtbarem Fortschrittsring** (sonst Pan); verbindliche Gestentabelle GP-UX-040 — verhindert versehentliches Verschieben beim Scrollen; Zwei-Finger = Pan/Zoom/Rotate-Geste (Rotate SHOULD). Touch-Ziele für Griffe ≥ 48 px (UI-NFR-001 R-011), auf Beeten ohne Griffe: ganze Fläche. | ja |
| GP-UX-009 | MUST | Tastatursteuerung vollständig (§24): Tab durch Objekte in DOM-Reihenfolge (Zeile, dann Spalte, UI-NFR-002 R-026), Pfeile verschieben, `R` rotiert 15°, `+/-` Zoom, `G` Raster, `Entf`, `Ctrl+D`, `Ctrl+Z/Y`, `Esc`. Hilfe-Overlay mit `?`. | ja |
| GP-UX-010 | MUST | Beschreibende Texte (Feedback-Memory „Beschreibende Texte in der UI"): Leerzustand des Plans erklärt in zwei Sätzen, was zuerst zu tun ist („Zeichne die Umrisse deines Gartens. Du kannst sie später jederzeit anpassen."); jedes Werkzeug hat einen Tooltip mit Verb. | ja |
| GP-UX-011 | MUST | Fachbegriffe (Pflanzabstand, Reihenabstand, Randabstand, Fruchtfolge) mit Glossar-Erklärung nach UI-NFR-011. | ja |
| GP-UX-012 | MUST | `data-testid` nach UI-NFR-022: `garden-plan-page`, `garden-plan-canvas`, `plan-tool-<name>`, `plan-object-<key>`, `plan-handle-<position>`, `plan-properties-panel`, `form-field-<name>`, `save-plan-button`, `plan-conflict-dialog`, `bed-detail-page`, `bed-plan-tab`, `care-event-row-<key>`. Neue Muster werden vor Verwendung in UI-NFR-022 registriert (R-020). | ja |
| GP-UX-013 | MUST | i18n-Schlüssel unter `pages.gardenPlanner.*`, Enums unter `enums.gardenObjectType.*`, `enums.bedStatus.*`, `enums.careEventCategory.*`, `enums.irrigationType.*`, `enums.layoutStrategy.*`; DE und EN vollständig (NFR-017). | ja |
| GP-UX-014 | SHOULD | Mini-Map rechts unten (120 × 120 px), bedingt sichtbar (§9.6), zeigt Viewport-Rechteck, Klick springt. | nein |
| GP-UX-015 | MUST | Phasenfarben und Icons der Pflanzen folgen UI-NFR-016; die Farbe ist nie der einzige Informationsträger (Icon + Beschriftung nach der LOD-Regel GP-NFR-067, nicht an einen Zoom-Prozentwert gebunden). | ja |
| GP-UX-016 | MUST | Dark Mode: Plan-Palette hat eigene Tokens (Boden, Rasen, Weg, Wasser) mit Kontrast ≥ 3:1 gegen den Hintergrund in beiden Themes (UI-NFR-006). | ja |
| GP-UX-017 | MUST | Fehler-Feedback nach UI-NFR-004: Validierungsfehler der API (§22) werden am betroffenen Objekt markiert (roter Rand) und im Panel erklärt; ein 409-Konflikt öffnet einen Dialog (`plan-conflict-dialog`, UI-NFR-022) mit „Neu laden" / „Meine Änderungen als Kopie behalten (JSON herunterladen)" — ein Wortlaut, identisch in GP-ACC-011 und UI-NFR-022. | ja |

### 17.3 Editor-Arbeitsfläche (v1.16, Welle 10)

**Anlass (#2820).** Der Editor der Gartenübersicht ist Funktion für Funktion gewachsen: Heute stehen sechs Steuerzeilen über der Zeichenfläche (Kopfaktionen, `SaveBar`, `EditorHeaderActions`, `ViewBar`, `ZoneLegend`, `EditorToolbar`), das leere Eigenschaftenpanel reserviert dauerhaft 320 px (`editor/layout.ts`, `PANEL_WIDTH_PX`), und die Beetliste (`BedListSection`) steht unter dem Editor. Auf einem Laptop mit 1366 × 768 ist der Plan damit das kleinste Element der Seite. **Entscheidung des Betreibers (2026-11-09, Kommentar in #2820):** Vorschlag A (Arbeitsfläche wie in einem Zeichenprogramm) zusammen mit Vorschlag C (Beetliste als eigener Tab); Vorschlag B entfällt.

**Geltungsbereich.** Dieser Abschnitt gilt für den Planungsmodus der Gartenübersicht (§9.6, `standorte/sites/:key/plan`) und damit auch für den Indoor-Plan (§9.8), der dieselbe Route nutzt. Unverändert bleiben die Beetansicht mit ihren Tabs (§9.6), der Feldmodus (§18, `?mode=field`) mit seinem eigenen Einstieg Liste · Karte (GP-UX-030) und die Interaktionsregeln aus §9.7; die `TouchBar` bleibt der Touch-Pfad für Zeichnen und Mehrfachauswahl (GP-UX-036, GP-UX-037). Wo §17.1 oder eine ältere Zeile dieses Abschnitts dem Layout hier widerspricht, gilt §17.3. GP-UX-052 gilt unter md weiter, mit einer Verschiebung, die in der Zeile selbst vermerkt ist: Rasterstufe und Snap liegen im Panel-Tab „Ansicht“ (im Bottom Sheet), die Zoom-Stufen als Overlay auf der Zeichenfläche statt im Überlauf; Exportieren bleibt im Überlauf. Ebenso vermerken GP-UX-005, GP-NFR-023 und GP-NFR-025 ihre Änderung ab Welle 10 selbst.

**Zwei Listen, zwei Zwecke.** Der Tab „Liste“ des Planungsmodus ist die alternative Darstellung des ganzen Plans (GP-NFR-023: Bereich → Beet → Pflanzen, mit allen Aktionen des Panels); die „Liste“ des Feldmodus ist der Einstieg „Meine Beete · heute fällig“ (GP-UX-030) und ändert sich mit §17.3 nicht.

**Verhältnis zu Shell und Seitenkopf.** App-Bar, Brotkrumen (UI-NFR-005 R-014, R-017a) und der Seitentitel mit dem Site-Namen (UI-NFR-017) gehören zur App-Shell, liegen außerhalb des Editors und zählen nicht als Steuerzeile der Arbeitsfläche. Die Editor-Kopfleiste ersetzt auf dieser Route die Aktions-Zone des Seitenkopfs (UI-NFR-021); der Seitenkopf trägt hier nur den Titel. Für die Aktionen der Kopfleiste gilt UI-NFR-021 sinngemäß: „Speichern“ ist die einzige Primäraktion (G1, R-004, R-009) und wandert nie in den Überlauf (R-017); der Überlauf „⋮“ trägt `aria-label`, `aria-haspopup="menu"` und `aria-expanded` (R-020), zeigt jeden Eintrag mit Icon und Text (R-019) und ist per Tastatur bedienbar (R-032). Abweichend von R-023 bricht die Kopfleiste auch auf xs nicht um, sondern verlagert in den Überlauf (GP-UX-063); unter md bleibt damit wie in R-024 nur „Speichern“ als Aktion sichtbar — Zurück ist Navigation, der Speichern-Status eine Anzeige.

**Zielbild**

| Bereich | Inhalt |
|---------|--------|
| **Kopfleiste** (genau eine Zeile) | Zurück zur Site (Beschriftung mit dem Site-Namen, unter md nur Icon mit `aria-label`) · Undo/Redo (GP-FR-155; unter md in der `TouchBar`) · Speichern-Status, Auto-Save-Schalter und „Speichern“ (GP-UX-003/004) · Tabs **Plan · Liste · Beete** · Wechsel in den Feldmodus (GP-UX-020) · Umschalter des Seitenpanels (GP-UX-068) · Überlauf „⋮“ mit den seltenen Aktionen: Tastaturhilfe, Unterlage (GP-FR-033), Alles auswählen, Export und Import (GP-UX-050/051) sowie „Als Vorlage speichern“, Letzteres nur, solange genau ein Beet ausgewählt ist (Beetvorlage GP-FR-044, §20.12; GP-UX-066). Was auf der Breite nicht passt, wandert nach der Reihenfolge aus GP-UX-063 in den Überlauf. |
| **Werkzeug-Leiste** (links, vertikal) | Genau die Werkzeuge aus GP-UX-001 (Referenzliste, keins entfällt): Auswahl, Hand/Pan, Bereich ▸ (Untermenü), Beet ▸ (Untermenü), Gartenobjekt ▸ (Untermenü), Pflanze setzen, Messen, Text (acht Werkzeuge, die Obergrenze; „Pflanze setzen“ nur für Rollen mit Schreibrecht, für Betrachter fehlt es; alle Werkzeuge aus GP-UX-071 sind gebaut, #2913) — Icon mit Tooltip, auf breiten Bildschirmen zusätzlich mit Beschriftung. „Aus Vorlage“ (GP-FR-044) ist ein Eintrag im Untermenü von Beet, „Mit Maßen hinzufügen“ (GP-UX-046) ein Eintrag in den Untermenüs von Bereich, Beet und Gartenobjekt; beide sind keine eigenen Werkzeuge der obersten Ebene (höchstens zwei Ebenen, GP-UX-001). Darunter die **Auswahlgruppe** (Drehen 15°/45°/90°, Ausrichten, Löschen), die nur bei bestehender Auswahl erscheint. |
| **Zeichenfläche** | Füllt die Höhe des Viewports unterhalb der Kopfleiste, mindestens 400 px. Zoom −/%/+, „An Fläche anpassen“, Maßstabsbalken und Mini-Map (bedingt, GP-UX-014) liegen als Overlays in den Ecken der Zeichenfläche. |
| **Seitenpanel** (rechts, einklappbar) | Tabs **Eigenschaften** (ausgewähltes Objekt, öffnet sich bei Auswahl), **Ansicht** (Rasterstufe, Snap, Einheit m/cm, Nordwinkel mit Kompass), **Ebenen** (Ebenen-Schalter mit Textbeschriftung, die Legende der Objektklassen und Phasenfarben nach GP-UX-005 — dort ein-/ausblendbar — und die Zonenlegende) und **Zonen** (Bewässerungszonen verwalten, §14). |
| **Tab „Liste“** | Die alternative Darstellung des Plans (GP-NFR-023, heute der Schalter „Als Liste anzeigen“); nicht zu verwechseln mit der „Liste“ des Feldmodus (GP-UX-030). |
| **Tab „Beete“** | Die Beetliste der Site (GP-FR-042, heute `BedListSection` unter dem Editor); im Indoor-Plan „Pflanzplätze“ (GP-FR-183). |

**Breakpoints** (UI-NFR-001 R-001): **ab md** Werkzeug-Leiste, Zeichenfläche und angedocktes Panel; die Zeichenfläche gibt dem offenen Panel die Breite ab, das Panel liegt nie über ihr (WCAG 2.2 SC 2.4.11, #2885) · **unter md** wird die Werkzeug-Leiste zur `TouchBar` und das Panel zum Bottom Sheet (GP-UX-052); auf xs bleibt der Feldmodus der Standard (GP-UX-020). Die Form des Panels (angedockt, Bottom Sheet) hängt **allein von der Breite** ab. Der Zeigertyp entscheidet nur über die `TouchBar`: Bei grobem Zeiger (`pointer: coarse`) zeigt der Editor sie auf jeder Breite, weil GP-UX-036 (Zeichen-Aktionsleiste) und GP-UX-037 (Umschalter „Mehrfachauswahl“) den Touch-Pfad unabhängig von der Breite verlangen; ab md steht sie zusätzlich zur Werkzeug-Leiste.

**Grundsätze.** Die Zeichenfläche zuerst; Rangfolge nach Häufigkeit (Werkzeuge und Speichern sichtbar, Ansicht und Ebenen einen Klick entfernt, Seltenes im Panel oder Überlauf); eine Stelle je Aufgabe (Dokument, Werkzeuge, Ansicht, Auswahl); keine umbrechenden Leisten — was nicht passt, wandert in den Überlauf. Die bestehenden Zusagen aus §9.7 und §24 bleiben: Skip-Links, Live-Region, Roving-Tabindex, Touch-Ziele ≥ 48 px, Tastenkürzel. Der Umbau verschiebt Komponenten, ohne bestehende Testkennungen umzubenennen (GP-UX-070), und baut alle Breiten aus einem Komponentenbaum (GP-UX-069).

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-UX-063 | SHOULD | **Eine Kopfleiste.** Über der Zeichenfläche steht im Planungsmodus genau eine Steuerzeile mit den Inhalten aus dem Zielbild; Speichern-Status, Undo/Redo und „Speichern“ bleiben auf jeder Breite sichtbar (GP-UX-052). Keine Steuerzeile der Arbeitsfläche bricht um: Was nicht passt, steht im Überlauf „⋮“ (Einträge ≥ 48 px, mit Icon und Text). **Verlagerungsreihenfolge** bei abnehmender Breite (zuerst verlagert zuerst genannt): (1) Auto-Save-Schalter, (2) Wechsel in den Feldmodus, (3) Umschalter des Seitenpanels (im Überlauf mit Text „Seitenpanel ein-/ausblenden“), (4) Tabs Plan · Liste · Beete (im Überlauf als drei Einträge, der aktive markiert). **Unter md** stehen in der Kopfleiste nur noch Zurück (Icon mit `aria-label`), der Speichern-Status (kompakt als Icon mit Zähler, Wortlaut nach GP-UX-003 als `aria-label` und in der Live-Region GP-NFR-022), „Speichern“ und „⋮“; alles andere steht im Überlauf, Undo/Redo stehen sichtbar in der `TouchBar` (GP-UX-052, GP-FR-155). Mit dieser Regel bricht die Kopfleiste bei 390 px Breite nicht um. | nein |
| GP-UX-064 | SHOULD | **Tabs Plan · Liste · Beete mit URL-Zustand.** Der aktive Tab steht im Query-Parameter `tab` mit den Werten `plan`, `list` und `beds`, neben `mode` (§18); fehlt `tab` oder ist der Wert unbekannt, gilt `plan`. Ein Link mit `tab` öffnet den Tab direkt, jeder Tab-Wechsel legt einen Verlaufseintrag an, sodass „Zurück“ zum vorigen Tab führt. Im Feldmodus (`mode=field`) gibt es die Tab-Leiste nicht; `tab` wird dort ignoriert. Ein Klick auf eine Zeile im Tab „Beete“ wechselt zu „Plan“ und hebt das Beet hervor (GP-FR-042). Der Tab „Beete“ zeigt den gespeicherten Stand und lädt nach jedem erfolgreichen Speichern neu. Im Indoor-Plan (§9.8) heißt der Tab „Pflanzplätze“ (GP-FR-183); der Wert in der URL bleibt `beds`. | nein |
| GP-UX-065 | SHOULD | **Tab-Wechsel verliert nichts.** Ein Wechsel zwischen Plan, Liste und Beete behält den Editorzustand (ungespeicherte Operationen, Undo-Verlauf, Auswahl, Viewport) und löst den Ungespeichert-Dialog (GP-UX-003) **nicht** aus. Der Dialog fragt weiterhin nach, sobald die Plan-Route mit ungespeicherten Änderungen verlassen wird. | nein |
| GP-UX-066 | SHOULD | **Vertikale Werkzeug-Leiste mit Auswahlgruppe.** Die Werkzeuge stehen in einer vertikalen Leiste links der Zeichenfläche, jedes mit Tooltip, das ein Verb nennt (GP-UX-010). Referenzliste ist GP-UX-001: Die Leiste trägt genau dessen Werkzeuge der obersten Ebene (höchstens 8; Hand/Pan ist das Werkzeug, das #2820 „Verschieben“ nennt); „Aus Vorlage“ und „Mit Maßen hinzufügen“ sind Untermenü-Einträge (Zielbild). Drehen, Ausrichten und Löschen (Auswahlgruppe der Leiste) werden nur gerendert, solange eine Auswahl besteht, „Als Vorlage speichern“ (im Überlauf) nur, solange genau ein Beet ausgewählt ist — das Einzige, woraus eine Beetvorlage entsteht (GP-FR-044, §20.12) — jeweils nicht als deaktivierte Schaltflächen. Die Leiste ist per Tastatur bedienbar (Roving-Tabindex wie GP-NFR-068). | nein |
| GP-UX-067 | SHOULD | **Zeichenfläche auf Viewport-Höhe.** Die Zeichenfläche nimmt die verbleibende Höhe des Viewports unter der Kopfleiste ein, mindestens 400 px. Zoom, „An Fläche anpassen“, Maßstab und Mini-Map sind Overlays auf der Zeichenfläche und beanspruchen keine eigene Zeile. | nein |
| GP-UX-068 | SHOULD | **Seitenpanel mit Tabs.** Das Panel hat die Tabs Eigenschaften, Ansicht, Ebenen und Zonen (Inhalte im Zielbild). Eingeklappt reserviert das Panel **keine Breite** neben der Zeichenfläche. **Umschalter:** Er steht in der Editor-Kopfleiste (GP-UX-063); auf schmalen Breiten darf er in den Überlauf wandern, dort als Eintrag ≥ 48 px mit Textbeschriftung. Er trägt `aria-expanded` (offen/zu) und `aria-controls` (auf das Panel). Ohne Auswahl geöffnet zeigt das Panel den zuletzt benutzten Tab, beim ersten Öffnen „Ansicht“. **Zustandsregel:** Eine neue Auswahl öffnet das Panel auf „Eigenschaften“. Wird die Auswahl aufgehoben, klappt das Panel nur dann wieder ein, wenn die Auswahl es geöffnet hatte. Ein vom Nutzer geöffnetes Panel bleibt über Auswählen und Abwählen hinweg offen. Ein vom Nutzer geschlossenes Panel bleibt zu, bis der Nutzer es öffnet oder eine neue Auswahl trifft. **Tabs:** Die Panel-Tabs folgen dem WAI-ARIA-Muster „Tabs“: `role="tablist"` mit `role="tab"`, `aria-selected` am aktiven Tab, `aria-controls` auf das zugehörige `role="tabpanel"` (das per `aria-labelledby` auf seinen Tab verweist) und Roving-Tabindex — nur der aktive Tab ist Tab-Stopp, Pfeil links/rechts bewegt den Fokus zum Nachbar-Tab, Pos1/Ende springen zum ersten/letzten; aktiviert wird ein Tab erst mit Eingabe- oder Leertaste bzw. Klick (manuelle Aktivierung, #2887). Der Skip-Link „Zum Eigenschaftenpanel“ (GP-NFR-070) führt bei eingeklapptem Panel auf dessen Umschalter. Die Ebenen-Schalter tragen im Tab „Ebenen“ eine sichtbare Textbeschriftung, zusammen mit der Legende (GP-UX-005, dort ein-/ausblendbar) und der Zonenlegende. | nein |
| GP-UX-069 | SHOULD | **Breakpoints aus einem Layout.** Desktop, Tablet und Telefon kommen aus einem Komponentenbaum mit Breakpoints, nicht aus parallelen Varianten der Seite; geprüft wird das im Code-Review der WP 10.3–10.5 (Prüfpunkt, kein Akzeptanzkriterium). Breakpoint-Regel wie oben: Die Panelform folgt allein der Breite — ab md angedocktes Panel neben der Zeichenfläche, unter md Bottom Sheet; das offene Panel verdeckt weder die Zoom-Stufen noch ein ausgewähltes Objekt: Öffnet eine Auswahl das Panel, schwenkt der Viewport, bis das Objekt im sichtbaren Teil der Zeichenfläche liegt (#2885); unter md wird die Werkzeug-Leiste zur `TouchBar`. Bei grobem Zeiger erscheint die `TouchBar` auf jeder Breite (GP-UX-036, GP-UX-037), ohne die Panelform zu ändern. Unter md liegen Rasterstufe und Snap im Panel-Tab „Ansicht“, die Zoom-Stufen als Overlay; Exportieren bleibt im Überlauf (GP-UX-052). Auf jeder Breite ab 1024 px ist jede Editor-Funktion ohne horizontales Scrollen der Seite erreichbar. Touch-Verhalten und Zielgrößen bleiben erhalten: Die bestehenden Unit- und E2E-Tests von `TouchBar` und Bottom Sheet bleiben grün, Touch-Ziele ≥ 48 px (UI-NFR-001 R-011, GP-UX-008, GP-NFR-027). | nein |
| GP-UX-070 | MUST | **Testkennungen bleiben.** Der Umbau verschiebt Komponenten, benennt aber keine bestehende `data-testid` um (GP-UX-012, UI-NFR-022 R-021: `data-testid` ist ein stabiler Vertrag); wird eine Kennung unvermeidbar ersetzt, ändern sich die E2E-Page-Objects im selben Arbeitspaket (R-021: Umbenennung nur zusammen mit den Page Objects). Neue Kennungen (Tabs, Panel-Tabs, Panel-Umschalter, Werkzeug-Leiste, Überlauf-Einträge) folgen UI-NFR-022 (R-020); jedes der WP 10.2–10.5 registriert seine neuen Kennungen in UI-NFR-022 §2.5.1 im selben Arbeitspaket, in dem es sie verwendet. | nein |
| GP-UX-071 | SHOULD | **Weitere Werkzeuge der obersten Ebene (zurückgestellt aus GP-UX-001, #2868).** Bereich (eine Bereichs-Location zeichnen, Eltern von Beeten), Pflanze setzen (eine Pflanze vom Plan aus in einen Slot setzen; heute über das Eigenschaftenpanel und den Pflanzdialog), Text/Label (freie Beschriftung auf dem Plan) und — COULD — Messen (Abstand auf dem Plan messen). Jedes Werkzeug kommt mit Logik, Schaltfläche in der Werkzeug-Leiste (Tooltip mit Verb, GP-UX-010; Roving-Tabindex), Touch-Pfad unter md und registrierter Testkennung (UI-NFR-022) in die Liste von GP-UX-001; AC-2 und TC-053-103 wachsen mit. Nicht MVP (#2913). **Stand:** Messen ist gebaut (#2913, erster Teil) — Klick für Klick eine Strecke oder ein Linienzug, Punkte rasten wie beim Zeichnen ein (Raster, Objektecken und -kanten), Länge je Abschnitt und Summe in der Längeneinheit des Nutzers (m/cm), die Summe zusätzlich als Statustext (`aria-live="polite"`); Enter oder Doppelklick beendet, Rücktaste nimmt den letzten Punkt zurück, Esc löscht; nichts wird gespeichert (keine Plan-Operation, kein Rückgängig-Schritt); unter md über die `TouchBar` („Punkt setzen“ am Fadenkreuz, „Rückgängig“, „Fertig“, „Löschen“); ohne Zeiger (WCAG 2.1.1) über die Werkzeug-Leiste: Solange Messen aktiv ist, bietet sie „Punkt setzen“ (Punkt am Fadenkreuz in der Planmitte; das Fadenkreuz erscheint, sobald der Knopf den Fokus hat oder benutzt wurde) und „Fertig“ (ab zwei Punkten), den Plan verschieben die Pfeiltasten auf der Zeichenfläche, der Statustext nennt diese Schritte. Abschnittslängen, für die die Strecke auf dem Bildschirm zu kurz ist, entfallen zugunsten der Summe. Die Werkzeuge stehen in einem Werkzeug-Register des Editors (`editor/toolRegistry.ts`), aus dem Leiste, `TouchBar`, Cursor und Zeichenfläche lesen. **Bereich** ist gebaut (#2913, zweiter Teil): Das Werkzeug zeichnet eine Bereichs-Location als Rechteck oder Vieleck (kein Kreis, keine Linie, §9.5) mit denselben Zeichenschritten wie ein Beet — eine `create_location`-Operation, ein Rückgängig-Schritt; Typ aus einer Auswahl über der Zeichenfläche (Garten, Terrasse, Balkon, Gewächshaus und eigene Bereichstypen; im Indoor-Plan Zimmer und eigene Indoor-Bereichstypen), Name „Bereich {n}“; ohne Zeiger über „Bereich ▸ Mit Maßen hinzufügen“ (GP-UX-046), unter md über die `TouchBar` wie beim Beet. **Eltern-Regel:** Ein Beet, Bereich oder Gartenobjekt, das *nach* dem Bereich ganz in ihm gezeichnet oder mit Maßen angelegt wird, bekommt ihn als Eltern (kleinste umschließende platzierte Location, wie der Server es prüft, V-03) und wandert beim Verschieben des Bereichs mit (GP-FR-151). Schon vorhandene Beete und Objekte werden **nicht** umgehängt — es gibt keine Operation dafür; ein Bereich, der um sie herum gezeichnet wird, ist zulässig (V-05 gilt nur unter Beeten), sie behalten ihre bisherigen Eltern und bewegen sich beim Verschieben des Bereichs nicht mit; der Editor sagt das nach dem Zeichnen in einem Hinweis, die Typauswahl nennt die Regel vorab. Ein Bereich liegt nie in einem Beet: Als Eltern eines Bereichs kommen nur Bereiche in Frage. Ausgewählt bietet ein Bereich keine Beet-Aktionen: Im Eigenschaftenpanel fehlen Beetausrichtung, Zonen-/Gieß-Zeile, Sonnenangaben und „Bepflanzen“, im Kontextmenü „Bepflanzen“ und „Als Vorlage speichern“; Name, Typ, Maße, Sperren, Duplizieren (samt Inhalt), Reihenfolge, Drehen, Ausrichten, Löschen und „Details öffnen“ bleiben. Löschen nimmt den Teilbaum mit (Beete, Objekte darunter); die Bestätigung nennt stehende Pflanzen als Grund, warum das Speichern ablehnt (V-09, 409 `location.has_active_plants`), und nennt Beete und Objekte, die schon vor dem Bereich darin lagen und stehen bleiben. **Pflanze setzen** ist gebaut (#2913, dritter Teil; Betreiberannahme 2026-11-13): Das Werkzeug setzt **genau eine Pflanze in genau den angeklickten freien Punkt-Pflanzplatz** — es legt keinen Pflanzlauf an, ordnet nichts an und ersetzt den Pflanzdialog des Beets nicht; Reihen und Flächen (Aussaat) und das Bepflanzen eines ganzen Beets bleiben im Beet. Ein Klick (Tippen) auf einen freien Pflanzplatz wählt ihn aus und öffnet einen kleinen Dialog für diesen Platz (Beetname und Platz im Titel): Art (Favoriten zuerst, Namen in der Sprache der Oberfläche), optional Sorte, Pflanztag (heute, UTC-Kalendertag), die Hinweise des Beets zu Fruchtfolge und Nachbarn für diese Art (ohne „Trotzdem pflanzen“) und die Slot-Prüfung des Servers. „Pflanze setzen“ legt die Pflanze über den vorhandenen Einzelpflanzen-Weg an (`POST /plant-instances` mit `slot_key`, keine Plan-Operation, kein Rückgängig-Schritt, nicht im Offline-Puffer); ungespeicherte Planänderungen werden vorher gespeichert, danach wird der Plan neu gelesen, die neue Pflanze ausgewählt und höflich angesagt („Tomate in Hochbeet 1 gesetzt“). Das Werkzeug bleibt aktiv, der nächste Platz ist einen Klick entfernt; Esc oder ein anderes Werkzeug beenden es. Was der Klick sonst trifft, wird gesagt, nie geraten und nie still übergangen: ein **belegter** Platz — kein Dialog, die Pflanze wird ausgewählt, der Hinweis sagt „Hier steht schon eine Pflanze“; ein für eine geplante Pflanzung **reservierter** Platz (GP-FR-074) — ausgewählt, Hinweis; eine **Reihe oder Fläche** — Hinweis, dass sie im Beet gesät wird; ein Beet **ohne Pflanzplätze** — das Beet wird ausgewählt, der Hinweis nennt den Weg („Details öffnen“ im Eigenschaftenpanel); daneben, ein Bereich, ein Gartenobjekt oder leerer Grund — Hinweis. Sind die Pflanzplätze bei der Zoomstufe als Zähler zusammengefasst (Detailstufe, GP-NFR-067), zoomt der Klick um die Klickstelle hinein, bis sie einzeln zu treffen sind, und sagt das. Der Server lehnt eine Einzelpflanze bei einem kritischen Fruchtfolge-Befund (`ROTATION_VIOLATION`) oder einem unverträglichen Nachbarn (`INCOMPATIBLE_COMPANION`) ab; für eine Einzelpflanze gibt es kein „Trotzdem pflanzen“. Der Dialog sagt das schon vor dem Absenden (Slot-Prüfung `POST /plant-instances/slots/{slot_key}/validate-planting`), sperrt „Pflanze setzen“ und verweist auf den Pflanzdialog des Beets, der mit Begründung trotzdem pflanzt („Zum Beet“). Ein inzwischen belegter oder reservierter Platz lehnt der Server mit 409 ab (V-25: `slot.occupied`, `slot.already_planned`); diese und jede andere Ablehnung erscheinen lesbar im Dialog, der Plan wird danach neu gelesen. Ohne Zeiger (WCAG 2.1.1): Pflanzplätze sind auf dem Plan nicht fokussierbar, Beete schon — das Eigenschaftenpanel bietet für ein ausgewähltes Beet mit freien Punkt-Pflanzplätzen „Pflanze setzen“ (der Platz wird im Dialog gewählt) und für einen ausgewählten freien Platz „Pflanze setzen“ für genau ihn. Unter md tippt man den Platz an (mit fingerbreiter Toleranz); die `TouchBar` bietet für dieses Werkzeug nichts an, Ziehen verschiebt den Plan. Rollen: Betrachter sehen weder das Werkzeug noch den Panel-Eintrag (REQ-049). Offline sagt der Statustext, dass das Werkzeug eine Verbindung braucht; es wird nichts gesetzt und nichts vorgemerkt. **Text** ist gebaut (#2913, vierter und letzter Teil): eine freie Beschriftung auf dem Plan als Gartenobjekt der Klasse `text_label` (§9.5, §20.4) — kein Beet, keine Location, keine Pflanzen. Ein Klick auf den Plan setzt den Ankerpunkt (links unten am Text; er rastet wie beim Zeichnen ein — Raster, Objektecken und -kanten; Alt rastet nicht), ein kleiner Dialog fragt nach dem Text (eine Zeile, höchstens 80 Zeichen; Zähler im Feld, Ablehnung als Satz unter dem Feld, Enter bestätigt, Esc bricht ab); ein Ziehen verschiebt den Plan. Die Beschriftung entsteht als ungespeicherte Planänderung wie ein gezeichnetes Beet — eine `create_garden_object`-Operation des Plan-Batches, ein Rückgängig-Schritt, Speichern und Auto-Save wie üblich; offline wie jede Planänderung gesperrt (Hinweis „plan.offline“) —, wird danach ausgewählt, und das Werkzeug gibt an „Auswahl“ ab. Ihre Höhe wählt der Editor so, dass sie bei der aktuellen Zoomstufe etwa so groß wie die Namen auf dem Plan erscheint (20 px, 5 cm bis 2 m), die Breite aus der Textlänge; sie skaliert mit dem Plan und erscheint im SVG/PDF-Export in derselben Größe (Text als Textknoten, maskiert wie jeder Name). Verschieben, Drehen (Drehgriff, Winkelschritt, Eingabe im Panel), Größe, Sperren, Duplizieren, Reihenfolge, Ausrichten und Löschen wie bei jedem Objekt; im Eigenschaftenpanel ist der Name das Feld „Text“ — eine Änderung prüft dieselben Regeln und passt die Breite der Box im selben Rückgängig-Schritt an den neuen Text an; Eigenschaften eines Gegenstands (Höhe, „außerhalb der Grenze“) bietet das Panel für eine Beschriftung nicht an. Der Server prüft den Text unabhängig vom Editor (`GardenObject`-Validator: leer, über 80 Zeichen, Zeilenumbruch, Steuer- oder Bidi-Formatzeichen → 422 `validation.invalid` auf `label`), auch beim JSON-Import. Eine Beschriftung, die über die Gartengrenze hinausliefe, lehnt der Dialog mit der Planregel V-03 ab und behält den Text. Ohne Zeiger (WCAG 2.1.1): Solange „Text“ aktiv ist, bietet die Werkzeug-Leiste „Text hier setzen“ (Ankerpunkt am Fadenkreuz in der Planmitte; das Fadenkreuz erscheint, sobald der Knopf den Fokus hat oder benutzt wurde), den Plan verschieben die Pfeiltasten; unter md die `TouchBar` mit „Punkt setzen“ am Fadenkreuz (kein Rückgängig, kein Fertig — es gibt nur einen Punkt). Rollen: wie Beet und Bereich — das Werkzeug steht auch Betrachtern in der Leiste, der Plan-Batch lehnt ihr Speichern ab (403; Löschen braucht wie bei jedem Objekt die Rolle `lead`). Damit sind alle Werkzeuge aus GP-UX-071 gebaut. | nein |

**Akzeptanzkriterien der Arbeitsfläche (AC-1…AC-11 aus #2820, AC-12…AC-17 aus dem Readiness-Review).** Die Kriterien sind die Abnahme der SHOULD-Zeilen GP-UX-063…069 (Arbeitspakete 10.2–10.5) und der MUST-Zeile GP-UX-070; sie werden in WP 10.13 als TC-053-Fälle abgeleitet. Gemessen im Planungsmodus der Gartenübersicht mit einem Plan, der mindestens ein Beet hat, bei 100 % Browser-Zoom; „Viewport“ meint die CSS-Pixel des Browserfensters. **„Jede Editor-Funktion“** meint: alle Werkzeuge aus GP-UX-001 (samt Untermenü-Einträgen), alle vier Panel-Tabs und alle Einträge des Überlaufs „⋮“. **„Kopfleiste“** meint die Editor-Kopfleiste; App-Bar, Brotkrumen und Seitentitel der App-Shell (UI-NFR-005, UI-NFR-017) liegen außerhalb des Editors und zählen nicht mit (Abschnitt „Verhältnis zu Shell und Seitenkopf“).

| AC | Kriterium | Anforderung | Nachweis |
|----|-----------|-------------|----------|
| AC-1 | Bei einem Viewport von 1366 × 768 ist die Zeichenfläche (`garden-plan-canvas`) mindestens 60 % der Viewport-Höhe hoch, und keine Steuerzeile bricht um (alle Bedienelemente der Kopfleiste liegen auf einer Zeile). | GP-UX-063, GP-UX-067 | E2E mit Screenshot-Checkpoint |
| AC-2 | Bei einem Viewport von 1024 × 768 ist jede Editor-Funktion (alle Werkzeuge aus GP-UX-001 samt ihrer Untermenü-Einträge, alle Panel-Tabs, alle Überlauf-Einträge) erreichbar, ohne dass die Seite horizontal scrollt (die Seitenbreite übersteigt die Viewport-Breite nicht). | GP-UX-069 | E2E mit Screenshot-Checkpoint |
| AC-3 | Zwischen den Elementen der App-Shell (App-Bar, Brotkrumen, Seitentitel — nicht gezählt) und der Zeichenfläche steht genau eine Editor-Kopfleiste; der Seitenkopf der Route trägt keine eigenen Aktionen; die Werkzeuge stehen in einer vertikalen Leiste. | GP-UX-063, GP-UX-066 | vitest, E2E |
| AC-4 | Drehen, Ausrichten und Löschen werden nur gerendert, solange eine Auswahl besteht; „Als Vorlage speichern“ nur, solange genau ein Beet ausgewählt ist. | GP-UX-066 | vitest |
| AC-5 | Ohne Auswahl (und ohne vom Nutzer geöffnetes Panel) reserviert das Seitenpanel keine Breite. Der Panel-Umschalter trägt `aria-expanded` und `aria-controls`; die Panel-Tabs folgen dem WAI-ARIA-Muster „Tabs“ (`role="tab"`, `aria-selected`, `aria-controls` auf ihr `tabpanel`, Roving-Tabindex mit Pfeiltasten, Aktivierung mit Eingabe- oder Leertaste) und sind per Tastatur erreichbar. | GP-UX-068 | vitest + axe, E2E |
| AC-6 | Die Ebenen-Schalter tragen im Tab „Ebenen“ eine sichtbare Textbeschriftung, zusammen mit der Legende. | GP-UX-068 | vitest |
| AC-7 | Die Beetliste ist ein eigener Tab „Beete“; der Tab-Zustand steht in der URL (`?tab=`, Deep-Link öffnet den Tab, „Zurück“ führt zum vorigen Tab); ein Klick auf eine Zeile öffnet „Plan“ mit hervorgehobenem Beet. | GP-UX-064 | vitest, E2E |
| AC-8 | Der Ungespeichert-Dialog erscheint beim Verlassen des Plans mit ungespeicherten Änderungen, aber nicht beim Wechsel zwischen Plan, Liste und Beete; die Änderungen sind nach dem Wechsel noch da. | GP-UX-065 | vitest, E2E |
| AC-9 | Unter md erscheinen `TouchBar` und Bottom Sheet, bei grobem Zeiger die `TouchBar` auf jeder Breite (die Panelform folgt allein der Breite). Die bestehenden Unit- und E2E-Tests von `TouchBar` und Bottom Sheet bleiben grün; alle Touch-Ziele sind ≥ 48 px (UI-NFR-001 R-011). | GP-UX-069, §9.7 | vitest, E2E bei 390 × 844 mit Screenshot-Checkpoint |
| AC-10 | Bestehende `data-testid` bleiben oder werden zusammen mit den E2E-Page-Objects migriert; Unit- und E2E-Suites sind grün. | GP-UX-070 | CI, E2E |
| AC-11 | REQ-053 beschreibt das neue Layout vor der Umsetzung. | dieser Abschnitt | erfüllt mit v1.16 (WP 10.1, #2822) |
| AC-12 | Ohne `tab` oder mit unbekanntem Wert (z. B. `?tab=xyz`) zeigt die Route den Tab „Plan“; mit `mode=field` erscheint keine Tab-Leiste, und ein zusätzliches `tab` bleibt ohne Wirkung. | GP-UX-064 | vitest, E2E |
| AC-13 | Nach einem erfolgreichen Speichern zeigt der Tab „Beete“ den gespeicherten Stand (ein neu gezeichnetes Beet steht in der Liste, ohne die Seite neu zu laden); im Indoor-Plan heißt der Tab „Pflanzplätze“ bei unverändertem URL-Wert `beds`. | GP-UX-064 | vitest |
| AC-14 | Zoom-Steuerung, Maßstabsbalken und Mini-Map liegen innerhalb des Rechtecks von `garden-plan-canvas` und beanspruchen keine Layouthöhe: Die Höhe der Zeichenfläche ist mit und ohne sichtbare Mini-Map gleich, und außerhalb der Zeichenfläche steht keine Zeile für Zoom oder Maßstab. | GP-UX-067 | vitest, E2E |
| AC-15 | Bei 390 × 844 zeigt die Kopfleiste auf einer Zeile ohne Umbruch nur Zurück, Speichern-Status, „Speichern“ und „⋮“; Auto-Save-Schalter, Feldmodus-Wechsel, Panel-Umschalter und die Tabs Plan · Liste · Beete stehen im Überlauf (Verlagerungsreihenfolge nach GP-UX-063), jeder Überlauf-Eintrag ist ≥ 48 px hoch und mit Text beschriftet; Undo/Redo sind in der `TouchBar` sichtbar. | GP-UX-063 | vitest, E2E bei 390 × 844 mit Screenshot-Checkpoint |
| AC-16 | Nach Plan → Beete → Plan (und Plan → Liste → Plan) sind die Auswahl und der Viewport (Ausschnitt und Zoomstufe) unverändert. | GP-UX-065 | vitest, E2E |
| AC-17 | Panel-Zustand: Eine neue Auswahl öffnet das Panel auf „Eigenschaften“; Abwählen schließt es nur, wenn die Auswahl es geöffnet hatte; ein vom Nutzer geöffnetes Panel bleibt über Aus- und Abwählen offen; ein vom Nutzer geschlossenes Panel bleibt zu, bis der Nutzer es öffnet oder neu auswählt; ohne Auswahl geöffnet zeigt es den zuletzt benutzten Tab, beim ersten Öffnen „Ansicht“. Der Umschalter steht in der Kopfleiste (oder als beschrifteter Überlauf-Eintrag ≥ 48 px). | GP-UX-068 | vitest |

**Offene Punkte der Abnahme Welle 10 (v1.17, WP 10.15).** Gemessen in der echten App (E2E TC-053-098…108); die Kriterien oben bleiben unverändert, bis der Betreiber in #2884 entscheidet (§32.7):

- **AC-2 ist ein lg-Kriterium.** Das App-Theme legt md = 768 px und lg = 1024 px fest (`theme/tokens.ts`); ein Viewport von 1024 × 768 zeigt daher schon das angedockte Panel, nicht den Drawer von md. TC-053-102 misst das md-Layout bei 820 × 1180, ohne AC-2 zu beanspruchen. AC-2 misst seit v1.19 die eingegrenzte Werkzeugliste von GP-UX-001 (TC-053-103, #2868); die zurückgestellten Werkzeuge sind GP-UX-071 (#2913).
- **AC-1 und der Light-Modus-Hinweis.** Im Light-Modus auf einem nicht-privaten Host zeigt die App über dem Editor einen Warnhinweis. Mit ihm ist die Zeichenfläche bei 1366 × 768 **58,5 %** der Viewport-Höhe hoch, ohne ihn **66,9 %**. Die E2E blendet ihn wie ein Nutzer aus. Ob der Hinweis als Teil der App-Shell (nicht gezählt) gilt, ist offen.
- **AC-6 und die Legende.** Die Ebenen-Legende erscheint im Tab „Ebenen“ erst, wenn mindestens eine Ebene eingeschaltet ist.
- **Drawer bei md — entschieden (v1.18).** Der Drawer über der Zeichenfläche verdeckte die Zoom-Steuerung und ein ausgewähltes Objekt (#2885). Ab md liegt das Panel angedockt neben der Zeichenfläche, die schmaler wird; eine Auswahl schwenkt in den sichtbaren Teil.
- **Hinweiszeilen.** Zeichen-Hinweis, Notiz und Info (`garden-plan-draw-hint`, `garden-plan-notice`, `garden-plan-info`) stehen weiter als Zeilen über der Zeichenfläche; sie erscheinen nur zeitweise und verschieben dann die Fläche.

---

## 18. Mobile Nutzung im Garten (Feldmodus)

### 18.1 Zentrales Szenario

Der Nutzer steht mit Smartphone oder Tablet im Garten, Hände feucht oder verschmutzt, Sonne auf dem Display, oft nur eine Hand frei. Er will **lesen und bestätigen**, selten zeichnen.

| Schritt | Interaktion im Feldmodus | Zielzeit |
|---------|--------------------------|----------|
| 1. Plan öffnen | Site-Liste → „Plan" (oder QR-Etikett am Beet, GP-FR-052); der Plan lädt mit letztem Viewport | < 3 s auf 4G (GP-NFR-002) |
| 2. Beet auswählen | Ein Tipp auf das Beet (ganze Fläche ist Ziel; Mindestgröße auf dem Bildschirm 48 px, sonst Auto-Zoom auf das Beet beim Tipp in die Nähe) | 1 Tipp |
| 3. Sehen, was gepflanzt ist | Bottom Sheet mit Beetname, Pflanzen (Spezies, Anzahl, Phase), offene Aufgaben | sofort |
| 4. Pflegeaufgabe sehen | Aufgaben als Liste im Sheet, überfällige zuerst, Kategorie-Icon ≥ 32 px | — |
| 5. Als erledigt markieren | Großer Button „Erledigt" (≥ 64 × 64 px, UI-NFR-019 R-007) → Schnell-Dialog mit optionalen Feldern (Menge/Notiz) → „Fertig". **Zwei Tipps** nach der Beetauswahl (GP-ACC-029); 8 s „Rückgängig" (GP-FR-149) | 2 Tipps |
| 6. Notiz hinzufügen | „Notiz" im Sheet → Textfeld + Spracheingabe des OS → `care_event(category = note)` | 3 Tipps |
| 7. Foto hinzufügen | „Foto" → Kamera (REQ-052 Profil `gallery`) → Zuordnung Beet oder Pflanze | 3 Tipps |
| 8. Neue Pflanzung dokumentieren | „Gepflanzt" → Spezies (Favoriten zuerst, REQ-020-Favoriten), Anzahl, Layout-Vorgabe → Run `active` + Pflanzen werden sofort erzeugt (Kurzpfad aus §11.1) | ≤ 6 Tipps |
| 9. Tatsächliche Position korrigieren | Pflanze antippen → „Position korrigieren" → **Stepper als Standard** (±10 cm, bildschirmbezogen hoch/runter/links/rechts, F-16) auf dem vergrößerten Beet; Long-Press-Drag als Alternative | ≤ 4 Tipps |

### 18.2 Anforderungen

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-UX-020 | MUST | Feldmodus ist die Standardansicht auf xs (< 600 px) und per Schalter auf allen Breiten verfügbar (`?mode=field`); er blendet Zeichenwerkzeuge, Raster und Griffe aus und vergrößert Touch-Ziele auf 64 px (Kiosk-Theme-Konstanten `KIOSK_TOUCH_TARGET` wiederverwenden). | ja |
| GP-UX-021 | MUST | Kontrast im Feldmodus ≥ 7:1 für Text und ≥ 4,5:1 für Objektgrenzen (UI-NFR-019 R-040 sinngemäß, Sonnenlicht); Phasenfarben bekommen Umriss. | ja |
| GP-UX-022 | MUST | Keine reine Swipe-Bedienung (UI-NFR-019 R-028); jede Geste hat eine Schaltflächen-Alternative. | ja |
| GP-UX-023 | MUST | Debounce 300 ms auf „Erledigt" (R-029), Long-Press 500 ms für Verschieben; destruktive Aktionen sind im Feldmodus nicht verfügbar (Löschen, Beet räumen nur im Planungsmodus); nach dem ersten Tipp auf „Erledigt" ist der Button bis zur Server-Antwort gesperrt (Doppeltipp, F-16). | ja |
| GP-UX-024 | SHOULD | Offline-Lesen des Plans (UI-NFR-012 R-020: Standorte offline lesbar): letzter geladener Plan je Site im IndexedDB-Cache (TTL 15 min, R-012); Erledigen/Notiz/Foto werden als Offline-Einträge gepuffert (R-015, max. 500, R-019) und bei Verbindung mit `performed_at` aus dem Erfassungszeitpunkt gesendet. Geometrie-Änderungen bleiben online-only (Konfliktrisiko). Cache-Schlüssel enthält `user_key` und `tenant_key`; Logout und Tenant-Wechsel leeren den Plan-Cache (SR-019). Der Offline-Puffer bleibt an Nutzer und Mandant gebunden: ausdrückliches Abmelden mit offenen Einträgen fragt nach, ein Tenant-Wechsel behält die Einträge des anderen Mandanten, Kill-Switch und Kontolöschung löschen ihn (v1.13, UI-NFR-012 R-056, §32.6 Pkt. 14). Bis dahin zeigt der Feldmodus bei fehlender Verbindung einen sichtbaren Offline-Hinweis und sperrt „Erledigt" statt still zu verlieren (F-17, MVP). | nein (Puffer), ja (Offline-Hinweis) |
| GP-UX-025 | MUST | Der Feldmodus funktioniert ohne Hover: alle Infos erscheinen per Tipp; Tooltips werden durch Sheet-Inhalte ersetzt. | ja |
| GP-UX-026 | SHOULD | GPS-Hilfe: Ist `Site.gps_coordinates` + `north_angle_deg` gesetzt und erlaubt der Nutzer die Ortung (REQ-002 Opt-in-Muster), markiert ein Punkt die ungefähre eigene Position auf dem Plan (Genauigkeitskreis ≥ 3 m). **Die Eigenposition verlässt das Gerät nie** (SR-019): kein API-Request, keine URL, kein Redux-Persist, kein IndexedDB, kein Log, kein Sentry-Event — nur flüchtiger Komponentenzustand. | nein |
| GP-UX-027 | MUST | Der Kurzpfad „Gepflanzt" (Schritt 8) erzeugt Run **und** Pflanzen in einem Request (`POST …/locations/{key}/quick-planting`), damit im Garten kein zweistufiger Ablauf nötig ist; der Run erhält `source = field_mode`. | ja |
| GP-UX-028 | SHOULD | Beet-QR-Code (GP-FR-052) öffnet direkt die Beetansicht im Feldmodus; ohne Session → Login → Rücksprung (bestehende Redirect-Logik, UI-NFR-014). | nein |
| GP-UX-029 | MUST | **Schnellprotokoll** im Feldmodus (F-03): sechs Chips (Gegossen · Geerntet · Gesät · Gejätet/Gemulcht · Gepflanzt · Notiz) im Beet-Sheet; jeder Chip erzeugt mit einem Tipp ein `care_event` (bzw. öffnet den Kurzpfad für Gepflanzt/Geerntet) und zeigt die Rückgängig-Snackbar. | ja |
| GP-UX-030 | MUST | **Einstieg über Liste** (F-18): Der Feldmodus startet mit „Meine Beete · heute fällig" (Liste, nach Zuweisung und Fälligkeit sortiert) und bietet „Karte" als zweiten Tab; Tenant, Site und Viewport werden je Gerät gemerkt (localStorage); Schrift ≥ 16 px; Aufgaben werden vor der Geometrie geladen (zwei Requests, Liste zuerst). | ja |
| GP-UX-031 | SHOULD | Ebene „zuletzt gegossen" (Farbskala Tage seit letztem `watering`-Ereignis je Beet) für Gießdienste (F-05). | nein |

---

## 19. Technische Architektur

### 19.1 Schichten (NFR-001)

```
Presentation  React 19 / MUI 9 / Redux Toolkit
  features/gardenPlanner/
    model/        PlanModel (TS-Typen = DTO v1), PlanOperation, applyOperation(), geometry.ts (Port der Calculators)
    state/        gardenPlanSlice (Plan, Auswahl, Werkzeug, Undo-Stack, Dirty-Flag, Konflikt)
    renderer/     PlanRenderer (Interface) → SvgPlanRenderer (MVP) | KonvaPlanRenderer (Fallback)
    editor/       GardenPlanEditor, Toolbar, PropertiesPanel, FieldModeSheet, Handles, Gestures
    api/          gardenPlan.ts (axios über tenantClient)
API           FastAPI  api/v1/garden_plan/ (tenant_router, schemas v1), Erweiterungen locations/slots/planting_runs/tasks
Business      domain/services/garden_plan_service.py, care_event_service.py, irrigation_zone_service.py
              domain/calculators/geometry_calculator.py, planting_layout_calculator.py
              domain/engines/adjacency_engine.py
Data Access   data_access/arango/garden_object_repository.py, care_event_repository.py, irrigation_zone_repository.py,
              Erweiterung site_repository (plan), location/slot (geometry); Stream-Transaktion im garden_plan_repository
Persistence   ArangoDB Collections + Edges (§20), Migration M1+
```

| ID | Prio | Anforderung |
|----|------|-------------|
| GP-NFR-001 | MUST | Keine neue Schicht, kein zweiter API-Stil: Endpunkte unter `/api/v1/t/{tenant_slug}/…`, Fehlerformat NFR-006, Pydantic-v2-Schemas mit `to_response`, Service-Signaturen mit `tenant_key` **keyword-only ohne Default** (Memory „Guard opt-in am Aufrufort"). |
| GP-NFR-002 | MUST | Plan-Ladezeit: `GET …/sites/{key}/plan` liefert den gesamten Plan (Site-Plan, Locations mit Geometrie, GardenObjects, Slots mit Geometrie, Pflanzen-Kurzinfo, Task-Zähler) in **einem** Request; Antwort ≈ 1 MB unkomprimiert bei einem großen Garten (GP-NFR-031, E-13) (§25) und ≤ 300 ms p95 serverseitig. |
| GP-NFR-003 | MUST | Der Editor wird per Dynamic Import geladen (UI-NFR-003 R-012/R-028); der Initial-Bundle-Zuwachs durch dieses Feature ist **0 KB**; der Editor-Chunk ≤ 120 KB gzip (SVG-Renderer) bzw. ≤ 200 KB gzip (mit Konva). `bundle-budget.json` erhält einen Eintrag `gardenPlanner` mit diesem Budget. |
| GP-NFR-004 | MUST | Versionierte DTOs: Plan-Schemas tragen `schema_version: "1"` im Export (§23) und in `GET /plan`; Breaking Changes erzeugen `schema_version: "2"` mit Import-Migration. |

### 19.2 Domänenmodell im Frontend

Das Frontend hält den Plan als **normalisiertes Modell** (`entities: {locations, gardenObjects, slots, plants}`, `ids`), identisch zum DTO. Der Renderer bekommt dieses Modell plus Viewport und liefert ein Bild; er hält keinen Zustand außer Caches. Alle Nutzeraktionen werden zu `PlanOperation`s:

```ts
type PlanOperation =
  | { op: 'create_location'; temp_key: string; data: LocationCreate }
  | { op: 'update_geometry'; entity: 'location' | 'garden_object' | 'slot'; key: string; geometry: Geometry }
  | { op: 'update_fields'; entity: ...; key: string; patch: Partial<...> }
  | { op: 'create_garden_object'; temp_key: string; data: GardenObjectCreate }
  | { op: 'delete'; entity: ...; key: string }
  | { op: 'set_boundary'; boundary: Geometry; north_angle_deg?: number };
```

`applyOperation(model, op) → model` ist rein und invertierbar (jede Operation kennt ihre Umkehrung für Undo). Die Operationsliste ist zugleich der Request-Body der Batch-API (§21.3).

### 19.3 State Management

| ID | Prio | Anforderung |
|----|------|-------------|
| GP-NFR-005 | MUST | Ein Slice `gardenPlanSlice` (RTK `createSlice`, Thunks für load/save, kein RTK Query — Bestandsmuster). Undo/Redo als `past[]/future[]` von Operationen im Slice; Dirty-Flag = `pending.length > 0`. |
| GP-NFR-006 | MUST | Optimistic Updates: Operationen werden sofort auf das Modell angewandt; Speichern sendet `pending[]` mit `expected_revision`; bei 2xx wird `plan_revision` übernommen und `pending` geleert; bei 409 bleibt `pending` erhalten, Konflikt-Dialog (GP-UX-017). |
| GP-NFR-007 | MUST | Concurrent Editing: **kein** Echtzeit-Mehrbenutzer-Editing (WON'T, §29). Schutz ist die optimistische Revision auf Site-Ebene **für Strukturänderungen** (Locations, GardenObjects, Boundary, Zonen — alles, was Containment betrifft). **Außerhalb der Revision** (F-09, D-06 revidiert) laufen: Slot-Geometrie-Korrekturen (GP-FR-068), Quick-Planting (GP-API-017), Slot-Batch eines Beets (GP-API-015), Tasks und `care_events` — sie kollidieren nicht mit einem offenen Planungs-Editor; der Editor übernimmt sie beim nächsten Laden oder per Hinweis „Beet 3 wurde aktualisiert" (Polling 30 s im Planungsmodus, SHOULD). Zwei Gärtner, die gleichzeitig Struktur ändern, bekommen beim zweiten Speichern 409. Parzellen können für Mitglieder `locked` sein (GP-FR-032); `locked` sperrt Struktur, nicht Pflege. |
| GP-NFR-008 | MUST | Custom Hooks mit Objekt-/Array-Rückgabe nutzen `useMemo` (FRONTEND.md); Renderer-Props sind referenzstabil, damit Objekte nur bei Änderung neu zeichnen. |

### 19.4 Rendering-Technologie

**Bewertungskriterien** (je 0–3; Lizenz ist K.-o.): Open-Source-Lizenz · React-19-Integration · Polygon-Bearbeitung · Zoom/Pan · Touch · Drag & Drop · Snap-to-Grid · Performance bei 2 000 Objekten · Persistierbarkeit (Trennung Modell/Ansicht) · Accessibility (DOM-Semantik) · Wartbarkeit/Testbarkeit (jsdom, Snapshot) · Bundle-Größe · Projektrisiko (Pflege, Bus-Faktor).

| Kriterium | **SVG in React** (kein Framework) | **Konva + react-konva** | **Fabric.js v6** | **HTML Canvas roh** | **Pixi.js** |
|-----------|----|----|----|----|----|
| Lizenz | — (Browser) ✔ | MIT ✔ | MIT ✔ | — ✔ | MIT ✔ |
| React 19 | 3 (nativ) | 3 (react-konva 19.x) | 1 (imperativ, Wrapper nötig) | 1 | 1 (react-pixi veraltet) |
| Polygon-Editing | 3 (DOM-Punkte, eigene Griffe) | 2 (Line + eigene Griffe) | 3 (eingebaut) | 1 | 1 |
| Zoom/Pan | 3 (viewBox) | 3 (Stage scale) | 2 | 2 | 3 |
| Touch | 2 (Pointer Events) | 3 | 2 | 2 | 3 |
| Drag & Drop | 2 (Pointer Events, eigene Logik) | 3 | 3 | 1 | 2 |
| Snap-to-Grid | 3 (Modellseitig, unabhängig) | 3 | 2 | 3 | 3 |
| Performance 2 000 Objekte | 2 (DOM; bis ~3 000 flüssig mit Culling) | 3 | 2 | 3 | 3 |
| Persistierbarkeit | 3 (Modell ist die Quelle) | 3 (wenn diszipliniert) | 1 (Fabric-JSON verführt zum Modell) | 3 | 3 |
| Accessibility | 3 (`role`, `aria-label`, Fokus je `<g>`) | 0 (Bitmap; Parallel-DOM nötig) | 0 | 0 | 0 |
| Testbarkeit | 3 (jsdom, Snapshot, `data-testid`) | 1 (Canvas-Mock) | 1 | 1 | 1 |
| Bundle | 3 (0 KB) | 2 (~50 KB gzip) | 1 (~100 KB) | 3 | 1 (~150 KB) |
| Projektrisiko | 3 | 2 (kleines Team, aktiv) | 2 (v6-Umbruch 2024) | 3 | 2 |
| **Summe** | **33** | **28** | **20** | **23** | **23** |

**Entscheidung D-01 (§33): SVG in React als MVP-Renderer**, mit `PlanRenderer`-Grenze, hinter der ein Konva-Renderer nachgerüstet wird, sobald die Performance-Schwelle (GP-NFR-013: > 3 000 sichtbare Objekte oder Frame-Zeit > 16 ms bei Drag) in der Messung gerissen wird. Begründung: Accessibility (UI-NFR-002 R-024–R-027 verlangen fokussierbare, benannte Objekte — mit Canvas nur über ein Parallel-DOM), Testbarkeit mit dem bestehenden vitest/jsdom-Setup, 0 KB Bundle (Budget-Memory), und die Gartengrößen der Zielgruppe (§25: „groß" = 500 Objekte, 2 000 Pflanzen) liegen innerhalb der SVG-Komfortzone mit Viewport-Culling. Konva wurde **nicht** verworfen, sondern als zweiter Renderer vorgesehen; die Grenze ist nicht spekulativ, weil sie die Testdoubles (Headless-Renderer für Unit-Tests) ohnehin braucht.

| ID | Prio | Anforderung |
|----|------|-------------|
| GP-NFR-009 | MUST | `PlanRenderer`-Interface: `render(model, viewport, selection, options) → ReactNode`, `hitTest(point_px) → key \| null`, `hitTestAll(point_px) → key[]` (Stapel, oberstes zuerst; GP-UX-033), `toScreen(p_m)`, `toModel(p_px)`. Editor-Logik (Werkzeuge, Griffe, Snap, Undo) importiert **keine** Renderer-Bibliothek. Ein ESLint-`no-restricted-imports`-Eintrag erzwingt das für `features/gardenPlanner/editor/**`. |
| GP-NFR-010 | MUST | Viewport-Culling: nur Objekte, deren `bbox` den Viewport schneidet (± 20 % Rand), werden gerendert; Detailstufen (Marker, Beschriftung, Icons) nach der LOD-Tabelle GP-NFR-067. |
| GP-NFR-011 | MUST | Drag-Rendering nutzt eine CSS-Transformation des bewegten `<g>` (kein Re-Render des Modells je Mausbewegung); das Modell wird erst beim Loslassen aktualisiert. |

### 19.5 Backend

| ID | Prio | Anforderung |
|----|------|-------------|
| GP-NFR-012 | MUST | Geometrie-Validierung und Flächenberechnung in `domain/calculators/geometry_calculator.py` (rein, ohne I/O, Property-Tests mit Hypothesis: Fläche ≥ 0, Shoelace = Rechteckformel für rect, Rotation erhält Fläche). Keine externe Geometrie-Bibliothek im MVP (Shapely wäre nur für Polygon-Schnitt nötig → COULD für GP-FR-012 Objekt-Snap und Überlappungsprüfung; Entscheidung D-04). |
| GP-NFR-013 | MUST | Die Batch-API läuft in **einer** ArangoDB-Stream-Transaktion (`db.begin_transaction(write=[…])`) mit Revisionsprüfung: `IF site.plan.plan_revision != expected → abort 409`. Alles-oder-nichts, im Gegensatz zum bestehenden `BatchResponse`-Teilerfolg bei Tasks (bewusste Abweichung: eine halb gespeicherte Geometrieänderung ist nicht reparierbar). **Komplexitätsbudget (SR-012):** zusätzlich zu 500 Operationen gilt Σ Polygonpunkte ≤ 20 000 je Batch, Request-Body ≤ 1 MiB (413 `body_too_large`, E-13) und ein Zeitbudget von 10 s (422 `batch.too_complex`); Containment- und Überlappungsprüfung laufen **vor** dem Öffnen der Transaktion (nur Revisionsprüfung und Schreiben laufen darin). |
| GP-NFR-014 | MUST | Containment-Regeln (§22) werden im Service geprüft, nicht im Router; der Service nimmt Eltern-Keys und `tenant_key` keyword-only (Memory „Prädikat in den Service"). |
| GP-NFR-015 | MUST | Migrationen nach NFR-016/ADR-005: **Migrations-Platzhalter:** M1…M6 sind logische Namen; die konkrete `vNNNN`-Nummer vergibt die Umsetzung als nächste freie Nummer (Stand 2026-10-04 abends ist `v0081` die letzte — die ursprünglich genannten v0072–v0077 waren auf `develop` bereits vergeben, Review-Finding). `M1_garden_plan_geometry` (Collections, Edges, Indizes; `dimensions` → `geometry`/`height_m` und `Slot.position` → `geometry` mit `pitch_m`, beide Felder danach entfernt — O-01/O-02), `M2_location_type_is_bed` (Seeds, `is_bed`), `M3_task_category_extension`, `M4_care_events_backfill` (SHOULD, GP-FR-105, Welle 8 — E-11), `M5_recurrence_cron_to_rrule` (O-05; konvertiert nur gespeicherte Alt-Cron-Strings, parkt nicht konvertierbare nach `recurrence_rule_unconvertible` (E-14) und entfernt den croniter-Fallback, weil die Engine seit `recurrence_engine.py:51` RRULE spricht — v1.4), `M6_nutrient_demand_split` (O-07). Stand 2026-10-15 ist `v0092` die letzte Nummer; M1 beginnt frühestens bei `v0093`, die Nummer wird beim Branch-Start vergeben. Jede Migration ist `reversible` oder begründet nicht; M1, M5 und M6 liefern einen Dry-Run-Report (`--dry-run`), weil sie Bestandsdaten umformen. |
| GP-NFR-016 | SHOULD | Celery: `adjacency_recompute` (nach Slot-Batch, entkoppelt, idempotent), `care_events_consistency` (täglich), `irrigation_zone_demand_aggregate` (täglich nach REQ-037). |
| GP-NFR-017 | MUST | **Harte Quoten (SR-004):** je Site ≤ 500 Locations + GardenObjects, ≤ 8 000 Slots; je Beet ≤ 2 000 Slots; Quick-Planting `quantity` ≤ 500. Überschreitung → 422 `plan.quota_exceeded {limit, current}`. **Seit Welle 7:** je Site ≤ 500 Bewässerungszonen → 422 `irrigation_zone.quota_exceeded` beim Anlegen (GP-API-050) und beim `merge`-/`replace`-Import; eine Site über der Grenze antwortet auf `GET /sites/{key}/plan` (mit `include=zones`), den Export und einen `replace`-Import ebenfalls mit 422, statt die Liste stillschweigend zu kürzen (#2525). Je Mandant ≤ 200 eigene Beetvorlagen → 422 `bed_template.quota_exceeded`. §25.1 „Belastungsgrenze" ist damit eine Quote, keine Prosa. |

### 19.6 Geteilte Berechnungen (Backend ↔ Frontend)

`planting_layout_calculator.py` und `geometry_calculator.py` werden in TypeScript portiert (`features/gardenPlanner/model/geometry.ts`, `layout.ts`). Beide Seiten laufen gegen **dieselben Testvektoren** (`spec/e2e-testcases/fixtures/garden-plan-vectors.json`, neu anzulegen, SSOT; je ein Test in pytest und vitest liest die Datei). Die Serverantwort ist bei Abweichung maßgeblich (GP-FR-063). Damit entsteht keine Logik-Duplikation ohne Kontrolle — das Memory-Muster „Test erreicht die Regel über einen anderen Pfad als die Produktion" wird durch die gemeinsamen Vektoren adressiert.

### 19.7 Import/Export-Architektur

Export und Import laufen serverseitig (§23): JSON-Backup über `garden_plan_service.export()`/`import_()`, PDF über den bestehenden `PrintEngine` mit einer Jinja-Vorlage `garden_plan.html`, in die ein serverseitig erzeugtes SVG eingebettet wird (ein Python-SVG-Writer in `domain/engines/plan_svg_engine.py`, ohne externe Lib — WeasyPrint rendert SVG nativ). PNG entsteht clientseitig aus dem SVG-DOM (Canvas `drawImage`, bestehendes Muster aus `PlantTagDialog`).

---

## 20. Datenmodell

### 20.1 Geometrie (eingebetteter Werttyp, Pydantic `Geometry`)

```json
{ "kind": "rect",     "origin": [2.000, 3.500], "width_m": 3.000, "length_m": 1.200, "rotation_deg": 0.0 }
{ "kind": "circle",   "origin": [8.250, 1.000], "radius_m": 0.400 }
{ "kind": "polygon",  "points": [[0,0],[4.2,0],[4.2,1.5],[2.0,2.6],[0,1.5]], "rotation_deg": 0.0 }
{ "kind": "polyline", "points": [[0,5],[12,5]], "width_m": 0.800 }
{ "kind": "point",    "origin": [0.300, 0.300] }
```

| Feld | Typ | Regel |
|------|-----|-------|
| `kind` | `rect \| circle \| polygon \| polyline \| point` | je Objektklasse eingeschränkt (§9.5) |
| `origin` | `[x, y]` in m | Rect: linke untere Ecke vor Rotation; Circle/Point: Mittelpunkt |
| `width_m`, `length_m`, `radius_m`, `width_m` (polyline) | float, 3 Dezimalen | 0,01 ≤ v ≤ 1 000 |
| `points` | `[[x,y], …]` | polygon ≥ 3, polyline ≥ 2, ≤ 200 Punkte; polygon einfach (keine Selbstschnitte) |
| `rotation_deg` | float | 0 ≤ r < 360; negativ abgelehnt, Werte die auf 360,000 runden wrappen auf 0,0 (E-12); für circle/point/polyline nicht erlaubt |

**Polygon-Pivot (E-12):** Ein Polygon dreht um seinen **ersten Punkt** (`points[0]`, zugleich Anker); `rect` dreht um `origin`. Festgelegt durch die Vektoren `bbox-polygon-002`/`transform-004`.

Abgeleitet (serverseitig, read-only im DTO): `area_m2`, `bbox`, `centroid`. Rechenbeispiel für die Konvention (GP-FR-008, CCW um `+x`, Rotation um `origin` = linke untere Ecke): `rect` mit `origin [1,1]`, `width_m 2` (entlang `+x` vor Rotation), `length_m 1`, `rotation_deg 90` hat die Ecken (1,1), (1,3), (0,3), (0,1) → `bbox [0,1,1,3]`.

**Rahmen:** `Site.plan.boundary`, `Location.geometry`, `GardenObject.geometry` → Plan-Rahmen. `Slot.geometry` → Beet-Rahmen der übergeordneten Location (§9.2).

### 20.2 Site (bestehend, additiv)

```json
{
  "_key": "site_7f3a",
  "tenant_key": "t_garten_sabine",
  "name": "Gemüsegarten hinterm Haus",
  "type": "outdoor",
  "gps_coordinates": [52.5200, 13.4050],
  "total_area_m2": 60.0,
  "plan": {
    "boundary": { "kind": "polygon", "points": [[0,0],[10,0],[10,6],[0,6]], "rotation_deg": 0.0 },
    "north_angle_deg": 15.0,
    "default_grid_m": 0.10,
    "adjacency_factor": 1.5,
    "plan_revision": 42,
    "plan_updated_at": "2026-10-04T09:12:33Z",
    "plan_updated_by": "u_sabine"
  }
}
```

`plan` ist optional; eine Site ohne `plan` ist eine Site ohne Gartenplan (Bestandsverhalten). `total_area_m2` wird bei gesetzter `boundary` daraus berechnet.

### 20.3 Location (bestehend, additiv) — Beispiel Beet

```json
{
  "_key": "loc_b03",
  "site_key": "site_7f3a",
  "parent_location_key": "loc_nutzgarten",
  "location_type_key": "raised_bed",
  "name": "Hochbeet 3",
  "description": "Südseite, Lärchenholz, 2024 gebaut",
  "depth": 2, "path": "site_7f3a/loc_nutzgarten/loc_b03",
  "geometry": { "kind": "rect", "origin": [1.0, 1.0], "width_m": 2.0, "length_m": 1.0, "rotation_deg": 90.0 },
  "height_m": 0.8,
  "area_m2": 2.0,
  "bbox": [0.0, 1.0, 1.0, 3.0],
  "bed_status": "active", "season_state": "planted",
  "sun_exposure": "full_sun",
  "irrigation_system": "drip",
  "irrigation_zone_key": "zone_sued",
  "soil_profile": {
    "growing_medium_kind": "raised_bed_mix", "soil_texture": "unknown", "stone_content_class": "none", "substrate_key": "sub_hochbeet_mix", "substrate_batch_key": null,
    "ph": 6.8, "ph_method": "cacl2", "ec_ms_cm": 1.1, "ec_method": "ratio_1_5", "humus_percent": 8.0, "caco3_percent": null, "drainage": "good", "site_water_regime": "fresh",
    "conditions": [], "target_ph": 6.5, "established_on": "2024-04-01", "rotation_reset_at": null, "rotation_exempt": false, "mulch_factor": 0.8, "last_analysis_at": "2026-03-12", "notes": "Kompost oben nachgefüllt"
  },
  "notes": "Tomaten hier wegen Regenschutz durch Dachüberstand.",
  "locked": false,
  "z_order": 10,
  "photo_refs": [], "cover_photo_ref": null,
  "orientation": "south",
  "light_type": "natural",
  "frost_exposed": true,
  "created_at": "…", "updated_at": "…"
}
```

Bestandsfelder `dimensions` (3-Tupel) und die in REQ-002 vorgesehenen `bed_width_cm`, `bed_length_cm`, `bed_orientation`, `bed_type`, `bed_rows`, `row_spacing_cm` werden **nicht** eingeführt bzw. als abgeleitet markiert (§20.8).

### 20.4 GardenObject (neu, Collection `garden_objects`)

```json
{
  "_key": "go_91ab",
  "site_key": "site_7f3a",
  "parent_location_key": null,
  "object_type": "water_source",
  "label": "Regentonne Ost",
  "geometry": { "kind": "point", "origin": [9.7, 0.4] },
  "bbox": [9.45, 0.15, 9.95, 0.65],
  "props": { "water_source_kind": "rain_barrel", "capacity_liters": 300, "last_refilled_at": null },
  "locked": false, "z_order": 5,
  "notes": "",
  "created_at": "…", "updated_at": "…", "created_by": "u_sabine"
}
```

| Feld | Regel |
|------|-------|
| `object_type` | `path \| lawn \| tree \| shrub \| building \| wall \| fence \| trellis \| water_source \| compost \| storage \| other` sowie Indoor (§9.8) `window \| door \| furniture \| lamp` und die Beschriftung `text_label` (GP-UX-071, #2913: nur `rect`, `label` ist der Text — eine Zeile, 1–80 Zeichen, kein Steuer-/Bidi-Zeichen —, `props` ohne Felder; additiver Wert innerhalb von `schema_version "1"` des JSON-Exports, keine Migration) |
| `props` | typabhängiges Objekt, Pydantic-Discriminated-Union nach `object_type` (`TreeProps{species_label?, crown_radius_m, height_m?}`, `WaterSourceProps{water_source_kind, capacity_liters?, last_refilled_at?}`, `PathProps{surface ∈ {gravel, paving, bark, grass, other}}`, …) |
| `parent_location_key` | optional: Objekt liegt in einem Bereich (z. B. Weg im Gewächshaus); Containment wird geometrisch validiert |
| `off_site` | `bool = false`; `true` nimmt das Objekt von V-03 aus (Nachbargrundstück, §9.5) |
| Tenant | **kein `tenant_key`** (E-01, v1.4): wie `Location` und `Slot` gehört ein GardenObject über `site_key` seiner Site; die Zugehörigkeit prüft der Service über das Site-Anker-Prädikat (§22.3, `location_ownership`). |

Edges: `has_garden_object` (sites → garden_objects). `belongs_to_tenant` wird **nicht** um `garden_objects` erweitert (Site-Anker, E-01).

### 20.5 Slot (bestehend, additiv)

```json
{
  "_key": "slot_b03_r2p05",
  "slot_id": "BEET03_R2P05",
  "location_key": "loc_b03",
  "slot_role": "position",
  "geometry": { "kind": "point", "origin": [0.30, 0.90] },
  "capacity_plants": 1,
  "currently_occupied": true,
  "row_index": 2, "sequence": 11,
  "geometry_source": "layout", "container_volume_l": null, "sown_at": null, "archived_at": null,
  "planned_spacing_cm": 30,
  "created_at": "…", "updated_at": "…"
}
```

`capacity_plants`: bei `position` 1–20 (Bestand), bei `row` und `zone` die Pflanzenzahl, die das Layout fasst (bis 100 000, nicht auf 20 begrenzt; v1.5 Nachtrag WP 3.2).

`position` (Rasterzelle) **entfällt** (O-01, §9.2a): Migration M1 leitet daraus `geometry` ab und füllt `row_index`/`sequence`; danach wird das Feld aus Modell, Schema und Frontend entfernt (`geometry_source ∈ {editor, layout, migrated_grid, season_copy}`; `season_copy` markiert einen Slot, den „Neue Saison aus Vorjahr“ (GP-FR-171) aus einem archivierten Slot des Vorjahres neu angelegt hat, dokumentiert die Herkunft). `pitch_m` (neu an Location, Standard 0,30) ist nur die Migrations-Annahme für Alt-Slots. `slot_role ∈ {position, row, zone}`; Standard `position`. Neu außerdem `container_volume_l` (Topfvolumen, W-016), `sown_at` (Direktsaat-Zustand, §11.3), `archived_at` (Slot eines abgeschlossenen Runs, GP-FR-055). Für `row`: `geometry.kind = polyline`; für `zone`: `polygon`.

### 20.6 PlantingRun / Entry (bestehend, additiv) und geplante Belegung

```json
{
  "_key": "run_2026_tom_b03",
  "name": "Tomaten Hochbeet 3 · 2026",
  "run_type": "monoculture",
  "status": "planned", "plan_role": "main_crop", "rotation_override_reason": null,
  "reserved_area_m2": null, "planned_from": null, "planned_until": null,
  "location_key": "loc_b03",
  "planned_quantity": 6,
  "planned_start_date": "2026-05-15",
  "source": "plan_editor",
  "entries": [
    {
      "_key": "entry_1", "species_key": "sp_solanum_lycopersicum", "cultivar_key": "cv_harzfeuer",
      "quantity": 6, "id_prefix": "TOM",
      "spacing_cm": 60, "row_spacing_cm": 80, "row_direction": "along_length", "edge_margin_along_cm": 30, "edge_margin_across_cm": 40, "depth_cm": 10, "depth_kind": "planting",
      "layout_strategy": "rows", "placement_hint": "interior",
      "row_assignment": null
    }
  ]
}
```

`row_assignment` (GP-FR-070, REQ-013 §2) ist `null` bei Monokultur; bei Mischkultur in alternierenden Reihen trägt jeder Entry seine Reihenindizes, z. B. Entry 1 `"row_assignment": [0, 2, 4]` (Tomate) und Entry 2 `"row_assignment": [1, 3]` (Basilikum) — disjunkt je Run. Die Indizes sind 0-basiert: in einem Beet mit 5 Reihen heißen sie `0` bis `4`.

Neu am Run (REQ-054 O-04): `reserved_area_m2`, `planned_from`, `planned_until` — eine **flächige** Reservierung eines Beets, bevor Slots berechnet sind (vom Anbauplaner gesetzt, im Bepflanzen-Dialog durch Slots ersetzt); V-08 und die Kapazitätsprüfung behandeln sie wie belegte Slots derselben Fläche.

Edge `run_planned_at` (planting_runs → slots): `{ "entry_key": "entry_1", "planned_species_key": "sp_…", "sequence": 3, "planned_from": "2026-05-15", "planned_until": "2026-10-15", "planned_at": "…" }`.

### 20.7 PlantInstance (bestehend, unverändert) — Beispiel

```json
{
  "_key": "pi_tom_003",
  "instance_id": "TOM-003",
  "species_key": "sp_solanum_lycopersicum",
  "site_key": "site_7f3a", "location_key": "loc_b03", "slot_key": "slot_b03_r2p05",
  "planted_on": "2026-05-16", "removed_on": null,
  "current_phase_key": "phase_vegetative",
  "photo_refs": ["att_…"]
}
```

Die Position der Pflanze ist `Slot.geometry` ihres `slot_key` — kein zusätzliches Feld (D-03).

### 20.8 Auflösung der REQ-002-Felder

| REQ-002-Feld | REQ-053-Entsprechung | Umgang |
|--------------|----------------------|--------|
| `bed_width_cm`, `bed_length_cm` | `geometry.width_m/length_m` | nicht einführen |
| `bed_orientation` | abgeleitet aus `rotation_deg` + `north_angle_deg` | nicht einführen; GP-FR-017 |
| `bed_type` | `location_type_key` mit `LocationType.is_bed` | nicht einführen |
| `bed_rows`, `row_spacing_cm` | `PlantingRunEntry.layout_strategy = rows`, `row_spacing_cm`; Slots `slot_role = row` | nicht einführen (Reihen hängen an der Pflanzung, nicht am Beet) |
| `dimensions: (l, b, h)` (im Code) | `geometry` + `height_m` | **Entfernt in Welle 1** (O-02): Migration M1 übernimmt `(l, b)` als `rect`-Geometrie mit `origin = (0,0)` für Locations ohne Geometrie und `h` als `height_m`; Leser im Code werden auf `geometry`/`height_m` umgestellt (Issue 56). |
| `Slot.dimensions_cm` (REQ-002) | `Slot.geometry` | nicht einführen |
| `Slot.position: (row, col)` (im Code) | `Slot.geometry` + `row_index`/`sequence` | **Entfernt in Welle 1** (O-01, §9.2a) |

### 20.9 Task (bestehend, additiv)

Neue Felder: `suggested: bool = false`, `suggestion_reason: str | null`. Neue `TaskCategory`-Werte: §12.1. `Task.entity_type` bleibt ein freier String (`task.py:156`, gemessen 2026-10-15 — **kein** neues Enum, Enum-Retirement-Falle); der Service, der `has_task` schreibt, prüft gegen die Allowlist `{plant_instance, planting_run, location, garden_object}` (identisch mit REQ-006 v3.5 „Entitätsbindung"; Wert außerhalb → 422) und dokumentiert `location` und `garden_object` im Schema als zulässige Werte (die Edge erlaubt `locations` bereits).

```json
{
  "_key": "task_mulch_b03",
  "name": "Hochbeet 3 mulchen",
  "category": "mulching",
  "entity_type": "location", "entity_key": "loc_b03",
  "status": "pending", "priority": "medium",
  "due_date": "2026-06-01",
  "recurrence_rule": "FREQ=YEARLY;BYMONTH=6;BYMONTHDAY=1",
  "origin": "user", "suggested": false,
  "checklist": [], "photo_refs": []
}
```

### 20.10 CareEvent (neu, Collection `care_events`)

```json
{
  "_key": "ce_8d2e",
  "tenant_key": "t_garten_sabine",
  "site_key": "site_7f3a",
  "location_key": "loc_b03",
  "plant_keys": ["pi_tom_003", "pi_tom_004"],
  "category": "feeding",
  "summary": "Tomaten mit Brennnesseljauche gedüngt",
  "performed_at": "2026-06-14T18:30:00Z",
  "performed_by_user_key": "u_sabine",
  "performed_for_user_key": null, "performed_by_label": null,
  "trigger": "task",
  "task_key": "task_feed_b03_w24",
  "reason": "Blattaufhellung, 2 Wochen seit letzter Gabe",
  "product_ref": { "kind": "fertilizer", "key": "fert_nettle_tea" },
  "product_label": null,
  "quantity": 2.0, "unit": "l_per_m2", "quantity_total": 4.0, "quantity_total_unit": "l",
  "material": null,
  "measurements": null,
  "observed_outcome": null, "outcome_rating": "unknown",
  "photo_refs": ["att_…"],
  "source_ref": { "collection": "feeding_events", "key": "fe_…" },
  "supersedes_key": null, "superseded_by_key": null,
  "voided_at": null, "voided_by": null, "void_reason": null,
  "redacted_at": null, "redacted_by": null, "redaction_reason": null,
  "created_at": "2026-06-14T18:31:02Z", "created_by": "u_sabine"
}
```

| Feld | Regel |
|------|-------|
| `category` | Vereinigung aus `TaskCategory` (§12.1) + protokollspezifische Werte `note`, `observation`, `soil_analysis`, `bed_status_change`, `position_corrected`, `planting`, `removal`, `clearing` |
| `trigger` | `task \| reminder \| suggestion \| manual \| observation \| backfill \| system`; der Client darf nur `manual`/`observation` setzen, alle anderen setzt der Server (SR-009) |
| `rotation_entry` | nur bei `category = planting`, `trigger = backfill` (GP-API-042, WP 3.4): `{year, season ∈ {spring, main, autumn}?, family_key?, species_key?, plan_role ∈ {main_crop, green_manure, fallow}}` — vom Server gesetzt, kein Client-Feld (SR-009); `family_key` fehlt nur bei `plan_role = fallow`; bleibt bei der Anonymisierung nach NFR-011 erhalten (Fruchtfolge-Rückblick) |
| `source_ref` | optionaler Zeiger auf `watering_events`, `feeding_events`, `treatment_applications`, `harvest_batches`, `care_confirmations` |
| `measurements` | nur bei `soil_analysis`/`ec_check`: Liste `{parameter ∈ {ph, ec, n_min, p, k, mg, humus, caco3, moisture}, value, unit, extraction_method?, sample_depth_cm?, source}` (§15.1) |
| Unveränderlich nach Anlage | alles außer `superseded_by_key`, `voided_at`, `voided_by`, `void_reason` und der Redaktion (GP-FR-109) |

Edges: `care_event_at` (care_events → locations), `care_event_for` — **bestehende** Edge (care_confirmations → plant_instances) wird um `care_events` als Quelle erweitert, `task_logged_as` (tasks → care_events). Indizes: `(tenant_key, location_key, performed_at desc)`, `(tenant_key, performed_at desc)`, `(task_key)`, `(source_ref.collection, source_ref.key)` unique-sparse.

### 20.11 IrrigationZone (neu, Collection `irrigation_zones`)

```json
{
  "_key": "zone_sued",
  "tenant_key": "t_garten_sabine", "site_key": "site_7f3a",
  "name": "Südzone (Tropfschlauch)",
  "irrigation_type": "drip",
  "water_source_key": "go_91ab",
  "actuator_key": null,
  "flow_rate_l_per_min": null, "flow_rate_source": "manual", "application_efficiency": 0.9, "flow_rate_ha_entity_id": null,
  "color": "#2E7D32",
  "schedule_hint": "morgens, 20 min",
  "created_at": "…", "updated_at": "…"
}
```

Edges: `has_irrigation_zone` (sites → irrigation_zones), `zone_covers` (irrigation_zones → locations), `zone_supplied_by` (irrigation_zones → garden_objects), `zone_actuated_by` (irrigation_zones → actuators).

### 20.12 BedTemplate (neu, SHOULD, Collection `bed_templates`)

`{ name, tenant_key | null (global), location_type_key, default_geometry, height_m?, default_layout {row_spacing_cm?, spacing_cm?}, soil_profile_defaults?, recurring_task_templates[] (→ task_templates) }`.

**Löschen einer Vorlage (#2528):** `DELETE /bed-templates/{key}` entfernt in derselben Stream-Transaktion `template_key` an allen daraus platzierten Beeten — eigene Vorlage: nur Beete der Standorte des Mandanten (Prädikat am Standort-Anker, da `locations` kein `tenant_key` trägt); Systemvorlage (nur Plattform-Admin): Beete aller Mandanten. `template_key` ist Herkunft, kein Fremdschlüssel: Ein Beet bleibt ohne Vorlage voll nutzbar. Beim Mandanten-Import gilt der Verweis als Herkunftsverweis (REQ-056 §8.4 Schritt 1, `nulled_references`). Altbestand mit verwaistem `template_key` bereinigt Migration v0102 (Schritt `locations_with_dangling_template_key`).

### 20.13 Zeitstempel, IDs, Historisierung

| Aspekt | Regel |
|--------|-------|
| IDs | ArangoDB `_key`, serverseitig vergeben; Client sendet `temp_key` für neu erzeugte Objekte im Batch und erhält die Zuordnung zurück |
| Zeitstempel | `created_at`, `updated_at` UTC ISO-8601 (Bestand); `performed_at` in `care_events` ebenfalls UTC, UI zeigt Site-Zeitzone |
| Plan-Historie | `Site.plan.plan_revision` monoton (nur Struktur, GP-NFR-007); **keine** Geometrie-Versionstabelle im MVP (O-03). **Pflicht-Audit (SR-011):** jede löschende oder strukturverändernde Operation (Batch-`delete`, `DELETE`-Endpunkte, `bed_status = retired`, Import `replace`, Redaktion) schreibt atomar in derselben Transaktion `garden_plan_audit {site_key, revision, user_key, op, entity, key, at, summary}` (Collection, **MUST**); vor Import `replace` wird ein Snapshot geschrieben (GP-FR-148 für diesen Pfad MUST) |
| Pflege-Historie | append-only mit Supersede/Void (§13.3) |
| Standort löschen (#2513) | `DELETE /sites/{key}` ist **eine** Stream-Transaktion: Beete (über `contains` bis zum Fixpunkt, vereinigt mit `site_key`), Slots, Gartenobjekte, Bewässerungszonen und die `site_key`-Zeilen aus `season_states`, `weather_forecasts`, `climate_normals`, `weather_source_configs`, `irrigation_demands` werden entfernt; jede Kante, die die Graph-Definitionen für diese Knoten ableiten (`edges_touching`), wird geschnitten. **Historie bleibt:** `care_events` und bestehende `garden_plan_audit`-Zeilen (GP-FR-101, Retention NFR-011 R-25/R-26, Mandanten-Löschung). In derselben Transaktion entsteht die Pflicht-Audit-Zeile `{op: delete, entity: site, key, user_key}` (SR-011). Zeilen mit fremdem `tenant_key` bleiben unberührt. Steht eine Pflanze mit `removed_on = null` auf dem Standort, einem seiner Beete oder Slots, wird mit 409 `site.has_active_plants` verweigert und nichts gelöscht (V-24). |
| Tenant | **Revidiert (E-01, v1.4; hebt SR-022 auf):** `locations`, `slots` und `garden_objects` tragen **kein** `tenant_key` — Migration v0087 (#2107, MT-010) hat das Feld bewusst entfernt, weil `""` als Global-Marker auf einer Mandantenzeile das Leck #706/#1397 war; die Site ist der einzige Eigentümer in der Kette und `domain/services/location_ownership.py` (`require_owned_site`, `resolve_owned_location`, `resolve_owned_slot`) ist das Prädikat. `care_events`, `irrigation_zones`, `bed_templates` und `garden_plan_audit` tragen `tenant_key`, weil sie mandantenweit gelistet werden (GP-FR-107) bzw. tenant-scoped Stammdaten sind. |

### 20.14 Graph-Änderungen (Zusammenfassung für M1)

Neue Collections: `garden_objects`, `care_events`, `irrigation_zones`, `bed_templates` (SHOULD), `garden_plan_audit` (MUST).
Neue Edge-Definitionen: `has_garden_object`, `run_planned_at`, `care_event_at`, `task_logged_as`, `has_irrigation_zone`, `zone_covers`, `zone_supplied_by`, `zone_actuated_by`.
Erweiterte Edge-Definitionen: `belongs_to_tenant` (+ `care_events`, `irrigation_zones`, `bed_templates` — **nicht** `garden_objects`, E-01), `care_event_for` (+ `care_events` als from), `has_task` (+ `garden_objects` als from).
Neue Indizes: `locations(site_key, bed_status)`, `garden_objects(site_key, object_type)`, `slots(location_key, slot_role)`, `care_events` (§20.10). Keine `tenant_key`-Indizes auf `locations`/`slots` (E-01).

---

## 21. API

Alle Pfade unter `/api/v1/t/{tenant_slug}`. Schemas in `api/v1/garden_plan/schemas.py` (v1). Fehler nach NFR-006 (`{code, message, details}`), Codes in §22.

### 21.1 Plan (Site-Ebene)

| ID | Methode & Pfad | Zweck | Rolle |
|----|----------------|-------|-------|
| GP-API-001 | `GET /sites/{key}/plan` | Vollständiger Plan (§20.2–20.5 + Pflanzen-Kurzinfo `{key, instance_id, species_key, phase_key, slot_key}` + Task-Zähler je Location + Zonen). Query: `include=plants,tasks,zones` (Standard alle), `as_of=YYYY-MM-DD` (SHOULD: historischer Stand der Pflanzen) | Alle Rollen |
| GP-API-002 | `PUT /sites/{key}/plan/boundary` | Gartengrenze + `north_angle_deg`, `default_grid_m`; legt `plan` an, wenn fehlend | Ab Gärtner |
| GP-API-003 | `POST /sites/{key}/plan/batch` | Transaktionale Operationsliste (§21.3). **Abschließende Op-Liste** `create_location`, `create_garden_object`, `update_geometry`, `update_fields`, `delete`, `set_boundary`, `set_locked`, `set_z_order`; **jede Operation wird einzeln gegen §21.8 geprüft, vor der Domain-Validierung** (SR-001): `delete` auf `location`/`garden_object` verlangt Leitung; enthält ein Batch eine Operation über der Rolle des Aufrufers, wird er komplett mit 403 `batch.operation_forbidden {op_index}` abgewiesen. Slot-Operationen laufen **nicht** über den Plan-Batch (GP-API-014/015, außerhalb der Revision). | Ab Gärtner (Lesen der Antwort: Alle) |
| GP-API-004 | `GET /sites/{key}/plan/export` | JSON-Sicherung (`schema_version`, alle Plan-Objekte, ohne Pflanzen/Tasks/Events). Teil-Export (GP-FR-172): `scope = site\|selection\|subtree` (Standard `site`), `keys` (kommagetrennt, höchstens 100, ein Gartenobjekt als `object:<key>`, bei `site` nicht erlaubt); eine Teil-Datei hat keine Plan-Einstellungen und nur die Zonen ihrer Beete | Alle Rollen (`Action.EXPORT`) |
| GP-API-005 | `POST /sites/{key}/plan/import` | Wiederherstellung; Modus `replace` (schreibt Snapshot, löscht vorhandene Geometrien nur für Beete **ohne** aktive Pflanzen — `force` hebt die Leer-Bedingung auf, V-09 gilt immer) oder `merge` (fügt hinzu, Keys werden immer neu vergeben). `dry_run=true` liefert `{would_create, would_update, would_delete, dropped_references[], errors}`. Beide Modi: **Nur Leitung** (SR-010). Zielwahl (GP-FR-172): `target = same_site\|other_site\|other_tenant` (bei `other_site`/`other_tenant` werden Verweise aus der Datei nie gegen die Ziel-Site aufgelöst, sondern `null` und in `dropped_references[]` berichtet; kein serverseitiges Lesen über Mandantengrenzen), `offset_m` (nur `merge`, je Achse ±1 000 m). Ein wiederholter `merge` legt die Zonen der Datei erneut an; je Site höchstens 500 Zonen (`irrigation_zone.quota_exceeded`). | Nur Leitung |
| GP-API-006 | `GET /sites/{key}/plan/render.svg` | Serverseitiges SVG (für PDF und Download), Query `scale`, `layers`, `locale` | Alle Rollen |
| GP-API-007 | `GET /print/garden-plan/{site_key}` | PDF (REQ-032-Muster), Query `paper=a4\|a3`, `orientation`, `scale=auto\|1:20\|1:25\|1:50\|1:75\|1:100\|1:125\|1:150\|1:200\|1:250\|1:300\|1:400\|1:500` (12 Stufen aus GP-FR-142), `layers`, `locale`, `bed_list` (zweite Seite mit der Beetliste), `underlay` (Unterlage als `data:`-URI nur mit `underlay=true`, GP-FR-033; im Export-Dialog das Opt-in „Unterlage mitdrucken“, nur bei vorhandener Unterlage, #2895), `parcel_list` (**v1.13, Welle 9, WP 9.10 #2750, gemountet seit #2803:** Zusatzseite Parzellenliste, GP-FR-176, nur mit `parcel_list=true` — Beet-Kennung, Fläche, Zone; die Kennung ist der Beetname plus eine laufende Nummer in Plan-Reihenfolge, ein Feld `bed_number` gibt es nicht, §32.6 Pkt. 8; die Zuweisung erscheint **nur** mit `include_assignment=true`, Opt-in wie SR-024/GP-API-068, ohne Opt-in keine Personenspalte; Option im Export-Dialog) | Alle Rollen |
| GP-API-008 | `GET /sites/{key}/plan/audit` | Plan-Änderungsprotokoll (SHOULD) | Alle Rollen |
| GP-API-057 | `POST /sites/{key}/plan/new-season` | „Neue Saison aus Vorjahr“ (GP-FR-171, §32.4 Pkt. 7). Body `{year, dry_run = true, expected_revision?}`; `year` ganzzahlig 2001–2100 und höchstens das nächste Jahr (sonst 422 `season.invalid_year`). Je Beet ohne aktive Pflanze werden die Slot-Plätze der im Jahr `year − 1` beendeten Runs als unbelegte Slots angelegt (`geometry_source = season_copy`); ein Beet mit aktiver Pflanze, ein stillgelegtes und eines, das über 2 000 Slots käme, wird übersprungen und berichtet. Zonen, Pflanzen, Runs und Historie bleiben unverändert. Eine Transaktion mit Revisionsprüfung (409 `plan.revision_conflict`) und Audit-Zeile; Budget wie GP-API-005 (je Mandant). Antwort `{year, source_year, dry_run, applied, plan_revision, beds_copied, beds_skipped, slots_to_create, beds[{location_key, status ∈ {copied, skipped_active_plants, skipped_retired, skipped_slot_quota, nothing_to_copy}, slots, slots_outside_bed}]}` | Nur Leitung |
| GP-API-058 | `GET /sites/{key}/plan/snapshots` | Stände, die ein `replace`-Import oder eine Wiederherstellung überschrieben hat (GP-FR-148/170, §32.4 Pkt. 15): neueste zuerst, seitenweise (`offset`/`limit`); je Eintrag `{audit_key, revision, at, summary, changed_by_name, locations, garden_objects, slots, zones}`, nie der Plan selbst. Je Site die 20 neuesten (GP-NFR-055), Aufbewahrung R-26 | Nur Leitung |
| GP-API-059 | `POST /sites/{key}/plan/snapshots/{audit_key}/restore` | Body `{dry_run = false, force = false, confirm_site_name?}` → Bericht wie GP-API-005. Ein `replace` mit dem gespeicherten Plan; der überschriebene Stand wird vorher selbst als Snapshot geschrieben, eine Wiederherstellung ist also umkehrbar. Zonen der Site, die der Snapshot nicht nennt, entfallen; technische Zonen-Kopplungen werden nicht wiederhergestellt. 404 für einen Snapshot einer anderen Site oder eines anderen Mandanten, 409 `import.not_empty` (aktive Pflanzen; `force` hebt das auf), 422 `import.site_name_mismatch` ohne Site-Namen | Nur Leitung |
| GP-API-060 | `PUT\|DELETE /sites/{key}/plan/underlay` | Hintergrund-Unterlage (GP-FR-033, §32.4 Pkt. 6). `PUT {attachment_key, calibration {p1_px, p2_px, distance_m}, origin, rotation_deg, opacity}`: eine je Site, ein Attachment der Kategorie `garden_plan_underlay` des eigenen Mandanten (sonst 422 `reference.not_found`), 422 `plan.required` ohne Plan; nicht Teil der Plan-Revision, nie im JSON-Export, im PDF nur mit `underlay=true` (GP-API-007). `DELETE` entfernt Unterlage und Attachment, sofern kein anderer Datensatz es hält; idempotent (204) | Ab Gärtner |
| GP-API-063 | `GET /sites/{key}/rotation-matrix?years=&offset=&limit=` | **Rotationsmatrix** (GP-FR-135, WP 8.12, v1.11): Beete × Jahre der Site. `years` 1–10, Standard `max(rotation_pause_years der beteiligten Familien, 5)` aus den Beeten der Seite (beim Blättern das `years` der ersten Antwort mitsenden); Beete nach Name, höchstens 500, seitenweise (`offset`/`limit`, `limit` ≤ 200); `total` zählt die gelesenen Beete nach dieser Grenze (Basis zum Blättern), `truncated = true` heißt, die Site hat mehr als 500 Beete und der Rest fehlt. Je Beet `rotation_applicable` + `not_applicable_reason` (`rotation_exempt` oder ausgeschaltet, GP-FR-137), `rotation_reset_at`, je Spalte eine **Liste** von Einträgen (Familie, `nutrient_demand`, `plan_role`, Saison) — dieselbe Zusammenführung wie GP-API-039 für dasselbe Beet und Jahr; Historie vor `rotation_reset_at` entfällt. **Keine Zukunftsspalten** (kein Speicher für `CropRotationPlan`, §32.5 Nachtrag A). Rate-Limit `rate_limit_plan_export` je Konto. Fremde Site 404 | Alle Rollen |
| GP-API-069 | `POST /sites/{key}/beds/import-csv?dry_run=true&expected_revision=` | **CSV-Beetlisten-Import** (GP-FR-174, WP 8.26, v1.11). Body ist die Datei (`text/csv`, `text/plain` oder `application/vnd.ms-excel`, sonst 415): UTF-8 (BOM toleriert), Trenner `;`, Kopfzeile `Name;Typ;Breite_m;Länge_m`, optional `Sonne`, `Bodenart`, `Zone`; ≤ 1 MiB (413) und ≤ 500 Zeilen (422 `plan.quota_exceeded`, auch wenn die Site über 500 Beete und Objekte käme). Dezimalkomma oder -punkt; `Typ` als Schlüssel oder deutscher/englischer Name, `Zone` als Name einer Zone der Site. Ein führendes Formelzeichen (`= + - @`, Tab, CR) einer Textzelle wird verworfen und als Warnung `csv.formula_stripped` gemeldet (SR-016). Datei-Fehler 422 (`csv.invalid_encoding`, `csv.invalid_delimiter`, `csv.empty`, `csv.malformed`, `csv.too_many_columns`, `csv.missing_column`, `csv.duplicate_column`), alles andere sind Zeilenfehler (Zeile wird übersprungen, z. B. `csv.does_not_fit`). Antwort `{dry_run, rows_total, rows[], rows_valid, rows_skipped, errors[], errors_total, warnings[], warnings_total, ignored_columns[], ignored_columns_total, applied, plan_revision}`; `dry_run=false` mit `expected_revision` des Probelaufs schreibt die gültigen Zeilen in einer Transaktion über den Batch-Pfad (Containment, Überlappung, Quote, Revision, Audit; geänderter Plan → 409). Platzierung als `rect` in Reihen ab der linken oberen Ecke der Grenze, 0,5 m Abstand, Umbruch an der Grenzbreite (§32.5 Pkt. 6). Rate-Limit `rate_limit_plan_csv_import` (10/min je Konto) und `rate_limit_plan_csv_import_tenant` (30/min je Mandant); der Body wird erst nach Gate, Limits und Site-Prüfung gelesen | Nur Leitung |

### 21.2 Locations / GardenObjects / Slots (Einzelressourcen)

| ID | Methode & Pfad | Zweck | Rolle |
|----|----------------|-------|-------|
| GP-API-010 | `PATCH /locations/{key}` (bestehendes `PUT` bleibt) | Teilupdate inkl. `geometry`, `soil_profile`, `bed_status`, `sun_exposure`, `irrigation_zone_key`, `notes`, `locked`, `z_order`; Geometrie-Update außerhalb des Batch erhöht ebenfalls `plan_revision` | Ab Gärtner |
| GP-API-011 | `GET /locations?site_key=&is_bed=true&bed_status=` | Beetliste mit Zählern (`active_plant_count`, `open_task_count`, `next_due_at`) und `nearest_water_source_m` (GP-FR-167, v1.14: Meter von der Beetkante zur nächsten Wasserquelle, `null` ohne Geometrie oder Quelle) | Alle Rollen |
| GP-API-012 | `GET /locations/{key}/summary` | Kopfdaten der Beetansicht (GP-FR-047); für ein Beet zusätzlich `nearest_water_source_m` (GP-FR-167, v1.14), sonst `null` | Alle Rollen |
| GP-API-013 | `GET\|POST /sites/{key}/garden-objects`, `GET\|PATCH\|DELETE /garden-objects/{key}` | Einzel-CRUD (Batch ist der Hauptweg) | Alle / Ab Gärtner / Nur Leitung (Löschen) |
| GP-API-014 | `PATCH /slots/{key}` | `geometry`, `slot_role`, `capacity_plants`; löst `adjacency_recompute` aus | Ab Gärtner |
| GP-API-056 | `PUT\|DELETE /slots/{key}/adjacent/{other_key}` | Manuelle Nachbarschaft zweier Slots derselben Site (GP-FR-130, SR-021; bestätigt in #2425 Punkt 4): `PUT` mit optionalem Body `{distance_cm?}` (0–100 000) schreibt `adjacent_to` mit `source = manual` in beide Richtungen, die Geometrie-Ableitung entfernt sie nie; `PUT` ersetzt dabei alle Kanten des Paares, auch eine abgeleitete. `DELETE` entfernt nur die manuelle Kante; eine geometrisch begründete Nachbarschaft entsteht erst bei der nächsten Neuberechnung des Beets (nächste Slot-Änderung) wieder. Antwort 204; Slot eines fremden Mandanten 404, Slot einer anderen Site 422 `adjacency.different_site`, derselbe Slot 422 `adjacency.same_slot` (vor der Mandantenauflösung geprüft: ein fremder Slot gegen sich selbst ergibt 422, nicht 404), archivierter Slot 422 `adjacency.slot_archived`; `distance_cm` außerhalb 0–100 000 ergibt den allgemeinen Pydantic-422 `VALIDATION_ERROR` (der Service-Code `adjacency.distance_out_of_range` ist über die Route nicht erreichbar) | Ab Gärtner |
| GP-API-015 | `POST /locations/{key}/slots/batch` | Slots eines Beets ersetzen/ergänzen (`mode = replace_unoccupied \| append`), transaktional | Ab Gärtner |
| GP-API-016 | `POST /locations/{key}/planting-layout/preview` | `{entry: {spacing_cm, row_spacing_cm, edge_margin_along_cm, edge_margin_across_cm, layout_strategy, max_count?}}` → `{slots: [SlotGeometry], count, capacity_max}` ohne Persistenz; Obergrenze 2 000 Positionen (GP-FR-062) | Alle Rollen |
| GP-API-017 | `POST /locations/{key}/quick-planting` | Feldmodus-Kurzpfad: Run anlegen + Slots + Pflanzen in einer Transaktion (GP-UX-027); `quantity` ≤ 500; läuft außerhalb der Plan-Revision | Ab Gärtner |
| GP-API-018 | `POST /locations/{key}/status` | `bed_status`-Wechsel mit `reason` (schreibt `care_event`) | Ab Gärtner |
| GP-API-019 | `POST /locations/{key}/clear` | Beet räumen (GP-FR-055): `{termination_type, reason?, harvested_batch?}` → beendet aktive Runs/Pflanzen, archiviert Slots, schreibt `care_event(clearing)` | Ab Gärtner |
| GP-API-067 | `GET\|POST /locations/{key}/photos`, `PUT /locations/{key}/photos/cover`, `DELETE /locations/{key}/photos/{attachment_id}` | **Beet-Fotos** (GP-FR-051, WP 8.18, v1.11). Hochladen vorher über `POST /attachments` mit `category=location` (EXIF/GPS wird dort entfernt). `GET`: Fotos neuester zuerst, Titelbild markiert, `can_remove` je Aufrufer, höchstens `max_photos` (50). `POST {attachment_id}`: verknüpft ein eigenes Beet-Foto des Mandanten (sonst 422 `reference.not_found`; 50 Fotos → 422 `location.photo_limit_reached`), das erste wird Titelbild. `PUT …/cover {attachment_id \| null}`: Titelbild wählen oder leeren (kein Foto des Beets → 422 `location.cover_not_a_photo`). `DELETE`: eigenes Foto ab Gärtner, fremdes nur Leitung; war es das Titelbild, wird das neueste verbleibende Titelbild; das Attachment wird gelöscht, sofern kein anderer Halter (Beet, Galerie, Aufgabe, Pflegeereignis) es nennt. Plan-JSON (GP-API-004) trägt keine Fotos | Alle Rollen (Lesen) / Ab Gärtner |
| GP-API-068 | `GET /locations?site_key=&format=csv&columns=&include_assignment=false&delimiter=comma\|semicolon&locale=de\|en&bed_status=&parent_location_key=` | **Beetliste als CSV** (GP-FR-145/175, WP 8.25, v1.11) — CSV-Form von GP-API-011: nur Beete (`is_bed=false` → 422 `export.beds_only`), nach Name, UTF-8 mit BOM, RFC 4180, Formel-Zellen mit `'` (SR-016). Standardspalten `name,type,area_m2,status,soil_texture,irrigation_zone,active_plants`; wählbar zusätzlich `sun_exposure`, `sun_window`, `direct_sun_hours_summer`, `foliage_shade_in_summer`, `frost_risk`, `cold_air_pocket`, `heat_retention`, `wind_exposure`, `slope_deg`, `aspect_deg`, `access_sides`, `site_flags`, `nearest_water_source_m` (GP-FR-167, v1.14); unbekannte Spalte 422 `export.unknown_column`, leere Auswahl `export.no_columns`. `assigned_to` (Anzeigenamen) nur mit `include_assignment=true` (SR-024, ohne eigene Rollenprüfung, §32.5 Pkt. 13). `delimiter=semicolon` = Excel-Variante mit Dezimalkomma. Kopfzeile und Enum-Zellen sind Maschinenwerte, Typ- und Zonennamen je `locale`. Mehr als 2 000 Beete → 422 `export.too_many_rows` (nie eine gekürzte Datei). Rate-Limit der Plan-Exporte je Konto und je Mandant (die JSON-Liste zählt nicht) | Alle Rollen |

### 21.3 Batch-Vertrag (GP-API-003)

Request:
```json
{
  "expected_revision": 42,
  "operations": [
    { "op": "create_location", "temp_key": "tmp1", "data": { "name": "Beet 6", "location_type_key": "bed", "parent_location_key": "loc_nutzgarten", "geometry": { "kind": "rect", "origin": [4,1], "width_m": 2, "length_m": 1, "rotation_deg": 0 } } },
    { "op": "update_geometry", "entity": "location", "key": "loc_b03", "geometry": { "kind": "rect", "origin": [1,1.5], "width_m": 2, "length_m": 1, "rotation_deg": 90 } },
    { "op": "create_garden_object", "temp_key": "tmp2", "data": { "object_type": "path", "geometry": { "kind": "polyline", "points": [[0,3],[10,3]], "width_m": 0.6 } } },
    { "op": "delete", "entity": "garden_object", "key": "go_old" }
  ]
}
```
Response 200:
```json
{ "plan_revision": 43, "key_map": { "tmp1": "loc_a91c", "tmp2": "go_77f0" }, "updated": ["loc_b03"], "deleted": ["go_old"], "derived": { "loc_b03": { "area_m2": 2.0, "bbox": [0.0,1.5,1.0,3.5] }, "loc_a91c": { "area_m2": 2.0, "bbox": [4,1,6,2] } } }
```
Fehler: 409 `plan.revision_conflict` `{current_revision, changed_by, changed_at}`; 422 `validation_error` mit `details[{op_index, field, code}]` — die gesamte Transaktion wird verworfen. Limit: 500 Operationen je Request.

### 21.4 Pflanzung

| ID | Methode & Pfad | Zweck | Rolle |
|----|----------------|-------|-------|
| GP-API-020 | `POST /planting-runs` (bestehend, erweitert) | Entries mit Layout-Feldern; bei `location_key` eines Beets mit Geometrie und `layout_strategy != free` werden Slots + `run_planned_at` erzeugt | Ab Gärtner |
| GP-API-021 | `POST /planting-runs/{key}/plan-slots` | Geplante Belegung setzen/ersetzen (`{entry_key, slot_keys[]}`), für `free`-Layouts und Korrekturen; `slot_keys` ⊆ Slots von `run.location_key` (GP-NFR-058) | Ab Gärtner |
| GP-API-022 | `DELETE /planting-runs/{key}/plan-slots/{slot_key}` | Reservierung freigeben | Ab Gärtner, solange der Run `planned` ist; sonst Nur Leitung (SR-010) |
| GP-API-023 | `POST /planting-runs/{key}/create-plants` (bestehend) | `assign_to_slots = true` nutzt `run_planned_at` in `sequence`-Reihenfolge | Ab Gärtner |
| GP-API-024 | `GET /locations/{key}/plantings?state=planned\|active\|harvested\|historical&year=` | Pflanzungen eines Beets nach Zustand (§11.3) | Alle Rollen |
| GP-API-025 | `POST /locations/{key}/validate-planting` | Beet-Variante von REQ-013/028-Validierung: Fruchtfolge + Nachbarn, nur Hinweise (MUST, GP-FR-131/132). Body `{species_key, slot_key?, rotation_window_years?, replant_of_plant_key?}` (`replant_of_plant_key`: Nachpflanzung eines ausgefallenen Slots, §11.3, #2888); Antwort 200 mit Stärkestufe und Grund je Hinweis (Nachtrag WP 3.4) | Alle Rollen |
| GP-API-065 | `GET /locations/{key}/companion-edges` | **Mischkultur-Kanten eines Beets** (GP-FR-134, WP 8.15, v1.11): je `adjacent_to`-Paar von Slots, in denen beide eine Spezies tragen (stehende Pflanze mit `removed_on = null` oder geplanter Run — dieselbe Menge wie der Pflanzdialog), Status `compatible \| incompatible \| unknown` nach derselben Regel wie GP-API-025 (inkompatibel gewinnt, sonst kompatibel mit Score, sonst unbekannt), Grund (`reason_code`, `reason`), `score`, entscheidendes Artenpaar, `distance_cm`, Slot-Anker in Plan-Koordinaten. Begrenzt: höchstens 2 000 Paare und 8 Spezies je Slot werden bewertet, höchstens 500 Kanten beantwortet (inkompatibel zuerst); `total` zählt exakt, `truncated` meldet Auslassungen. Fremdes Beet 404 | Alle Rollen |

### 21.5 Pflege und Historie

| ID | Methode & Pfad | Zweck | Rolle |
|----|----------------|-------|-------|
| GP-API-030 | `GET /tasks/queue?location_key=&include_children=true` (bestehend, Filter neu) | Aufgaben eines Beets/Bereichs | Alle Rollen |
| GP-API-031 | `POST /tasks/{key}/complete` (bestehend, Body erweitert) | `{performed_at?, notes?, photo_refs?, plant_keys?, reason?, product_ref?, product_label?, quantity?, unit?, material?, measurements?, observed_outcome?, outcome_rating?}` → schreibt `care_event` + Fachereignis atomar (§12.3); Server-Felder (`trigger`, `task_key`, `source_ref`, Ausführender, Mandant) sind im Body verboten (422, SR-009) | Ab Gärtner |
| GP-API-032 | `POST /tasks/batch/status` (bestehend, Body erweitert) | gleiche Fachfelder für n Tasks (Gießdienst); ≤ 200 Tasks, fremder Schlüssel = 404 für den ganzen Batch (§12.3) | Ab Gärtner |
| GP-API-033 | `POST /care-events` | Protokoll ohne Task (GP-FR-090); Body ohne `trigger`-Werte außer `manual`/`observation`, ohne `created_by`/`source_ref` (serverseitig, SR-009) | Ab Gärtner |
| GP-API-034 | `GET /care-events?location_key=&plant_key=&category=&from=&to=&performed_by=&include_superseded=false&format=json\|csv` | Historie (mandantenweit oder je Beet). Filter `performed_by` **rollenabhängig (E-16, SR-020, #2411):** Betrachter und Gärtner dürfen nur auf sich selbst filtern, die Leitung und Mitglieder mit dem `management`-Scope auf jedes Mitglied, sonst 403; der Löschmarker `_anonymized` ist für niemanden filterbar (422) (ein Personenfilter ist ein bis zu fünfjähriges Aktivitätsprofil — Datenminimierung, DSFA nach REQ-025); `performed_by` erscheint als Anzeigename oder „anonymisiert", nie als Nutzer-Key | Alle Rollen |
| GP-API-035 | `GET /care-events/{key}` | Einzelereignis inkl. Supersede-Kette | Alle Rollen |
| GP-API-036 | `POST /care-events/{key}/supersede` | Korrektur (neuer Eintrag, alter bleibt) | Ab Gärtner (eigene = `created_by` ist der Aufrufer), Nur Leitung (fremde); Prädikat im Service |
| GP-API-037 | `POST /care-events/{key}/void` | Storno mit Grund | Nur Leitung; **Ausnahme:** eigenes Ereignis (`created_by` = Aufrufer) innerhalb von 10 Minuten nach `created_at` mit `void_reason = undo`: Ab Gärtner (Rückgängig im Feldmodus, GP-FR-149) — Prädikat im Service |
| GP-API-038 | `GET /locations/{key}/history?from=&to=` | Kombinierte Historie (care_events + Pflanzungsereignisse), paginiert | Alle Rollen |
| GP-API-039 | `GET /locations/{key}/rotation?years=` | Zeitstrahl Familie/Spezies je Jahr (GP-FR-103); Query-Default `years = max(rotation_pause_years der beteiligten Familien, 5)`, Obergrenze 10 (größere Werte → 422 nach NFR-006) | Alle Rollen |
| GP-API-040 | `POST /tasks/{key}/accept-suggestion`, `POST /tasks/{key}/dismiss-suggestion` | Vorschläge (SHOULD) | Ab Gärtner |
| GP-API-041 | `POST /care-events/{key}/redact` | Redaktion (GP-FR-109) `{reason}`; wirkt auf die Supersede-Kette | Nur Leitung |
| GP-API-042 | `POST /locations/{key}/history/backfill` | **Vorjahre nacherfassen** (GP-FR-131, REQ-054 §5.3): `{year, season ∈ {spring, main, autumn}?, species_key?, family_key, plan_role ∈ {main_crop, green_manure, fallow}}` → `care_event(category = planting, trigger = backfill, performed_at = {year}-07-01 bzw. Saisonmitte, source = backfill)`; `year` ≤ laufendes Jahr − 1 und ≥ laufendes Jahr − 10; **ausgenommen von V-11** (der Server setzt `trigger = backfill` selbst, der Client nie — SR-009 bleibt gewahrt); `DELETE …/history/backfill/{care_event_key}` stornieren (`void_reason = backfill_error`) | Ab Gärtner |
| GP-API-064 | `GET /locations/{key}/succession-recommendation` | **Folgekultur-Empfehlung** (GP-FR-133, WP 8.14, v1.11) — nur Reihenfolge, keine Mengen: nächster Schritt nach dem letzten erfassten Jahr im Zyklus Starkzehrer → Mittelzehrer → Schwachzehrer → Gründüngung/Brache → Starkzehrer (`nutrient_demand`, `plan_role`); Kandidaten sind die `rotation_after`-Nachfolger der Familien dieses Jahres ohne die, deren Pause im Beet noch läuft (`held_back`). Eine Spezies erscheint nur mit gespeichertem `nutrient_demand` (bzw. `green_manure_suitable` für den aufbauenden Schritt), kein Standardwert. `status` erklärt eine leere Liste (`no_history`, `demand_unknown`, `no_successor_data`, `no_matching_species`, `not_applicable`); `rotation_applicable` + Grund wie GP-API-063 | Alle Rollen |
| GP-API-066 | `GET /locations/{key}/soil-analyses?parameter=&from=&to=&limit=200` | **Bodenanalysen eines Beets** (GP-FR-122, WP 8.7, v1.11): Serien der `soil_analysis`-Messwerte je Parameter (`ph`, `ec`, `n_min`, `p`, `k`, `mg`, `humus`, `caco3`, `moisture`) **und Methode** (`ec_method` für die Leitfähigkeit, `ph_method` für den pH, sonst `extraction_method`; `unknown` ist eine eigene Methode). Punkte `{performed_at, value, unit, source, sample_depth_cm, content_class, event_key}`; `method_changes` nennt einen Methodenwechsel zwischen zwei Analysen; Werte verschiedener Methoden werden nie zusammengeführt, verglichen oder umgerechnet. `liming_hint` ist der Text „Kalkung wahrscheinlich sinnvoll“ des aktuellen Profils, nie eine Menge (§32.5 Pkt. 14). `limit` 1–500 (Standard 200) Analysen, neueste zuerst, `truncated` | Alle Rollen |

### 21.6 Bewässerungszonen (SHOULD)

| ID | Methode & Pfad | Rolle |
|----|----------------|-------|
| GP-API-050 | `GET\|POST /sites/{key}/irrigation-zones`, `GET\|PATCH\|DELETE /irrigation-zones/{key}` | Alle / Ab Gärtner / Nur Leitung; Felder `actuator_key`, `flow_rate_ha_entity_id`: nur Technik (SR-014) |
| GP-API-051 | `PUT /irrigation-zones/{key}/locations` `{location_keys[]}` | Ab Gärtner |
| GP-API-052 | `GET /irrigation-zones/{key}/status` → `{last_watering, next_planned, demand_liters_today, consumption_liters_30d}` | Alle Rollen |
| GP-API-053 | `POST /irrigation-zones/{key}/log-watering` `{volume_liters (> 0, ≤ 100 000), allocation: by_area\|equal, performed_at?, summary? (≤ 500 Zeichen)}` → 201 `{event_keys, shares[{location_key, liters}], allocation, performed_at, skipped_location_keys}`: je Beet der Zone ein `care_event(watering)` in einer Transaktion, jedes mit `allocation` gekennzeichnet (`CareEventAllocation`, additiv; Standard und Wert der Altzeilen ist `measured`). `by_area` lässt Beete ohne Fläche aus und nennt sie in `skipped_location_keys`; 422 `irrigation_zone.no_beds` / `irrigation_zone.no_bed_area`, wenn nichts zu verteilen ist. `by_demand` und „Regen — übersprungen“ (GP-FR-117) sind nicht umgesetzt (§32.4 Pkt. 1/2) | Ab Gärtner |
| GP-API-055 | `POST /planting-runs/mixed-culture` `{location_key, runs[{name, entry, free_points?, container_volume_l?}], planned_start_date?, planned_from?, planned_until?, plan_role?, rotation_override_reason?, source?}` → `{runs[]}` (201) | Legt die je Art getrennten Läufe einer Mischkultur (REQ-013 §2) samt Layout-Slots, Reservierungen und frei gesetzten Punkten **in einer Transaktion** an (alles oder nichts; kein clientseitiges Zurücknehmen). Das Layout wird für alle Einträge gemeinsam berechnet. Fremdes Beet → 404, fremde Art → 422 `reference.not_found`; Rolle: Ab Gärtner. `DELETE /planting-runs/{key}` bleibt Nur Leitung (#2463). |

### 21.7 Vorlagen (SHOULD)

| ID | Methode & Pfad | Rolle |
|----|----------------|-------|
| GP-API-061 | `GET /bed-templates` (System-Vorlagen ∪ eigene, nach Name, seitenweise), `POST /bed-templates`, `PATCH\|DELETE /bed-templates/{key}`; je Mandant höchstens 200 eigene Vorlagen (422 `bed_template.quota_exceeded`); Löschen gibt die daraus platzierten Beete frei (§20.12, #2528) | Alle / Ab Gärtner / Nur Leitung; System-Vorlagen ändern und löschen nur Plattform-Admins |
| GP-API-062 | `POST /sites/{key}/plan/place-template` `{template_key, origin, rotation_deg = 0 (0 ≤ r < 360, zur Drehung der Vorlage addiert), expected_revision}` → `PlanBatchResponse` über denselben Pfad wie `create_location` (eine Transaktion, eine Revision, Audit); `key_map.template_bed` nennt das neue Beet, das `template_key` als Herkunft trägt. Reihenfolge der Prüfungen: Vorlage (422 `reference.not_found`, eine fremde wie eine fehlende), Geometrie (422 `geometry.invalid`), Containment/Überlappung (422 `geometry.outside_parent`, `bed.overlap`), Revision (409 `plan.revision_conflict`). Opt-in `create_recurring_tasks = false`: mit `true` legt es je `recurring_task_templates`-Schlüssel eine jährlich wiederkehrende Aufgabe am neuen Beet an (GP-FR-087, #2897; vor der Geometrie geprüft: 422 `reference.not_found` auf `recurring_task_templates[i]` für eine fremde oder fehlende Aufgabenvorlage); die Antwort trägt zusätzlich `created_tasks[]` und `recurring_tasks_failed` | Ab Gärtner |
| GP-API-070 | `GET /bed-templates/{key}/export` → JSON-Datei einer Beetvorlage (**v1.13, Welle 9, WP 9.9 #2749, gemountet seit #2799;** GP-FR-173): `schema_version`, Geometrie, Standardgrößen, Pflanzraster; **ohne** Mandanten-Keys, Notizen und Personenbezüge (kein `tenant_key`, kein `created_by`) | Alle Rollen (Lesen nach §21.8) |
| GP-API-071 | `POST /bed-templates/import` `{dry_run}` (**v1.13, Welle 9, WP 9.9 #2749, gemountet seit #2799;** GP-FR-173): Datei ≤ 256 KB (sonst 413), Schema-Validierung (422), Namenskollision → 409 mit Namensvorschlag; Keys aus der Datei werden ignoriert, Referenzen werden nicht aufgelöst; Quoten nach GP-NFR-017 und GP-API-061; Härtungen wie GP-FR-141; angenommen werden die letzten zwei `schema_version`-Stände (die aktuelle und eine Vorgängerversion, wie GP-NFR-072), ältere → 422. `dry_run=true` liefert den Prüfbericht ohne Schreiben; Oberfläche: „Exportieren“ je Vorlage und „Importieren“ mit Prüfbericht im Vorlagen-Panel | Ab Gärtner (Anlegen nach §21.8) |

### 21.8 Autorisierung

Standardregel: Lesen „Alle Rollen", Anlegen/Ändern „Ab Gärtner", Löschen „Nur Leitung" (REQ-049 §3.3). `ResourceType` erhält `garden_object`, `care_event`, `irrigation_zone`, `bed_template`; Plan-Batch nutzt `ResourceType.LOCATION` + `Action.UPDATE` als Eingangs-Gate **und** eine Rollenprüfung je Operation im Service (SR-001). Datenabhängige Regeln dieser Tabelle (belegt/unbelegt, eigene/fremde, `planned`) setzt der **Service** durch (`require_permission` ist heute rollen-, nicht ressourcenabhängig); je Zeile und Rolle gibt es einen Negativtest (SR-010).

| Ressource | Lesen | Anlegen | Ändern | Löschen | Sonderaktionen |
|-----------|-------|---------|--------|---------|----------------|
| Gartenplan (Grenze, Batch) | Alle Rollen | Ab Gärtner | Ab Gärtner | — | Batch-`delete`: Nur Leitung (je Op geprüft); Import `merge`/`replace`: Nur Leitung; Export: Alle Rollen |
| Beet (Location) | Alle Rollen | Ab Gärtner | Ab Gärtner | Nur Leitung | Status `retired`: Nur Leitung |
| Gartenobjekt | Alle Rollen | Ab Gärtner | Ab Gärtner | Nur Leitung | — |
| Slot (Pflanzposition) | Alle Rollen | Ab Gärtner | Ab Gärtner | Ab Gärtner (unbelegt, keine aktive Reservierung), Nur Leitung (belegt) — Prädikat im Service, nicht im Router-Gate | Position korrigieren: Ab Gärtner |
| Pflanzdurchlauf / geplante Belegung | Alle Rollen | Ab Gärtner | Ab Gärtner | Nur Leitung (Run); Reservierung: Ab Gärtner solange `planned` | Beet räumen: Ab Gärtner |
| Pflegeaufgabe | Alle Rollen | Ab Gärtner | Ab Gärtner | Nur Leitung | Erledigen: Ab Gärtner |
| Pflegeereignis | Alle Rollen | Ab Gärtner | Eigene (Supersede), Nur Leitung (fremde) | — (Void: eigene ≤ 10 min als Rückgängig ab Gärtner, sonst Nur Leitung; Redaktion: Nur Leitung) | Filter nach Person: nur auf sich selbst; Leitung/`management` auf jedes Mitglied (SR-020, E-16) |
| Bewässerungszone | Alle Rollen | Ab Gärtner | Ab Gärtner | Nur Leitung | Aktor-/HA-Kopplung (`actuator_key`, `flow_rate_ha_entity_id`): Technik; Aktor-Befehl: Rolle nach REQ-018 (Bedienen), nicht Technik (REQ-049 §2) |
| Beetvorlage (tenant) | Alle Rollen | Ab Gärtner | Ab Gärtner | Nur Leitung | Globale Vorlagen: Plattform-Admin |

Die Standort-Zuweisung (`location_assignments`) bleibt Koordination ohne Schreibgrenze (REQ-049 §3.5). Modul-Sichtbarkeit (O-15, entschieden): Modul `garden_planner` ist registriert (REQ-042 v1.3); Navigation unter „Standorte" (Plan als Unterpunkt der Site, kein eigener Hauptmenüpunkt, REQ-021); im Light-Modus (REQ-027) verfügbar.

---

## 22. Validierung

### 22.1 Ebenen

| Ebene | Prüft | Reaktion |
|-------|-------|----------|
| **UI** | Snap, Mindestgrößen beim Zeichnen, Containment-Vorschau (rote Markierung), Pflichtfelder, Zahlenbereiche | sofort, verhindert Operation oder markiert |
| **API (Pydantic)** | Typen, Bereiche, Enum-Werte, Punktzahl, Rotation, Operationslimit | 422 `validation_error` |
| **Domain (Service/Calculator)** | Geometrie einfach, Containment, Überlappung, Pflanzabstände, Zustandsübergänge, zeitliche Plausibilität, Tenant-Anker | 409/422 mit Fachcode |
| **Datenbank** | Unique-Indizes (`slot_id` je Location, `source_ref`), Edge-Definitionen (erlaubte Collections), Transaktion | Transaktion bricht ab; Fehler wird in 409/500 übersetzt |

**Feste Prüfreihenfolge (SR-013):** (1) Authentifizierung → (2) Tenant-Anker und Auflösung aller referenzierten Keys (§22.3, GP-NFR-058) → (3) Rolle je Operation (§21.8) → (4) Pydantic → (5) Domain-Validierung → (6) Revisionsprüfung in der Transaktion. Ein fremder oder fehlender Kontext liefert immer 404 ohne Body-Details; `changed_by` im 409 ist der Anzeigename, nie der Nutzer-Key. So kann weder ein 409 die Existenz fremder Sites noch ein `outside_parent` fremde Geometrie verraten.

### 22.2 Regeln

| Regel | Ebene | Code | Inhalt |
|-------|-------|------|--------|
| V-01 | API | `geometry.invalid` | Maße > 0, Punkte im zulässigen Bereich (Plan-Rahmen 0 ≤ x,y ≤ 1 000 m; Beet-Rahmen −1 000 ≤ x,y ≤ 1 000 m, E-12), Rotation 0–359,999 (negativ → abgelehnt; rundet auf 360,000 → 0,0), Polygon ≥ 3 Punkte, ≤ 200 Punkte |
| V-02 | Domain | `geometry.self_intersecting` | Polygon ist einfach (Segment-Schnitt-Test, O(n²) bei n ≤ 200 akzeptabel) |
| V-03 | Domain | `geometry.outside_parent` | Location/GardenObject mit `parent_location_key` liegt vollständig in der Eltern-Geometrie (Punkt-in-Polygon aller Eckpunkte; für rotierte Rects über die 4 transformierten Ecken). Ohne Eltern: innerhalb der Gartengrenze, falls gesetzt. Toleranz 1 cm. |
| V-04 | Domain | `slot.outside_bed` | Slot-Geometrie liegt innerhalb der Beet-Geometrie (Beet-Rahmen), Randabstand als **Inset** zur Kante — **die geforderte Regel „Pflanzen dürfen nicht außerhalb eines Beetes liegen"** |
| V-05 | Domain | `bed.overlap` | Zwei Beete derselben Eltern-Location dürfen sich nicht überlappen (Bounding-Box-Vortest, dann Polygon-Schnitt über Separating-Axis für konvexe bzw. Kantentest für konkave Formen). Beet ↔ Gartenobjekt darf überlappen (Weg unter Hochbeet) — nur Warnung in der UI. |
| V-06 | Domain | `slot.overlap` | Slot-Zonen (`zone`) innerhalb eines Beets dürfen sich nicht überlappen — geprüft nur gegen **aktive und geplante** Slots (`archived_at = null`, F-02); Positionen (`point`) haben keinen Überlappungsbegriff |
| V-07 | Domain (Hinweis) | `planting.spacing_below_minimum` | Abstand zweier geplanter Positionen < `spacing_cm` → **Hinweis** in Preview-Antwort (`warnings[]`), kein Fehler (GP-FR-072) |
| V-08 | Domain | `slot.already_planned` | Slot hat eine Reservierung mit **überlappendem Zeitfenster** oder eine aktive Pflanze, deren erwartetes Ende nach `planned_from` liegt (GP-FR-065) |
| V-09 | Domain | `location.has_active_plants` | Löschen/`retired` eines Beets mit Pflanzen `removed_on = null` verweigert |
| V-10 | Domain | `bed_status.invalid_transition` | nur Übergänge aus §7.4 |
| V-11 | Domain | `care_event.performed_in_future` / `care_event.too_old` | `performed_at ≤ now + 5 min` und `≥ now − 365 d`; ausgenommen Ereignisse, die der Server mit `trigger = backfill` erzeugt (GP-API-042, GP-FR-105 — bis 10 Jahre zurück) |
| V-12 | Domain | `care_event.immutable` | Änderung an bestehendem Ereignis außer Supersede/Void |
| V-13 | Domain | `care_event.sequence` | `supersedes_key` muss selbes Beet + nicht bereits superseded sein (keine Verzweigung) |
| V-14 | Domain | `plan.revision_conflict` | `expected_revision != plan_revision` |
| V-15 | Domain | `tenant.mismatch` → 404 | Site/Location/Slot gehört nicht zum aktiven Tenant (bestehendes 404-Muster) |
| V-16 | Domain | `garden_object.not_plantable` | Run/Task/Slot auf ein GardenObject |
| V-17 | API | `batch.too_many_operations` | > 500 |
| V-18 | Domain | `reference.not_found` | Ein in Body/Import referenzierter Key ist nicht auflösbar oder gehört nicht zum Tenant (GP-NFR-058) — ein Text für beides |
| V-19 | Domain | `boundary.shrinks_below_objects` | Neue Gartengrenze lässt bestehende Objekte außerhalb → Fehler mit Liste der Keys (Nutzer verschiebt zuerst) |
| V-20 | DB | unique `slots(location_key, slot_id)` | bestehende Regel |
| V-21 | API | `batch.operation_forbidden` | Operation über der Rolle des Aufrufers (403, SR-001) |
| V-22 | API/Domain | `plan.quota_exceeded`, `layout.too_many_positions`, `batch.too_complex` (Request-Body > 1 MiB: 413 `body_too_large`) | Quoten (GP-NFR-017), Layout-Obergrenze (GP-FR-062), Komplexitäts-/Zeitbudget (GP-NFR-013) |
| V-23 | Domain | `tent.photoperiod_conflict` | Hinweis (kein Fehler): Pflanzen verschiedener Photoperiode-Phasen in einer Zelt-Location (SHOULD); nur belegte Lichtdauern (`sourced`) zählen, sonst `tent.photoperiod_unknown` (§9.2a, #2857) |
| V-24 | Domain | `site.has_active_plants` | `DELETE /sites/{key}` verweigert (409, `details[0].active_plant_count`), solange eine Pflanze mit `removed_on = null` den Standort (`site_key`) oder ein Beet/einen Slot trägt, der mit gelöscht würde; V-09 eine Ebene höher (GP-FR-024), geprüft in der Lösch-Transaktion vor dem ersten Schreibzugriff |
| V-25 | Domain | `slot.occupied` (409), `slot.already_planned` (409, V-08) | Eine Einzelpflanze (`POST /plant-instances` mit `slot_key`, `PlantInstanceService.create_plant`) auf einem Pflanzplatz der Rolle `position` wird abgelehnt, wenn dort schon eine Pflanze des Mandanten mit `removed_on = null` steht (`slot.occupied`, derselbe Code wie beim Säen und Vereinzeln) oder ein lebender Pflanzlauf (`planned`/`active`/`harvesting`) den Platz für ein Fenster reserviert, das nicht vor heute (UTC) endet (`slot.already_planned` mit `conflicting_run_key`, `overlap_from`, `overlap_until`). Gilt auch mit `skip_validation`. Reihen und Flächen (`row`, `zone`) nehmen weiter bis `capacity_plants` Pflanzen. Prüfen-dann-Schreiben wie `create-plants` (keine Transaktion, kein eindeutiger Kantenindex): zwei gleichzeitige Anfragen können beide durchkommen (GP-UX-071, #2913) |

### 22.3 Mandanten-Anker und Referenzauflösung

Locations, Slots und GardenObjects tragen **kein** `tenant_key` (E-01, v1.4). Der Mandanten-Anker ist die Site: jede Service-Methode löst den Eigentümer über `location_ownership` auf, und zwar so, dass `site_key` **nie aus dem Request stammt** (SR-002):

| Regel | Inhalt |
|-------|--------|
| T-01 | `site_key` wird **immer aus dem gespeicherten Dokument** abgeleitet: Location → `site_key`; Slot → `location_key` → `site_key`; GardenObject/Zone/CareEvent → `site_key`. Request-Felder mit `site_key` werden ignoriert. |
| T-02 | Für Endpunkte mit Site im Pfad gilt `resource.site_key == path.site_key`, sonst 404. |
| T-03 | Im Batch und im Import wird jede referenzierte Location bzw. jeder Slot (einschließlich `parent_location_key`) **vor** jeder Geometrie- oder Containment-Prüfung aufgelöst und muss zur Pfad-Site gehören. |
| T-04 | Jede Service-Methode nimmt `tenant_key` keyword-only ohne Default und prüft `site.tenant_key == tenant_key` vor der ersten Schreib- oder Rechenoperation (Prädikat im Service, nicht im Router — Memory „Guard opt-in am Aufrufort"). |

| ID | Prio | Anforderung |
|----|------|-------------|
| GP-NFR-058 | MUST | **Referenzauflösung (SR-003):** Jeder Key in einem Request-Body oder Import wird serverseitig gegen den aktiven Tenant aufgelöst; globale Stammdaten mit `tenant_key = null` sind nur für `species`, `cultivar`, `fertilizer`, `substrate`, `bed_template`, `location_type` zulässig. Teilmengenregeln: `care_events.plant_keys` ⊆ Pflanzen mit `location_key` im Teilbaum des Event-Beets; `slot_keys` (GP-API-021) ⊆ Slots von `run.location_key`; Zone `location_keys` ⊆ Locations der Zone-Site; `water_source_key` = GardenObject `water_source` derselben Site; `actuator_key` = Aktor des Tenants an einer Location derselben Site; `photo_refs` = Attachments des Tenants, die der Aufrufer hochgeladen hat oder die dem Zielobjekt zugeordnet sind; `supersedes_key` = Event desselben Tenants und Beets; `source_ref` nur serverseitig; Task-Keys in `tasks/batch/*` einzeln tenant-geprüft, ein fremder Key lässt den Batch mit 404 scheitern. Ungültige Referenz → 422 `reference.not_found` ohne Unterscheidung fremd/fehlt. Negativtest je Feld (GP-ACC-041). |

## 23. Import und Export

| ID | Prio | Format | Inhalt | Richtung | MVP |
|----|------|--------|--------|----------|-----|
| GP-FR-140 | MUST | **JSON** (`schema_version: "1"`) | Site-Plan, Locations (Beet-Felder, Geometrie, Bodenprofil, Standortmerkmale `site_conditions`, Alt-Feld `frost_exposed`), GardenObjects, Slots, Zonen, Vorlagen-Referenzen; **keine** Pflanzen, Tasks, Ereignisse, Fotos | Export | ja |
| GP-FR-141 | SHOULD | JSON | Import `merge`/`replace` (GP-API-005) mit Vorab-Prüfbericht (`dry_run=true`). **Grenzen (SR-018):** Quoten aus GP-NFR-017, ≤ 10 Ebenen Verschachtelung, alle V-Regeln und GP-NFR-058; interne Verweise über eine Import-lokale Key-Map umgeschrieben, externe gegen den Tenant aufgelöst oder auf `null` gesetzt und als `dropped_references[]` berichtet; `flow_rate_ha_entity_id` und `actuator_key` werden beim Import **immer** verworfen (Neukopplung durch Technik). | Import | nein |
| GP-FR-142 | MUST | **PDF** | Maßstäblicher Plan: Standard **A4 quer, Maßstab automatisch** (O-12); Stufen **1:20, 1:25, 1:50, 1:75, 1:100, 1:125, 1:150, 1:200, 1:250, 1:300, 1:400, 1:500** (F-15: feinere Stufen, damit ein 28 × 20-m-Garten auf 1:150 statt 1:200 fällt); A3 wird automatisch vorgeschlagen, wenn A4 unter 1:200 fiele; Ebenenwahl für den Druck; Maßstabsleiste, Nordpfeil, Legende, Titelblock (Garten, Datum, Revision), Beetbeschriftungen; Tagged PDF, DE/EN (REQ-032 NFR). **Standardmäßig ohne personenbezogene Angaben** (SR-024): keine Mitgliedernamen, Zuweisungen, Notizen, GPS-Koordinaten, `*_by`-Felder; „Zuweisungen anzeigen" ist eine ausdrückliche Option. Vorschau mit Maßstab vor dem Download. Optional zweite Seite: Beetliste. | Export | ja |
| GP-FR-143 | MUST | **SVG** | Serverseitig (GP-API-006), Einheit mm (`viewBox` in mm, 1 m = 1 000 Einheiten), Layer als `<g id="layer-…">`, Objekt-IDs als `data-key` | Export | ja |
| GP-FR-144 | SHOULD | **PNG** | Clientseitig aus dem SVG-DOM in 1×/2×/4× Auflösung; Wasserzeichen „Kamerplanter · Datum" | Export | nein |
| GP-FR-145 | SHOULD | **CSV** | Beetliste (`GET /locations?…&format=csv`): Name, Typ, Fläche, Status, Bodenart, Zone, aktive Pflanzen; Historie (GP-FR-104) (gleiche CSV-Härtung wie GP-FR-104) | Export | nein |
| GP-FR-146 | WON'T | **GeoJSON** | **Gestrichen (O-21 revidiert, E-06, v1.4).** Begründung: WGS84-Koordinaten sind der Wohnort (SR-024), kein Nutzer der Zielgruppen verlangt das Format, und PDF/SVG/JSON decken Drucken, Weitergabe und Sicherung ab. Wird es je gebraucht, ist es ein eigenes Vorhaben mit eigener DSFA. | — | — |
| GP-FR-147 | MUST | JSON | Sicherung und Wiederherstellung: JSON-Export ist in der DSGVO-Datenexport-Kaskade (`DataExportEngine`, REQ-025) enthalten; Import in dieselbe Site stellt Geometrien vollständig wieder her (AC in §30) | beide | ja (Export), SHOULD (Import) |
| GP-FR-148 | SHOULD (vor Import `replace`: MUST, SR-011; Rückholung: GP-FR-170) | JSON | Automatischer Snapshot je Saison (`garden_plan_snapshots`, 1. Januar / vor `replace`-Import) mit Wiederherstellung | beide | nein |

### 23.1 Erweiterungen (v1.3 — Entscheidungen in §32.1)

| ID | Prio | Format | Inhalt | Richtung | MVP |
|----|------|--------|--------|----------|-----|
| GP-FR-170 | MUST | JSON | **Wiederherstellung in den MVP:** Eine Sicherung, die sich nicht zurückspielen lässt, ist keine. Import `replace` auf dieselbe Site mit `dry_run`-Prüfbericht und **Pflicht-Snapshot** (SR-011) wird MVP; die Grenzen aus GP-FR-141/SR-018 gelten unverändert. Löst den Widerspruch GP-FR-147 (MUST) ↔ GP-FR-141 (SHOULD) auf. Erst die Rückholfunktion macht den Snapshot (GP-FR-148) wertvoll. *(O-18 entschieden 2026-10-11: MVP.)* | beide | ja |
| GP-FR-171 | SHOULD | Aktion | **„Neue Saison aus Vorjahr“:** übernimmt Beete, Slots und Zonen, legt **keine** Pflanzen an; Historie bleibt an den Slots (§13), Fruchtfolge-/Mischkultur-Hinweise (GP-FR-131/132) nutzen die Vorjahresbelegung; optional Anzeige „Hier stand: Tomate“ als Planentwurf. Ergänzt GP-FR-078 (Kopie der Runs): GP-FR-171 kopiert die Beetstruktur, GP-FR-078 die geplanten Runs; beides darf in einem Schritt angeboten werden. Datenkopie gehört zu REQ-053, Belegungsvorschläge zu REQ-054 (O-20 entschieden 2026-10-11); gilt für Garten **und** Wohnung/Indoor (§9.8). | Kopie | nein |
| GP-FR-172 | SHOULD | JSON | **Teil-Export und Zielwahl:** Export `scope ∈ {site, selection, subtree}` (nur diese Beete / ein Bereich mit Unterbeeten); Import `target ∈ {same_site, other_site, other_tenant}` für Umzug und Parzellenübergabe. Referenzregeln wie GP-FR-141 (externe Verweise → `null`, Bericht `dropped_references[]`); Rolle: Leitung beider Seiten. | beide | nein |
| GP-FR-173 | COULD | JSON | **Vorlagen-Austausch:** Beet-Vorlage (GP-FR-044) einzeln als JSON exportieren/importieren, ohne Mandanten-Keys, Notizen, Personenbezüge; Härtungen wie GP-FR-141. Eine kuratierte Vereinsbibliothek gehört nicht hierher. API: GP-API-070/071 (v1.13). | beide | nein |
| GP-FR-174 | SHOULD | **CSV** | **Beetlisten-Import** zur Massenanlage: Spalten `Name; Typ; Breite_m; Länge_m` (optional Sonne, Bodenart, Zone); Prüfbericht mit Zeilenfehlern (`dry_run`), UTF-8, Semikolon (deutsches Excel), Formel-Injektions-Härtung wie GP-FR-104/145. Legt Beete ohne Layout an (zunächst in einer Reihe); die Anordnung erfolgt im Editor. Export zusätzlich als Excel-Variante (Semikolon, BOM). | Import | nein |
| GP-FR-175 | SHOULD | CSV | **Spaltenauswahl im Export:** Standardspalten wie GP-FR-145; wählbar zusätzlich Standortmerkmale (§10.2) und Zuweisung (nur mit Opt-in, SR-024). | Export | nein |
| GP-FR-176 | COULD | PDF | Optionale Zusatzseite **Parzellenliste** (Beetnummer, Fläche, bei Opt-in Zuweisung) für Vorstand/Verpächter; ergänzt die Beetliste aus GP-FR-142. API: `parcel_list` an GP-API-007 (v1.13); „Beetnummer“ ist kein Feld, sondern Beetname plus laufende Nummer in Plan-Reihenfolge (§32.6 Pkt. 8). | Export | nein |
| GP-NFR-072 | SHOULD | JSON | **Schema-Rückwärtskompatibilität:** Import migriert mindestens die letzten zwei `schema_version`-Stände; ein Januar-Export muss im Dezember lesbar sein (ergänzt GP-NFR-004). | Import | nein |

Anpassungen an bestehenden Zeilen: PNG-Wasserzeichen (GP-FR-144) ist **Option**, nicht Standard; SVG-Download (GP-FR-143) bleibt MUST als Zwischenformat, der eigenständige Download wird SHOULD; die zwölf PDF-Maßstabsstufen (GP-FR-142) stehen im Dialog unter „erweitert“, Standard bleibt „automatisch“. GeoJSON-Export (GP-FR-146) ist Streichkandidat (O-21).

---

## 24. Accessibility (WCAG 2.1 AA, UI-NFR-002)

| ID | Prio | Anforderung | MVP |
|----|------|-------------|-----|
| GP-NFR-020 | MUST | Jedes Plan-Objekt ist ein fokussierbares `<g role="button" tabindex="0" aria-label="Hochbeet 3, Beet, 2 × 1 m, 6 Pflanzen, 2 offene Aufgaben">`; die DOM-Reihenfolge folgt Zeile → Spalte nach `bbox` (R-026). | ja |
| GP-NFR-021 | MUST | Vollständige Tastatur-Alternative für jede Drag-Interaktion (R-024): Verschieben per Pfeiltasten, Skalieren/Drehen über das Eigenschaftenpanel, Polygon-Punkte über eine Punktliste im Panel mit x/y-Feldern. Griffe nur für die Maus: `tabindex="-1"` (R-025). | ja |
| GP-NFR-022 | MUST | `aria-live="polite"`-Region meldet Ergebnis jeder Operation („Hochbeet 3 verschoben nach x 1,0 m, y 1,5 m", „Gespeichert, Revision 43", „Konflikt") (R-027). | ja |
| GP-NFR-023 | MUST | **Alternative Darstellung des Plans:** Schalter „Als Liste" (ab Welle 10 der Tab „Liste“, GP-UX-064) zeigt dieselben Objekte als hierarchische Liste (Bereich → Beet → Pflanzen) mit allen Werten des Panels; alle Aktionen (außer Freihandzeichnen) sind dort ausführbar. Die Liste ist zugleich die Screenreader-Hauptnavigation. | ja |
| GP-NFR-024 | MUST | Kontraste: Objektfüllung gegen Hintergrund ≥ 3:1 (R-017), Text ≥ 4,5:1, Fokusring 2 px mit ≥ 3:1 (R-005); Information nie nur über Farbe (R-018): Beettyp über Muster + Icon, Phase über Icon + Text im Tooltip/Liste. | ja |
| GP-NFR-025 | MUST | 200 % Browser-Zoom ohne Funktionsverlust (R-019): Werkzeugleiste umbricht, Panel wird Bottom Sheet. Ab Welle 10 gilt statt des Umbruchs die Breakpoint-Regel GP-UX-069 nach der effektiven Breite (`TouchBar` und Bottom Sheet), Überzähliges wandert in den Überlauf (GP-UX-063). | ja |
| GP-NFR-026 | MUST | `prefers-reduced-motion`: keine Zoom-Animation, kein Geisterobjekt-Fading (R-022). | ja |
| GP-NFR-027 | MUST | Touch-Bedienung ohne Hover (GP-UX-025), Ziele ≥ 48 px, im Feldmodus ≥ 64 px. | ja |
| GP-NFR-028 | MUST | `vitest-axe` auf Editor und Beetansicht; E2E-a11y-Lauf (bestehende Nightly-Kontrolle) enthält den Plan. | ja |
| GP-NFR-029 | SHOULD | SVG-Export trägt `<title>`/`<desc>` je Objekt; PDF ist Tagged PDF mit Lesereihenfolge (REQ-032). | nein |

---

## 25. Performance

### 25.1 Größenklassen (Begründung: Zielgruppen-Betriebsgrößen aus `spec/target-audiences/`)

| Klasse | Beispiel | Beete | Gartenobjekte | Pflanzen (aktiv) | Slots | Ereignisse/Jahr |
|--------|----------|-------|---------------|------------------|-------|-----------------|
| **klein** | Balkon, Kleingarten (ZG-002 untere Grenze, UZG-001) | ≤ 5 | ≤ 10 | ≤ 50 | ≤ 60 | ≤ 500 |
| **mittel** | Gemüsegarten 60–200 m² (ZG-002) | ≤ 20 | ≤ 40 | ≤ 300 | ≤ 400 | ≤ 3 000 |
| **groß** | Gemeinschaftsgarten 30 Parzellen, Gewächshausbetrieb (ZG-004, UZG-005) | ≤ 150 | ≤ 300 | ≤ 2 000 | ≤ 3 000 | ≤ 20 000 |
| **Belastungsgrenze** | Marktgärtnerei (UZG-002) | 500 | 500 | 5 000 | 8 000 | 50 000 |

Die Zielwerte gelten für „groß"; die Belastungsgrenze ist zugleich die **harte Quote** (GP-NFR-017, SR-004) und die Schwelle, ab der der Konva-Renderer (D-01) verpflichtend wird; die serverseitige Paginierung bzw. `include=`-Nachladung der Pflanzen gilt ab der Klasse „groß" (GP-NFR-031, E-13).

### 25.2 Zielwerte

| ID | Prio | Metrik | Ziel | Begründung |
|----|------|--------|------|------------|
| GP-NFR-030 | MUST | `GET /plan` p95 Serverzeit (groß) | ≤ 300 ms | Ein Request, Indizes auf `site_key`; 3 000 Slots sind ein AQL-Scan |
| GP-NFR-031 | MUST | `GET /plan` Antwortgröße (groß) | ≈ 1 MB unkomprimiert (E-13); die Quote von 500 Objekten bleibt die harte Grenze | Pflanzen serverseitig paginiert bzw. per `include=` nachladbar, kein eigenes Wire-Format, keine Abhängigkeit von gzip; keine Fotos |
| GP-NFR-032 | MUST | Zeit bis interaktiver Plan nach Navigation (groß, Desktop, Cache warm) | ≤ 2,0 s; Feldmodus 4G ≤ 3,0 s | UI-NFR-003 TTI < 3,5 s mit Reserve für den Dynamic Import |
| GP-NFR-033 | MUST | Drag-Frame-Zeit (groß, 1 Objekt) | ≤ 16 ms (60 fps) auf Mittelklasse-Laptop, ≤ 33 ms auf Mittelklasse-Smartphone | CSS-Transform statt Re-Render (GP-NFR-011) |
| GP-NFR-034 | MUST | Zoom/Pan-Frame-Zeit (groß) | ≤ 16 ms | `viewBox`-Änderung, Culling |
| GP-NFR-035 | MUST | Batch-Speichern (50 Operationen) p95 | ≤ 500 ms | eine Transaktion, Containment-Checks O(n·m) mit bbox-Vortest |
| GP-NFR-036 | MUST | Layout-Preview (200 Positionen, Polygon-Beet) | ≤ 100 ms serverseitig, ≤ 50 ms clientseitig | reine Rechnung |
| GP-NFR-037 | MUST | Historie-Seite (50 Einträge aus 20 000) | ≤ 200 ms | Index `(tenant_key, location_key, performed_at desc)` |
| GP-NFR-038 | MUST | PDF-Erzeugung (groß) | ≤ 5 s (REQ-032) | WeasyPrint mit SVG; Pflanzen-Marker ab 2 000 als Zähler je Beet statt Einzelsymbol |
| GP-NFR-039 | SHOULD | Speicher Editor-Tab (groß) | ≤ 150 MB Heap | DOM-Knoten ≈ 4 × Objekte + Culling |
| GP-NFR-040 | MUST | Messung: Lighthouse-CI (`lighthouserc.json`) erhält die Plan-Route; vitest-Benchmark für `applyOperation` und `compute_layout`; pytest-Benchmark für Containment-Check mit 3 000 Slots | CI-Assertion | Zielwerte werden als Assertion geführt, nicht als Prosa |
| GP-NFR-071 | SHOULD | Messprofile Interaktion (MVP nein, §9.7): INP für Auswahl, Drag-Start und Zoom; Pinch-Zoom-Frametime auf Smartphone; Low-End-Android-Profil (CPU 4× gedrosselt) für den Feldmodus | INP ≤ 200 ms; Pinch ≤ 33 ms | Ergänzt GP-NFR-033/-034 um die Eingabelatenz (Web-Vitals INP) |

---

## 26. Sicherheit

| ID | Prio | Anforderung |
|----|------|-------------|
| GP-NFR-050 | MUST | Alle Endpunkte tenant-scoped (`/t/{slug}`), Rollen nach §21.8 über `require_permission`; fremde Ressourcen liefern 404 (Bestandsmuster). Negativtests je Endpunkt (cross-tenant read/write) nach dem Muster der ZAP-Nightly (NFR-015). |
| GP-NFR-051 | MUST | Import (JSON): Größe ≤ 5 MB, `schema_version` geprüft, keine Keys aus dem Import übernommen (immer neue `_key`), Grenzen und Referenzregeln nach GP-FR-141/GP-NFR-058; der Export enthält keine `*_by`-Felder und keine Nutzer-Keys. |
| GP-NFR-052 | MUST | **SVG/PDF-Härtung (SR-015):** (a) Die PDF-Erzeugung nutzt einen restriktiven WeasyPrint-`url_fetcher`, der nur `data:`-URIs und Pfade unterhalb des Template-Verzeichnisses zulässt — der heutige `PrintEngine` (`print_engine.py:172`) ruft `HTML()` ohne `url_fetcher` auf, der Default lädt `http(s)://` und `file://` (SSRF/Local-File-Read; betrifft auch die bestehenden `/print/*`-Endpunkte → eigenes Issue). (b) Der SVG-Writer emittiert nur eine Allowlist (`svg, g, rect, circle, polygon, polyline, line, path, text, tspan, title, desc, defs, pattern`) ohne `href`/`xlink:href`/`style url()`/`foreignObject`/`script`/`image`; Nutzertext wird kontextgerecht escaped (Text **und** Attribut). (c) `color` passt auf `^#[0-9A-Fa-f]{6}$`; `layers`, `locale`, `scale`, `paper` sind Enums. (d) Jinja-Autoescape an. (e) SVG-Download mit `Content-Disposition: attachment`, `X-Content-Type-Options: nosniff`, `Content-Security-Policy: default-src 'none'` (das SVG trägt kein `style`-Element und kein `style`-Attribut, nur Präsentationsattribute — daher kein `style-src`, #2542). (f) Bilder im PDF nur als serverseitig eingebettete `data:`-URIs aus NFR-013-Attachments des Tenants. Negativtest: Beetname `"><image href="http://169.254.169.254/"/>` und `file:///etc/passwd` erzeugen weder Abruf noch Element (GP-ACC-045). |
| GP-NFR-053 | MUST | Fotos über die bestehende Attachment-Pipeline (NFR-013: EXIF-Strip, Größenlimits, Virenscan-Hook); keine GPS-Daten aus Fotos in den Plan übernehmen. QR-Deep-Links (GP-FR-052) enthalten nur einen relativen App-Pfad, kein Token; Rücksprung nach Login nur same-origin; Nicht-Mitglied → 404 ohne Tenant-Wechsel (SR-023). |
| GP-NFR-054 | MUST | `performed_by_user_key` wird aus dem Token gesetzt, nie aus dem Body; `performed_by_label` (Dritte) ist Freitext ohne Nutzerbezug. |
| GP-NFR-055 | MUST | DSGVO (REQ-025/NFR-011): **Retention (SR-005, Betreiberentscheid):** NFR-011 erhält die Zeile `care_events` — **5 Jahre** ab `performed_at` (analog Fruchtfolge-Rückblick GP-FR-103), danach werden `performed_by_user_key`, `performed_for_user_key`, `created_by`, `voided_by`, `redacted_by`, alle Freitexte und `photo_refs` anonymisiert bzw. gelöscht, Kategorie/Zeit/Menge/Beet/Pflanzen bleiben (Fruchtfolge); für `category ∈ {pest_control, ipm}` gilt der PflSchG-Vorbehalt wie bei `treatment_applications`; `garden_plan_audit` 1 Jahr, danach Hard-Delete; davon unabhängig hält eine Site höchstens die **20 neuesten** `import_snapshot`-Zeilen (`MAX_SNAPSHOTS_PER_SITE`, #2542) — jeder `replace`-Import und jede Wiederherstellung entfernt in derselben Transaktion die älteren Snapshots dieser Site, andere Protokollzeilen bleiben unberührt. Je ein eigener Celery-Beat-Task setzt das durch (`retention.anonymize_expired_care_events`, `retention.purge_expired_garden_plan_audit`; NFR-011 §3.1 kennt keinen Master-Task — v1.4 korrigiert). **Löschkaskade (SR-007):** `ErasureEngine.ANONYMIZE_COLLECTIONS` ersetzt den Nutzer-Key in `care_events.{performed_by_user_key, performed_for_user_key, created_by, voided_by, redacted_by}`, `garden_objects.created_by`, `sites.plan.plan_updated_by`, `garden_plan_audit.user_key` (dort als Tombstone-Hash, damit die Zeilen untereinander verknüpfbar bleiben — WP 1.8), `bed_templates.created_by` durch `_anonymized`; ein Inventar-Test prüft, dass jedes `*_by`/`*_user_key`-Feld der neuen Collections in der Kaskade steht. **Art. 15/20 (SR-008):** der DSGVO-Export enthält alle `care_events`, die der Betroffene ausgeführt oder angelegt hat, und seine `garden_plan_audit`-Einträge. **Freitexte gelöschter Mitglieder (E-16):** In geteilten Mandanten bleiben die Freitexte einer Protokollzeile stehen, genau wie der Text eines `plant_diary_entries`-Eintrags (REQ-050 §7.4): nur die Kontoverweise werden ersetzt (die Anzeige lautet „anonymisiert"), kein Freitextfeld wird bei der Kaskade geleert; die Leitung kann einen Text, der eine Person benennt, nach GP-FR-109 redigieren, und die fünfjährige Retention leert den Rest. Geometrien sind keine personenbezogenen Daten; GPS der Site unterliegt der bestehenden Regel; Eigenposition siehe GP-UX-026. |
| GP-NFR-056 | MUST | **Rate-Limits (SR-017)** über den Bestands-Limiter, 429 nach NFR-006 mit `Retry-After`: Batch 10/min je Nutzer; Preview 60/min; PDF/SVG/Export/CSV 10/min je Nutzer und 30/min je Tenant; Import 3/min je Tenant; `quick-planting`, `slots/batch`, `log-watering`, `clear` 20/min je Nutzer; `POST /care-events` und `tasks/batch/status` 60/min je Nutzer, Batch-Größe ≤ 200 Tasks; `GET /plan?as_of=` 30/min. |
| GP-NFR-057 | SHOULD | `security-review`-Skill auf den PR mit Batch-API und Import; ZAP-Nightly-Negativtest für `POST /plan/import` cross-tenant. |

---

## 27. Observability (NFR-007)

| ID | Prio | Anforderung |
|----|------|-------------|
| GP-NFR-060 | MUST | Structlog-Events: `garden_plan.batch_applied {site_key, revision, op_count, duration_ms}`, `garden_plan.revision_conflict`, `garden_plan.validation_failed {codes[]}`, `care_event.created {category, trigger}`, `planting_layout.computed {strategy, count, duration_ms}`; keine Nutzertexte in Logs; Batch-/Import-Payloads, Pydantic-`input`-Werte in 422-Details (Log-Seite), `flow_rate_ha_entity_id` und Dateinamen werden nie geloggt (SR-025, NFR-011 L-1…L-9). |
| GP-NFR-061 | MUST | Prometheus-Metriken: `garden_plan_batch_duration_seconds` (Histogram), `garden_plan_conflicts_total`, `care_events_created_total{category}`, `garden_plan_size_objects` (Gauge je Request-Bucket klein/mittel/groß). |
| GP-NFR-062 | MUST | Frontend: Sentry nur bei erteilter Einwilligung (REQ-025 `ConsentGuard` auf Service-Ebene; im Frontend entscheidet die gespeicherte Einwilligung `error_tracking` — es gibt keine Middleware dafür; SR-019); Breadcrumbs enthalten Ereignistyp und Zähler, aber keine Namen, Notizen, Koordinaten oder Keys; Redux-State geht nicht an Sentry (`stateTransformer → null`); Fehler im Renderer werden mit Modellgröße (nicht Inhalt) gemeldet. Web-Vitals der Plan-Route über die bestehende Lighthouse-CI. |
| GP-NFR-063 | SHOULD | Celery-Tasks (Adjacency, Konsistenz) melden Laufzeit und Trefferzahl; Konsistenz-Job alarmiert ab > 100 Fachereignissen ohne Protokoll. |
| GP-NFR-064 | MUST | Fehlerbehandlung: alle Fachfehler als NFR-006-Fehlerobjekte; 500 nur bei echten Defekten; der Konflikt-Dialog bietet den JSON-Download der ungespeicherten Operationen (kein Datenverlust). |

---

## 28. MVP

### 28.1 Umfang (MUST-Anforderungen mit „MVP = ja")

| # | Vorgabe aus dem Auftrag | Erfüllt durch |
|---|-------------------------|---------------|
| 1 | Garten anlegen | bestehende Site + GP-API-002 (UC-01) |
| 2 | Gartenfläche definieren | GP-FR-005/015, Boundary + Nordwinkel |
| 3 | Beete zeichnen | GP-FR-019/040, rect/circle/polygon |
| 4 | Beete verschieben und skalieren | GP-FR-021/022/023 (+ drehen GP-FR-008) |
| 5 | Metrische Maße anzeigen | GP-FR-004/014, Maßstabsbalken GP-FR-009 |
| 6 | Raster verwenden | GP-FR-011/012 |
| 7 | Beete speichern | GP-API-003 Batch mit Revision, GP-NFR-013 |
| 8 | Pflanzen einem Beet zuordnen | GP-FR-060–066, GP-API-020/023 |
| 9 | Pflanzen grafisch darstellen | GP-FR-067 |
| 10 | Einfache Pflanzabstände | GP-FR-062/063/073 (grid, rows, free) |
| 11 | Pflegeaufgaben erstellen | GP-FR-080–082 |
| 12 | Pflegeaufgaben als erledigt markieren | GP-FR-083–085, GP-API-031 |
| 13 | Pflegehistorie anzeigen | GP-FR-100–103/107, GP-API-034/038 |
| 14 | Responsive Bedienung | §17.1, Feldmodus GP-UX-020–023/025/027 |
| 15 | REST API | §21 (MUST-Zeilen) |
| 16 | Persistente Speicherung in ArangoDB | §20, Migrationen M1–M3, M5, M6 |

Zusätzlich im MVP, weil ohne sie das Obige nicht abnehmbar ist: Gartenobjekte `path`, `tree`, `building`, `fence`, `water_source`, `other` (Orientierung auf dem Plan); Undo/Redo (ohne es ist jeder Fehlklick ein Datenverlust); PDF/SVG-Export (REQ-032 §2.5 wartet darauf); JSON-Export (Sicherung) **und `replace`-Import mit Pflicht-Snapshot (Wiederherstellung, GP-FR-170, v1.3)**; Bodenprofil-Grundfelder (Beetfelder laut Auftrag §6); Beet-Nachbarschaft aus Geometrie (sonst läuft die bestehende Mischkultur-Engine für Beete leer); **nach Review (F-12, Betreiberentscheid):** Fruchtfolge-Hinweis auf Beet-Ebene mit Anbaupausen je Familie, Mischkultur-Hinweis im Dialog, Vorjahr am Beet (GP-FR-077/131/132), Beet räumen (GP-FR-055), Schnellprotokoll und Rückgängig im Feldmodus (GP-UX-029, GP-FR-149), Redaktion (GP-FR-109), Quoten und Pflicht-Audit.

### 28.2 Bewusst nicht im MVP (mit Begründung)

| Funktion | Prio | Begründung |
|----------|------|------------|
| Bewässerungszonen, Aktor-Kopplung, HA-Export (§14) | SHOULD/COULD | Fachlich eigenständig; der Plan funktioniert ohne Zonen. Zuerst muss die Beet-Ebene stehen, an der Zonen hängen. |
| JSON-Import, Vorlagen, Standardgrößen-Schnellwahl (§10, §23) | SHOULD | Export sichert die Daten; Import und Vorlagen sind Komfort und erzeugen eigene Validierungsfälle (`replace`-Semantik). |
| Mischkultur-Overlay, Rotationsmatrix, Folgekultur-Empfehlung (§16) | SHOULD | Die **Hinweise** sind im MVP (F-12); Overlay und Matrix sind Visualisierungen derselben Daten und folgen in Welle 8. |
| Bodenanalyse-Ereignisse, Nährstoff-Ampel, Flächendosierung (§15) | SHOULD | Flächendosierung hängt an REQ-004-Arbeit; die Ampel braucht ein begründbares Regelwerk (Agrobiologie-Review). |
| Offline-Lesen/-Puffern (GP-UX-024) | SHOULD | Zum MVP war UI-NFR-012 repo-weit nicht umgesetzt (kein Workbox); UI-NFR-012 wird in Welle 9 gebaut (E-06), der Plan ist der erste Offline-Fall des Repos (F-17 revidiert durch E-06). Im MVP: sichtbarer Offline-Hinweis und gesperrtes „Erledigt" statt stillem Verlust. **Stand v1.15:** Basis (WP 9.1), Offline-Lesen (WP 9.2) und Puffer für Erledigt/Notiz/Foto (WP 9.4) gemergt und abgenommen (§34); Geometrie bleibt online-only. |
| Vorgeschlagene Aufgaben (GP-FR-086) | SHOULD | Hängt an ADR-008 Phase 2 (Propagationskanten) — eigener Strang, nicht Teil von REQ-053; ADR-008 Phase 3 wird hier nur für den Task-Abschluss umgesetzt (E-02). |
| Objekt-Snap, Ausrichten/Verteilen, Messwerkzeug, Hintergrundbild | SHOULD/COULD | Editor-Komfort ohne fachlichen Mehrwert für die ersten Nutzer. |
| PNG, CSV | COULD/SHOULD | PDF/SVG decken Drucken und Weitergabe ab. GeoJSON ist gestrichen (GP-FR-146 WON'T, v1.4). |
| Konva-Renderer | bedingt | Erst bei gemessener Schwelle (GP-NFR-013); die Renderer-Grenze ist im MVP. |
| Echtzeit-Mehrbenutzer, persistente Gruppen, Sonnen-/Schattenberechnung | WON'T | §29 bzw. GP-FR-030 |

### 28.3 Priorisierte MVP-Anforderungsliste

Reihenfolge = Implementierungsreihenfolge (Abhängigkeiten), siehe §34.

1. GP-NFR-015: Migration M1 (Collections, Edges, Indizes, `dimensions`/`position` → Geometrie), M2 (`is_bed`, Seeds), M3 (TaskCategory), M5 (Cron → RRULE), M6 (NutrientDemand-Split); Entfernung der Altfelder samt Lesern
2. GP-FR-004–008, GP-NFR-012: `Geometry`-Typ, `geometry_calculator` (Fläche, bbox, Containment, Einfachheit) + Testvektoren
3. GP-API-001/002/003, GP-NFR-013/014, V-01–V-05, V-14, V-15, V-17, V-19: Plan lesen, Grenze, Batch
4. GP-API-010/013/014/015: Einzelressourcen
5. GP-NFR-003/005/006/009/010/011: Editor-Grundgerüst (Slice, Operationen, SVG-Renderer, Culling, Dynamic Import)
6. GP-FR-001–003, 009–015, 019–028, 031, 032, 150–156: Editor-Grundsätze, Werkzeuge, Raster, Snap, Undo/Redo, Panel, Kontextmenü, Interaktionsregeln §9.7
7. GP-UX-001–003, 005–013, 015–017, 032–038, 040, 043–052, 058–062: UX-Grundlagen, Konflikt-Dialog, testids, i18n, Touch/Gesten, Fokusmodell, Leerzustände, Pflanzeninfo und -zustände
8. GP-NFR-020–028, 065–070: Accessibility und Editor-Interaktions-NFRs (parallel zu 5–7, nicht danach)
9. GP-FR-040–043, 046–048, 050, 053, 055, 157, 160, GP-API-011/012/018/019: Beetverwaltung, Beetansicht, Beet räumen, Sonne/Schatten-Kacheln, Eignungs-Ampel
10. GP-FR-060–070, 072, 073, 077, 190–192, GP-API-016/020–025, 054, V-04, V-06–V-08: Pflanzplanung (mit Zeitfenster-Reservierung, Reihenzuweisung, Vorjahr), Pflanzeninfo als Mouseover und Pflanzenzustände
11. GP-FR-130–132, 137, 138/139: Adjacency, Fruchtfolge-/Mischkultur-Hinweis, NutrientDemand-Split
12. GP-FR-080–085, 088, GP-API-030–032, V-11: Beetpflege
13. GP-FR-100–103, 107, 109, 110a, 149, GP-API-033–038, 041, V-11–V-13, GP-NFR-055: Pflegeprotokoll, Redaktion, Historie, Rückgängig im Feldmodus
14. GP-FR-120/121: Bodenprofil
15. GP-UX-020–023, 025, 027, 029, 030, GP-API-017: Feldmodus mit Schnellprotokoll und Listen-Einstieg
16. GP-FR-140, 142, 143, 147, 170, GP-API-004/006/007: Export und `replace`-Import mit Pflicht-Snapshot
17. GP-NFR-017, 030–038, 040, 050–056, 058, 060–062, 064: Quoten, Performance-/Security-/Observability-Nachweise

---

## 29. Future Features

Alle als WON'T für dieses Vorhaben; das Datenmodell lässt sie zu, ohne dass heute etwas dafür gebaut wird.

| Funktion | Anknüpfungspunkt im Modell | Was fehlt |
|----------|---------------------------|-----------|
| Automatische Bewässerungsempfehlung | `irrigation_zones` + `irrigation_demands` (REQ-037) + `care_events(watering)` | Regelwerk „Bedarf − letzte Gabe − Niederschlag" |
| Wetterintegration | `Site.gps_coordinates`, REQ-046 Quellen | Niederschlag in die Verbrauchsbilanz |
| Bodenfeuchtesensoren | REQ-005 Sensoren an Locations | Zuordnung Sensor → Beet/Zone (GP-FR-118) |
| Home Assistant | `zone_actuated_by`, `ha_publish` | Entitätsvertrag (HA-Dokument) |
| NFC/RFID | Beet-QR (GP-FR-052) | NFC-Tag-URL = dieselbe Deep-Link-Route |
| Automatische Pflegeerinnerungen am Beet | `Task.suggested`, REQ-022 Engine | Beet-Profile (Intervalle je Beettyp/Saison) |
| Pflanzenkrankheitserkennung | REQ-036/038/044 am Foto | Foto-Zuordnung Beet → Pflanze (GP-FR-051) |
| Automatische Anbauplanung (Beetbelegung aus Pflanzenliste + Historie) | → **REQ-054** spezifiziert sie: deterministischer Optimierer mit harten Restriktionen, gewichteter Zielfunktion und Erklärung je Zuordnung; Ausgabe sind geplante Runs mit Zeitfenster (GP-FR-065) | nicht mehr WON'T hier, sondern eigene Anforderung nach dem REQ-053-MVP |
| Automatische Fruchtfolgeplanung | → REQ-054 (Kriterium `rotation`, Mehrjahresplanung AP-FR-009 als COULD) | — |
| Automatische Mischkulturplanung | → REQ-054 (Kriterium `companion`, Beet-Nachbarschaft); Zonen **innerhalb** eines Beets bleiben GP-FR-070 | — |
| Sonnen-/Schattenberechnung | `north_angle_deg`, `gps_coordinates`, GardenObject `tree.height_m`, `building` (Höhe COULD), `sun_calculator` | Schattenwurf-Geometrie, Stundenintegration → `sun_exposure` vorbelegen. **Jetzt angelegt (billig, später teuer):** `height_m` an `building`/`wall`/`fence`/`shrub`/`trellis`/`tree`, `ridge_height_m`, `crown_base_height_m`, `foliage`, `opacity`, `off_site` (§9.5); `Site.plan.terrain {slope_deg, aspect_deg}` und `Site.elevation_m` (optional, SHOULD); Frühbeet/Tunnel `cover_material`, `light_transmission_percent`; `Location.sun_exposure_source ∈ {manual, computed}` + `sun_hours_direct`; `sun_exposure`-Schwellen konfigurierbar (GP-FR-164; Standard `full_sun` > 6 h, `partial_shade` 3–6 h, `shade` 2–3 h, `deep_shade` < 2 h direkte Sonne am 21. Juni, H-006) |
| Ertrags-/Ernteplanung | `harvest_batches`, `area_m2`, `yield_per_m2_g` (REQ-007) | Prognose je Beet aus Historie |
| Echtzeit-Mehrbenutzer-Editing | `plan_revision` | CRDT/OT, WebSocket — bewusst nicht (Gartenpläne werden selten gleichzeitig bearbeitet) |
| Georeferenzierte Unterlage (Luftbild) | GP-FR-033 | Kachel-Quelle, Lizenz |

---

## 30. Akzeptanzkriterien

Alle Kriterien sind Given/When/Then; Tier in Klammern (U = Unit, I = Integration/API, E = E2E). TC-IDs stehen in `spec/e2e-testcases/TC-REQ-053.md` (44 Fälle + Abdeckungs-Matrix; U-/I-Kriterien dort unter „Nicht abgedeckte Akzeptanzkriterien" mit Testebene).

**Geometrie und Editor**

- **GP-ACC-001** (I) Given eine Outdoor-Site ohne Plan, When `PUT /plan/boundary` mit einem Rechteck 10 × 10 m und `north_angle_deg = 0` gesendet wird, Then antwortet die API 200 mit `plan_revision = 1`, `total_area_m2 = 100.0`, und `GET /plan` liefert die Grenze unverändert.
- **GP-ACC-002** (E) Given ein Garten 10 × 10 m, When der Nutzer mit dem Beet-Werkzeug ein Rechteck zieht, das nach Snap 2,0 × 1,0 m misst, und speichert, Then enthält `GET /plan` eine Location mit `geometry.width_m = 2.0`, `length_m = 1.0`, `area_m2 = 2.0`, And das Beet wird bei Zoom 100 % in genau dem Verhältnis 2:1 gerendert (SVG-`width`/`height` in Modelleinheiten).
- **GP-ACC-003** (U) Given ein Polygon mit den Punkten (0,0),(4,0),(4,3),(0,3), When `geometry_calculator.area()` aufgerufen wird, Then ist das Ergebnis 12,000; And für dasselbe Polygon mit `rotation_deg = 37` bleibt die Fläche 12,000 (±0,001).
- **GP-ACC-004** (U) Given ein Polygon mit Selbstschnitt (0,0),(2,2),(2,0),(0,2), When validiert wird, Then wird `geometry.self_intersecting` zurückgegeben.
- **GP-ACC-005** (I) Given ein Beet mit 12 Slots, When `update_geometry` das Beet um 1 m verschiebt und 90° dreht, Then bleiben alle 12 Slot-Geometrien im Datenbankdokument byte-identisch, And `GET /plan` liefert ihre Plan-Koordinaten transformiert (Stichprobe: Slot (0,0) landet auf `origin + R(90°)·(0,0)`).
- **GP-ACC-006** (E) Given ein gespeicherter Plan mit Raster 10 cm, When der Nutzer ein Beet mit der Maus um 23 cm nach rechts zieht, Then liegt die neue x-Koordinate auf einem Vielfachen von 0,10 m (hier +0,20), And bei gehaltener Alt-Taste bei genau +0,23.
- **GP-ACC-007** (E) Given ein Beet ausgewählt, When der Nutzer `Ctrl+Z` drückt, nachdem er es verschoben hat, Then steht das Beet an der ursprünglichen Position, der Speichern-Status zeigt „Ungespeicherte Änderungen (0)", And `Ctrl+Shift+Z` stellt die Verschiebung wieder her.
- **GP-ACC-008** (E) Given ein Beet ausgewählt und die Tastatur als einziges Eingabegerät, When der Nutzer Pfeil-rechts dreimal drückt, Then ist das Beet um 3 Rasterschritte verschoben, And die `aria-live`-Region hat die neue Position angesagt (Text enthält die Koordinate).
- **GP-ACC-009** (I) Given ein Garten mit Grenze 10 × 10 m, When ein Batch eine Location mit `origin = [9.5, 9.5]`, 2 × 1 m erzeugen will, Then antwortet die API 422 mit `details[0].code = geometry.outside_parent` und `op_index = 0`, And es wurde nichts persistiert (`plan_revision` unverändert).
- **GP-ACC-010** (I) Given zwei Nutzer mit demselben `expected_revision = 5`, When beide einen Batch senden, Then erhält der erste 200 mit `plan_revision = 6`, der zweite 409 `plan.revision_conflict` mit `current_revision = 6`, And die Operationen des zweiten sind nicht persistiert.
- **GP-ACC-011** (E) Given der 409 aus GP-ACC-010 im Browser des zweiten Nutzers, When der Konflikt-Dialog (`plan-conflict-dialog`) erscheint, Then bietet er „Neu laden" und „Meine Änderungen als Kopie behalten (JSON herunterladen)", And nach „Neu laden" zeigt der Plan Revision 6 und der Undo-Stapel ist leer.
- **GP-ACC-012** (I) Given ein Beet mit 2 aktiven Pflanzen, When `DELETE /locations/{key}`, Then 409 `location.has_active_plants` mit `details.active_plant_count = 2`.
- **GP-ACC-013** (I) Given ein Batch mit 501 Operationen, When gesendet, Then 422 `batch.too_many_operations`.
- **GP-ACC-014** (I) Given Tenant A besitzt Site S, When Nutzer aus Tenant B `GET /t/b/sites/S/plan` oder `POST /t/b/sites/S/plan/batch` aufruft, Then 404 in beiden Fällen, And kein Log-Eintrag `garden_plan.batch_applied`.

**Beetverwaltung**

- **GP-ACC-015** (I) Given ein Beet `active` ohne aktive Pflanzen, When `POST /locations/{key}/status {bed_status: "planned"}`, Then 422 `bed_status.invalid_transition`; When stattdessen `retired` mit `reason`, Then 200 And ein `care_event(category = bed_status_change)` existiert mit `reason`; And `GET /plan` liefert für das Beet `season_state = empty` — ein Beet ohne aktiven Run in der laufenden Saison ist `empty`, `fallow` erscheint nur mit einem `CropRotationPlan`-Eintrag `plan_role = fallow` für das Jahr (§7.4, nie als `bed_status`).
- **GP-ACC-016** (E) Given die Beetliste einer Site mit 3 Beeten, When der Nutzer eine Zeile anklickt, Then ist das Beet auf dem Plan selektiert und im Viewport (Bounding Box sichtbar).

**Pflanzplanung**

- **GP-ACC-017** (U) Given ein Rechteckbeet 3,0 × 1,2 m, `layout_strategy = rows`, `spacing_cm = 30`, `row_spacing_cm = 40`, `edge_margin_along_cm = 15`, `edge_margin_across_cm = 15`, When `compute_layout` läuft, Then entstehen 3 Reihen (y = 0,15/0,55/0,95) × 10 Positionen (x = 0,15 … 2,85) = 30 Positionen, And alle liegen innerhalb des Beets abzüglich Rand, And das TypeScript-Pendant liefert für denselben Vektor aus `garden-plan-vectors.json` dieselben 30 Punkte (±0,001).
- **GP-ACC-018** (U) Given ein Polygonbeet (Dreieck (0,0),(4,0),(0,3)), `grid`, 50 cm, Rand 0, When `compute_layout`, Then liegt jede Position innerhalb des Dreiecks (Point-in-Polygon), And keine außerhalb.
- **GP-ACC-019** (I) Given ein Beet mit Geometrie, When `POST /planting-runs` mit einem Entry (`quantity = 6`, `rows`, 60/80 cm) und `location_key` des Beets, Then existieren 6 Slots mit `slot_role = position` und `run_planned_at`-Edges mit `sequence 1..6`, And `GET /locations/{key}/plantings?state=planned` listet 6 geplante Positionen.
- **GP-ACC-020** (I) Given GP-ACC-019, When `POST /planting-runs/{key}/create-plants {assign_to_slots: true}`, Then existieren 6 `plant_instances` mit `slot_key` genau der geplanten Slots in `sequence`-Reihenfolge, And `state=planned` ist leer, `state=active` hat 6.
- **GP-ACC-021** (I) Given ein Slot ist für Run A (`planned`) reserviert, When Run B denselben Slot per `plan-slots` beansprucht, Then 409 `slot.already_planned`.
- **GP-ACC-022** (E) Given eine aktive Pflanze auf Position (0,30, 0,90) im Beet, When der Nutzer im Feldmodus „Position korrigieren" wählt und per Long-Press-Drag auf (0,60, 0,90) zieht, Then hat `Slot.geometry.origin = [0.60, 0.90]`, And in der Historie steht ein `care_event(category = position_corrected)` mit `plant_keys = [die Pflanze]`.
- **GP-ACC-023** (I) Given ein Beet mit Slots im Abstand 30 cm und `adjacency_factor = 1.5`, When ein Slot verschoben wird, Then existieren `adjacent_to`-Kanten genau zwischen Slots mit Zentrumsabstand ≤ 45 cm (beidseitig, `distance_cm` gesetzt), And eine Kante mit `source = manual` bleibt unverändert.

**Beetpflege und Historie**

- **GP-ACC-024** (I) Given ein Task `category = feeding`, `entity_type = location`, `entity_key = Beet`, When `POST /tasks/{key}/complete` mit `{product_ref: fertilizer X, quantity: 2, unit: "l_per_m2", plant_keys: [p1, p2]}`, Then ist der Task `completed`, And genau ein `care_event` existiert mit `task_key`, `category = feeding`, `quantity_total = 2 × area_m2` (gerundet auf 3 Stellen) und `quantity_total_unit = "l"`, `performed_by_user_key` = Aufrufer, `source_ref` auf ein neu erzeugtes `feeding_events`-Dokument, And beides liegt in einer Transaktion (Fehler beim `feeding_event` → Task bleibt `pending`, kein `care_event`).
- **GP-ACC-025** (I) Given `POST /tasks/{key}/complete` mit `performed_at` 10 Minuten in der Zukunft, Then 422 `care_event.performed_in_future`; mit `performed_at` vor 400 Tagen, Then 422 `care_event.too_old`.
- **GP-ACC-026** (I) Given ein `care_event` E1, When `POST /care-events/E1/supersede` mit korrigierter Menge, Then existiert E2 mit `supersedes_key = E1`, E1 hat `superseded_by_key = E2`, And `GET /care-events?location_key=…` liefert nur E2, mit `include_superseded=true` beide; When `PATCH /care-events/E1` versucht wird, Then 405 oder 422 `care_event.immutable`.
- **GP-ACC-027** (E) Given ein Beet mit 60 `care_events` über 2 Jahre, When der Nutzer den Tab „Historie" öffnet und nach Kategorie „Gießen" filtert, Then erscheinen nur Gieß-Ereignisse, paginiert zu 50, neueste zuerst, And der Zeitstrahl zeigt je Jahr die Familien der Pflanzungen.
- **GP-ACC-028** (I) Given Pflanzen in einem Beet 2024 (Solanaceae) und 2025 (Fabaceae), When `GET /locations/{key}/rotation?years=5`, Then enthält die Antwort je Jahr die Familie, `nutrient_demand` und `plan_role`.

**Feldmodus, Export, Accessibility, Performance**

- **GP-ACC-029** (E, Viewport 390 × 844) Given ein Beet mit einer offenen Aufgabe „Gießen", When der Nutzer das Beet antippt und im Sheet „Erledigt" tippt und ohne weitere Eingabe „Fertig" tippt, Then ist die Aufgabe `completed` mit genau 2 Tipps nach der Beetauswahl, And das Touch-Ziel „Erledigt" misst ≥ 64 × 64 px, And ein `care_event(category = watering)` ohne Menge existiert.
- **GP-ACC-030** (I) Given ein Plan mit Grenze 10 × 6 m und 3 Beeten, When `GET /print/garden-plan/{site}?paper=a4&orientation=landscape&scale=auto`, Then ist das PDF ≤ 5 s erzeugt, Maßstab 1:50 gewählt (10 m → 200 mm passen auf 277 mm), And ein Beet 2 × 1 m misst im PDF 40 × 20 mm (±0,5 mm, geprüft über das eingebettete SVG), And Maßstabsleiste, Nordpfeil und Legende sind vorhanden.
- **GP-ACC-031** (I) Given ein Plan mit 5 Beeten, 20 Slots, 3 Gartenobjekten, When `GET /plan/export` und anschließend `POST /plan/import {mode: "replace"}` in eine leere Site desselben Tenants, Then stimmen alle Geometrien, Namen, Typen und Bodenprofile überein (Diff ohne `_key`, Zeitstempel leer), And die Keys sind neu vergeben.
- **GP-ACC-032** (E) Given der Plan im Browser, When die Ansicht „Als Liste" aktiviert wird, Then sind alle Objekte als Liste mit Name, Typ, Position, Maßen erreichbar, And `vitest-axe` meldet keine Verstöße auf Editor und Liste.
- **GP-ACC-033** (U, Benchmark) Given ein Modell der Klasse „groß" (150 Beete, 300 Objekte, 3 000 Slots, 2 000 Pflanzen), When `applyOperation(move)` 100-mal läuft, Then ≤ 1 ms Median, And der SVG-Renderer rendert bei Viewport auf 10 % der Fläche ≤ 400 DOM-Objekte (Culling).
- **GP-ACC-034** (I, Benchmark) Given dieselbe Klasse „groß" in ArangoDB, When `GET /plan` 20-mal läuft, Then p95 ≤ 300 ms und Antwort ≈ 1 MB unkomprimiert (≤ 1 000 000 Bytes, GP-NFR-031).
- **GP-ACC-035** (I) Given ein Beet ohne Geometrie (Bestandsdaten), When `GET /plan`, Then erscheint es in `locations` mit `geometry = null` und bleibt in der Beetliste; When der Nutzer ihm eine Geometrie gibt, Then wird `area_m2` überschrieben; And Bestands-Locations mit `dimensions ≠ (0,0,0)` haben nach M1 eine `rect`-Geometrie mit diesen Maßen und `height_m`.
- **GP-ACC-036** (E) Given eine Indoor-Site mit einer Location `tent` 1,2 × 1,2 m und 9 Slots, die M1 aus `position` (3 × 3, `pitch_m = 0.3`) abgeleitet hat, When der Nutzer die Beetansicht öffnet und den mittleren Slot per Drag um 10 cm nach rechts verschiebt, Then liegt `geometry.origin` bei `(0.40, 0.30)`, And Ansicht, Werkzeuge und Historie sind identisch zur Beetansicht eines Outdoor-Beets (gleiche Komponenten, kein Zelt-Sonderpfad — nachweisbar über denselben `data-testid`-Satz).
- **GP-ACC-037** (I) Given eine Familie mit `typical_nutrient_demand = "heavy"` vor M6, When die Migration läuft, Then steht dort `heavy_feeder`; And `PUT /botanical-families/{key}` mit `typical_nutrient_demand = "fallow"` antwortet 422; And `CropRotationPlan.demand_level = "green_manure"` ist danach `plan_role = green_manure` mit `nutrient_demand = null`.
- **GP-ACC-038** (I) Given ein Task mit `recurrence_rule = "0 8 * * 1"` vor M5, When die Migration läuft, Then ist die Regel `FREQ=WEEKLY;BYDAY=MO;BYHOUR=8;BYMINUTE=0`, And `POST /tasks` mit einer Cron-Regel antwortet 422 `recurrence.rrule_required`.
- **GP-ACC-039** (I) Given ein Slot mit Reservierung Run A `planned_from = 2026-05-15`, `planned_until = 2026-09-30`, When Run B denselben Slot mit `planned_from = 2026-10-05` beansprucht, Then 200 (Nachkultur); When Run C mit `planned_from = 2026-08-01`, Then 409 `slot.already_planned` mit `overlap_from = 2026-08-01`, `overlap_until = 2026-09-30`.
- **GP-ACC-040** (I) Given ein Beet mit 2 aktiven Runs und 12 Pflanzen, When `POST /locations/{key}/clear {termination_type: "senesced"}`, Then sind alle 12 Pflanzen `removed_on = heute`, beide Runs `completed`, 12 Slots `archived_at` gesetzt, ein `care_event(clearing)` existiert; And ein neuer Run im Beet mit Zonen-Layout wird **nicht** durch V-06 gegen die archivierten Slots abgewiesen.
- **GP-ACC-041** (I) Given Tenant B besitzt Pflanze P, When Tenant A `POST /t/a/care-events {plant_keys: [P], …}` sendet, Then 422 `reference.not_found`, And kein `care_event_for`-Edge auf P; dasselbe für `slot_keys` in `plan-slots`, `location_keys` in Zonen, `photo_refs` mit fremdem Attachment, `supersedes_key` auf fremdes Event, `water_source_key` auf fremdes Objekt.
- **GP-ACC-042** (I) Given ein Gärtner (nicht Leitung), When er `POST /plan/batch` mit `[{op: "update_geometry", …}, {op: "delete", entity: "location", key: …}]` sendet, Then 403 `batch.operation_forbidden {op_index: 1}`, And auch die erste Operation ist nicht persistiert.
- **GP-ACC-043** (I) Given ein Beet 1 000 × 1 000 m, When `planting-layout/preview` mit `spacing_cm = 5`, Then 422 `layout.too_many_positions` mit `estimated ≈ 4e8`, And die Antwortzeit ist < 50 ms (Vorab-Schätzung, keine Punkterzeugung).
- **GP-ACC-044** (I) Given ein `care_event` E1 mit `summary = "Nachbarin Frau Müller hat gegossen"` und zwei Fotos, superseded durch E2, When die Leitung `POST /care-events/E2/redact {reason}`, Then enthalten E1 und E2 `summary = "[redacted]"`, `photo_refs = []`, `redacted_by` = Leitung, die beiden Attachments sind gelöscht, And `garden_plan_audit` hat einen Eintrag `op = redact`.
- **GP-ACC-045** (I) Given ein Beet mit `name = '"><image href="http://169.254.169.254/"/>'`, When `GET /plan/render.svg` und `GET /print/garden-plan/{site}`, Then enthält das SVG kein `<image>`-Element und den Namen escaped als Text, And der Test-`url_fetcher` protokolliert keinen Abruf; dasselbe für `file:///etc/passwd` im Namen.
- **GP-ACC-046** (I, revidiert v1.4/E-01) Given Location L von Tenant A, When `garden_plan_service` (und jede andere Service-Methode dieses Dokuments) L mit `tenant_key = B` auflöst (`resolve_owned_location(source, L, tenant_key=B)`), Then `NotFoundError` → 404 ohne Body-Details, And das gespeicherte Dokument von L, von Slots und von GardenObjects trägt **kein** Attribut `tenant_key` (Guard: ein Inventar-Test über die Pydantic-Modelle `Location`, `Slot`, `GardenObject` und ein AQL-Scan im Integrationstest), And der Guard `tests/unit/guards/test_keyed_service_writes_take_the_tenant.py` listet `garden_plan_service`, `care_event_service`, `irrigation_zone_service`.
- **GP-ACC-047** (E) Given ein Beet, in dem 2025 Brassicaceae standen und `rotation_pause_years(Brassicaceae) = 4`, When der Nutzer 2026 „Bepflanzen" mit Blumenkohl öffnet, Then zeigt der Dialog vor der Layout-Wahl einen Fruchtfolge-Hinweis mit Grund und Stärke, And „Trotzdem pflanzen" verlangt einen Grund, der am Run als `rotation_override_reason` gespeichert wird, And das Beet trägt danach ein Badge.
- **GP-ACC-048** (E, 390 × 844) Given das Beet-Sheet im Feldmodus, When der Nutzer den Chip „Gejätet/Gemulcht" tippt, Then existiert nach einem Tipp ein `care_event(category = weeding)` mit `trigger = manual`, And eine Snackbar „Rückgängig" ist 8 s sichtbar; When er sie tippt, Then ist das Event `voided_at` gesetzt mit `void_reason = undo`.
- **GP-ACC-049** (U) Given die Familie Fabaceae mit `nitrogen_fixing = true` und die Spezies Erbse mit `nutrient_demand = light_feeder`, When M6 auf einem Bestand mit `nutrient_demand_level = nitrogen_fixer` läuft, Then hat die Spezies `nitrogen_fixing = true` und `nutrient_demand` aus dem Steckbrief (oder `null` + Eintrag im Dry-Run-Report), And `PUT /species/{key}` mit `nutrient_demand = "fallow"` oder `"nitrogen_fixer"` antwortet 422.

- **GP-ACC-050** (U) Given eine Pflanze in der Phase Blüte mit zwei überfälligen Aufgaben und einem offenen Befund, When `plant_state_calculator.compute` läuft, Then ist `lifecycle = active`, `attention = [problem, overdue]` (Priorität nach GP-UX-060) und das Frontend-Port liefert für dieselben Eingaben identische Werte.
- **GP-ACC-051** (E) Given ein Beet mit 40 Pflanzen, When der Nutzer 300 ms über einen Marker verweilt, Then erscheint die Pflanzen-Info (Art, Phase mit Fortschritt, Alter, nächste Aufgabe, Handlungsbedarf) **ohne** zusätzlichen Netzwerkaufruf, bleibt beim Wechsel des Zeigers in die Blase sichtbar und verschwindet mit Esc; dieselbe Information ist per Tastaturfokus und als `aria-label` verfügbar.
- **GP-ACC-052** (E) Given Pflanzen im Zustand geplant, gesät, aktiv, in Ernte und ausgefallen, When der Plan in Graustufen und mit simulierter Rot-Grün-Schwäche gerendert wird, Then sind alle fünf Zustände weiterhin unterscheidbar (Ring-Stil und Badge-Form, nicht nur Farbe).

**Nachtrag 2026-10-16 (Spec-Readiness-Review)**

- **GP-ACC-053** (U) Given die gemeinsamen Testvektoren für `site_fit_calculator.compute(sun_exposure, light_requirement, shade_tolerance)` (§19.6), When Python und TypeScript-Port je Vektor laufen, Then liefern beide identische Werte für mindestens diese Fälle: Anspruch `full_sun` auf `shade`-Beet → `poor` (zwei Stufen schattiger); Anspruch `full_sun`, Beet `partial_shade`, `shade_tolerance = partial_shade` → `marginal` (eine Stufe schattiger, Toleranz deckt); Anspruch `full_sun`, Beet `partial_shade`, `shade_tolerance = null` → `marginal` mit Begründung „Toleranz unbekannt" (GP-FR-160); Anspruch `shade`, Beet `full_sun` → `poor` (zwei Stufen sonniger); `sun_exposure = unknown` oder `light_requirement = null` → `unknown`.
- **GP-ACC-054** (I) Given ein Rechteckbeet mit 5 Reihen (Indizes 0-basiert, `0`–`4`) und ein Run mit zwei Entries (Tomate `row_assignment = [0, 2, 4]`, Basilikum `row_assignment = [1, 3]`), When `POST /planting-runs` die Slots erzeugt (GP-FR-070), Then sind die `row_assignment`-Mengen der Entries disjunkt (Überschneidung → 422), And jeder Slot einer Reihe trägt über `run_planned_at.entry_key` genau den Entry, dem die Reihe zugewiesen ist, And ein Run mit `row_assignment = [1, 2]` und `[2, 3]` antwortet 422.
- **GP-ACC-055** (I) Given je eine Location vom Typ `planter`, `tent` und `shelf` mit Pflanzhistorie (2025 Solanaceae), When `validate-planting` 2026 mit einer Solanaceae-Art läuft (GP-FR-137), Then enthält die Antwort **keinen** Fruchtfolge-Hinweis; When die Fruchtfolge für genau eine dieser Locations je Beet eingeschaltet wird, Then liefert nur diese den Hinweis.
- **GP-ACC-056** (I) Given eine Site, When `PUT /plan/boundary` mit einem Polygon gesendet wird, dessen Punkt `x = 1000.5` m beträgt (GP-FR-013), Then antwortet die API 422 `geometry.invalid` mit dem Punktindex in `details`, And `plan_revision` ist unverändert; mit `x = 1000.0` antwortet sie 200.
- **GP-ACC-057** (I) Given Tenant A mit 120 `care_events` über 200 Tage und Tenant B mit eigenen Events, When ein Mitglied von A `GET /t/a/care-events` ohne Filter aufruft (GP-FR-107), Then enthält die Antwort nur Events von A mit `performed_at` innerhalb der letzten 90 Tage, paginiert (Seitengröße 50 wie GP-ACC-027, Folgeseite abrufbar), neueste zuerst, And kein Event von B.
- **GP-ACC-058** (I, E-12) Given ein Beet, When `PUT` mit `rotation_deg = -1` gesendet wird, Then 422 `geometry.invalid`; And `rotation_deg = 359.9996` wird als `0.0` gespeichert; And ein Slot-Punkt mit `x = -1000` im Beet-Rahmen wird angenommen, `x = -1000.5` mit 422 abgelehnt; And ein Polygon dreht um `points[0]` (Vektoren `bbox-polygon-002`/`transform-004`).
- **GP-ACC-059** (I, E-14) Given Tasks mit `recurrence_rule = "0 8 * * 1"` und einer nicht konvertierbaren Cron-Regel, When M5 läuft, Then ist die erste Regel RRULE, And die zweite steht in `recurrence_rule_unconvertible` mit `recurrence_rule = null`, And der Dry-Run-Report listet jede geparkte Regel, And die Migrationskette läuft weiter.
- **GP-ACC-060** (I, E-13) Given ein Batch-Request mit Body > 1 MiB, When `POST /plan/batch`, Then 413 `body_too_large` vor jeder Operationsprüfung; And 500 Operationen unter 1 MiB werden regulär geprüft.
- **GP-ACC-061** (I, #2513) Given ein Standort mit einem Beet, einem Gartenobjekt, einer Bewässerungszone, einem Pflegeereignis und einer aktiven Pflanze (`removed_on = null`), When `DELETE /sites/{key}`, Then 409 `site.has_active_plants` mit `details[0].active_plant_count = 1` und nichts ist gelöscht; And When die Pflanze `removed_on` trägt und der Aufruf wiederholt wird, Then sind Beet, Slots, Gartenobjekt, Zone und alle ihre Kanten entfernt, das Pflegeereignis und die vorherigen Audit-Zeilen bestehen weiter, und genau eine neue Audit-Zeile `{op: delete, entity: site}` existiert.

**Welle 9 (v1.13; seit der Abnahme v1.15 alle drei mit Test)**

- **GP-ACC-062** (I, WP 9.9 #2749) Given eine eigene Beetvorlage, When `GET /bed-templates/{key}/export` (GP-API-070), Then enthält die Datei `schema_version`, Geometrie, Standardgrößen und Pflanzraster; And weder `tenant_key` noch `created_by` noch eine Notiz (Negativsuche im Test); And `POST /bed-templates/import` mit genau dieser Datei ergibt eine gleiche Vorlage (Roundtrip).
- **GP-ACC-063** (I, WP 9.9 #2749) Given eine Importdatei, When `POST /bed-templates/import` (GP-API-071), Then > 256 KB → 413; And ein Schemafehler oder eine ältere als die Vorgänger-`schema_version` → 422; And ein vorhandener Name → 409 mit Namensvorschlag; And Keys aus der Datei werden ignoriert; And `dry_run=true` schreibt nichts.
- **GP-ACC-064** (I, WP 9.10 #2750) Given eine Site mit zugewiesenen Beeten, When `GET /print/garden-plan/{site_key}?parcel_list=true` (GP-API-007), Then enthält das PDF eine Parzellenliste mit Kennung (Beetname + laufende Nummer), Fläche und Zone, aber **keine** Personenspalte; And erst mit `include_assignment=true` erscheint die Zuweisung (Prüfung über den Textlayer des PDF); And ohne `parcel_list` fehlt die Seite.

---

## 31. Risiken

| ID | Risiko | Eintritt | Auswirkung | Gegenmaßnahme |
|----|--------|----------|------------|---------------|
| R-01 | SVG-Renderer skaliert nicht bis zur Belastungsgrenze (5 000 Pflanzen) | mittel | Ruckeln beim Pan auf großen Plänen | Renderer-Grenze (GP-NFR-009) + Culling + Benchmark GP-ACC-033; Konva als zweiter Renderer hinter derselben Schnittstelle |
| R-02 | Logik-Drift zwischen Python- und TypeScript-Layout-Rechner | mittel | Vorschau ≠ gespeichertes Ergebnis | gemeinsame Testvektoren (§19.6), Server maßgeblich |
| R-03 | Zweite Schreibstelle `care_events` driftet von Fachcollections | mittel | Historie unvollständig | Atomarität im Abschluss-Übergang, Konsistenz-Job (GP-FR-105), Metrik |
| R-04 | Cron→RRULE-Migration (O-05) trifft nicht konvertierbare Ausdrücke | mittel | Einzelne Regeln ohne RRULE-Äquivalent | Dry-Run-Report vor dem Lauf; nicht konvertierbare Regeln werden nach `recurrence_rule_unconvertible` geparkt (E-14), `recurrence_rule = null`, und manuell übersetzt; ADR-008 ist mit Welle 0 Accepted |
| R-05 | Bundle-Budget (Ist 343 KB bei 300 Ziel) | hoch | CI rot | Dynamic Import, 0 KB Initial-Zuwachs, eigener Chunk mit Budget (GP-NFR-003) |
| R-06 | Touch-Konflikte (Pan vs. Drag) auf Mobil | mittel | Frust im Feldmodus | Long-Press-Regel (GP-UX-008), E2E auf 390 px |
| R-07 | Polygon-Containment/Überlappung ohne Geometrie-Lib fehlerhaft bei konkaven Formen | mittel | falsche 422 oder stille Überlappung | Property-Tests; Shapely als COULD (D-04), falls Fälle auftreten |
| R-08 | Bestandsbeete ohne Geometrie (`dimensions = (0,0,0)`) und Alt-Slots mit falscher `pitch_m`-Annahme | sicher | Plan zeigt nicht alle Beete; Zelt-Slots liegen zu eng/weit | GP-ACC-035: Locations ohne Geometrie bleiben in Listen, Plan bietet „auf dem Plan platzieren"; `geometry_source = migrated_grid` wird im Editor als „geschätzt" markiert, bis der Nutzer die Location einmal speichert |
| R-09 | Locations ohne `tenant_key` → Tenant-Leck über Slot-/Geometrie-Endpunkte, wenn ein Service den Site-Anker auslässt | mittel | Datenleck | §22.3 (T-01…T-04), `location_ownership` als einziges Prädikat, Negativtests GP-ACC-014/041/046 je Endpunkt und je Body-Feld, Guard `test_keyed_service_writes_take_the_tenant.py` um die neuen Services erweitert (v1.4 — das Stempeln von `tenant_key` wurde mit #2107 als eigene Leck-Quelle verworfen) |
| R-10 | Enum-Erweiterung `TaskCategory` kollidiert mit Frontend-Mappings/i18n | mittel | Startup-/Render-Fehler | additive Migration, i18n-Vollständigkeits-Check (`i18n-completeness-checker`) |
| R-11 | Accessibility-Anspruch (Liste + Tastatur + aria-live) verdoppelt UI-Aufwand | hoch | Zeit | Liste ist zugleich mobile Fallback und Test-Oberfläche; früh bauen (Welle 2) |
| R-12 | ADR-007 (Breakpoints Code ≠ UI-NFR-001) offen | niedrig | Layout-Umschaltpunkte uneinheitlich | Feldmodus an `useMediaQuery(theme.breakpoints.down('sm'))` binden, nicht an Pixelzahlen |
| R-13 | `calculate_plants_per_m2` und `print_engine` werden von Bestandscode genutzt; die Erweiterungen (Reihenabstand, `url_fetcher`) ändern Verhalten außerhalb von REQ-053 | sicher | bestehende Tests/`/print/*` betroffen | eigene Issues (Anhang A, 6d/6e) mit Regressionstests vor Welle 1; `url_fetcher` ist eine Sicherheitskorrektur und geht zuerst |
| R-14 | `nutrient_demand` ist für viele Spezies im Steckbrief nicht erfasst → M6 lässt `null` | hoch | Fruchtfolge-Hinweise ohne Zehrerstufe | Dry-Run-Report als Arbeitsliste für `plant-info-document-generator`; Hinweis funktioniert familienbasiert auch ohne Spezieswert |

---

## 32. Offene Fragen — entschieden am 2026-10-04

Alle Punkte wurden vom Betreiber entschieden; die Tabelle bleibt als Protokoll stehen. Spalte „Eingearbeitet" nennt die Stelle, an der die Entscheidung im Dokument wirkt.

| ID | Frage | Entscheidung | Eingearbeitet |
|----|-------|--------------|---------------|
| O-01 | `Slot.position` für Beet-Slots füllen? | **Kein zweites Positionsmodell.** Zelt und Beet laufen auf `Slot.geometry`; `position` wird migriert und entfernt. | §9.2a, §20.5, §20.8, GP-ACC-036, M1 |
| O-02 | Wann `Location.dimensions` entfernen? | **Sofort in Welle 1** — Migration übernimmt (l, b) als Geometrie, h als `height_m`; keine Spiegelung. | §20.8, GP-ACC-035, Issue 56 |
| O-03 | Geometrie-Snapshots im MVP? | **Nein**, nur `garden_plan_audit` (SHOULD); Snapshots COULD mit Import-Welle. | §20.13, GP-FR-148 |
| O-04 | Beete mit Kind-Locations? | **Nein** — Reihen und Zonen sind Slots (`slot_role`). | R-7.5, D-10 |
| O-05 | ADR-008-Status | **Accepted in Welle 0**, RRULE kanonisch, Cron-Bestand per M5 konvertiert, REQ-006 umgestellt. **Präzisiert (E-02, 2026-10-15):** Phase 3 nur für den Task-Abschluss in Welle 4; Kadenz-Vorschübe bleiben eigener Strang. | §12.2, GP-NFR-015, GP-ACC-038, Issue 5 |
| O-06 | Kante für care_events → Pflanze | **`care_event_for` wiederverwenden**, Edge-Definition um `care_events` erweitern. | §20.10, §20.14 |
| O-07 | Zehrer-Enums | **In REQ-053 lösen** — zunächst als 6-Werte-Enum, nach K-001 revidiert zu `NutrientDemand` (3) + `nitrogen_fixing` + `PlanRole`; REQ-001/REQ-002 ziehen nach; M6. | §16.3 (GP-FR-138/139), GP-ACC-037/049 |
| O-08 | Indoor-Sites auf dem Plan? | **Ja, für alle Site-Typen** (Folge von O-01); V-18 entfällt. | §2.3, §9.2a, §22.2 |
| O-09 | `shelf` als Beet? | **Nein** — nur `bed`, `raised_bed`, `planter`, `greenhouse_bed`, `cold_frame`. | GP-FR-040 |
| O-10 | Polygon-Zeichnen auf Smartphone | **Zulassen, nicht abnehmen.** | §17.1 |
| O-11 | Quelle für `spacing_cm_default` | **Steckbrief-Pipeline erweitern** (Schema, Vorlage, `plant-info-to-seed-yaml`, Validator). | GP-FR-061, Issue 57 |
| O-12 | PDF-Standard | **A4 quer, Maßstab automatisch**; A3 und fester Maßstab wählbar. | GP-FR-142 |
| O-13 | Durchfluss-Quelle der Zone | **Manuell mit optionaler HA-Überschreibung**, Provenienz am Verbrauchswert. | §14.1, GP-FR-114, §20.11 |
| O-14 | Fremde `care_events` korrigieren | **Eigene ab Gärtner, fremde nur Leitung.** | §21.8, GP-API-036 |
| O-15 | Modulname und Navigation | **`garden_planner`, unter „Standorte"**, kein eigener Hauptmenüpunkt. | §21.8, Issue 41 |
| K-001 | `nitrogen_fixer` im Zehrer-Enum (Review Agrobiologie) | **O-07 revidiert:** 3 Stufen + Bool + `PlanRole`. | §16.3, GP-FR-138/139, GP-ACC-049 |
| SR-022 | `tenant_key` auf Location/Slot (Review Security) | ~~Ja, M1.~~ **Revidiert 2026-10-15 (E-01):** nein — #2107/MT-010 (v0087) hat das Feld entfernt, die Site ist der einzige Eigentümer; Prädikat `location_ownership`. | §20.4, §20.13, §22.3, GP-ACC-046, R-09, D-18 |
| F-12 | Fruchtfolge/Mischkultur im MVP (Review Persona) | **Ja, Hinweise + Vorjahr.** | GP-FR-077/131/132, §28 |
| F-09/F-17 | Revision je Objekt / Offline-Puffer (Review Persona) | **Revision nur für Struktur; Offline-Puffer SHOULD, Offline-Hinweis MVP.** | GP-NFR-007, GP-UX-024 |
| SR-005 | Retention `care_events` (Review Security) | **5 Jahre.** | GP-NFR-055, NFR-011 |
| SR-020 | `performed_by`-Filter (Review Security) | ~~Alle Rollen~~ — **revidiert am 2026-10-18 (E-16, v1.6):** Betrachter/Gärtner nur auf sich selbst, Leitung und `management` auf jedes Mitglied. | GP-API-034 |
| F-01/F-02 | Reservierung ohne Zeitfenster, kein Saisonwechsel (Review Persona) | **Modellkorrektur eingearbeitet.** | GP-FR-055/065, V-06/V-08, GP-ACC-039/040 |
| W-014 | Beetstatus mischt Lebenszyklus und Saison (Review Agrobiologie) | **Getrennt.** | §7.4, D-19 |

Es gibt (Stand v1.2) keine offenen Fragen mehr, die die Implementierung des MVP blockieren; die Fragen aus v1.3 stehen in §32.1 (alle entschieden). Neue Fragen, die während der Umsetzung entstehen, werden als Issue mit Label `spec:REQ-053` erfasst, nicht hier nachgetragen.

### 32.1 Fragen aus v1.3 (2026-10-11)

| ID | Frage | Entscheidung | Eingearbeitet |
|----|-------|--------------|---------------|
| O-16 | Skala `sun_exposure` um `deep_shade` erweitern? | **Ja, ergänzt** (Feld neu, keine Migration). **Semantik entschieden 2026-10-15 (E-05):** `Species.shade_tolerance` bleibt **Toleranz** („verträgt Schatten bis Stufe X"); neues `Species.light_requirement ∈ {full_sun, partial_shade, shade}` ist der **Anspruch**. `site_fit` vergleicht `sun_exposure` mit `light_requirement`; `shade_tolerance` liefert die Gelb-Zone (`marginal`). Steckbrief-Vorlage, Schema und Seeds erhalten `light_requirement` (Welle 0, Issue 57/77). | GP-FR-061/157/160, §10.1, REQ-001 |
| O-17 | Fachprüfung der Sonnenklassen-Schwellen, des Bezugsdatums und der Erreichbarkeits-Richtwerte | ~~Später.~~ **Welle 0 (E-10):** `agrobiology-requirements-reviewer` mit Websuche, Quelle je Wert, Bericht `spec/analysis/agrobiology-thresholds-req-053.md`; Werte ohne belastbare Quelle bleiben `unverified` und konfigurierbar. | GP-FR-164/166 |
| O-18 | `replace`-Import + Pflicht-Snapshot in den MVP? | **Ja.** | GP-FR-170 |
| O-19 | Hintergrund-Unterlage als SHOULD? | **Ja**; Georeferenzierung bleibt COULD. | GP-FR-033 |
| O-20 | „Neue Saison aus Vorjahr“ | **Datenkopie in REQ-053**, Belegungsvorschläge in REQ-054; gilt auch für Indoor. | GP-FR-171 |
| O-21 | GeoJSON-Export streichen? | ~~Nein, bleibt COULD.~~ **Revidiert 2026-10-15 (E-06): ja, gestrichen** — GP-FR-018 und GP-FR-146 sind WON'T. | GP-FR-018/146, §8, §28.2, §34 |
| O-22 | Umfang des Indoor-/Wohnungs-Grundrisses (§9.8) und seine MVP-Zugehörigkeit | **SHOULD, nicht MVP.** Dieselben Zeichenfunktionen wie im Garten auch für Wohnung/Indoor, aber erst nach dem MVP. | §9.8 |

### 32.2 Entscheidungen zum Implementierungsstart (2026-10-15, v1.4)

Vollständig ausformuliert in `.audits/plans/req-053-garden-bed-planning-implementation.md` §5; hier das Protokoll mit Wirkungsort.

| ID | Entscheidung | Eingearbeitet |
|----|--------------|---------------|
| E-01 | **#2107 gilt:** kein `tenant_key` auf `locations`/`slots`/`garden_objects`; Site-Anker über `location_ownership`. `care_events`, `irrigation_zones`, `bed_templates`, `garden_plan_audit` tragen `tenant_key`. Hebt SR-022/D-18 auf. | §20.4, §20.13, §20.14, §22.3, GP-ACC-046, R-09, §33, Anhang 6f |
| E-02 | **ADR-008 → Accepted**, Phase 3 nur für den Task-Abschluss (`complete_task`, `tasks/batch/status`, `reopen`); Kadenz-Vorschübe eigener Strang. | §12.2, O-05, §34 Welle 4 |
| E-03 | Scope der autonomen Umsetzung: **alle Wellen 0–10**. | §34 |
| E-04 | Merge-Autonomie wie Issue-Lauf 2026-10-09 (kein `--admin`, keine Budget-Anhebung). | Plan §2 |
| E-05 | `shade_tolerance` = Toleranz; neues `Species.light_requirement` = Anspruch; `site_fit` im MVP. | GP-FR-061/160, O-16, REQ-001 |
| E-06 | Welle 9 baut die **UI-NFR-012-Basis** (Workbox) + Plan-Offline; **GeoJSON gestrichen**. | GP-FR-018/146, GP-UX-024, §8, §28.2, §34, O-21 |
| E-07 | Deploy nur bis `develop` + Dev-Cluster; Prod-Rollout durch den Betreiber an Freigabepunkten P-1…P-5. | Plan §8 |
| E-08 | Welle 0 in der Planungssession; ab Welle 1 je Arbeitspaket ein Worktree mit frischer Session, max. 3 Lanes. | Plan §2, §9 |
| E-09 | Issues je Welle beim Wellenstart. | Anhang A |
| E-10 | Agronomische Werte durch Agenten mit Websuche, **Quelle je Wert**, sonst `null`. | GP-FR-061, O-17 |
| E-11 | M4 Backfill in Welle 8. | GP-NFR-015, §34 |

### 32.3 Entscheidungen vom 2026-10-18 (v1.5)

Vollständig in `.audits/plans/req-053-garden-bed-planning-implementation.md` §5.

| ID | Entscheidung | Eingearbeitet |
|----|--------------|---------------|
| E-12 | **Geometrie (#2333):** Beet-Rahmen ±1 000 m, Plan-Rahmen 0…1 000 m; Polygon-Pivot = erster Punkt; negatives `rotation_deg` abgelehnt, Rundung auf 360,000 wrappt auf 0,0; GP-NFR-012 bleibt unverändert (Property-Tests mit Hypothesis). | GP-FR-008, §9.2, §20.1, V-01 |
| E-13 | **Response-Budget (#2349):** „groß" ≈ 1 MB unkomprimiert, 500-Objekte-Quote bleibt hart; Pflanzen paginiert bzw. per `include=`; Body-Grenze 1 MiB (413 `body_too_large`); kein eigenes Wire-Format, kein gzip-Verlass. | GP-NFR-031, §25.2, GP-NFR-013 |
| E-14 | **M5 parken (#2346):** nicht konvertierbare Rules → `recurrence_rule_unconvertible`, `recurrence_rule = null`, Report listet alle, Migrationskette läuft weiter. | §12.2 |
| E-15 | **Steckbrief-Datenregeln (#2371):** Quellenlage entscheidet; quellenbelegtes `nutrient_demand` schlägt `nutrient_demand_level`; Obst-Reihenabstände ohne Hausgarten-Quelle `null`; schwach belegte Werte `confidence: low`. | §16.3, §10.2 |
| E-16 | **Folgeentscheidungen (#2411):** `performed_by`-Filter rollenabhängig (Betrachter/Gärtner nur auf sich selbst; Leitung und `management` auf jedes Mitglied); Pflegeprotokoll ist kein PflSchG-§11-Nachweis; Freitexte gelöschter Mitglieder bleiben in geteilten Mandanten wie bei `plant_diary_entries`; ein neuer RRULE leert `recurrence_rule_unconvertible` (kein API-Feld, keine Benachrichtigung). | GP-API-034, SR-020, D-22, §13.2, GP-NFR-055, §12.2 |
| E-17 | **EC-Skalierung / `nutrient_demand_level` (#2411), Vorentscheidung, ersetzt durch die Zeile „E-17 (Ergebnis)“ darunter:** nicht jetzt; gehört in Welle 8 (Bodenanalyse und Düngung) mit agrobiologischer Prüfung. | §15, §16.3 |
| E-17 (Ergebnis) | **ENTSCHIEDEN am 2026-11-03: Variante A** (Betreiberantwort #2643 Frage 1; Grundlage `spec/analysis/agrobiology-req-053-wave8-ec.md`, F-001). **Keine EC-Skalierung nach Zehrerstufe für Boden und Beet.** Die Zehrerstufe steuert nur den Hinweistext in GP-FR-125 und die Fruchtfolge. Die Boden-`ec_ms_cm` liefert nur einen Salz-Grenzwert-Hinweis, ausgewertet je `ec_method` (§15.1); die Schwelle ist konfigurierbar, Default `null` (kein Hinweis, bis eine Quelle vorliegt, E-10). Die ungenutzte Tabelle `_FEEDER_EC_FACTOR` im Code entfällt (WP 8.11, startet nach WP 8.5). Die EC-Skalierung für Nährlösung und Substrat bleibt phasenbasiert (REQ-004-A). | §15, §16.3, GP-FR-125 |

### 32.4 Antworten auf die Platzhalter der Welle 7 (2026-10-19, #2466; v1.9)

Der Betreiber hat am 2026-10-19 die Platzhalter des Bündels #2466 beantwortet: Punkte 1–7, 9–11 und 13–15 sind bestätigt, wie umgesetzt; Punkt 8 ist entschieden (kein `create_slot`); Punkt 12 ist mit #2512 entschieden. Dazu kommen drei Fragen aus WP 7.1. Die Tabelle nennt den gültigen Stand und wo er eingearbeitet ist.

| Pkt. | Thema | Entscheidung (gilt) | Eingearbeitet / Stand im Code |
|------|-------|---------------------|-------------------------------|
| 1 | Verteilung der Gießrunde (GP-FR-117 ↔ GP-API-053) | `allocation = by_area \| equal`; `by_demand` erst, wenn der Zonenbedarf (WP 7.5) existiert. Beete ohne Fläche fallen bei `by_area` heraus und stehen in der Antwort. | GP-API-053. WP 7.5 ist gemergt, `by_demand` ist **nicht** umgesetzt (offen, Teil-Lücke in `GP-REQ-wave7-gaps.json`). |
| 2 | „Regen — übersprungen“ (F-05) | Je Beet der Zone ein `care_event(category = rainfall)` ohne Menge; offene Gieß-Tasks bleiben offen. | **Nicht umgesetzt:** keine Route, keine Aktion im Gießrunden-Dialog; TC-053-047 ist deshalb nicht automatisierbar. |
| 3 | Zonentyp ↔ `Location.irrigation_system` (GP-FR-119) | Hinweis nur, wenn beide einen gemeinsamen Wert tragen (`manual`, `drip`) und sich unterscheiden; keine Abbildungstabelle. | GP-FR-119; umgesetzt (WP 7.5). |
| 4 | Standard-`application_efficiency` (GP-FR-114, W-017) | Tropf 0,88 (Quelle R-005), alle anderen Typen `null` („Wirkungsgrad unbekannt“, nur Netto-Liter); Wert je Zone setzbar (E-10). | §14.1; umgesetzt (WP 7.5). |
| 5 | W-017-Deckelung Pflanzgefäß/Hochbeet/Zelt | Keine Deckelung (keine belegten Werte). | umgesetzt (WP 7.5). |
| 6 | Unterlage: Grenzen und Teilen (GP-FR-033) | Eine je Site, bestehende Upload-Grenze aus NFR-013, Eichung an der Site (alle Mitglieder sehen sie), Sichtbarkeit je Nutzer (localStorage); nie im JSON-Export, im PDF nur mit ausdrücklicher Option. | GP-API-060, GP-API-007; die Option bieten die API und der Export-Dialog („Unterlage mitdrucken“, #2895). |
| 7 | „Neue Saison aus Vorjahr“ (GP-FR-171, TC-053-042) | Gleiche Site; je Beet ohne aktive Pflanzen werden die Slot-Geometrien der im Vorjahr beendeten Runs als unbelegte Slots neu angelegt (`geometry_source = season_copy`); Beete mit aktiven Pflanzen übersprungen und berichtet; Zonen bleiben; keine Pflanzen, keine Runs (GP-FR-078 bleibt COULD); nur Leitung; zuerst Probelauf. | GP-API-057. Der Satz „übernimmt Beete, Slots und Zonen“ in GP-FR-171 ist in diesem Sinn zu lesen: Beete und Zonen bleiben, wie sie sind. |
| 8 | Mehrfach-Duplizieren und Slots (GP-FR-025) | **Entschieden:** keine `create_slot`-Batch-Operation; Duplikate ohne Slots (das Panel bietet danach ein Layout an). | GP-FR-025: der Teilsatz „bei Beeten werden Slots mitkopiert“ ist damit nicht erfüllt (auch nicht beim einfachen Duplizieren). |
| 9 | Beetvorlagen (GP-FR-044/045, §20.12) | (a) Hochbeet 1,2 × 2,4 m und 2 × 1 × 0,8 m als zwei System-Vorlagen; (b) `recurring_task_templates[]` gespeichert, von `place-template` nicht angewandt (abgelöst durch die Betreiberentscheidung 2026-11-11, #2897: angewandt auf Opt-in beim Platzieren, GP-FR-087); (c) `Location.template_key` als Herkunft, exportiert, beim Import aufgelöst oder in `dropped_references[]` berichtet. | GP-API-061/062, §20.12. |
| 10 | Laubschatten „belegt Saisonwerte vor“ (GP-FR-159) | Nur der Schalter und ein Hinweistext; `site_fit` unverändert (das Modell hat keine saisonalen Sonnenfelder). | GP-FR-159 ist in diesem Sinn zu lesen. |
| 11 | Pflanzenzustand-Ebene im Übersichtsplan (GP-UX-061) | Ein `GET /locations/{key}/plant-states` je sichtbarem Beet oberhalb der Marker-LOD (seitenweise 200), darunter Cluster; kein Site-Lesepfad. | umgesetzt (WP 7.22). |
| 12 | Frost-Ebene und `normal` nach #2464 | **Entschieden in #2512:** `normal` lässt ein erzwungenes `false` unberührt; nur `high` → `normal` hebt ein `true` auf. | Nachtrag #2512 der Versionshistorie. |
| 13 | Teil-Export und Import in einen anderen Mandanten (GP-FR-172 „Leitung beider Seiten“) | Teil-Export für alle Rollen lesbar (wie GP-API-004); `target = other_tenant` braucht die Leitung nur im Ziel-Mandanten (die Datei ist der Transportweg, kein serverseitiges Lesen über Mandantengrenzen). | GP-API-004/005; „Leitung beider Seiten“ in GP-FR-172 ist in diesem Sinn zu lesen. |
| 14 | Klassen der Ebene „zuletzt gegossen“ (GP-UX-031) | 0–1 / 2–3 / 4–7 / > 7 Tage seit dem letzten Gießen, formuliert als „Tage seit“, nie als „braucht Wasser“. | umgesetzt (WP 7.7). |
| 15 | Snapshot-Liste und Wiederherstellen | Nur Leitung; Aufbewahrung R-26 (ein Jahr) unverändert; eine Wiederherstellung schreibt vorher einen eigenen Snapshot. | GP-API-058/059. |
| WP 7.1 (1) | `PUT /irrigation-zones/{key}/locations` verschiebt ein Beet aus einer anderen Zone | Stilles Verschieben (`moved_from` in der Antwort) bleibt, kein 409. | GP-API-051. |
| WP 7.1 (2) | Altes `delete_site` ließ `garden_objects`, `care_events`, `garden_plan_audit` zurück | Eigenes Issue #2513 (gemergt als Kaskade, Nachtrag #2513). | Nachtrag #2513. |
| WP 7.1 (3) | Quote für Zonen je Site | Antwort: keine Quote, die Liste bleibt seitenweise. **Stand im Code abweichend:** #2525 (Review-Folge zu #2521) hat je Site höchstens 500 Zonen eingeführt, weil ein wiederholter `merge`-Import die Zonen der Datei jedes Mal neu anlegt und der Plan-Lesepfad die Zonen ungekürzt liefert. | GP-NFR-017 (seit v1.9); Bestätigung der Grenze ist ein Betreiberpunkt. |

### 32.5 Antworten auf die Platzhalter der Welle 8 (2026-11-03, #2643; v1.11)

Der Betreiber hat am 2026-11-03 die neun Fragen des Bündels #2643 beantwortet: „Empfehlung je Frage übernehmen“. Danach sind im selben Issue Nachträge aus der Umsetzung dazugekommen; sie haben einen Standard, mit dem der Code ausgeliefert ist, und blockieren nichts. Die Tabelle nennt den gültigen Stand und wo er eingearbeitet ist. **Offen** heißt: der Standard gilt, bis der Betreiber anders entscheidet.

| Pkt. | Thema | Entscheidung bzw. ausgelieferter Standard | Eingearbeitet / Stand im Code |
|------|-------|-------------------------------------------|-------------------------------|
| 1 | E-17, EC nach Zehrerstufe (WP 8.11) | **Entschieden: Variante A.** Keine EC-Skalierung nach Zehrerstufe im Boden; Boden-`ec_ms_cm` nur als Salz-Hinweis (Schwelle konfigurierbar, Standard `null`); `_FEEDER_EC_FACTOR` entfällt. | §32.3 Zeile „E-17 (Ergebnis)“, §15.3 Flag M5; umgesetzt (#2737). |
| 2 | Frost beetgenau (WP 8.20) | Bestätigt: `high` immer genannt, `low` nie, `normal`/`unknown` wie bisher; kein Temperatur-Versatz je Beet; Frost-Grund = Beet `high` + Vorhersage. | GP-FR-162, §11.4; umgesetzt (#2689). |
| 3 | Vorschlags-Tasks (WP 8.17) | Bestätigt: Annehmen/Verwerfen und der Abschnitt ohne Erzeuger ausliefern; erster Erzeuger-Kandidat ist der Zonenbedarf (GP-FR-113), sobald der ADR-008-Phase-2-Strang geplant ist. | GP-API-040, GP-FR-086; umgesetzt (#2761). Teil-Lücke GP-FR-086 in `GP-REQ-wave8-gaps.json`. |
| 4 | Hang/Exposition (WP 8.24) | Bestätigt: nur je Beet, kein `terrain`-Feld an der Site, kein Erben. | GP-FR-168 („vom Site-Wert geerbt“ gilt nicht, Teil-Lücke in `GP-REQ-wave8-gaps.json`); umgesetzt (#2707). |
| 5 | M4 Backfill (WP 8.1) | Bestätigt: nur im R-25-Fenster, ohne Kontoverweis `performed_by_user_key = null`, Quellen ohne Beet gezählt, nicht geschrieben. Den Dry-Run-Bericht auf dem Prod-Abzug vor P-6 lesen. | v0104 (#2691); P-6-Bericht `.audits/prod-release/2026-11-07-req053-p6-wave8.md`. |
| 6 | CSV-Beetlisten-Import (WP 8.26) | Bestätigt: nur Leitung. **Nachtrag (offen):** Beete als `rect` ab der linken oberen Ecke des Grenz-Rahmens, 0,5 m Abstand, Umbruch an der Grenzbreite, vorhandene Beete der obersten Ebene werden übersprungen; ein Beet ohne Platz ist der Zeilenfehler `csv.does_not_fit`; ohne Grenze gilt der Plan-Rahmen (1 000 m). Rate-Limit 10/min je Konto (`rate_limit_plan_csv_import`) statt der 3/min des JSON-Imports, dazu 30/min je Mandant. | GP-API-069; umgesetzt (#2725). |
| 7 | Beet-Fotos (WP 8.18) | Bestätigt: ab Gärtner, fremde Fotos entfernt die Leitung. | GP-API-067; umgesetzt (#2717). |
| 8 | Grenzen der Welle | Bestätigt: Anhang-A-Reste 60–63 und die Welle-7-Lücken `by_demand`/„Regen — übersprungen“ nicht in Welle 8, gebündelt in die Planung der Welle 9 (WP 8.33); „Regen — übersprungen“ darf ein eigenes Welle-9-Paket werden. | Plan §3 Welle 9 (#2760). |
| 9 | Nährstoff-Hinweis (WP 8.10) | Bestätigt: jetzt mit Schwellen `null` umsetzen; Aktivierung ist eine Konfigurationsänderung, sobald WP 8.5 Quellen liefert. | GP-FR-125, §15.3; umgesetzt (#2733), inert (Teil-Lücke). |
| 10 | Quellenregel E-10 für Salzschwellen (R-001, aus WP 8.5 #2686) | **Offen.** Drei veröffentlichte Tabellen (Maas & Hoffman, FAO-29, UC) gehen auf eine Datenlinie zurück; das Review zählt sie als eine Quelle. Standard: strenge Lesart (nur unabhängige Quellen), höchstens eine konfigurierbare Hinweisschwelle mit `source`, Standard `null`; auch die N-Saisonsummen-Warnung aus WP 8.9 bleibt `null`. | `domain/engines/soil_salinity_hint.py`, `domain/engines/nutrient_hint_engine.py`. |
| A | Zukunftsspalten der Rotationsmatrix (WP 8.12) | **Offen.** `CropRotationPlan` hat weder Modell noch Repository; die Matrix endet beim laufenden Jahr. Empfehlung: geplante Runs (`planned_from`, `plan_role`) als Quelle statt eines neuen Speichers. | GP-API-063, GP-FR-135 (Teil-Lücke). |
| B | Spec-Zeile der Matrix-Route (WP 8.12) | Erledigt mit dieser Abnahme. | GP-API-063. |
| C | Beet nach dem Versand der Nachtwarnung auf `high` gesetzt (WP 8.20) | **Offen.** Die Idempotenz bleibt `(site_key, Datum)`: diese Nacht wird nicht erneut gewarnt, der Pflanzenzustand zeigt den Frost-Grund sofort. Empfehlung: Abweichung für eine Nacht hinnehmen. | `tasks/frost_forecast_tasks.py`. |
| D | `high` an einer Location, die kein Beet ist (WP 8.20) | **Offen.** Die Warnung nennt jede Location mit `frost_risk = high`. Empfehlung: festhalten, nicht jetzt filtern (eigenes Paket). | §10.2 Implementierungsstand. |
| E | Wortlaut des Frost-Grunds (WP 8.20) | **Offen.** Der Grund erscheint ab dem ersten Tag des Horizonts (Standard 2 Tage, `frost_forecast_horizon_days`), nicht nur in der Frostnacht. Empfehlung: so lassen, UI-Text „Frost erwartet“, nie „jetzt“. | §11.4 Implementierungsstand. |
| 11 | Profil nach Storno/Korrektur einer Bodenanalyse (#2706, Review von #2701) | **Entschieden und umgesetzt (#2706, v1.12).** Standard laut #2643: das `soil_profile` wird in derselben Transaktion aus der neuesten nicht stornierten Analyse neu abgeleitet — je Parameter aus der neuesten Analyse, die ihn gemessen hat; je Messfeld gewinnt die neueste Beobachtung aus Handeintrag (`hand_values`) und neuester offener Analyse; ein Storno kehrt zur neueren verbleibenden zurück (§15.1). | §15 Implementierungsstand. |
| 12 | Beet-Fotos: Rechtsfragen aus dem Datenschutz-Review (#2661/#2662) | **Offen, Rechtsprüfung (DSB/Anwalt).** (a) Art. 17 im geteilten Garten: Beet-Fotos liegen wie Unterlagen im Anonymisierungsumfang `user_diary_attachments` — bei der Kontolöschung bleibt das Foto am Beet, der Hochlader wird anonymisiert; die genannte Grundlage (NFR-011 R-16/R-17/R-18, CanG/PflSchG) trifft auf Gartenfotos nicht zu, tatsächlich wäre es das berechtigte Interesse der anderen Mitglieder (Art. 6 Abs. 1 lit. f). Frage: reicht das, oder müssen die eigenen Beet-Fotos gelöscht werden (`user_personal`)? (b) Art. 15 Abs. 3 / Art. 20: der Export trägt Metadaten und Verweise, die Bilddateien sind „in der App verfügbar“; eine abgebildete Person ohne Konto kann heute nur über die Leitung entfernen lassen. (c) Art. 30 / Art. 13: eigene Kategorie für Beet-Fotos? Standard: anonymisieren wie Unterlagen. | Technische Folgepunkte #2715. |
| 13 | Beetliste als CSV (WP 8.25, #2668) | **Offen.** (a) Kopfzeile und Enum-Zellen sind Maschinenwerte (`area_m2`, `assigned_to`, `active`, `loam`), nur Typ- und Zonennamen sind Namen (Typ je `locale`). (b) Höchstens 2 000 Zeilen je Download (422 `export.too_many_rows`, nie eine gekürzte Datei); die Site-Quote ist 500 Locations. (c) **Keine Rollenprüfung** an `include_assignment`: jedes Mitglied darf die Namen exportieren, weil auch ein Betrachter `GET /{slug}/members` und `GET /{slug}/assignments` liest — eine Schranke nur an der CSV schützte nichts; sollen Zuweisungen nur für Leitung/`management` lesbar sein, ändert das auch diese Routen. (d) `format=csv` mit `is_bed=false` ist 422 `export.beds_only`. | GP-API-068; umgesetzt (#2763). |
| 14 | Bodenanalysen-Oberfläche (WP 8.8, #2651) | **Offen.** (a) `liming_hint` ist `likely` nur für gewachsenen Boden mit bekannter Bodenart, `ph_method = cacl2` und einem pH unter einem vom Nutzer aus dem Laborbericht eingetragenen Ziel-pH (CaCl₂); sonst `not_assessable` mit dem ersten fehlenden Grund oder `not_indicated`. Kein Ziel-pH aus der Bodenart (Bleibt-null-Punkt, R-008). Entscheiden: so lassen oder gar kein Hinweis bis R-008. (b) P, K, Mg, Nmin, CaCO₃ und Feuchte erscheinen nur als Text im Historieneintrag, nicht als eigenes Diagramm. (c) Eine Analyse lässt sich höchstens 365 Tage zurückdatieren (`MAX_AGE_DAYS` der Pflegeereignisse). | GP-API-066, GP-FR-122; umgesetzt (#2701, #2731). |
| 15 | Flächendosierung (WP 8.9, #2652) | **Offen.** (a) Eine Dosis pro m² an einem Beet ohne Fläche speichert der Server weiter ohne `quantity_total` (`null`, wie GP-FR-123), die Oberfläche sperrt die m²-Einheiten dort; ein serverseitiges 422 bräuchte eine Textänderung an GP-FR-123. (b) Der Kalk-Hinweis „nicht über Ziel-pH / nicht bei Säurepflanzen“ (U-005) wird immer gezeigt, ohne `source`-Feld; R-011 belegt „Kalk und Holzasche heben den pH“ institutionell, „nicht bei Säurepflanzen“ nur ein Portal. Entscheiden: so lassen, Quelle ergänzen oder standardmäßig aus. (c) `NUTRIENT_MATERIALS` (`task_completion_engine.py`) kennt nur `compost`, `manure`, `horn_shavings`; neue Codes (z. B. `coffee_grounds`, `wood_ash`) erzeugen kein `feeding_event` — agronomische Entscheidung. (d) Mulch bleibt beim gespeicherten Code `straw` (GP-FR-124 nennt `straw_mulch`), keine Umbenennung. | GP-FR-123, GP-FR-124; umgesetzt (#2730). |
| 16 | Reviews je Paket (Plan §3 WP 8.32) | Laut PR-Beschreibungen: Security-Review lief für WP 8.18 (#2717, `code-security-reviewer`, keine kritischen/hohen Befunde) und WP 8.26 (#2725, `code-security-reviewer`, ein mittlerer und drei niedrige Befunde behoben); Datenschutz-Review lief für WP 8.18 (#2717, `gdpr-data-protection-reviewer`, Fragen in Pkt. 12). **Nicht belegt:** Security-Review für WP 8.4 (#2699) und WP 8.25 (#2763), Datenschutz-Review für WP 8.1 (#2691) und WP 8.3 (#2696) — offene Punkte im P-6-Bericht. | P-6-Bericht §6. |

### 32.6 Welle 9 — Platzhalter und offene Betreiberfragen (Stand 2026-11-09, v1.15)

Gespiegelt aus dem `needs-decision`-Issue #2759 (Plan `.audits/plans/req-053-garden-bed-planning-implementation.md`, §3 „Welle 9 — Offline & Konva …“, Absatz „Platzhalter-Annahmen Welle 9“). **Beantwortet ist nur Pkt. 1** (Betreiberentscheidung 2026-11-09, v1.16); für alle anderen Punkte gilt: jedes WP setzt den Standard um und nennt ihn im PR. Eine abweichende Antwort wird in einem Folge-PR umgesetzt.

| Pkt. | Thema | Standard (gilt bis zur Antwort) | Betrifft |
|------|-------|---------------------------------|----------|
| 1 | Anhang A 60–63 (Saatzustand/Ausdünnen, Kategorien-Angebot, Rankhilfen/`off_site`, `supports_layout`/Lichtprofil) | ~~Nicht in Welle 9; eigener Strang „Welle 11 — Domänen-Reste“ nach Welle 10~~ → **Beantwortet 2026-11-09 (Betreiber, Kommentar in #2759 zu Frage 1):** Anhang A 60–63 gehören zu **Welle 10**, eine Welle 11 gibt es nicht. Pakete: 60 → WP 10.9 (#2830), 61 → WP 10.12 (#2833), 62 → WP 10.6 (#2827, `trellis`/`off_site` im Panel) und WP 10.10 (#2831), 63 → WP 10.8 (#2829, `supports_layout`) und WP 10.11 (#2832); ausdetailliert in WP 9.18 (#2758) | §34, Anhang A |
| 2 | Welle-7-Lücken (GP-FR-117 „Regen — übersprungen“ + `by_demand`; GP-FR-025 Slot-Kopie, GP-FR-111) | In Welle 9 (#2753, #2754) | `GP-REQ-wave7-gaps.json` |
| 3 | Konva | Go nur bei gemessenem D-01-Verstoß auf dem Mobile-Profil (CPU 4×); dann 200 KB gzip nur für den Konva-Chunk (GP-NFR-003), E-04 sonst unberührt | §19.4, #2746/#2747 |
| 4 | Offline-Schreibpfad | Allowlist Erledigt/Notiz/Foto über ein `offlineSlice`, kein generischer Interceptor (UI-NFR-012 R-053, R-058); UI-NFR-012 Phase 3/4 repo-weit bleibt eigener Strang | GP-UX-024, #2744 |
| 5 | Abnahme „Lighthouse PWA-Score ≥ 90“ | Ersetzt durch CDP-Kriterien (UI-NFR-012 §5.1.5) | #2745 |
| 6 | Installierbarkeit | Nur Manifest-Link und vorhandene Icons, kein Install-Prompt-UI | UI-NFR-012 R-001…R-006 |
| 7 | Token-Persistenz / `device_id` (UI-NFR-012 R-048…R-051, R-049b) | Nicht in Welle 9; der Sync nach langer Offline-Zeit läuft über den normalen Refresh (HttpOnly-Cookie, 30 Tage); der Puffer übersteht ein erneutes Anmelden, weil jeder Eintrag `user_key` + `tenant_key` trägt | UI-NFR-012 R-056 |
| 8 | Parzellenliste | Kein Feld `bed_number`; Kennung = Beetname + laufende Nummer in Plan-Reihenfolge | GP-FR-176, GP-API-007, #2750 |
| 9 | PNG-Wasserzeichen | Option, Standard aus (§23.1) | GP-FR-144, #2748 |
| 10 | Kill-Switch | `PWA_CACHING_ENABLED=false` in `runtime-config.js` deregistriert den Worker und löscht Caches (und IndexedDB) — Pflicht vor P-7 | UI-NFR-012 R-059 |
| 11 | `rainfall` ohne Menge aus „Regen — übersprungen“ | Geht nicht in die Wasserbilanz; GP-FR-113 bleibt ohne Konsument | GP-FR-117, #2753 |
| 12 | Cache-Allowlist | Service Worker: `GET …/plan`, `GET …/sites`, `GET …/locations/{key}/summary`; alles andere Network-only; nie `/auth/*`, `/privacy/*`, `/admin/*`, Attachment-Originale. Die IndexedDB-Leseschicht (WP 9.2) hält diese drei und zusätzlich Beetliste, Aufgaben-Warteschlange und Pflanzenzustände des Beets — sechs Pfade (UI-NFR-012 R-057) | UI-NFR-012 R-057 |
| 13 | `Cache-Control` der drei Lesepfade (Nachtrag aus WP 9.1, Kommentar in #2759) | `no-store` bleibt (MT-044 unberührt); offline gelesen wird aus IndexedDB (WP 9.2). Alternative: `private, no-cache`, damit der Service Worker sie halten darf | UI-NFR-012 §2.3, R-057 |
| 14 | Lebensdauer des Schreibpuffers auf dem Gerät (Nachtrag aus der Spec-Readiness-Prüfung zu WP 9.5) | Lesecache wird bei Logout, Tenant-Wechsel, Kill-Switch, Kontolöschung und einem mit 401/403 abgewiesenen Refresh geleert; der Schreibpuffer bleibt beim Sitzungsende ohne ausdrückliches Abmelden erhalten und synchronisiert nur für denselben Nutzer im selben Mandanten; ausdrückliches Abmelden mit offenen Einträgen fragt nach; Kill-Switch und Kontolöschung löschen den Puffer; ausstehende Einträge älter als 365 Tage (V-11, `MAX_AGE_DAYS`, gemessen am `performed_at`, das der Eintrag senden würde) und Einträge, die nicht mehr automatisch gesendet werden (`failed`, `conflict`, behalten), 90 Tage nach der Erfassung werden beim App-Start, nach der Anmeldung und vor jedem Sync mit Hinweis und Anzahl verworfen; die Kapazität von 500 Einträgen gilt je Nutzer (Geräte-Obergrenze 5 000 als Speicherschutz) — beide Fristen sind Platzhalter-Standard, für geteilte Geräte kann der Betreiber kürzere wählen. **Bekannte Lücke:** wird das Konto auf einem anderen Gerät gelöscht, scheitert hier nur der Refresh (widerrufene Tokens); die Einträge dieses Nutzers bleiben bis zur Frist liegen, weil der Refresh ein gelöschtes Konto nicht von einer widerrufenen Sitzung unterscheidet (WP 9.4, #2744) | UI-NFR-012 R-056, R-060 |
| 15 | DSGVO-Nachzug für Daten auf dem Gerät (Nachtrag aus der Spec-Readiness-Prüfung zu WP 9.5) | **Erledigt in WP 9.17 (#2757):** REQ-025 v1.40 §10 (TTDSG-Zeilen, Einstufung „technisch notwendig“ als Vorschlag, Rechtsprüfung offen #2517), NFR-011 v1.46 §2.1 (R-41 Lesecache, R-42 Schreibpuffer mit bekannter Lücke), Nutzerdoku „Daten auf deinem Gerät“ | REQ-025 §10, NFR-011 §2.1, UI-NFR-012 R-060 |
| 16 | Sicherheitsnotiz aus der Abnahme (SEC-003, #2757) | **Bekannte Notiz, keine Änderung in Welle 9:** Der HMAC-Schlüssel der Client-Event-Digests ist `erasure_tombstone_salt` selbst (`domain/models/client_event.py`, `_digest_key`), ohne Domänentrennung zu den Grabsteinen. Ein abgeleiteter Schlüssel (fester Kontext je Verwendung) macht alle gespeicherten Digests ungültig — ein Replay nach dem Deploy würde zu 409 `client_event.payload_mismatch` — und braucht eine Übergangsregel. Die übrigen Funde der Reviews sind behoben (SEC-002, SEC-004, GDPR-004) oder in Nutzerdoku, NFR-011 R-42 und `GP-REQ-wave9-gaps.json` festgehalten (GDPR-002, GDPR-003, GDPR-005, GDPR-006); die TTDSG-Einstufung wartet auf die Rechtsprüfung (#2517) | `domain/models/client_event.py`, REQ-025 §10 |

### 32.7 Welle 10 — offene Betreiberfragen (Stand 2026-11-11, v1.17)

Gespiegelt aus dem `needs-decision`-Issue #2884 (Abnahme Welle 10, WP 10.15). Der Standard gilt bis zur Antwort; kein Kriterium wurde still geändert.

| Pkt. | Thema | Standard (gilt bis zur Antwort) | Betrifft |
|------|-------|---------------------------------|----------|
| 1 | AC-2 bei 1024 × 768 ist wegen lg = 1024 px ein lg-Kriterium | Entschieden mit v1.19: Wortlaut bleibt, AC-2 wird bei 1024 × 768 gemessen (TC-053-103); md bei 820 × 1180 (TC-053-102) | §17.3 AC-2, GP-UX-069 |
| 2 | AC-1 mit dem Light-Modus-Hinweis (58,5 % statt ≥ 60 %) | Gemessen ohne den Hinweis (66,9 %) | §17.3 AC-1, GP-UX-067 |
| 3 | Ebenen-Legende nur mit mindestens einer eingeschalteten Ebene | Wie gebaut | §17.3 AC-6, GP-UX-005 |
| 4 | Indoor-Leerzustand mit zwei Handlungen statt einer | Zwei Handlungen („Grundriss zeichnen“, „Foto als Vorlage laden“); „Grundriss zeichnen“ startet den Grenz-Modus und zeichnet zuerst den Wohnungsumriss (#2890) | GP-UX-049, GP-FR-182 |
| 5 | GP-UX-008 Touch-Ziel | Erledigt ohne Entscheidung: die Zeile nennt schon 48 px (UI-NFR-001 R-011); 44 px stand nur in #2820 | GP-UX-008 |
| 6 | Drawer bei md als Überlagerung der Zeichenfläche | Entschieden mit v1.18 (#2885): angedockt neben der Zeichenfläche, keine Überlagerung | GP-UX-069 |
| 7 | Werkzeuge Bereich, Pflanze setzen, Messen, Text/Label | Entschieden mit v1.19 (#2868 „ABGRENZEN“): GP-UX-001 nennt die vorhandenen vier Werkzeuge, die anderen sind GP-UX-071 (#2913) | GP-UX-001, GP-UX-066, AC-2 |

---

## 33. Entscheidungsvorlagen

| ID | Entscheidung | Optionen | Empfehlung | Begründung |
|----|--------------|----------|------------|------------|
| **D-01** | Rendering-Technologie | SVG-in-React · Konva · Fabric · Canvas roh · Pixi | **SVG-in-React** mit Renderer-Grenze; Konva bei gemessener Schwelle | §19.4: Accessibility, Testbarkeit, 0 KB, Zielgrößen |
| **D-02** | Garten/Beet als neue Entitäten oder bestehende | neue Collections `gardens`/`beds` · Site/Location erweitern | **Site/Location erweitern** | keine Parallelarchitektur; Edges, Tasks, Sensoren, Fruchtfolge hängen bereits an Location |
| **D-03** | Pflanzenposition | eigenes Feld an PlantInstance · Slot-Geometrie | **Slot-Geometrie** (Slot = Position) | `placed_in` existiert; eine Wahrheit statt zwei |
| **D-04** | Geometrie-Bibliothek Backend | keine · Shapely | **keine im MVP** (eigene Calculator, Property-Tests) | Rechtecke/Kreise/einfache Polygone ≤ 200 Punkte; Shapely erst bei Bedarf (Objekt-Snap, komplexe Überlappung) |
| **D-05** | Koordinatenrahmen | alles im Plan-Rahmen · Slots beet-lokal | **Slots beet-lokal** | Beet verschieben = 1 Dokument (GP-ACC-005) |
| **D-06** | Nebenläufigkeit | keine · Revision je Objekt · Revision je Plan · Echtzeit | **Revision je Plan für Struktur** (Locations, GardenObjects, Boundary, Zonen); Slots, Quick-Planting, Pflege außerhalb (revidiert F-09) | Containment ist planweit; Feldarbeit darf den Desktop-Planer nicht mit 409 stören |
| **D-07** | Pflegeprotokoll | AQL-Projektion · eigene Collection mit Referenz · Fachcollections ersetzen | **eigene Collection `care_events`** | §13.2 |
| **D-08** | Batch-Semantik | Teilerfolg (Bestand bei Tasks) · Transaktion | **Transaktion** (alles oder nichts) | halbe Geometrieänderung ist nicht reparierbar |
| **D-09** | Fruchtfolge-/Mischkultur-Verstöße beim Bepflanzen | blocken (`validate_or_raise`) · Hinweis | **Hinweis** für Beete | Gärtner entscheiden bewusst; Blocker frustriert; Slot-Ebene bleibt wie bisher |
| **D-10** | Reihen | Locations · Slots (`row`) · Entry-Attribut | **Slots mit `slot_role = row`** + Layout am Entry | Reihen gehören zur Pflanzung, nicht zum Beet |
| **D-11** | GardenObject-Typen | je Collection · eine Collection mit Enum + Props-Union | **eine Collection** | zehn fast leere Collections wären Overhead ohne Nutzen |
| **D-12** | Auto-Save | ja · nein · optional | **nein im MVP**, optional SHOULD | explizites Speichern + Revision ist erklärbar; Auto-Save mit 409 ist es nicht |
| **D-13** | Persistente Gruppen | ja · nein | **nein** (WON'T) | GP-FR-030 |
| **D-14** | ID-Schema im Dokument | FR-xxx · GP-FR-xxx | **GP-** | Kollision mit `spec/nfr/NFR-0xx` |
| **D-15** | Positionsmodell Indoor vs. Outdoor | zwei Modelle (Raster + Geometrie) · ein Modell | **ein Modell** (`Slot.geometry`) | O-01: keine Sonderbehandlung; Mischkultur-Engine sieht damit auch Zelt-Nachbarn |
| **D-16** | Altfelder `Location.dimensions`, `Slot.position` | spiegeln · sofort entfernen | **sofort entfernen** (M1) | O-01/O-02: zwei Wahrheiten für Maße sind die Fehlerquelle, die REQ-053 beseitigen soll |
| **D-17** | Zehrer-Enum | eigenes Spec-Issue · in REQ-053 | **in REQ-053**: `NutrientDemand` (3) + `nitrogen_fixing` (Bool) + `PlanRole` (revidiert nach K-001) | O-07: Rotationslogik braucht ein Enum; N-Fixierung ist orthogonal zur Zehrerstufe |
| **D-18** | `tenant_key` auf Location/Slot | nein (Site-Anker) · ja (stempeln) | **nein — Site-Anker** (revidiert 2026-10-15, E-01; hebt SR-022 auf) | #2107/MT-010 hat das Feld mit v0087 entfernt: ein nie geschriebenes `tenant_key: ""` las sich als *global* und war selbst die Leck-Quelle (#706/#1397). Ein einziges Prädikat (`location_ownership`) statt zweier Wahrheiten |
| **D-19** | Beetstatus vs. Saisonzustand | ein Enum · getrennt | **getrennt** (W-014): `bed_status` Lebenszyklus, `season_state` abgeleitet | Gründüngung ist eine Pflanzung, keine Brache |
| **D-20** | Slot-Reservierung | exklusiv · Zeitfenster | **Zeitfenster** (F-01) | Nachkultur im selben Jahr ist der Normalfall |
| **D-21** | Fruchtfolge/Mischkultur im MVP | nein · Hinweise ja | **Hinweise ja** (F-12) | Persona bleibt sonst für die Jahresplanung bei Papier |
| **D-22** | `performed_by`-Filter | Leitung/me · alle | ~~alle Rollen~~ → **Leitung/`management` auf jedes Mitglied, sonst nur auf sich selbst** (E-16, 2026-10-18) | Datenminimierung im Gemeinschaftsgarten (Aktivitätsprofil) |
| **D-23** | Offline-Puffer im MVP | ja · nein | **nein** (F-17) | wartet auf UI-NFR-012-Basis; Offline-Hinweis statt stillem Verlust |

---

## 34. Implementierungs-Roadmap

Wellen sind sequenziell abhängig; innerhalb einer Welle sind die Pakete parallelisierbar (ein Agent je Paket, schreibende Agenten auf geteiltem Tree sequenziell — Feedback-Memory). Jede Welle endet mit grünem Quality-Gate, Review (`/code-review`), PR gegen `develop`, und — bei Frontend-Änderungen — der 3-Agent-Kette (Memory `feedback_auto_docs`).

| Welle | Inhalt | Pakete | Abhängig von | Schätzung |
|-------|--------|--------|--------------|-----------|
| **0 — Spec-Abschluss** | ✅ Betreiberentscheidungen O-01…O-15 (2026-10-04); ✅ ADR-008 auf Accepted gehoben (E-02, 2026-10-15; REQ-006 v3.5, REQ-022 v3.0, REQ-030 v1.13); ✅ Agrobiologie-, Outdoor-Persona- und Security-Review (2026-10-04, `spec/analysis/*-req-053.md`); ✅ Restliste der Reviews als Issues (Anhang A, 58–66); ✅ verbleibende Review (`agrobiology-requirements-reviewer`) und Outdoor-Review (`outdoor-garden-planner-reviewer`) auf dieses Dokument; ✅ Security-Spec-Review; ✅ `TC-REQ-053.md` aus §30 (`test-case-extractor`, 44 Fälle, v1.4 mit Mapping GP-ACC-053…057); ✅ REQ-002/REQ-013/REQ-006-Pins und Querverweise (REQ-002 v4.6, REQ-013 v2.8, REQ-006 v3.5, REQ-001 v4.11, REQ-032 v1.2, REQ-042 v1.3, NFR-011 v1.44, Kopfzeile); ✅ v1.3: Frontend-Design- und Outdoor-Persona-Review (2026-10-11, `spec/analysis/*-req-053-v1.3.md`), Betreiberentscheidungen O-16…O-22; ✅ Folge-Issues: Fachprüfung der Sonnenklassen-Schwellen und Erreichbarkeits-Richtwerte (O-17, `spec/analysis/agrobiology-thresholds-req-053.md`), ✅ Semantik von `Species.shade_tolerance` in REQ-001 geklärt (E-05, Voraussetzung für `site_fit`), ✅ `TC-REQ-053.md` um §9.7/§10.2/§11.4/GP-FR-170 erweitert; ✅ Spec-Readiness-Review eingearbeitet (2026-10-16, Nachtrag v1.4) | 5 | — | 1 Woche |
| **1 — Fundament Backend** | M1 (ohne `tenant_key`-Stempel, E-01) – M3 + M5 (Alt-Cron→RRULE, Fallback entfernen) + M6 (NutrientDemand-Split), jeweils mit Dry-Run-Report; `print_engine` `url_fetcher` (Sicherheitskorrektur, zuerst); `calculate_plants_per_m2` mit Reihenabstand; GP-NFR-058 Referenzauflösung + Quoten + Pflicht-Audit; Entfernung von `Location.dimensions` und `Slot.position` samt aller Leser (Backend + Frontend); `Geometry`, `geometry_calculator` + Testvektoren; Site-`plan`, Location-/Slot-/GardenObject-Felder; `garden_plan_service` mit Batch-Transaktion und Containment; Endpunkte GP-API-001–003, 010–015; Tenant-Negativtests; Observability-Events | 6 | 0 | 2 Wochen |
| **2 — Editor-Kern** | `gardenPlanSlice`, Operationen, Undo/Redo; `PlanRenderer` + `SvgPlanRenderer` + Headless-Renderer; Werkzeuge Auswahl/Pan/Beet/Objekte/Polygon; Raster/Snap; Panel; Kontextmenü; Konflikt-Dialog; **Liste-Ansicht + Tastatur + aria-live** (nicht später!); Dynamic Import + Budget-Eintrag; i18n DE/EN; testids; vitest + axe; E2E-Grundlauf; **Interaktionsregeln §9.7 (v1.3):** Hit-Priorität + Stapelauswahl (`hitTestAll`), Touch-Zeichenleiste und Mehrfachauswahl-Umschalter, Gestentabelle, `px_per_m`-Zoom + LOD-Tabelle + Label-Platzierung, Snap-Reihenfolge, Undo-Granularität, Löschschutz mit Zählung, Eltern-Kind-Verhalten, Roving-Tabindex + Skip-Links, „Hinzufügen mit Maßen“, Leerzustände, Live-Validierung (GP-UX-032…054, GP-FR-150…156, GP-NFR-065…070); Hintergrund-Unterlage mit Zwei-Punkt-Eichung ist SHOULD (Welle 7) | 8 | 1 | 4 Wochen |
| **3 — Beet & Pflanzung** | `is_bed`-Seeds, Beetansicht mit Tabs, Beetliste, Summary; Bodenprofil; Entry-Layout-Felder, `planting_layout_calculator` (py + ts), Preview-Endpunkt, `run_planned_at`, `create-plants`-Anpassung, Pflanzen-Marker, Position korrigieren; Adjacency-Engine + Celery-Task; Bepflanzen-Dialog mit Fruchtfolge-/Mischkultur-Hinweis (Beet-Validator, `rotation_pause_years`); Zeitfenster-Reservierung; Beet räumen; Vorjahr am Beet; **v1.3:** Sonne/Schatten-Kacheln (5 Stufen inkl. `deep_shade`, Stapel-Zuweisung) und Eignungs-Ampel `site_fit` im Bepflanzen-Dialog (GP-FR-157/160, nach Klärung `shade_tolerance`); **Pflanzeninfo als Mouseover und Zustandskanäle** (§11.4: `plant_state_calculator` py + ts, `GET …/plant-states`, Marker-Kanäle, Aufmerksamkeits-Badge, Cluster-Zusammenfassung, Legende, `aria-label`; GP-FR-190…192, GP-UX-058…062, GP-API-054) | 7 | 2 | 3 Wochen |
| **4 — Pflege & Historie** | ADR-008 ist Accepted (Welle 0) und RRULE migriert (Welle 1); `TaskCategory`-Erweiterung; `care_events` + Service + Endpunkte inkl. Redaktion; Rückgängig-Snackbar; Abschluss-Übergang atomar; Batch-Erledigen; Historie-Tab + Zeitstrahl + `rotation`-Endpunkt; DSGVO-Kaskade; Abschluss-Übergang = ADR-008 Phase 3 **nur für Tasks** (E-02); Backfill-Migration M4 → Welle 8 (E-11) | 6 | 1 (parallel zu 2–3 möglich, Merge nach 3) | 2 Wochen |
| **5 — Feldmodus & Export** | Feldmodus (Listen-Einstieg, Sheet, Schnellprotokoll-Chips, Stepper, Sofortspeichern, Offline-Hinweis, Quick-Planting); `plan_svg_engine`, PDF-Vorlage, Print-Endpunkt, JSON-Export; E2E auf 390 px; Lighthouse-Route; Performance-Benchmarks GP-ACC-033/034; **`replace`-Import mit `dry_run` und Pflicht-Snapshot (GP-FR-170, O-18; zieht Issue 44 aus Welle 7 vor)**; Export-Dialog mit Vorschau und Kopfzeilen-Überlauf (GP-UX-050/052) | 7 | 3, 4 | 2 Wochen |
| **6 — MVP-Abnahme** | Alle GP-ACC-001…035 grün (Unit/Integration/E2E), ZAP-Negativtests, Docs (MkDocs DE/EN: Nutzerhandbuch „Gartenplan", technische Seite Geometriemodell), Release-Notes, REQ-042-Modul, REQ-032 §2.5-Verweis; zusätzlich GP-ACC-050…052 (Pflanzenzustand, Mouseover ohne Netzaufruf, Graustufen/Rot-Grün-Test); Docs ergänzen: Gestenübersicht, Standortmerkmale, Pflanzenzustände in der Legende | 4 | 5 | 1 Woche |
| **7 — SHOULD-Welle A** | Bewässerungszonen (§14), Beetvorlagen, Standardgrößen, Objekt-Snap, Ausrichten; Hintergrund-Unterlage (GP-FR-033), „Neue Saison aus Vorjahr“ (GP-FR-171), Teil-Export/Zielwahl (GP-FR-172), Import-Assistent (GP-UX-051), Sonnenprofil + Laubschatten (GP-FR-158/159), Karten-Ebenen Sonne/Feuchte/Frost (GP-FR-169), Pflanzenzustand-Ebene + Filter (GP-UX-061) | 9 | 6 | 4 Wochen |
| **8 — SHOULD-Welle B** | Fruchtfolge-Beet-Validator, Hinweise im Dialog, Mischkultur-Overlay, Rotationsmatrix, Bodenanalyse-Ereignisse, Flächendosierung, Vorschlags-Tasks, Beet-Fotos, CSV; CSV-Beetlisten-Import und Spaltenauswahl (GP-FR-174/175), Mikroklima/Frostrisiko beetgenau mit Frost-Frühwarnung (GP-FR-162), Wind/Hang/Erreichbarkeit (GP-FR-161/163/166/168), Schema-Rückwärtskompatibilität (GP-NFR-072), Messprofile INP (GP-NFR-071); **M4 Backfill + Konsistenz-Job + `care_confirmations` → `care_event`** (E-11). **Stand 2026-11-07 (v1.11):** WP 8.1–8.27, 8.29–8.31 und 8.33 gemergt; offen WP 8.28 (#2671, GP-NFR-072) und die Abnahme 8.32 (#2675). Matrix `spec/e2e-testcases/GP-REQ-wave8-matrix.md`: 36 von 37 Zeilen mit Test, fünf mit Teil-Lücke; Prod-Punkt P-6 vorbereitet (`.audits/prod-release/2026-11-07-req053-p6-wave8.md`, kein Deploy, E-07) | 13 | 6, ADR-008 | 4 Wochen |
| **9 — Offline & Konva** | **UI-NFR-012-Basis** (Workbox/Service Worker im Vite-Build, tenant-/nutzergebundener Cache-Schlüssel, Logout/Tenant-Wechsel leert, CSP-verträglich) als erster Offline-Fall des Repos, danach Plan-Cache + Offline-Puffer (GP-UX-024, E-06); Konva-Renderer bei gemessener Schwelle, PNG; Vorlagen-Austausch (GP-FR-173), Parzellenliste (GP-FR-176), `root_competition`/Wasserzugang (GP-FR-165/167); ~~GeoJSON~~ (WON'T). **Stand 2026-11-09 (v1.15, Abnahme WP 9.17 #2757):** WP 9.1–9.16 gemergt; die Matrix `spec/e2e-testcases/GP-REQ-wave9-matrix.md` belegt alle 16 REQ-053-Zeilen und 35 UI-NFR-012-Kriterien der Welle mit Tests (vier Teil-Lücken bei #2759). Konva ist nach der Messung (WP 9.6) als eigener Lazy-Chunk ab 3 000 Objekten gebaut (WP 9.7, GP-NFR-003: 200 KB gzip nur für diesen Chunk). Offline gelesen wird aus IndexedDB, weil das Backend `Cache-Control: no-store` sendet (MT-044; §32.6 Pkt. 13). Prod-Punkt P-7 vorbereitet (`.audits/prod-release/2026-11-09-req053-p7-wave9.md`, kein Deploy, E-07); offen WP 9.18 (#2758, Welle 10 anlegen). Alle Platzhalter der Welle stehen in §32.6 (gespiegelt aus #2759) | 5 | 6, Messung | 3 Wochen + Messung |
| **10 — Editor-Arbeitsfläche, Indoor-/Wohnungs-Grundriss, Domänen-Reste (SHOULD, O-22; letzte Welle von REQ-053)** | **Arbeitsfläche** (§17.3, GP-UX-063…070, AC-1…AC-17; #2820 Vorschlag A + C): Tabs Plan · Liste · Beete mit URL-Zustand, eine Kopfleiste, Zeichenfläche auf Viewport-Höhe, vertikale Werkzeug-Leiste, Seitenpanel mit Tabs (WP 10.2–10.5); **Indoor-Grundriss** (§9.8, GP-FR-180…183): Eigenschaften der Objekte `window`/`door`/`furniture`/`lamp` samt `trellis` und `off_site`, Fenster-Himmelsrichtung → `sun_profile`-Vorschlag mit Bestätigung, Indoor-Leerzustand, Raster 5 cm, Pflanzplätze (WP 10.6–10.8); **Domänen-Reste** Anhang A 60–63 (§32.6 Pkt. 1): Saatzustand/Vereinzeln/Nachpflanzen, Aufgaben an Gartenobjekten und Rankhilfe im Pflanzdialog, Zelt-Regeln (`adjacency_factor` je Location, `lighting`-Felder ohne Berechnung, Photoperiode-Hinweis, Topfvolumen-Prüfung), Pflegekatalog-Rest (WP 10.9–10.12); E2E Teil A/B und Abnahme mit Restliste als Einzel-Issues (WP 10.13–10.15). Zeichenfunktionen, Unterlage und Export kommen aus Wellen 2/5/7. **Stand 2026-11-10 (v1.16):** WP 10.1–10.15 = #2822–#2836 (Milestone „REQ-053 Welle 10“, Plan §3 „Welle 10“); WP 10.1 (diese Version) erledigt. **Stand 2026-11-11 (v1.17, Abnahme WP 10.15):** WP 10.1–10.14 gemergt, Matrix `GP-REQ-wave10-matrix.md` (34 Zeilen, 33 mit Test, 7 Teil-Lücken, AC-2 offen). **Restliste — keine Welle 11:** offene MUST-Reste #2890 (Gartengrenze), #2891 (Beet räumen), #2892 (Space+Drag), #2893 (Slot-Raster), GP-FR-025 Slot-Kopie (#2759); SHOULD #2894 (Sonnenauf-/-untergang, Ausrichtung), #2895 (Unterlage im PDF-Dialog), #2896 (Sukzession reserviert Slots), #2897 (Aufgaben aus Beetvorlagen), #2898 (GPS-Hilfe), #2899 (Beet-QR), #2900 (SVG/PDF barrierefrei), #2901 (`as_of`); Befunde der Abnahme #2885–#2889, #2902–#2906, #2882; offene Fragen #2884, #2759, #2643, #2854, #2857, #2862; COULD-Zeilen ohne Welle (GP-FR-034, 052, 054, 071, 075, 076, 078, 091, 108, 115, 116, 118, 126, 127, 136) und niedrige Punkte als Liste im P-7-Bericht `.audits/prod-release/2026-11-11-req053-p7-wave10.md` | 15 | 7, 9; #2813 vor WP 10.2, #2764 vor WP 10.5 (Partition `2026-11-09-req053`) | ≈ 5 Wochen seriell |

Gesamt bis MVP (Wellen 0–6): ~17–18 Wochen (Review-Zuwachs: Fruchtfolge-/Mischkultur-Hinweis, Beet räumen, Redaktion, Quoten, Referenzauflösung; v1.3: Interaktionsregeln §9.7 +1 Woche, Pflanzenzustand/`site_fit` und `replace`-Import ≈ +0,5 Wochen) Kalenderzeit bei einem durchgängigen Strang, kürzer bei paralleler Welle 4.

---

## Anhang A: GitHub-Issue-Kandidaten

Direkt aus den Anforderungen ableitbar; Titel englisch (Feedback-Memory). Labels: `feature`, `spec:REQ-053`, Bereich. Schätzung S/M/L. Reihenfolge = Roadmap.

**Welle 0 — Spec**

| # | Titel | IDs | Größe |
|---|-------|-----|-------|
| 1 | spec(REQ-053): record operator decisions O-01…O-15 — ✅ erledigt mit v1.1 | §32 | S |
| 2 | spec(REQ-053): agrobiology + outdoor-planner + security reviews of garden planning requirements | §30 | M |
| 3 | spec(REQ-053): derive TC-REQ-053 test cases from acceptance criteria | GP-ACC-* | M |
| 4 | spec(REQ-002/013/006): cross-reference REQ-053, mark bed_* fields as superseded — ✅ erledigt (REQ-002 v4.6, REQ-013 v2.8, REQ-006 v3.5, 2026-10-15) | §20.8 | S |
| 5 | spec(ADR-008): set status Accepted (RRULE canonical, single completion transition), update REQ-006 recurrence_rule to RRULE — ✅ erledigt (E-02, REQ-006 v3.5, REQ-022 v3.0, REQ-030 v1.13, 2026-10-15) | O-05, §12.2 | M |

**Welle 1 — Backend-Fundament**

| # | Titel | IDs | Größe |
|---|-------|-----|-------|
| 6 | feat(db): migration M1 garden plan collections/edges/indexes + dimensions→geometry/height_m + Slot.position→geometry (pitch_m, dry-run report); M2 LocationType.is_bed + seeds; M3 TaskCategory extension | GP-NFR-015, §9.2a, §20.14, GP-ACC-035/036 | L |
| 6a | refactor(locations)!: remove Location.dimensions and Slot.position from models, schemas, repositories and frontend after M1 | O-01, O-02, D-16 | M |
| 6b | feat(db): migration M5 recurrence cron→RRULE with dry-run report; API rejects cron (422 recurrence.rrule_required) | O-05, GP-ACC-038 | M |
| 6c | feat(db): migration M6 NutrientDemand split (3 levels + nitrogen_fixing bool + PlanRole), BotanicalFamily light/medium/heavy → *_feeder, dry-run report for species without nutrient_demand, seed/schema update | GP-FR-138/139, GP-ACC-037 | M |
| 6d | fix(print)!: restrictive WeasyPrint url_fetcher (no http/file), Jinja autoescape, SVG allowlist — affects existing /print/* (SR-015) | GP-NFR-052, GP-ACC-045 | S |
| 6e | fix(calculators): calculate_plants_per_m2 with row_spacing and strategy; bed-level crop rotation validator with BotanicalFamily.rotation_pause_years | GP-FR-073/131, W-003, K-004 | M |
| ~~6f~~ | ~~feat(db): M1 stamps tenant_key on locations/slots + indexes~~ — entfällt (E-01, v1.4: Site-Anker über `location_ownership`; GP-ACC-046 revidiert und in Issue 14 enthalten) | SR-022 revidiert | — |
| 6g | feat(garden-plan): per-operation role check in batch, closed op list, GP-NFR-058 reference resolution, quotas GP-NFR-017, mandatory garden_plan_audit, complexity/time budget | SR-001/003/004/011/012/013, GP-ACC-041/042/043 | L |
| 7 | feat(domain): Geometry value type + geometry_calculator (area, bbox, containment, simple-polygon) with shared test vectors | GP-FR-004–008, GP-NFR-012, GP-ACC-003/004 | M |
| 8 | feat(sites): Site.plan (boundary, north_angle_deg, grid, revision) + PUT /plan/boundary | GP-API-002, GP-FR-015, GP-ACC-001 | S |
| 9 | feat(garden-plan): GET /sites/{key}/plan aggregated read model | GP-API-001, GP-NFR-002/030/031, GP-ACC-034/035 | M |
| 10 | feat(garden-plan): transactional POST /plan/batch with plan revision conflict (409) and containment validation | GP-API-003, GP-NFR-013/014, V-01–V-05, V-14, V-17, V-19, GP-ACC-005/009/010/013 | L |
| 11 | feat(locations): geometry, soil_profile, bed_status, sun_exposure, notes, locked, z_order on Location; PATCH endpoint; status transition endpoint | GP-API-010/018, GP-FR-046, GP-ACC-012/015 | M |
| 12 | feat(garden-objects): garden_objects collection, props union, CRUD endpoints | GP-API-013, §20.4 | M |
| 13 | feat(slots): slot geometry, slot_role, PATCH + batch replace endpoint | GP-API-014/015, §20.5 | M |
| 14 | test(security): cross-tenant negative tests for every garden-plan endpoint | GP-NFR-050, GP-ACC-014 | S |
| 15 | feat(observability): structlog events + Prometheus metrics for garden plan | GP-NFR-060/061 | S |

**Welle 2 — Editor-Kern**

| # | Titel | IDs | Größe |
|---|-------|-----|-------|
| 16 | feat(frontend): gardenPlanSlice with PlanOperation model, undo/redo, dirty state, optimistic save + conflict handling | GP-NFR-005–007, GP-FR-026, GP-ACC-007/011 | L |
| 17 | feat(frontend): PlanRenderer interface + SvgPlanRenderer with viewport culling and CSS-transform drag; headless renderer for tests; ESLint import boundary | GP-NFR-009–011, GP-ACC-033 | L |
| 18 | feat(frontend): editor tools — select, pan, rect/circle/polygon/polyline drawing, handles, rotate, polygon vertex editing | GP-FR-019–023, GP-UX-002/007 | L |
| 19 | feat(frontend): grid + snap (1 cm…1 m), scale bar, zoom levels, compass widget | GP-FR-009–012, 014, 015, GP-ACC-006 | M |
| 20 | feat(frontend): properties panel, context menu, duplicate, delete with confirmation, lock | GP-FR-024/025/027/028/032 | M |
| 21 | feat(frontend): accessibility — list view, keyboard operation, aria-live announcements, focus order | GP-NFR-020–027, GP-ACC-008/032 | L |
| 22 | feat(frontend): garden plan page route, dynamic import, bundle budget entry, i18n de/en, data-testids | GP-NFR-003, GP-UX-012/013, UI-NFR-022 registration | M |
| 23 | test(e2e): garden plan editor baseline (draw, move, save, conflict) desktop + one tent scenario proving no indoor special path | GP-ACC-002/006/007/011/036 | M |

**Welle 3 — Beet & Pflanzung**

| # | Titel | IDs | Größe |
|---|-------|-----|-------|
| 24 | feat(beds): bed detail page with Plan/Planting/Care/Soil/History tabs, bed list with counters, summary endpoint | GP-FR-041/042/047, GP-API-011/012, GP-ACC-016 | L |
| 25 | feat(beds): soil profile editing + substrate linkage | GP-FR-120/121 | S |
| 26 | feat(planting): PlantingRunEntry layout fields + planting_layout_calculator (py + ts) + preview endpoint | GP-FR-060/062/063/073, GP-API-016, GP-ACC-017/018 | L |
| 27 | feat(planting): run_planned_at reservation **with time window** (F-01), plan-slots endpoints, bed clearing endpoint (GP-FR-055), create-plants uses planned slots, plantings-by-state endpoint | GP-FR-064–066, GP-API-020–024, V-08, GP-ACC-019–021 | L |
| 28 | feat(frontend): planting dialog with crop-rotation + companion hints (MVP, F-12), live preview, row assignment for mixed culture, free placement, plant markers, "correct position", previous-year line in bed tooltip | GP-FR-067/068/072, GP-ACC-022 | L |
| 29 | feat(engines): adjacency_engine deriving adjacent_to from slot geometry + Celery task | GP-FR-130, GP-NFR-016, GP-ACC-023 | M |

**Welle 4 — Pflege & Historie**

| # | Titel | IDs | Größe |
|---|-------|-----|-------|
| 30 | feat(care-events): care_events collection, service, append-only supersede/void/**redact** (GP-FR-109), server-side trigger/created_by, endpoints, DSGVO cascade incl. all *_by fields, NFR-011 retention rows (5 y / 1 y), Art. 15/20 export | GP-FR-100/101/107, GP-API-033–037, V-11–V-13, GP-NFR-055, GP-ACC-025/026 | L |
| 31 | feat(tasks): location-bound tasks, queue filter by location, per-plant fan-out, suggested flag | GP-FR-080/081, GP-API-030, §20.9 | M |
| 32 | feat(tasks): atomic completion transition writing care_event + domain event; batch completion with care fields | GP-FR-083–085/088, GP-API-031/032, GP-ACC-024 | L |
| 33 | feat(frontend): bed care tab (complete inline, category-specific quick dialog) | GP-FR-084, GP-FR-089 badge | M |
| 34 | feat(history): combined bed history endpoint, rotation timeline endpoint, history tab UI | GP-FR-102/103, GP-API-038/039, GP-ACC-027/028 | L |
| 35 | feat(db): care_events backfill migration from watering/feeding/treatment/harvest records (SHOULD) | GP-FR-105, M4 | M |

**Welle 5 — Feldmodus & Export**

| # | Titel | IDs | Größe |
|---|-------|-----|-------|
| 36 | feat(frontend): field mode (list-first entry, bottom sheet, 64 px targets, quick-protocol chips, undo snackbar, stepper default, immediate save, offline notice) + quick-planting endpoint | GP-UX-020–023/025/027, GP-API-017, GP-ACC-029 | L |
| 37 | feat(print): plan_svg_engine + garden plan PDF (finer scale steps, A3 auto-suggest, no personal data by default, preview) + SVG endpoint with allowlist + CSP | GP-FR-142/143, GP-API-006/007, GP-NFR-052, GP-ACC-030 | L |
| 38 | feat(garden-plan): JSON export (schema_version 1) + inclusion in DSGVO data export | GP-FR-140/147, GP-API-004 | M |
| 39 | test(e2e): field mode on 390 px viewport; lighthouse route; performance benchmarks | GP-ACC-029/033/034, GP-NFR-040 | M |

**Welle 6 — Abnahme**

| # | Titel | IDs | Größe |
|---|-------|-----|-------|
| 40 | docs(mkdocs): user guide "Gartenplan" (de/en) + technical page geometry model | NFR-005, DOCS.md | M |
| 41 | feat(modules): register garden_planner module (REQ-042), navigation placement (REQ-021), REQ-032 §2.5 link | O-15 | S |
| 42 | test(security): ZAP nightly negative tests for plan import/batch | GP-NFR-057 | S |

**Wellen 7–9 — SHOULD/COULD (Auswahl)**

| # | Titel | IDs | Größe |
|---|-------|-----|-------|
| 43 | feat(irrigation): irrigation_zones model, endpoints, zone overlay, zone status, log-watering by area | GP-FR-110–114/117, GP-API-050–053 | L |
| 44 | feat(garden-plan): JSON import with dry-run, merge/replace — **replace + snapshot is MVP (O-18, GP-FR-170)** | GP-FR-141/170, GP-API-005, GP-ACC-031 | M |
| 45 | feat(beds): bed templates + standard sizes + place-template | GP-FR-044/045, GP-API-… §21.7 | M |
| 46 | feat(rotation): bed-level crop rotation validator + hints in planting dialog + rotation matrix | GP-FR-131–133/135, GP-API-025 | L |
| 47 | feat(companion): compatibility overlay on plan | GP-FR-134 | M |
| 48 | feat(soil): soil analysis events, area-based dosing in feeding dialog, amendment materials | GP-FR-122–124 | M |
| 49 | feat(tasks): suggested tasks accept/dismiss (after ADR-008 phase 3) | GP-FR-086, GP-API-040 | M |
| 50 | feat(beds): bed photos (location attachments category) | GP-FR-051 | M |
| 51 | feat(frontend): object snap, align/distribute, mini-map, auto-save option | GP-FR-012/029, GP-UX-004/014 | M |
| 52 | feat(frontend): KonvaPlanRenderer behind PlanRenderer (only if GP-NFR-013 threshold is measured) | D-01 | L |
| 53 | feat(export): PNG client-side, CSV bed list + history (GeoJSON gestrichen, v1.4) | GP-FR-144/145 | M |
| 54 | feat(offline): plan read cache + offline completion buffer (blocked on UI-NFR-012 baseline) | GP-UX-024 | L |
| 55 | spec(REQ-001/REQ-002): adopt NutrientDemand/nitrogen_fixing/PlanRole from REQ-053 §16.3 and BotanicalFamily.rotation_pause_years (changelog lines, enum tables) — ✅ erledigt (REQ-001 v4.11, REQ-002 v4.6, 2026-10-15) | O-07 | S |
| 56 | ~~chore(locations): retire Location.dimensions after geometry adoption~~ → in Welle 1 (Issue 6a) | O-02 | — |
| 57 | feat(knowledge): row_spacing_cm, nutrient_demand (required for crops), rotation_pause_years in plant_info/botanical_families schema; Steckbrief template section; plant-info-to-seed-yaml extraction; validator ranges | O-11, GP-FR-061 | M |

**Restliste aus den Reviews (eigene Issues nur für medium+, Rest als Bündel-Notiz — Feedback-Memory „Folge-Issue-Inflation")**

| # | Titel | Quelle | Größe |
|---|-------|--------|-------|
| 58 | feat(beds): season_state derivation (empty/planted/green_manure/fallow/winter_covered) + bed_status transitions planned→retired, retired→active | W-014, §7.4 | M |
| 59 | feat(soil): soil_profile v2 — growing_medium_kind, soil_texture + finger-test helper, conditions[], site_water_regime, target_ph derivation, established_on, rotation_exempt, mulch_factor; soil_analysis measurements with method/unit/depth | K-002/K-003, W-009/W-011/W-012 | L |
| 60 | feat(planting): sown state for zone/row slots, thinning creates plants, harvesting/failed states, replant suggestion on failed slot — → Welle 10, WP 10.9 (#2830) | W-015 | M |
| 61 | feat(tasks): TaskCategory additions thinning/hilling/tillage/covering/uncovering/ventilating/clearing/soil_analysis/rainfall/pollinating; context-dependent category offer; organic amendments also write feeding_events — → Welle 10, WP 10.12 (#2833) | W-006/W-007, F-03 | M |
| 62 | feat(garden-objects): trellis type, heights/opacity/foliage props, off_site flag, tasks on compost/water_source/storage — → Welle 10, WP 10.6 (#2827) und WP 10.10 (#2831) | W-005/W-008, §29 | M |
| 63 | feat(tent): LocationType.supports_layout, Slot.container_volume_l check against species, per-location adjacency_factor, lighting profile fields (SHOULD), photoperiod conflict hint (SHOULD) — → Welle 10, WP 10.8 (#2829) und WP 10.11 (#2832) | W-016 | M |
| 64 | feat(irrigation): application_efficiency, irrigated-area based demand, rainfall intake, zone/location irrigation_type conflict rule, source capacity check, HA entity validation (Technik only) | W-017, SR-014, GP-FR-119 | L (Welle 7) |
| 65 | feat(frontend): bed multi-duplicate with naming scheme, last-watered layer, print preview with scale | F-10, GP-UX-031, F-15 | M (Welle 7) |
| 66 | feat(export): CSV formula hardening, PDF without personal data by default | SR-016/SR-024 | S |
| 67 | chore(spec): register REQ-053 testids in UI-NFR-022, module garden_planner in REQ-042, NFR-011 rows care_events/garden_plan_audit, REQ-049 note on Technik vs. actuator command | GP-UX-012, O-15, SR-005, SR-010 | S |
| 68 | feat(garden-plan): plant info on hover + graphic plant states (plant_state_calculator, GET /locations/{key}/plant-states, 4 state channels + attention badge, legend, a11y labels) | GP-FR-190–192, GP-UX-058–062, GP-API-054, GP-ACC-050–052 | M |
| 69 | feat(garden-plan): hit priority, stack selection (`hitTestAll`), roving tabindex, skip links, focus return | GP-UX-032–035, GP-NFR-065/068–070 | M |
| 70 | feat(garden-plan): touch drawing action bar, multi-select toggle, gesture table, touch CSS, phantom-touch filter | GP-UX-036–038/040/041, GP-NFR-066 | M |
| 71 | feat(garden-plan): `px_per_m` zoom, LOD table, label placement, handle rules for small objects | GP-FR-150, GP-NFR-067, GP-UX-047/048 | M |
| 72 | feat(garden-plan): snap priority, undo granularity, parent-child move/scale/delete, delete protection, locked objects | GP-FR-151–156, GP-UX-043 | M |
| 73 | feat(garden-plan): add-with-dimensions dialog, keyboard rules (WCAG 2.1.4), empty states, header overflow, client live validation | GP-UX-044–046/049/052–054 | M |
| 74 | feat(garden-plan): export dialog with preview and import wizard (dry-run report, site-name confirmation) | GP-UX-050/051 | M |
| 75 | feat(locations): `site_conditions` model (sun profile, microclimate, wind, slope, access sides, flags), `deep_shade`, migrate `frost_exposed` | GP-FR-157–159/161–168 | M |
| 76 | feat(garden-plan): sun/shade tile selector with bulk assignment and `site_fit` hint in the planting dialog | GP-FR-157/160, GP-ACC-050 | M |
| 77 | spec(REQ-001): `shade_tolerance` = tolerance, add `Species.light_requirement` (requirement) and the `site_fit` mapping table — **entschieden E-05, Welle 0** — ✅ erledigt (REQ-001 v4.11, 2026-10-15) | O-16 | S |
| 78 | spec(REQ-053): agrobiology check of sun-class thresholds, reference date and reach values — ✅ erledigt (`spec/analysis/agrobiology-thresholds-req-053.md`, 2026-10-15; Werte ohne Quelle bleiben `unverified`/konfigurierbar) | O-17, GP-FR-164/166 | S |
| 79 | feat(garden-plan): map layers sun/moisture/frost and plant-state layer with attention filter | GP-FR-169, GP-UX-061 | M |
| 80 | feat(garden-plan): background underlay with two-point calibration (not exported, size-limited) | GP-FR-033 | M |
| 81 | feat(garden-plan): new season from previous year (structure copy) and partial export/target selection | GP-FR-171/172 | M |
| 82 | feat(garden-plan): CSV bed list import with dry-run and export column selection | GP-FR-174/175 | M |
| 83 | feat(garden-plan): template exchange as JSON, parcel list page in PDF | GP-FR-173/176 | S |
| 84 | feat(garden-plan): indoor objects window/door/furniture/lamp, window orientation to sun-profile prefill, indoor plan route — → Welle 10, WP 10.6–10.8 (#2827–#2829) | GP-FR-180–183 | L |
| 85 | chore(garden-plan): import schema migration for the last two versions, INP/pinch measurement profile | GP-NFR-071/072 | S |
| 86 | ✅ spec(REQ-053): extend TC-REQ-053 for the v1.3 delta (§9.7, §10.2, §11.4, GP-FR-170, §9.8) | GP-ACC-050–052 | S |

Bündel-Notizen (keine eigenen Issues): H-001 Beetbreiten-Warnung → in 24; H-002/H-003 Feldnamen → in 59; H-005 Tiefenprüfung → in 24; H-007 Lichtdurchlässigkeit → in 62; F-06 MoSCoW-Bereinigung → erledigt in v1.2; F-14 Ergebnisfelder einklappen → in 33; F-18 Schrift/Foto-Standard → in 36; SR-021 Adjacency-Payload → in 29; SR-023 QR → in 36; SR-025 Logging → in 15; SR-028 ha_publish → HA-Dokument.
