# Review REQ-054 v1.1 (Automatische Anbauplanung) — Gartenbesitzerin / Gemeinschaftsgarten

**Datum:** 2026-10-04 · **Reviewer:** `outdoor-garden-planner-reviewer` (Bericht vom Aufrufer abgelegt; der Agent gab ihn als Text zurück) · **Perspektive:** Sabine (ZG-002), Tom/Aisha (ZG-004), Jonas (UZG-005) · **Gelesen:** REQ-054 vollständig; REQ-053 und `spec/target-audiences/` nicht geöffnet — Aussagen dazu waren unverifiziert und sind unten vom Aufrufer nachgemessen.

**Nachgemessen (Aufrufer, 2026-10-04):** `Site.eisheilige_date` existiert bereits (`domain/models/site.py:130`) → F-04 nutzt es. Ein Saatgutvorrat existiert **nicht** im System → F-08 Hinweis entfällt. `Species.watering_interval_days` je Phase existiert → Gießbedarf-Proxy für F-10/F-11. REQ-053 §14 kennt Bewässerungszonen (`irrigation_zones`) und Wasserquellen (`water_source`) → F-11 nutzt sie. `rotation_reset_at` existiert in REQ-053 §15.1 → F-12 braucht nur den UI-Hinweis. Beet-Nachbarschaft ist in REQ-053 GP-FR-130 beetübergreifend SHOULD → F-21 Hinweis ist berechtigt.

## Gesamteindruck

Das Grundgerüst überzeugt: Vorschlag mit Begründung, beetweise Annahme, kein Übersteuern, Historie als Pflichteingang. Drei Dinge brächten mich zurück zum Papierplan: ein einziger `must`-Konflikt verwirft den ganzen Plan (F-01); vorgezogene Pflanzen und Dauerkulturen kommen nicht vor (F-02/F-03); ohne Nachkultur im MVP bleibt das Beet im Juli leer, ohne Eisheiligen-Datum setzt der Planer Tomaten zu früh (F-04/F-09).

| Bereich | Note |
|---|---|
| Jahresplanung / Bedarf | 3/5 |
| Fruchtfolge-Logik | 4/5 |
| Erklärung | 3/5 |
| Gemeinschaftsgarten | 2/5 |
| MVP-Tauglichkeit | 3/5 |
| Mobil | 4/5 |

## Kritisch

**F-01 `infeasible` verwirft den ganzen Plan (H-08, AP-FR-002, AP-ACC-003).** Ein `must`, der nur mit Regelbruch platzierbar ist, löscht alle anderen Belegungen. Gärtner wollen den bestmöglichen Plan mit markierter Lücke und dem am wenigsten schlechten Beet als Angebot. → Status `proposed_incomplete`; `unallocated[].least_bad_candidates[]` (Beet, verletzte Regel, `years_short`); Seitenleiste „Trotzdem in Beet X (Anbaupause fehlt 1 Jahr)" erzeugt Fixierung mit `rotation_override_reason`; `infeasible` nur, wenn nirgends platzierbar. ACC-003 umschreiben.

**F-02 Vorgezogene Pflanzen fehlen (§5.1).** „20 Tomaten vorgezogen, die MÜSSEN irgendwohin" — Bedarf kennt weder Bestand noch Pflanzdatum. → `supply ∈ {to_sow, in_hand}`, bei `in_hand` `available_from` und `source_run_key`; H-03 Start = `max(available_from, Frostgrenze)`; Menge nie still gekürzt, nur verteilt.

**F-03 Dauerkulturen blockieren nichts (§5.2, H-04).** Erdbeeren, Rhabarber, Spargel sind keine Runs mit Ende; „Vorjahr übernehmen" würde Rhabarber als Bedarf anlegen. → Bestandspflanzungen blockieren ihre Fläche ganzjährig; „Vorjahr übernehmen" überspringt Dauerkulturen und Gründüngung; `keep_place_if_possible` als weiche Präferenz (+1), H-01 untergeordnet.

**F-04 Frostdatum zu optimistisch, Eisheilige fehlen (H-03/H-05).** Mittelwert-Datum heißt: jedes zweite Jahr kommt Frost danach. → `frost_safe_date` je Site (vorhanden als `eisheilige_date`); für `frost_sensitivity = high` das spätere aus beiden; `window_source` um `user_frost_safe_date` erweitern.

**F-05 Parzellengrenzen und Schreibrechte (§13, AP-API-006).** Ein Mitglied könnte „alle annehmen" auf fremde Parzellen schreiben; kein Scope in Schritt 1. → `scope_location_keys[]` am Request („Gemeinschaftsbeete / meine Parzellen / ausgewählte"); bei Annahme je Beet Schreibrecht prüfen (`proposal.forbidden_bed`, übrige gehen durch); fremde Parzellen zählen als Nachbarn/Reservierungen, werden nie beplant.

## Wichtig

**F-06 `fit` unverständlich/unterbestimmt.** → UI „Rest auffüllen" mit Tooltip; `max_quantity`; mehrere `fit` teilen den Rest gewichtet nach Priorität (AP-FR-003).
**F-07 Menge „für 4 Personen".** → Hilfsfeld „Richtwert je Person" aus Steckbrief, schreibt nur `quantity`; ohne Wert ausgeblendet. *(Aufrufer: Steckbrief-Feld existiert nicht → O-09.)*
**F-08 Saatgut/Staffelsaat.** Saatgut: entfällt (kein Vorrat im System). Staffelsaat: `succession {interval_days, count}` am Bedarf → Planer reserviert Fläche über das ganze Staffelfenster, Termine bleiben REQ-013.
**F-09 Vor-/Nachkultur muss in den MVP (AP-FR-008).** Hauptgrund für Papier. → mindestens Minimalform „eine Nachkultur oder Gründüngung je Beet, wenn ≥ 6 Wochen frei"; Gründüngung als `plan_role = green_manure` in der Ausgabe; alternativ Hinweis „n Beete im Herbst frei".
**F-10 Profile.** Namen unverständlich; §3 nennt 4, §7.3 führt 5; `low_effort` nicht im MVP obwohl Tom danach fragt. → Alltagsnamen mit Satz (Ausgewogen · Boden schonen · Gesund halten · Viel Ernte · Wenig Arbeit); harmonisieren; `low_effort` in den MVP; Anfänger über Lernzeile (F-14), kein Profil; `water_demand` als Kriterium, wenn Gießbedarf je Art vorliegt.
**F-11 `effort` bildet Gießdienst nicht ab.** → Wasserzone (REQ-053 §14) und `water_access ∈ {drip, near_tap, far}` je Beet; durstige Art + `far` bestraft; ohne Daten neutral + `notes[effort_water_unknown]`.
**F-12 Tunnel-Tomaten jährlich am selben Platz.** → `rotation_reset_at` reicht (REQ-053); UI-Hinweis „Boden getauscht? Fruchtfolge zurücksetzen"; Fixierung in `greenhouse_bed` warnt ohne roten Alarm.
**F-13 Breakdown-Tabelle mit Gewichten stört.** → Standard: Symbol (Daumen, nicht nur Farbe) + Kurztext je Kriterium; Zahlen/Gewichte hinter „Details für Fortgeschrittene" (REQ-021); Gesamtscore nur im Vergleich.
**F-14 Beispielsatz widerspricht sich (AP-FR-011, §10.2).** „Solanaceae vor 3 Jahren — Pause 4 Jahre eingehalten" ist falsch; `warnings: []` trotz Übersteuerung; lateinische Familiennamen; `pinned_by_user +1,0` als Pluspunkt statt `override`; `benefit_reason` ungenutzt. → beide Beispiele korrigieren; Trivialnamen; ein Klauselmuster je Kriterium mit `benefit_reason`; Template-Test „nie ‚eingehalten' bei years < pause".
**F-15 Mehrfachbelegung eines Beets nicht erklärt.** → „teilt sich das Beet mit X" + Hinweis bei Annahme „Anordnung legst du im nächsten Schritt fest".
**F-16 Schritt 7 / §10.4 „vorbelegt" unklar.** → Bestätigungsdialog „Beet 3 wird für Tomaten reserviert (3,8 m², 10. Mai–15. Okt.). Die Reihen legst du beim Bepflanzen fest."; Muster „reserviert, ohne Positionen" im Plan; „vorbelegt" = Art, Sorte, Menge, `layout_strategy`.
**F-17 „Vorjahr übernehmen" und Plan-Historie.** → Quelle „tatsächlich gepflanzt" (Standard) vs. „Plan des Vorjahres"; §5.3: nur gepflanzte/abgeschlossene Runs zählen, nie `planned`; zweite Annahme derselben Saison fragt „Ersetzen oder behalten?".
**F-18 Versammlung braucht Druckfassung.** → Druck-/PDF-Ansicht MUST (Liste Beet → Art → Satz, strittige Beete markiert); Seitenleiste „Zu besprechen" (Warnungen, Fixierungen, `unallocated`, knapper Score-Abstand); Beetkommentar SHOULD.
**F-19 Wer plant was.** → ein Request je Parzelle + einer „Gemeinschaftsbeete" (Scope aus F-05); Vorschlag warnt, wenn Reservierungen anderer Requests den Scope berühren.

## Hinweis

**F-20 Mobil.** Warnungen müssen **vor** dem Annehmen auf der Karte stehen; „alle annehmen" fordert Bestätigung „1 Beet mit Warnung"; Alternativen aufklappbar; „Hierhin verschieben" darf mobil entfallen.
**F-21 Nachbarschaft/Space.** Ohne Beet-Nachbarschaft ist `companion` zwischen Beeten neutral → `notes[neighbourhood_unknown]`; `space` 85 % bestraft Reserve für Rankhilfe/Mulch → in Goldfällen prüfen.
**F-22 Aussaat-Hinweis.** Ergebnis nennt „Aussaat der Tomaten ab 15. März, siehe Aussaatkalender" (REQ-015).

## Top-5
1. F-01 `proposed_incomplete` mit least-bad-Angebot. 2. F-05/F-19 Scope + Schreibrechte. 3. F-02/F-03 Vorgezogenes + Dauerkulturen. 4. F-09 Nachkultur/Gründüngung in den MVP. 5. F-04/F-14 Eisheilige + Satzfehler.

## Einarbeitung (Aufrufer, REQ-054 v1.2, 2026-10-04)

| Befund | Status | Wo |
|--------|--------|----|
| F-01 | eingearbeitet (Betreiberentscheid) — `proposed_incomplete` + least-bad | §8.3, H-08, AP-ACC-003/012 |
| F-02 | eingearbeitet — `supply = in_hand`, `available_from` | §5.1, AP-ACC-005 |
| F-03 | eingearbeitet — Bestandskulturen blockieren, `keep_place_if_possible`, Vorjahr überspringt Dauerkulturen | §5.2, H-04, AP-ACC-016 |
| F-04 | eingearbeitet — `eisheilige_date` als Frost-Sicherheitsdatum (Feld existiert bereits) | §5.5, D-09, AP-ACC-017 |
| F-05, F-19 | eingearbeitet — `scope`, Schreibrecht je Beet bei Annahme, `forbidden_beds` | AP-FR-014, AP-API-006, V-08/V-09, AP-ACC-018 |
| F-06 | eingearbeitet — „Rest auffüllen", `max_quantity`, Aufteilungsregel | §5.1 |
| F-07 | eingearbeitet — Mengenhilfe aus `plants_per_person` (neues Schema-Feld, O-09) | §5.1 |
| F-08 | Saatgut: entfällt (kein Vorrat im System); Staffelsaat eingearbeitet (`succession`) | §5.1 |
| F-09 | eingearbeitet (Betreiberentscheid: voll im MVP) | AP-FR-008, AP-ACC-019/020 |
| F-10 | eingearbeitet — Alltagsnamen, 5 Profile im MVP, Gewichte korrigiert | §7.3 |
| F-11 | eingearbeitet — `water_access`, `water_demand_class`, Bewässerungszone (REQ-053 §14 existiert) | §7.2 `effort` |
| F-12 | eingearbeitet — `rotation_reset_at` reicht; UI-Hinweis | AP-UX-003 |
| F-13 | eingearbeitet — Symbol-Breakdown, Zahlen hinter Details | AP-FR-015 |
| F-14 | eingearbeitet — Beispiel korrigiert, Trivialnamen, `benefit_reason`, `override`, Template-Test | AP-FR-011, §10.2, AP-NFR-008 |
| F-15, F-16 | eingearbeitet — „teilt sich das Beet mit", Annahmedialog, „reserviert"-Muster, „vorbelegt" definiert | §9.1, §10.4 |
| F-17 | eingearbeitet — Vorjahr aus Ist-Runs, `planned` zählt nie, „Ersetzen oder behalten?" | §5.3, §9.1, AP-ACC-021 |
| F-18 | eingearbeitet (Betreiberentscheid) — Druckfassung MUST, „Zu besprechen"; Kommentare SHOULD | AP-UX-009/010, AP-ACC-027 |
| F-20 | eingearbeitet — Warnungen vor Annehmen, Bestätigung | AP-UX-007, AP-ACC-013 |
| F-21 | eingearbeitet — `notes[neighbourhood_unknown]`; `space`-Ziel als Site-Einstellung | §7.2 |
| F-22 | eingearbeitet — Aussaat-Hinweis | §9.1 |
