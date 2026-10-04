# Spezifikation: REQ-054 - Automatische Anbauplanung

```yaml
ID: REQ-054
Titel: Automatische Anbauplanung — aus einer Pflanzenliste und der Beet-Historie eine erklärbare, optimierte Beetbelegung je Saison ableiten
Kategorie: Planung & Empfehlung
Fokus: Nutzpflanze (Freiland, Gewächshaus, Hochbeet, Kübel)
Technologie: Python 3.14+, FastAPI, Celery, ArangoDB, React 19, TypeScript 6, MUI 9, WeasyPrint
Status: Entwurf
Priorität: Mittel (nach REQ-053 MVP)
Version: 1.2 (Agrobiologie- und Outdoor-Persona-Review eingearbeitet)
Datum: 2026-10-04
Tags: [crop-planning, optimisation, crop-rotation, companion-planting, explainability, proposal, green-manure]
Abhängigkeit: REQ-053 v1.2 (Beete mit Geometrie und Fläche, `care_events`, `season_state`, Zeitfenster-Reservierung `run_planned_at`, `PlantingRun.reserved_area_m2`, Beet-Validator GP-FR-131, `NutrientDemand`/`nitrogen_fixing`/`PlanRole` §16.3, `rotation_exempt`, `rotation_reset_at`, `irrigation_zones`, `trellis`, Layout-Rechner GP-FR-062/073), REQ-001 v4.x (`rotation_after.benefit_score`, `shares_pest_risk`, BotanicalFamily, `root_depth`, `soil_ph_preference`), REQ-002 v4.4 (`CropRotationPlan`, `optimization_goal`, `location_assignments`), REQ-013 v2.7 (PlantingRun `planned`, Entries, Sukzession), REQ-028 (`compatible_with`/`incompatible_with` mit Score/Severity/`evidence_level`, `adjacent_to`), REQ-015/REQ-015-A (Saat-/Pflanz-/Erntefenster, `growing_periods`), REQ-046/REQ-039 (Frostdaten `last_frost_date_avg`, `first_frost_date_avg`, `eisheilige_date`, Klimazone), REQ-007 (Ertrags-Historie), REQ-032 (PrintEngine), REQ-024 v1.7 (Mandant), REQ-049 v1.4 (Rollenvokabular, Standort-Zuweisung), REQ-042 (Modul-Sichtbarkeit), REQ-021 (UI-Stufen), REQ-031 (KI-Assistent — nur als optionale Erklärschicht), NFR-006 (Fehlerformat), NFR-007 (Observability), NFR-011 (R-27)
Wird benötigt von: —
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.2 | 2026-10-04 | **Zwei Reviews eingearbeitet** (`spec/analysis/agrobiology-review-req-054.md`, `spec/analysis/outdoor-garden-planner-review-req-054.md`) mit Betreiberentscheidungen: **Teilplan statt Totalausfall** — Status `proposed_incomplete` mit least-bad-Angebot je unerfüllbarem `must` (F-01/W-003); **Vor-/Nachkultur und Gründüngung voll im MVP** (F-09/W-009, AP-FR-008 → MUST); **Profil „Wenig Arbeit" und Druckfassung im MVP** (F-10/F-18); **vier neue Kriterien im MVP**: `soil_cover`, `rotation_future`, `support_required` in `site_fit`, `root_depth_rotation` + `soil_fit` (W-005). Fachkorrekturen: Score-Aggregation nach Flächenanteil, `pest_risk` als Maximum, `companion` als Minimum (K-005); Zehrer-Matrix mit Mittelzehrern und Leguminosenform (K-006); `timing` über Puffertage statt widersprüchlicher 80 % (K-007); `nutrition` aus schlechtester P/K/Mg-Klasse, Humus und geplanter Düngung, N nur über Vorfrucht (K-008); **Frostmodell**: Sicherheitsdatum (`eisheilige_date`) statt Mittelwert für frostempfindliche Arten, Gewächshaus-Offset, Anker `last_frost`/`first_frost`/`calendar` über `growing_periods`, Voranzucht-Vorlauf, Erntefenster-Ende (K-003/K-004/W-007/F-04); **neue harte Regeln** H-10 `soil_hazards` (persistente Bodenpathogene, Juglon) und H-11 familienübergreifende Wirtskreise (K-001/K-002); H-01 mit Jahreskonvention, gleicher Familie innerhalb der Saison und Historie-Lücke als „nicht prüfbar"; H-04 nur angenommene Runs und Bestandskulturen (W-001); H-06 Nachbarbeet weich (W-001); `usable_fraction` je Beettyp ohne Doppelreserve, `turnaround_days` je Übergang (W-002); Bedarf mit `supply = in_hand`, `keep_place_if_possible`, `fit` mit `max_quantity` und Aufteilungsregel, `succession` (F-02/F-06/F-08); Dauerkulturen blockieren (F-03); **Geltungsbereich und Beet-Schreibrechte** bei Annahme (F-05/F-19); Beispiel §10.2 korrigiert (F-14), Trivialnamen und `benefit_reason` im Satz, `override` statt Pluspunkt; Breakdown-Standardansicht mit Symbolen, Zahlen hinter „Details" (F-13); „Vorjahr übernehmen" aus tatsächlichen Runs (F-17); Annahmedialog und „reserviert"-Muster (F-16); Warnungen vor „alle annehmen" auf Mobil (F-20); Profile mit Alltagsnamen und korrigierten Gewichten; 12 neue Akzeptanzkriterien (AP-ACC-016…027). Goldfälle (a)–(e) liegen im Agrobiologie-Bericht und sind die Fixture-Vorlage (AP-NFR-004). |
| 1.1 | 2026-10-04 | Alle offenen Punkte O-01…O-08 entschieden (§17). |
| 1.0 | 2026-10-04 | Erstfassung. |

---

## 0. Verhältnis zu bestehenden Spezifikationen

| Dokument | Liefert | Verhältnis zu REQ-054 |
|----------|---------|-----------------------|
| **REQ-053** | Beete mit Fläche, Historie je Beet (`care_events`, Pflanzungen, `season_state` je Jahr), Beet-Validator mit Anbaupausen, Zeitfenster- und Flächen-Reservierung, Bewässerungszonen, Rankhilfen, Layout-Rechner | **Datengrundlage und Ausgabeziel.** REQ-054 liest, was REQ-053 persistiert, und schreibt Vorschläge als geplante Runs (`reserved_area_m2`, `planned_from/until`). Ohne REQ-053-MVP ist REQ-054 nicht implementierbar. Folge-Issue für REQ-053: zusätzliche Historie-Eingänge und Beetfelder (§15). |
| **REQ-001 / REQ-002** | Rotationsgraph (`rotation_after`), `shares_pest_risk`, `root_depth`, `soil_ph_preference`, `CropRotationPlan` mit `optimization_goal`, Standort-Zuweisungen | **Wissensquelle** der Fruchtfolge- und Bodenbewertung; `CropRotationPlan` ist das **Ausgabeformat** des angenommenen Vorschlags; `optimization_goal` bekommt hier erstmals einen Konsumenten. Folge-Issue für REQ-001: Erreger → Wirtsfamilien-Mengen und `soil_persistence_years` (H-11, K-002). |
| **REQ-028** | Kompatibilität Art × Art, Familie × Familie, `evidence_level`, `adjacent_to` | **Wissensquelle** der Mischkultur-Bewertung. |
| **REQ-015 / REQ-015-A** | `growing_periods` je Art (Anker, Offsets), Monatsfelder als Fallback | **Wissensquelle** der zeitlichen Machbarkeit; REQ-054 rechnet daraus Tagesfenster (§5.5). Folge-Issue für das Seed-Schema: vorzeichenbehaftete Frost-Offsets, Herbst-Anker, Gewächshaus-Offset (K-004). |
| **REQ-013** | Runs, Entries, Sukzession | Ausgabeformat; Sukzession bleibt REQ-013 — REQ-054 reserviert nur die Fläche über das Staffelfenster (§5.1). |
| **REQ-032** | PrintEngine (WeasyPrint) | Druckfassung des Vorschlags (AP-UX-009). |
| **REQ-031** | KI-Assistent | **Nicht** die Planungs-Engine; optional Prosa-Schicht über dem berechneten Breakdown (AP-FR-013, D-01). |

---

## 1. Business Case

### 1.1 User Stories

- *Als Freilandgärtnerin (Sabine, ZG-002) möchte ich im Januar meine Wunschliste eingeben — Tomaten, Zucchini, Bohnen, Salat, Möhren, Kräuter — und einen Vorschlag bekommen, welches Beet was bekommt, der die letzten Jahre berücksichtigt, damit ich nicht wieder Kohl nach Kohl setze und die Starkzehrer dorthin kommen, wo letztes Jahr Bohnen standen.*
- *Als Gärtnerin, die 20 Tomaten vorgezogen hat, möchte ich sagen „die sind da und müssen ab dem 15. Mai irgendwohin" — ohne vorher wissen zu müssen, in welches Beet.*
- *Als Leitung eines Gemeinschaftsgartens (Tom, ZG-004) möchte ich für die Gemeinschaftsbeete einen Vorschlag rechnen, ihn ausdrucken und vor der Mitgliederversammlung durchgehen, damit die Diskussion bei den strittigen Beeten beginnt und nicht bei null — und ein Mitglied darf dabei nicht meine Parzelle verplanen.*
- *Als Gärtnermeister (Jonas, UZG-005) möchte ich dem Planer sagen, dass Tomaten im Tunnel bleiben und Beet 7 brach liegt, und für den Rest einen Vorschlag bekommen, der Vor- und Nachkultur nutzt.*
- *Als Nutzerin ohne Fruchtfolge-Wissen (Aisha, ZG-004) möchte ich bei jedem Vorschlag in einem Satz lesen, **warum** eine Pflanze in dieses Beet soll, mit deutschen Namen, damit ich etwas lerne.*

### 1.2 Warum eine eigene Anforderung

Die Bausteine existieren verstreut: ein Validator, der eine gewählte Art gegen ein Beet prüft; eine Empfehlung, welche Familie in **einem** Beet als nächstes sinnvoll wäre; ein Kompatibilitäts-Check; ein Layout-Rechner innerhalb eines Beets. Keiner beantwortet „ich habe diese Pflanzen und diese Beete — wie belege ich sie über die Saison?". Das ist ein **Zuordnungsproblem** mit Restriktionen und Zielkonflikten, und seine Entscheidungen — welche Regel hart ist, welche weich, was gewichtet wird — sind fachlich, nicht technisch.

### 1.3 Leitplanken

1. **Vorschlag, nie Ausführung.** Nichts wird angelegt, bevor der Nutzer nicht je Beet angenommen hat.
2. **Bestmöglicher Teilplan statt Totalausfall.** Ein unerfüllbarer Bedarf verwirft nicht den Plan; er steht mit Grund und dem am wenigsten schlechten Angebot daneben (§8.3).
3. **Erklärbar je Zuordnung** — in einem Satz mit deutschen Namen und dem Warum aus dem Wissensmodell; Zahlen für die, die sie wollen.
4. **Deterministisch** (Seed für Tie-Breaks); Goldfälle frieren das Verhalten ein.
5. **Historie ist Pflichteingang.** Lücken werden benannt, nie als „frei" gezählt.
6. **Fachregeln bleiben in ihren Quellen.** REQ-054 kombiniert; es definiert keine Agronomie neu. Alle Heuristik-Beträge sind **Modellparameter** (§7.5), keine Fachfakten.

---

## 2. Ziel und Scope

### 2.1 Ziel

Aus einer Bedarfsliste, einem Planungszeitraum und den Beeten eines Geltungsbereichs eine Belegung über die Saison berechnen (Vor-, Haupt-, Nachkultur, Gründüngung), die alle harten Restriktionen erfüllt und die gewichtete Zielfunktion maximiert — und sie so präsentieren, dass der Nutzer sie beetweise annehmen, ändern oder verwerfen kann.

### 2.2 Im Scope

- Bedarfsliste: Art/Sorte, Menge (Stück, m², „Rest auffüllen" mit Obergrenze), Priorität, Bestand („vorgezogen, ab Datum verfügbar"), Beet-Wunsch/-Ausschluss/-Fixierung, „am gleichen Platz wie letztes Jahr", Staffelsaat-Fläche.
- Geltungsbereich: Gemeinschaftsbeete / eigene Parzellen / ausgewählte Beete; Schreibrechte je Beet bei Annahme.
- Saison mit **bis zu drei Fenstern je Beet** (Vorkultur, Hauptkultur, Nachkultur oder Gründüngung); Gründüngung/Mulch-Vorschlag für freie Beete und den Winter.
- Harte Restriktionen (§6) und gewichtete Ziele (§7) mit fünf Profilen in Alltagssprache.
- Historie der letzten `rotation_window_years` je Beet (REQ-053), Bodengefahren außerhalb des Fensters.
- Deterministischer Optimierer mit Ein-Jahres-Vorausschau, Alternativen und Erklärung.
- Vorschlag als Dokument mit Teilplan-Status; Annahme je Beet; Druckfassung; Vergleich (SHOULD).

### 2.3 Nicht im Scope

- Positionen **innerhalb** eines Beets (REQ-053 `compute_layout` nach der Annahme).
- Sukzessions-Termine innerhalb einer Belegung (REQ-013); REQ-054 reserviert nur die Fläche.
- Ertrags-**Prognose** in kg (§7.4 COULD); Düngeplanung (nur Hinweis „hier Kompost einplanen"); Anzuchtkapazität (nur Hinweis „60 Jungpflanzen brauchen Anzuchtplatz").
- Automatisches Anlegen neuer Beete; Sonnen-/Schattenberechnung (REQ-053 §29); Mehrjahres-Optimierung (AP-FR-009 COULD — die Ein-Jahres-Vorausschau `rotation_future` deckt den Alltag).
- LLM als Planer (D-01).

---

## 3. Begriffe

| Begriff | Definition |
|---------|------------|
| **Bedarf** (`DemandItem`) | Art/Sorte mit Menge, Priorität, Bestand und Vorgaben (§5.1). |
| **Belegungseinheit** (`Allocation`) | Zuordnung eines Bedarfs (ganz oder anteilig) zu einem Beet in einem Fenster (`slot ∈ {pre, main, post}`). |
| **Vorschlag** (`PlantingProposal`) | Alle Belegungen einer Planung plus nicht unterbringbarer Rest, Gründüngungs-/Mulch-Vorschläge, Bewertung, Begründungen; Status `proposed`, `proposed_incomplete`, `partially_accepted`, `accepted`, `discarded`, `infeasible`. |
| **Fenster** | `[from, until]` in Kalenderdaten (§5.5); Belegung über den Jahreswechsel ist zulässig (Winterkulturen). |
| **Profil** | Gewichtssatz der Zielfunktion mit Alltagsnamen (§7.3): Ausgewogen · Boden schonen · Gesund halten · Viel Ernte · Wenig Arbeit. |
| **Härtegrad** | Hart (nie verletzt) oder weich (Strafterm); die Zuordnung ist **nicht** konfigurierbar (D-03). |
| **Geltungsbereich** | Beete, die der Planer beplanen darf (`scope`); alle übrigen Beete der Site zählen nur als Nachbarn und Reservierungen. |
| **Bodengefahr** (`soil_hazard`) | Bestätigter Befall mit persistentem Bodenpathogen oder Allelopathie-Quelle am Beet, gültig unabhängig vom Rückblickfenster (§6 H-10). |

---

## 4. Fachliches Modell

```
PlanningRequest ──for_site──▶ Site          PlanningRequest.scope → Location[] (Beete im Geltungsbereich)
PlanningRequest ──has_demand──▶ DemandItem (1..n)
PlanningRequest ──produced──▶ PlantingProposal (0..n, je Lauf)
PlantingProposal ──has_allocation──▶ Allocation (0..n, slot ∈ {pre, main, post}) ──targets──▶ Location
PlantingProposal ──suggests_cover──▶ CoverSuggestion (0..n: Gründüngung/Mulch für freie Beete) ──targets──▶ Location
Allocation ──fulfils──▶ DemandItem
Allocation (accepted) ──materialised_as──▶ PlantingRun (planned; reserved_area_m2, planned_from/until, plan_role)
PlantingProposal (accepted) ──summarised_as──▶ CropRotationPlan (Beet × Jahr, plan_role, planned_species_keys)
```

Mehrere Requests je Saison und Site sind der Normalfall im Gemeinschaftsgarten (ein Request je Parzelle, einer für die Gemeinschaftsbeete, F-19). Sie rechnen unabhängig; angenommene Runs anderer Requests sind Reservierungen (H-04).

---

## 5. Eingangsdaten

### 5.1 Bedarf (Nutzereingabe)

| Feld | Regel |
|------|-------|
| `species_key`, `cultivar_key?` | Stammdaten (REQ-001); Sorte optional, überschreibt Zeitfenster/Abstände, wenn sie Werte trägt |
| `quantity`, `quantity_unit ∈ {plants, m2, fit}` | `fit` heißt in der UI **„Rest auffüllen"** („nimmt, was nach den anderen Pflanzen übrig bleibt"), wird zuletzt zugeteilt und braucht `max_quantity`; mehrere `fit`-Bedarfe teilen den Rest **gleichmäßig, gewichtet nach Priorität** (`must` 3 : `want` 2 : `nice` 1), deterministisch (F-06) |
| `priority ∈ {must, want, nice}` | `must` darf nie still unerfüllt bleiben (§8.3) |
| `supply ∈ {to_sow, in_hand}` (F-02) | `in_hand` = Pflanzen sind vorhanden (vorgezogen/gekauft); dann `available_from` (Pflanzreife) und optional `source_run_key` (Anzucht-Run, REQ-013). H-03 nimmt `max(available_from, Frostgrenze)` als Start. Bei `in_hand` + `must` ist die Menge fix: nie kürzen, nur auf mehrere Beete verteilen |
| `preferred_location_keys[]`, `excluded_location_keys[]` | weiche Präferenz (+1 in `preference`) bzw. harter Ausschluss |
| `pinned_location_key?` | harte Fixierung; der Planer prüft nur die Machbarkeit und warnt |
| `keep_place_if_possible: bool` (F-03) | weiche Präferenz (+1) für das Beet, in dem die Art im Vorjahr stand (Kletterbohnen am Rankgitter); H-01 bleibt übergeordnet |
| `succession {interval_days, count}?` (F-08) | Staffelsaat: der Planer reserviert die Fläche über das gesamte Staffelfenster (`count × interval_days + Kulturdauer`), die Termine legt REQ-013 fest |
| `window_override?` | explizites Fenster statt Ableitung |
| Mengenhilfe (UI) | „Richtwert je Person" aus `Species.plants_per_person` (**neu**, O-09) schreibt nur `quantity` vor; ohne Wert ausgeblendet (F-07) |

### 5.2 Beete (REQ-053)

Je Beet im Geltungsbereich mit `bed_status = active` und `supports_layout`: `area_m2`, Beettyp, `sun_exposure`, `soil_profile` (`growing_medium_kind`, `soil_texture`, `ph`, `rotation_exempt`, `rotation_reset_at`, `established_on`, `conditions[]`), `irrigation_zone_key`, **`water_access ∈ {drip, near_tap, far, unknown}`** (neu an Location, F-11), **`soil_hazards[] {hazard ∈ {clubroot, cyst_nematode, root_knot_nematode, white_rot, pea_root_rot, sclerotinia, verticillium, juglone}, affected_families[], confirmed_at, source}`** (neu, K-001/H-10), `usable_fraction` (Beet-Attribut, Standard je Typ: Bodenbeet 1,0 — die Fläche ist bereits ohne Wege gemessen; `greenhouse_bed`/`raised_bed` 0,9; `planter` 1,0; W-002), Rankhilfe vorhanden (`trellis`-GardenObject in ≤ 0,5 m, REQ-053), Reservierungen (H-04), **Bestandskulturen** (F-03): Dauerkulturen und mehrjährige Pflanzungen mit `removed_on = null` blockieren ihre Fläche ganzjährig.

Beete **außerhalb** des Geltungsbereichs (fremde Parzellen) werden gelesen — als Nachbarn (H-06, `companion`) und Reservierungen (H-04) — aber nie beplant.

### 5.3 Historie (REQ-053) — Pflichteingang

Je Beet und Jahr im Rückblick `rotation_window_years` (Standard 4, bis 8; V-01 verlangt ≥ größte Anbaupause der Familien im Bedarf): Familien und Arten je Fenster (Vor-/Haupt-/Nachkultur), `season_state`, `plan_role`, Gründüngung mit **Art, Leguminosen-Flag und Einarbeitungsdatum** (REQ-053-Folge-Issue), Düngung/Kompost mit **Menge je m²**, **Kalkung** (Datum, Menge), letzte Bodenanalyse (Gehaltsklassen je Nährstoff), Ertragsereignisse, Pflanzenschutz-Ereignisse mit **Erreger und `confirmed`-Flag**, Ernterückstände (`residues ∈ {removed, incorporated}` am Run, REQ-053-Folge).

**Was zählt:** nur Runs mit Status `active`/`harvesting`/`completed` und nacherfasste Vorjahre (`source = backfill`, gleichwertig). **Nie** `planned`-Runs — ein nie ausgeführter Plan verfälscht keine Fruchtfolge (F-17). Gründüngung zählt mit ihrer Familie, auch familienübergreifend (Senf/Ölrettich sind Wirt für Rübenzystennematoden, K-002).

### 5.4 Fehlende und lückenhafte Historie

| Fall | Verhalten |
|------|-----------|
| Beet ohne jede Historie | `rotation` neutral 0 (nicht „frei"), `history_coverage = none`, Hinweis im Vorschlag |
| Jahre ohne Eintrag innerhalb der Anbaupause einer Familie | H-01 gilt als **nicht prüfbar** → Belegung erhält `warnings[history_gap_in_pause_window]`; der Pause-Bonus (§7.2) wird **nicht** vergeben (ein Datenloch belohnt kein Beet, W-004) |
| Hochrisiko-Familie (`shares_pest_risk high` oder persistentes Pathogen) auf Beet mit Lücke | zusätzlich Strafe `−0,3 × (unbekannte Jahre / Pause)` in `pest_risk` (W-008) |
| `must`-Bedarf bei sonst gleicher Bewertung | bevorzugt Beete mit vollständiger Historie |

Der Vorschlag nennt „n von m Beeten ohne oder mit lückenhafter Historie — Vorjahre nacherfassen verbessert den Plan" mit Link zur Nacherfassung (REQ-053 GP-FR-131).

### 5.5 Wissensquellen und Fenster-Ableitung

| Quelle | Inhalt |
|--------|--------|
| Anbaupause | `BotanicalFamily.rotation_pause_years`, Spezies-Override (REQ-053 K-004); Konvention: **Art ist im Jahr Y erlaubt, wenn `Y − letztes_Anbaujahr ≥ Pause`** (Kalenderjahr-Granularität; eine Herbstkultur 2024 und eine Frühjahrskultur 2025 zählen als 1 Jahr — Hinweis in der UI) |
| Rotationsnutzen | `rotation_after.benefit_score`/`benefit_reason` (REQ-001), sonst Zehrer-Matrix §7.2 |
| Bodenpathogene | `soil_hazards` am Beet; Sperrdauer `soil_persistence_years` je Hazard (Wissensfeld, **REQ-001-Folge-Issue**, befüllt nach Recherche R-001); familienübergreifende Wirtskreise (`pathogen_hosts` → Familienmengen, REQ-001-Folge, K-002) |
| Kompatibilität | REQ-028 mit `evidence_level` (im Breakdown angezeigt) |
| Zehrerstufe / N-Fixierung / Wurzeltiefe / pH-Präferenz | `Species.nutrient_demand`, `nitrogen_fixing` (REQ-053 §16.3), `root_depth`, `soil_ph_preference` (vorhanden) |
| Standortansprüche | `light_requirement` (O-01, neu), `crop_organ ∈ {fruit, leaf, root, flower}` (**neu**, für die Lichtdifferenzierung W-004 — aus `harvested_part` ableitbar, wenn vorhanden), `greenhouse_recommended`, `container_suitable`, `frost_sensitivity`, `support_required`, `plants_per_person` (neu, O-09), `water_demand_class ∈ {low, medium, high}` (**neu**, abgeleitet aus `watering_interval_days` der Hauptphase, bis ein Steckbrief-Feld existiert) |
| Flächenbedarf | `spacing × row_spacing`, Fallback `spacing²`, über `calculate_plants_per_m2` (O-02); **keine** zusätzliche Reserve — `usable_fraction` wirkt nur auf die Beetfläche, nicht nochmals auf den Pflanzenbedarf (W-002) |

**Fenster-Ableitung (H-03), in dieser Reihenfolge:**

1. `Species.growing_periods[]` (REQ-015-A, `_defs.schema.yaml#growing_period`) mit Anker `last_frost | first_frost | calendar` und vorzeichenbehaftetem Offset hat **Vorrang** (K-004). Die Flachfelder `direct_sow_months`/`harvest_months` sind Fallback (`window_source = month_fallback`).
2. **Frostempfindliche Arten** (`frost_sensitivity = high`): Start = spätestes aus `Site.eisheilige_date` (vorhanden; UI „Frost-Sicherheitsdatum", Vorbelegung 15.5. für Mitteleuropa), `last_frost_date_avg + sowing_outdoor_after_last_frost_days` und `available_from`; `window_source = frost_safe_date`. Der Mittelwert allein ist ein 50-%-Risiko (K-003/F-04). COULD: `Site.frost_risk_percentile ∈ {50, 25, 10}`, wenn REQ-046 Perzentile liefert; `Site.frost_date_offset_days` für Frostlagen.
3. **Gewächshaus:** `greenhouse_offset_days` je `greenhouse_bed` (Beet-Attribut, Standard −21 für unbeheizt; ⚠️ R-021) verschiebt Start und Ende.
4. **Voranzucht:** Beetbelegung beginnt mit der **Pflanzung**, nicht der Aussaat (`sowing_indoor_weeks_before_last_frost`, W-007); die Kulturdauer im Beet ist die Dauer ab Pflanzung. Hinweis „n Jungpflanzen brauchen Anzuchtplatz ab {Datum}" im Vorschlag.
5. **Ende** = Pflanzung + Kulturdauer bis Erntebeginn (`typical_duration_days` der Phasen) **+ Erntefenster** (`harvest_window_days`, **neu** im Schema; Fallback aus `harvest_months`); für frostempfindliche Arten gedeckelt durch `first_frost_date_avg`; **frostharte Arten** dürfen darüber hinaus stehen, das Fenster darf im Folgejahr enden (Winterkulturen) und sperrt das Beet dort (H-04).
6. `turnaround_days` je Übergang: Ernte → Pflanzung 7; nach Einarbeitung einer Gründüngung oder von Ernterückständen 21 (⚠️ R-013; Wissensfeld `turnaround_after_incorporation_days` am Gründüngungs-Eintrag).

---

## 6. Harte Restriktionen (nie verletzt)

| ID | Restriktion | Quelle | Verhalten bei Konflikt |
|----|-------------|--------|------------------------|
| H-01 | **Anbaupause:** `Y − letztes_Anbaujahr(Familie) ≥ rotation_pause_years(Familie)` für jedes Fenster; **gleiche Familie innerhalb derselben Saison** (Vorkultur → Nachkultur, z. B. Kohl nach Kohl) ist gesperrt; `rotation_reset_at` setzt die Historie zurück; `rotation_exempt`-Beete sind für neue Hauptkulturen gesperrt. Ist die Historie in den Pause-Jahren lückenhaft → **nicht prüfbar** (§5.4), kein stilles Bestehen | REQ-053 GP-FR-131, K-001, W-001 | Beet für diese Art ausgeschlossen bzw. Warnung |
| H-02 | **Fläche:** Σ Flächenbedarf je Beet und überlappendem Fenster ≤ `area_m2 × usable_fraction(Beettyp)` | REQ-053, W-002 | teilen oder Rest |
| H-03 | **Fenster** nach §5.5; zwei Fenster eines Beets überlappen nicht und halten `turnaround_days` ein | REQ-015-A, K-003/K-004 | verschieben oder ausschließen |
| H-04 | **Reservierungen:** nur **angenommene** (`planned` mit `proposal_key`) und aktive Runs, Bestandskulturen (F-03) und Winterkulturen des Vorjahres blockieren — **nicht** unangenommene Vorschläge (sonst blockieren sich zwei Vorschläge derselben Saison, W-001) | REQ-053 V-08 | wie H-03 |
| H-05 | **Standort:** `frost_sensitivity = high` nur in Beeten mit Frostschutz (`greenhouse_bed`, `cold_frame`) oder mit Start nach dem Frost-Sicherheitsdatum (§5.5 Nr. 2 — die frühere Klausel „nach `last_frost_date_avg`" ist gestrichen, K-003); `container_suitable = false` nicht in `planter`; `light_requirement = full_sun` nicht in `sun_exposure = shade`; **pH-Extreme:** Art mit `soil_ph_preference.max < 6,0` (Säurezeiger) nicht auf Beet mit `ph > 6,5` und umgekehrt (⚠️ R-011) | REQ-001, REQ-046, REQ-053 | Beet ausgeschlossen |
| H-06 | **Inkompatibilität `severe` im selben Beet** (gleiches oder überlappendes Fenster); für **Nachbarbeete** nur hart, wenn `adjacent_to.distance_cm ≤ 30` (⚠️ R-009), sonst weich mit −1,0 in `companion` und `warnings[severe_incompatibility_neighbour]` — ein Datenfehler in einer Kante darf kein Beet sperren | REQ-028, W-001 | Beet ausgeschlossen / Warnung |
| H-07 | **Nutzer-Fixierungen** `pinned_location_key`, `excluded_location_keys` | §5.1 | Fixierung gegen H-01/H-05/H-06/H-10 → Belegung mit `warnings[...]` und `override`-Kennzeichen, kein Ausschluss |
| H-08 | **`must`-Bedarfe** werden vollständig untergebracht, **sonst Teilplan** (§8.3): Status `proposed_incomplete`, Bedarf in `unallocated[]` mit `least_bad_candidates[]`; `infeasible` nur, wenn kein Beet den Bedarf auch mit Regelbruch aufnehmen könnte (keine Fläche, kein Fenster) | F-01/W-003 | Teilplan |
| H-09 | **Beetstatus:** nur `active`; `planned`-Beete nur mit Schalter | REQ-053 §7.4 | — |
| H-10 | **Bodengefahr:** Beet mit `soil_hazards[]` ist für `affected_families` gesperrt, bis `confirmed_at + soil_persistence_years(hazard)` erreicht ist — unabhängig vom Rückblickfenster; `juglone` sperrt Solanaceae, Rosaceae-Beeren u. a. (⚠️ R-010) | K-001, W-001 | Beet ausgeschlossen; Übersteuerung nur per Fixierung mit `warnings[persistent_soil_pathogen]` |
| H-11 | **Familienübergreifender Wirtskreis** (SHOULD, abhängig vom REQ-001-Folge-Issue `pathogen_hosts`): ist im Beet in den letzten 4 Jahren ein **bestätigtes** `pest_control`/`ipm`-Ereignis mit Erreger E protokolliert, sind alle Wirtsfamilien von E gesperrt, auch über Familiengrenzen (Meloidogyne, Heterodera schachtii, Sclerotinia, Verticillium; ⚠️ R-002). Bis dahin wirkt `shares_pest_risk` nur weich | K-002 | Beet ausgeschlossen |

Härtegrade sind **nicht** konfigurierbar (D-03). Die Übersteuerung per Fixierung ist sichtbar: Warnung an der Belegung, `rotation_override_reason` am Run, `override` statt Pluspunkt im Breakdown (F-14).

---

## 7. Zielfunktion (weiche Kriterien)

### 7.1 Form und Aggregation (K-005)

`score(proposal) = Σ_allocations Σ_k w_k · s_k(a) · share(a)` mit `share(a) = area(a) / area(demand)` — eine Aufteilung auf drei Beete erzeugt **keine** drei vollen Summanden; `s_k ∈ [−1, +1]`, auf diesen Bereich **geklemmt**. Innerhalb eines Kriteriums gilt: `pest_risk` = **Maximum** der Strafen über alle betrachteten Familien (nicht Summe); `companion` = **Minimum** über alle Partner (der schlechteste Partner zählt, nicht der Mittelwert). Der Planer maximiert. Scores sind nur **innerhalb eines Profils** vergleichbar (H-003).

### 7.2 Kriterien

| k | Kriterium | Berechnung `s_k` | Quelle |
|---|-----------|------------------|--------|
| `rotation` | Fruchtfolge-Reihenfolge | `benefit_score(vorjahr_familie → neue_familie)` aus `rotation_after`, sonst **Zehrer-Matrix** (Vorfrucht ↓ / Nachfrucht →): Leguminose-Gründüngung eingearbeitet → Stark +0,6 / Mittel +0,3 / Schwach 0; Leguminose geerntet → +0,4 / +0,3 / 0; Stark → −0,6 / +0,3 / +0,3; Mittel → 0 / −0,2 / +0,3; Schwach oder nicht-leguminose Gründüngung → 0 / 0 / 0 (K-006). Stark→Stark wird 0 statt −0,6, wenn für das Beet eine Düngung im Planjahr als Annahme gesetzt ist. Pause länger als Minimum: +0,1 je **erfasstem** Jahr bis +0,3 (nie bei Lücke, §5.4). Bildet die **Reihenfolge** ab, nicht den Bodenzustand (Entflechtung K-006) | REQ-001, REQ-053 §16.3 |
| `pest_risk` | Schädlings-/Krankheitsdruck | max über Familien der letzten 2 Jahre (Insekten, Blattpathogene; ⚠️ R-014) von −`risk_level` (`low` −0,2, `medium` −0,5, `high` −0,9) aus `shares_pest_risk`; bestätigtes Ereignis mit derselben Familie in den letzten 2 Jahren → −0,9; Verdachts-Ereignis −0,5; Historie-Lücke bei Hochrisiko-Familie −0,3 × Anteil; geklemmt auf −1 | REQ-001, REQ-053 `care_events` |
| `companion` | Mischkultur | min über Paare im Beet (gleiches/überlappendes Fenster) und zu Nachbarbeeten: `compatibility_score` (+), `mild` −0,3, `moderate` −0,7, `severe` Nachbar −1,0 (H-06); Nachbarbeet-Faktor 0,5 (⚠️ R-016, Platzhalter); `evidence_level` wird mitgeführt | REQ-028 |
| `nutrition` | Bodenzustand ↔ Bedarf | aus (a) **schlechtester** Gehaltsklasse P/K/Mg (A/B −, C 0, D +, **E 0** — Überversorgung ist kein Bonus, K-008), (b) Humus (`humus_percent` ≥ 4 +0,2), (c) geplanter Düngung/Kompost im Planjahr (Planungsannahme „Kompost einplanen" +0,3 → Hinweis im Vorschlag), (d) Hochbeet-Erstjahr (`established_on` im Vorjahr: Starkzehrer +0,4, nitratspeichernde Blattarten −0,3; ⚠️ R-008); **N nur über die Vorfrucht** (`rotation`); Leguminose auf P/K-armem Beet 0 (sie braucht P/K); `insufficient_data` → 0 mit Hinweis | REQ-053 §15, GP-FR-125 |
| `space` | Flächenausnutzung | `1 − abs(Auslastung − target) / target`, `Auslastung = Σ Bedarf / (area_m2 × usable_fraction)`, `target` Site-Einstellung (Standard 0,85); **keine** Strafe für Reste — Reste < 0,5 m² erzeugen den Hinweis „Gründüngung/Untersaat möglich" (W-004) | REQ-002 |
| `timing` | Zeitpuffer | Puffer = Fensterende − berechnetes Kulturende; Puffer < 14 Tage −0,3 (Reife-/Frostrisiko, ⚠️ R-006), ≥ 14 Tage 0; Vor-/Nachkultur-Kombination, die alle Fenster mit Puffer ≥ 14 Tagen nutzt +0,3 (K-007) | §5.5 |
| `preference` | Nutzerwunsch | +1 bei `preferred_location_keys` oder `keep_place_if_possible` erfüllt; sonst 0 (nur Nutzerwünsche — Dauerkultur/Rankhilfe sind hier entfernt, W-004) | §5.1 |
| `site_fit` | Standort-Eignung | Licht: `light_requirement = full_sun` in `partial_shade` → **Fruchtgemüse −0,8, Blatt-/Wurzelgemüse −0,4** (`crop_organ`, ⚠️ R-017); `sun_exposure = unknown` 0. Gewächshaus **symmetrisch**: `greenhouse_recommended` in `greenhouse_bed` +0,5, sonst −0,3; Art **ohne** `greenhouse_recommended` in `greenhouse_bed` −0,2 (knappe Ressource); kühle Kulturen im Gewächshaus Juni–August −0,4. **Rankhilfe:** `support_required` ohne `trellis` am Beet −0,6 + `warnings[support_missing]` (W-005) | REQ-001, REQ-053 |
| `effort` | Arbeitsaufwand | −1,0 je zusätzlichem Beet, auf das ein Bedarf verteilt wird (K-005); `water_demand_class = high` auf Beet mit `water_access = far` −0,6, `near_tap`/`drip` 0 (F-11); gemischte Wasserbedarfsklassen in einer Bewässerungszone −0,3; `water_access = unknown` → 0 + `notes[effort_water_unknown]` | REQ-053 §14 |
| `soil_cover` (neu, MVP) | Bodenbedeckung | Beet, das nach der letzten Belegung ≥ 6 Wochen vor dem Winter frei ist oder ganz unbelegt bleibt: −0,5, es sei denn der Vorschlag enthält eine `CoverSuggestion` (Gründüngung aus `green_manure_suitable`-Arten, Fruchtfolge-konform, oder Mulch); mit Vorschlag +0,3 (W-005/W-009) | REQ-053 `season_state` |
| `root_depth_rotation` (neu, MVP) | Wurzeltiefen-Wechsel | Tief nach Flach oder Flach nach Tief +0,3; gleich 0 (`root_depth`) | REQ-001 Schema |
| `soil_fit` (neu, MVP) | Bodenart/pH-Passung | Wurzelgemüse (`crop_organ = root`) in `clay`/`clay_loam` −0,5; `soil_ph_preference` verfehlt um > 0,5 −0,4, getroffen +0,2; Extreme sind hart (H-05) | REQ-053 §15, REQ-001 |
| `rotation_future` (neu, MVP) | Ein-Jahres-Vorausschau | Anteil der Beete im Geltungsbereich, die im Folgejahr für die Familien des Bedarfs noch H-01-zulässig wären: sinkt er durch diese Belegung unter 1 Beet je Familie → −0,5; der Greedy-Planer verbraucht so nicht das letzte freie Beet (W-005) | H-01 |
| `water_match` (SHOULD) | Wasserbedarf-Gruppierung im Beet | gemischte Klassen im selben Beet −0,4 | `water_demand_class` |
| `shading_neighbour` (COULD) | Verschattung niedriger Nachbarbeete durch hohe Kulturen nach Himmelsrichtung | `mature_height_cm`, `north_angle_deg` (REQ-053) | — |

### 7.3 Profile (Gewichte `w_k`; Startwerte nach Review, ⚠️ Modellparameter)

| Profil (UI-Name) | rotation | pest_risk | companion | nutrition | space | timing | preference | site_fit | effort | soil_cover | root_depth | soil_fit | rotation_future | `optimization_goal` |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `balanced` **Ausgewogen** | 1,0 | 0,8 | 0,6 | 0,6 | 0,3 | 0,4 | 0,5 | 0,6 | 0,3 | 0,5 | 0,3 | 0,4 | 0,5 | — |
| `soil_health` **Boden schonen** | 1,5 | 1,0 | 0,5 | 1,0 | 0,2 | 0,3 | 0,4 | 0,5 | 0,2 | **1,0** | **0,6** | 0,6 | 0,8 | `soil_health` |
| `pest_control` **Gesund halten** | **1,3** | 1,5 | 0,9 | 0,4 | 0,2 | 0,3 | 0,4 | 0,5 | 0,2 | 0,5 | 0,3 | 0,4 | 0,8 | `pest_control` |
| `yield` **Viel Ernte** | 1,0 | 0,8 | 0,5 | 0,9 | **0,6** | 0,8 | 0,4 | 0,8 | 0,2 | 0,3 | 0,2 | 0,5 | 0,5 | **`yield`** (neuer Wert; die frühere Abbildung auf `nutrient_balance` war falsch, W-010) |
| `low_effort` **Wenig Arbeit** | 0,8 | 0,6 | 0,4 | 0,4 | 0,3 | 0,4 | 0,5 | 0,5 | **1,0** | 0,4 | 0,2 | 0,3 | 0,4 | — |

Jedes Profil hat in der UI einen Satz („Boden schonen: Bohnen und Gründüngung vor Starkzehrern, Wurzeltiefen wechseln"). Alle fünf sind im MVP (F-10). Ein Anfängerprofil gibt es nicht — Lernen passiert im Erklärsatz (§8.2). `care_load` (pflegeleichte Arten) für „Wenig Arbeit" folgt, sobald der Steckbrief ein Pflegeaufwand-Feld hat (SHOULD). Gewichte sind als Site-Einstellung überschreibbar; das Profil wird am Vorschlag gespeichert.

### 7.4 Ertrag (COULD)

Liegen ≥ 3 Ertragsereignisse einer Art auf Beeten der Site vor (REQ-007), darf „Viel Ernte" ein Kriterium `expected_yield` hinzuziehen. Vorher ist Ertrag nur Flächenbedarf.

### 7.5 Status der Zahlen

Alle Beträge in §7.2/§7.3 sind **Modellparameter**: ihre *Richtung* ist agronomisch begründet (Agrobiologie-Review W-004), ihr *Betrag* ist kalibrierbar und nicht belegt. Die Recherchepunkte R-001…R-024 des Reviews sind vor dem Einfrieren der Goldfälle abzuarbeiten (Issue 1). Goldfälle testen **Rang und Ausschlussgründe**, Scores nur mit Toleranz ±0,05 (H-002).

---

## 8. Verfahren

### 8.1 Anforderungen an das Verfahren

| ID | Prio | Anforderung |
|----|------|-------------|
| AP-FR-001 | MUST | **Deterministisch**: gleiche Eingabe (Request-Snapshot, Wissensstand, `seed`) → identischer Vorschlag; `inputs_hash`, `knowledge_version` am Vorschlag. |
| AP-FR-002 | MUST | Liefert in ≤ 10 s (klein/mittel) bzw. ≤ 60 s (groß) eine Belegung, die alle harten Regeln erfüllt — als **Teilplan**, wenn `must`-Bedarfe unerfüllbar sind (§8.3); nie einen Vorschlag, der eine harte Regel bricht. |
| AP-FR-003 | MUST | Zwei Phasen: (1) **Konstruktion** — Bedarfe `must` → `want` → `nice`, innerhalb nach Restriktivität (wenige zulässige Beet-Fenster zuerst), gierig auf das bestbewertete zulässige Beet-Fenster; `fit`-Bedarfe zuletzt nach §5.1-Regel; (2) **Verbesserung** — lokale Suche (Tausch, Verschiebung, Teilen/Zusammenlegen, Fensterwechsel pre/main/post) bis keine Verbesserung > 0,01 oder Zeitbudget; `rotation_future` wirkt in beiden Phasen; Tie-Breaks über `seed`. Reines Python (D-02). |
| AP-FR-004 | MUST | Je Belegung die **drei besten verworfenen Alternativen** (Beet, Fenster, Score, Hauptgrund). |
| AP-FR-005 | MUST | Reine Funktion `plan(request_snapshot, beds, history, knowledge, weights, seed) → Proposal` in `domain/engines/planting_planner_engine.py` ohne I/O. Property-Tests: keine harte Regel verletzt; Determinismus; Score monoton in Gewichten; Teilplan-Invariante (jede Belegung erfüllt H-01…H-11). |
| AP-FR-006 | MUST | Große Läufe (> 30 Beete oder > 40 Bedarfe) als Celery-Task mit Fortschritt; kleine synchron. |
| AP-FR-007 | SHOULD | „Rest neu planen": angenommene Belegungen bleiben fest, der Rest wird neu gerechnet. |
| AP-FR-008 | MUST | **Vor-, Haupt- und Nachkultur** (Betreiberentscheid F-09): je Beet bis zu drei Fenster (`pre`, `main`, `post`), wenn §5.5 sie erlaubt und H-01/H-03 eingehalten sind; Vorkultur zählt in der Fruchtfolge als eigener Eintrag mit Familie; gleiche Familie innerhalb der Saison ist gesperrt (H-01). **Gründüngung** ist ein eigenes Planergebnis (`plan_role = green_manure`, Art aus `green_manure_suitable`, Fruchtfolge-konform — Senf nicht in einer Kohl-Rotation); freie Beete und freie Herbst-/Winterfenster erhalten eine `CoverSuggestion` (Gründüngung oder Mulch, §7.2 `soil_cover`). |
| AP-FR-009 | COULD | Mehrjahresplanung (drei Saisons), spätere Jahre nur als Familien-Empfehlung (O-07). |
| AP-FR-010 | COULD | Solver-Backend hinter `plan()` bei gerissener Belastungsgrenze. |
| AP-FR-014 | MUST | **Geltungsbereich** (F-05/F-19): `scope` am Request; Schritt 1 bietet „Gemeinschaftsbeete / meine Parzellen (aus `location_assignments`) / ausgewählte Beete". Beete außerhalb werden nie beplant, aber als Nachbarn und Reservierungen gelesen. Berühren angenommene Runs anderer Requests ein Beet des Geltungsbereichs, nennt der Vorschlag `notes[scope_overlap {request_key, location_key}]`. |

### 8.2 Erklärung

| ID | Prio | Anforderung |
|----|------|-------------|
| AP-FR-011 | MUST | Jede Belegung trägt `explanation { breakdown[], sentence_de, sentence_en, alternatives[] }`. Der Satz wird **regelbasiert** aus dem Breakdown erzeugt: **ein Klauselmuster je Kriterium**, Familien mit **Trivialnamen** (lateinisch in Klammern), das **Warum** aus `benefit_reason`/`reason` des Wissensmodells. Beispiel: „Tomaten sind Starkzehrer und profitieren davon, dass hier letztes Jahr Bohnen standen (Hülsenfrüchtler binden Luftstickstoff). Basilikum nebenan ist ein guter Nachbar. Nachtschattengewächse standen hier zuletzt 2021 — die Pause von 4 Jahren ist eingehalten." Template-Test: bei `years_since_same_family < pause_required` enthält der Satz nie „eingehalten" (F-14). |
| AP-FR-012 | MUST | `unallocated[]` nennt je Bedarf `reason_code` (`no_bed_without_rotation_conflict`, `insufficient_area {missing_m2}`, `no_window`, `excluded_by_user`, `frost_risk`, `soil_hazard`, `severe_incompatibility`), `least_bad_candidates[]` (§8.3) und, wenn möglich, `suggestion_de` („2,4 m² fehlen — Beet 6 wird im Juli frei, wenn der Salat als Vorkultur läuft"). |
| AP-FR-013 | COULD | Prosa-Erklärung über REQ-031: Eingabe ausschließlich das Breakdown-JSON, mit Einwilligung, lokal-first, gekennzeichnet; nie Grundlage der Zuordnung (D-01). |
| AP-FR-015 | MUST | **Standardansicht des Breakdowns** (F-13): je Kriterium ein Symbol (gut/neutral/schlecht — Icon **und** Text, nicht nur Farbe) und ein Kurztext; Zahlen und Gewichte nur unter „Details für Fortgeschrittene" (UI-Stufe REQ-021); der Gesamtscore erscheint nur im Vergleich (AP-UX-005). `pinned_by_user`/`keep_place` erscheinen als **„Vorgabe"**, nicht als Pluspunkt. |

### 8.3 Teilplan und least-bad-Angebot (F-01, entschieden)

| ID | Prio | Anforderung |
|----|------|-------------|
| AP-FR-016 | MUST | Kann ein `must`-Bedarf nicht ohne Verletzung einer harten Regel platziert werden, werden **alle übrigen Bedarfe regulär belegt**; der Vorschlag erhält `status = proposed_incomplete`. Je unerfüllbarem Bedarf listet `least_bad_candidates[]` bis zu drei Beete mit der verletzten Regel und dem Abstand (`years_short` bei H-01/H-10, `missing_m2` bei H-02, `days_short` bei H-03). Die Seitenleiste bietet „Trotzdem in Beet X (Anbaupause fehlt 1 Jahr)" — das erzeugt eine Fixierung mit `rotation_override_reason` und rechnet den Rest neu (angenommene Belegungen bleiben). `infeasible` gilt nur, wenn kein Beet den Bedarf auch mit Regelbruch aufnehmen könnte. |

---

## 9. Ablauf und Oberfläche

### 9.1 Ablauf

1. **Planung starten** (Gartenplan → „Saison planen"): Saison, **Geltungsbereich** (AP-FR-014), Profil (fünf Alltagsnamen mit Satz), Rückblick-Jahre (Vorbelegung = größte Anbaupause im Bedarf), Schalter „Vor-/Nachkultur und Gründüngung zulassen" (Standard an), „geplante Beete einbeziehen".
2. **Bedarf erfassen:** Pflanzenliste (Favoriten, Suche), je Zeile Menge/Einheit (mit „Richtwert je Person", wenn vorhanden), Priorität, **Bestand** („vorgezogen/gekauft, verfügbar ab …"), „am gleichen Platz wie letztes Jahr", Beet-Wunsch/-Ausschluss/-Fixierung, Staffelsaat. **„Vorjahr übernehmen"** bietet zwei Quellen — „Was tatsächlich gepflanzt wurde" (Standard, aus abgeschlossenen/aktiven Runs) und „Plan des Vorjahres" — und überspringt Dauerkulturen und Gründüngung mit Hinweis „3 Dauerkulturen nicht übernommen" (F-17).
3. **Beete prüfen:** Liste der Beete im Geltungsbereich mit Historie-Ampel (vollständig/lückenhaft/fehlt), Bodengefahren, Wasserzugang, Rankhilfe; Link „Vorjahre nacherfassen".
4. **Rechnen** → Ergebnisansicht.
5. **Ergebnis:** Gartenübersicht (REQ-053) mit Ebene „Vorschlag" (Beete in Artfarbe je Fenster, Gründüngungs-/Mulch-Vorschläge gestrichelt, **Warnsymbol mit Text direkt an der Beetkachel**); Seitenleiste: Profil, **„Zu besprechen"** (Beete mit Warnungen, Fixierungen, `unallocated`, knappem Score-Abstand zur Alternative, F-18), `unallocated[]` mit least-bad-Angebot, Hinweise (Historie-Lücken, Anzuchtplatz, Aussaat-Termine „Tomaten aussäen ab 15. März — siehe Aussaatkalender", F-22, Kompost einplanen). Klick auf ein Beet: Satz, Symbol-Breakdown, „Warum nicht Beet 5?", „teilt sich das Beet mit Basilikum" (F-15), Details.
6. **Bearbeiten:** Belegung per Drag auf anderes Beet/Fenster (Planer prüft H-01…H-11 sofort, zeigt Score-Differenz und Warnung), Bedarf ändern, „Rest neu planen", least-bad annehmen.
7. **Annehmen:** je Beet oder „alle annehmen" (bei Warnungen Bestätigung „1 Beet mit Warnung", F-20); **Bestätigungsdialog** „Beet 3 wird für Tomaten reserviert (3,8 m², 10. Mai – 15. Okt.). Die Reihen legst du beim Bepflanzen fest." (F-16) → geplante Runs mit `reserved_area_m2`/`planned_from/until`/`plan_role`, `CropRotationPlan`-Einträge, Status `accepted`/`partially_accepted`. Beete ohne Schreibrecht des Annehmenden bleiben `proposed` (AP-API-006). Gibt es für dieselbe Saison bereits angenommene Runs aus einem anderen Vorschlag im Geltungsbereich, fragt die UI „Ersetzen oder behalten?" (F-17). Auf dem Plan zeigt eine reservierte, noch nicht gelayoutete Belegung das Muster **„reserviert, ohne Positionen"** (nicht „bepflanzt"), bis `reserved_area_m2 = null`.

### 9.2 UX-Anforderungen

| ID | Prio | Anforderung |
|----|------|-------------|
| AP-UX-001 | MUST | Ergebnis als Ebene in der REQ-053-Gartenübersicht; `unallocated` und „Zu besprechen" in der Seitenleiste, nie nur in einem Tab. |
| AP-UX-002 | MUST | Begründung je Beet in **einem Satz** (Trivialnamen, Warum); Symbol-Breakdown darunter; Zahlen nur hinter „Details für Fortgeschrittene" (AP-FR-015). |
| AP-UX-003 | MUST | Warnungen aus Fixierungen stehen an der Belegung **und** an der Beetkachel; bei Annahme als `rotation_override_reason` am Run. Fixierung in `greenhouse_bed` warnt ohne roten Alarm mit Text „typisch für Gewächshäuser — Boden getauscht? Dann Fruchtfolge zurücksetzen" (F-12, `rotation_reset_at`). |
| AP-UX-004 | MUST | Annehmen je Beet reversibel, solange der Run `planned` ist; Vorschlag bleibt als Dokument. |
| AP-UX-005 | SHOULD | Vergleich zweier Vorschläge derselben Saison (Beet-Diff, Score-Differenz je Kriterium, nur gleiches Profil). |
| AP-UX-006 | MUST | Leerzustand erklärt in zwei Sätzen, was der Planer braucht; Fachbegriffe mit Glossar (UI-NFR-011). |
| AP-UX-007 | MUST | Mobil (< 600 px): Belegung als Liste (Beet → Fenster → Art → Satz), Warnsymbol mit Text **vor** „Annehmen", Alternativen aufklappbar, „Annehmen" je Beet ≥ 48 px, „alle annehmen" mit Bestätigung bei Warnungen; Bedarfserfassung, Gewichte und Drag sind Desktop-/Tablet-Funktionen (F-20). |
| AP-UX-008 | MUST | `data-testid`: `planning-request-page`, `planning-scope-select`, `planning-demand-row-<key>`, `planning-run-button`, `planning-proposal-page`, `proposal-allocation-<location_key>-<slot>`, `proposal-cover-<location_key>`, `proposal-accept-button`, `proposal-unallocated-list`, `proposal-discuss-list`, `proposal-print-button`; i18n `pages.cropPlanning.*`, `enums.planningProfile.*`, `enums.unallocatedReason.*`, `enums.soilHazard.*`. |
| AP-UX-009 | MUST | **Druckfassung** (F-18, Betreiberentscheid): PDF über den REQ-032-PrintEngine — Liste Beet → Fenster → Art → Satz, „Zu besprechen" zuerst, Warnungen markiert, ohne Scores/Gewichte, ohne Nutzernamen; A4 hoch. |
| AP-UX-010 | SHOULD | Beetkommentar mit Autor und Status „besprochen/entschieden" am Vorschlag (Versammlung, F-18). |

---

## 10. Datenmodell

### 10.1 PlanningRequest (Collection `planning_requests`)

```json
{
  "_key": "pr_2026_main",
  "tenant_key": "t_garten_sabine", "site_key": "site_7f3a",
  "name": "Saison 2026",
  "scope": { "kind": "selected", "location_keys": ["loc_b01", "loc_b02", "loc_b03", "loc_gh1"] },
  "season": { "year": 2026, "allow_pre_post_culture": true, "allow_green_manure": true },
  "profile": "balanced", "weights": null,
  "rotation_window_years": 4,
  "include_planned_beds": false,
  "demands": [
    { "key": "d1", "species_key": "sp_solanum_lycopersicum", "cultivar_key": "cv_harzfeuer", "quantity": 20, "quantity_unit": "plants", "priority": "must", "supply": "in_hand", "available_from": "2026-05-10", "source_run_key": "run_anzucht_2026", "pinned_location_key": null, "keep_place_if_possible": false },
    { "key": "d2", "species_key": "sp_phaseolus_vulgaris", "quantity": 3, "quantity_unit": "m2", "priority": "want", "supply": "to_sow", "keep_place_if_possible": true },
    { "key": "d3", "species_key": "sp_lactuca_sativa", "quantity": 0, "quantity_unit": "fit", "max_quantity": 2, "max_quantity_unit": "m2", "priority": "nice", "supply": "to_sow", "succession": { "interval_days": 21, "count": 3 } }
  ],
  "created_by": "u_sabine", "created_at": "…", "updated_at": "…"
}
```

`scope.kind ∈ {community_beds, my_assignments, selected}`; bei `my_assignments` werden die Beete aus `location_assignments` des Erstellers aufgelöst (REQ-024/REQ-049).

### 10.2 PlantingProposal (Collection `planting_proposals`) — Beispiel korrigiert (F-14)

```json
{
  "_key": "pp_7c1e",
  "tenant_key": "t_garten_sabine", "site_key": "site_7f3a", "request_key": "pr_2026_main",
  "status": "proposed_incomplete",
  "engine_version": "1.0.0", "knowledge_version": "2026-10-01", "inputs_hash": "sha256:…", "seed": 42,
  "profile": "balanced", "weights_used": { "rotation": 1.0, "…": 0 },
  "total_score": 11.2,
  "history_coverage": { "beds_total": 4, "beds_full": 2, "beds_partial": 1, "beds_none": 1, "years": 4 },
  "allocations": [
    {
      "key": "a1", "demand_key": "d1", "location_key": "loc_b01",
      "window": { "from": "2026-05-15", "until": "2026-10-10", "slot": "main", "window_source": "frost_safe_date" },
      "quantity_plants": 7, "area_m2": 3.36, "share": 0.35, "utilisation": 0.84,
      "score": 1.02,
      "breakdown": [
        { "k": "rotation", "s": 0.4, "w": 1.0, "share": 0.35, "contribution": 0.14, "reason_code": "heavy_after_legume_harvested", "detail": { "previous_family": "Fabaceae", "previous_family_de": "Hülsenfrüchtler", "years_since_same_family": 5, "pause_required": 4, "benefit_reason": "Leguminosen binden Luftstickstoff" } },
        { "k": "pest_risk", "s": 0.0, "w": 0.8, "share": 0.35, "contribution": 0.0, "reason_code": "no_shared_risk" },
        { "k": "companion", "s": 0.4, "w": 0.6, "share": 0.35, "contribution": 0.084, "reason_code": "compatible_neighbours", "detail": { "partner": "Ocimum basilicum", "partner_de": "Basilikum", "evidence_level": "traditional" } },
        { "k": "site_fit", "s": 0.0, "w": 0.6, "share": 0.35, "contribution": 0.0, "reason_code": "full_sun_met" },
        { "k": "effort", "s": -1.0, "w": 0.3, "share": 0.35, "contribution": -0.105, "reason_code": "split_across_beds", "detail": { "beds": 3 } }
      ],
      "warnings": [],
      "override": null,
      "history_coverage": "full",
      "explanation": { "de": "Tomaten sind Starkzehrer und profitieren davon, dass hier letztes Jahr Bohnen standen (Hülsenfrüchtler binden Luftstickstoff). Basilikum nebenan ist ein guter Nachbar. Weil 20 Pflanzen nicht in ein Beet passen, sind sie auf drei Beete verteilt. Nachtschattengewächse standen hier zuletzt 2021 — die Pause von 4 Jahren ist eingehalten.", "en": "…" },
      "alternatives": [ { "location_key": "loc_gh1", "slot": "main", "score": 0.9, "main_difference": "greenhouse_already_used_by_d4" } ],
      "accepted": false, "materialised_run_key": null
    },
    {
      "key": "a9", "demand_key": "d7", "location_key": "loc_gh1",
      "window": { "from": "2026-04-24", "until": "2026-10-20", "slot": "main", "window_source": "frost_safe_date" },
      "warnings": [ { "code": "rotation_pause_violated", "detail": { "family_de": "Nachtschattengewächse", "years_since_same_family": 1, "pause_required": 4, "years_short": 3 } } ],
      "override": { "kind": "pinned_by_user", "reason": "Gewächshaus — Boden wird jährlich getauscht" },
      "explanation": { "de": "Paprika ins Gewächshausbeet, wie von dir vorgegeben. Hinweis: Nachtschattengewächse standen hier schon letztes Jahr — die Pause von 4 Jahren ist nicht eingehalten (typisch für Gewächshäuser; wenn du den Boden getauscht hast, setze die Fruchtfolge am Beet zurück).", "en": "…" }
    }
  ],
  "cover_suggestions": [
    { "location_key": "loc_b03", "window": { "from": "2026-09-15", "until": "2027-03-31", "slot": "post" }, "kind": "green_manure", "species_key": "sp_phacelia", "reason_de": "Beet 3 ist ab Mitte September frei — Phacelia als Gründüngung (gehört keiner Gemüsefamilie an, stört die Fruchtfolge nicht)." }
  ],
  "unallocated": [
    { "demand_key": "d5", "species_key": "sp_brassica_oleracea", "priority": "must", "reason_code": "no_bed_without_rotation_conflict",
      "least_bad_candidates": [ { "location_key": "loc_b02", "rule": "H-01", "years_short": 1, "earliest_year": 2027 }, { "location_key": "loc_b01", "rule": "H-01", "years_short": 2, "earliest_year": 2028 } ],
      "suggestion_de": "Kohl passt dieses Jahr nirgends ohne Fruchtfolge-Konflikt. Am wenigsten schlecht: Beet 2 (Kreuzblütler zuletzt 2023, Pause fehlt 1 Jahr). Du kannst es trotzdem vorgeben." }
  ],
  "notes": [
    { "code": "history_partial", "detail": { "beds": ["loc_b03"] } },
    { "code": "history_none", "detail": { "beds": ["loc_b02"] } },
    { "code": "seedlings_needed", "detail": { "species_de": "Tomate", "count": 20, "sow_from": "2026-03-15" } },
    { "code": "compost_assumed", "detail": { "beds": ["loc_b01"] } }
  ],
  "computed_at": "…", "computed_by": "u_sabine", "duration_ms": 2140,
  "accepted_at": null, "accepted_by": null
}
```

`reason_code`, `warnings[].code`, `notes[].code` sind geschlossene Enums; `detail` ist strukturiert und trägt zu jeder Familie den Trivialnamen (`*_de`).

### 10.3 Edges und Indizes

`has_planning_request` (sites → planning_requests), `request_produced` (planning_requests → planting_proposals), `allocation_targets` (planting_proposals → locations, `allocation_key`, `slot`), `allocation_materialised_as` (planting_proposals → planting_runs). Indizes: `planting_proposals(tenant_key, site_key, status)`, `planning_requests(tenant_key, site_key)`. `belongs_to_tenant` wird um beide Collections erweitert. Neu an `locations`: `water_access`, `soil_hazards[]`, `usable_fraction`, `greenhouse_offset_days` (REQ-053-Folge-Issue).

### 10.4 Annahme → bestehende Modelle

| Erzeugt | Felder | Quelle |
|---------|--------|--------|
| `PlantingRun` (`planned`) je Belegung | `location_key`, `planned_from`, `planned_until`, `reserved_area_m2` (O-04), `plan_role` (`main_crop` / `green_manure` für angenommene Cover-Vorschläge), `source = crop_planner`, `proposal_key`, `rotation_override_reason` bei `override` | REQ-013, REQ-053 §20.6 |
| `PlantingRunEntry` | `species_key`, `cultivar_key`, `quantity`, `spacing_cm`/`row_spacing_cm` aus Steckbrief, `layout_strategy = rows`; **„vorbelegt"** = Art, Sorte, Menge, Layout-Strategie (F-16) | REQ-053 GP-FR-060 |
| Slots / `run_planned_at` | erst im Bepflanzen-Dialog nach `compute_layout`; bis dahin flächige Reservierung | REQ-053 GP-FR-065 |
| `CropRotationPlan` je Beet/Jahr | `plan_role`, `planned_species_keys`, `nutrient_demand`, `optimization_goal` ← Profil (`yield` als neuer Wert), `proposal_key` | REQ-002 |

---

## 11. API

Alle Pfade unter `/api/v1/t/{tenant_slug}`; Standardregel Lesen „Alle Rollen", Anlegen/Ändern „Ab Gärtner", Löschen „Nur Leitung".

| ID | Methode & Pfad | Zweck | Rolle |
|----|----------------|-------|-------|
| AP-API-001 | `GET\|POST /sites/{key}/planning-requests`, `GET\|PATCH\|DELETE /planning-requests/{key}` | Bedarfslisten mit Geltungsbereich | Alle / Ab Gärtner / Nur Leitung |
| AP-API-002 | `POST /planning-requests/{key}/compute` `{seed?, profile?, weights?}` → 200 `{mode: sync, proposal}` oder 202 `{mode: async, task_id}` | Rechnen | Ab Gärtner |
| AP-API-003 | `GET /planning-requests/{key}/compute/{task_id}` | Fortschritt/Ergebnis | Alle Rollen |
| AP-API-004 | `GET /sites/{key}/planting-proposals?season=&status=`, `GET /planting-proposals/{key}` | Vorschläge | Alle Rollen |
| AP-API-005 | `POST /planting-proposals/{key}/allocations/{akey}/move` `{location_key, slot?, window?}` → neu bewertet + Warnungen (Vorschau); `PATCH …/allocations/{akey}` persistiert; `POST …/unallocated/{dkey}/pin` `{location_key, reason}` erzeugt die least-bad-Fixierung und rechnet den Rest neu | Bearbeiten | Ab Gärtner |
| AP-API-006 | `POST /planting-proposals/{key}/accept` `{allocation_keys[] \| all: true, cover_keys[]?, replace_existing: bool}` → geplante Runs + CropRotationPlan, transaktional je Beet; **Schreibrecht je Beet** (F-05): Beete ohne Recht des Aufrufers bleiben `proposed`, Antwort nennt `forbidden_beds[]`; 409 `proposal.stale` bei geändertem `inputs_hash`; idempotent (D-04) | Annehmen | Ab Gärtner |
| AP-API-007 | `POST /planting-proposals/{key}/replan` `{keep_accepted: true}` | Rest neu planen (SHOULD) | Ab Gärtner |
| AP-API-008 | `POST /planting-proposals/{key}/discard` | Verwerfen | Ab Gärtner (eigene), Nur Leitung (fremde) |
| AP-API-009 | `GET /planting-proposals/compare?a=&b=` | Vergleich (SHOULD) | Alle Rollen |
| AP-API-010 | `GET /sites/{key}/planning-readiness?scope=` → `{beds, beds_with_history, beds_partial, beds_missing_area, beds_missing_water_access, species_missing_fields[]}` | Vorabprüfung | Alle Rollen |
| AP-API-011 | `GET /print/planting-proposal/{key}?locale=` | Druckfassung PDF (AP-UX-009) | Alle Rollen |
| AP-API-012 | `POST\|DELETE /locations/{key}/soil-hazards` | Bodengefahren pflegen (H-10) | Ab Gärtner / Nur Leitung |

Referenzen in Request-Bodies unterliegen REQ-053 GP-NFR-058. Rate-Limit: `compute` 6/min je Nutzer, 20/min je Tenant; `move`/`pin` 60/min; `print` 10/min.

---

## 12. Validierung

| Regel | Ebene | Code | Inhalt |
|-------|-------|------|--------|
| V-01 | API | `validation_error` | ≤ 100 Bedarfe; `quantity > 0` außer `fit`; `fit` verlangt `max_quantity`; `rotation_window_years` 1–8 **und** ≥ größte `rotation_pause_years` im Bedarf (sonst Hinweis `rotation_window_below_pause`); Gewichte 0–2; `available_from` nur bei `in_hand` |
| V-02 | Domain | `planning.site_not_ready` | keine Beete im Geltungsbereich mit Fläche > 0 → 422 mit `readiness` |
| V-03 | Domain | — | Fixierung verletzt H-01/H-05/H-06/H-10 → Belegung mit Warnung und `override`, kein Fehler |
| V-04 | Domain | `proposal.stale` | Annahme nach Änderung von Beeten/Reservierungen → 409 mit `changed[]` |
| V-05 | Domain | `proposal.allocation_conflict` | Verschieben auf Beet/Fenster, das eine harte Regel verletzt → 422 mit Regel; mit `override_reason` erlaubt |
| V-06 | Domain | `planning.too_large` | > 500 Beete oder > 100 Bedarfe |
| V-07 | Domain | `reference.not_found` | fremde/fehlende Keys |
| V-08 | Domain | `proposal.forbidden_bed` | Annahme auf Beet ohne Schreibrecht (je Allocation, übrige gehen durch) |
| V-09 | Domain | `proposal.scope_violation` | Belegung/Fixierung auf Beet außerhalb des Geltungsbereichs → 422 |

Prüfreihenfolge wie REQ-053 §22.1.

---

## 13. Berechtigungen, Datenschutz, Modul

| Ressource | Lesen | Anlegen | Ändern | Löschen | Sonderaktionen |
|-----------|-------|---------|--------|---------|----------------|
| Bedarfsliste | Alle Rollen (O-05) | Ab Gärtner | Ab Gärtner (eigene), Nur Leitung (fremde) | Nur Leitung | Rechnen: Ab Gärtner |
| Vorschlag | Alle Rollen | (durch Rechnen) | Ab Gärtner (Belegung verschieben, nur im eigenen Geltungsbereich) | Nur Leitung | Annehmen: Ab Gärtner **je Beet mit Schreibrecht** (REQ-049 §3.5-Zuweisung zählt hier als Schreibrecht für Parzellen; Gemeinschaftsbeete: Ab Gärtner); Verwerfen: eigene ab Gärtner, fremde Nur Leitung; Druck: Alle Rollen |
| Bodengefahr am Beet | Alle Rollen | Ab Gärtner | Ab Gärtner | Nur Leitung | — |

- Retention NFR-011 R-27 (O-08). Nutzer-Keys (`created_by`, `computed_by`, `accepted_by`, Kommentar-Autor) in der Löschkaskade.
- KI-Prosa (AP-FR-013) nur mit Einwilligung; Eingabe ohne Nutzerfelder.
- Modul `crop_planner` (REQ-042), Navigation „Standorte → Gartenplan → Saison planen"; abhängig von `garden_planner`.

---

## 14. Nichtfunktionale Anforderungen

| ID | Prio | Anforderung |
|----|------|-------------|
| AP-NFR-001 | MUST | Größenklassen wie REQ-053 §25.1: klein (5 Beete, 10 Bedarfe, 3 Fenster) ≤ 1 s sync; mittel (20/30) ≤ 10 s sync; groß (150/60) ≤ 60 s async; Belastungsgrenze 500/100. pytest-Benchmark mit synthetischen Sites. |
| AP-NFR-002 | MUST | Determinismus-Test: 20 Läufe → byte-identisch. |
| AP-NFR-003 | MUST | Property-Tests (Hypothesis): keine harte Regel verletzt; `must` erfüllt oder in `unallocated` mit Kandidaten; Score monoton in Gewichten; Aggregation nach Flächenanteil (Aufteilung erhöht den Score nicht allein durch Summandenzahl). |
| AP-NFR-004 | MUST | **Goldfälle:** die fünf Szenarien (a)–(e) aus `spec/analysis/agrobiology-review-req-054.md` §Goldfälle werden 1:1 als Fixtures `spec/e2e-testcases/fixtures/crop-planning-golden/{a..e}.json` angelegt — mit eigenem `knowledge`-Block je Fixture (Pausen, Zehrerstufen, Flächenbedarf, Kompatibilität, Frostdaten als **Fixture-Setzungen**, unabhängig von Seeds, H-001). Sie prüfen Belegung, `reason_code`, Warnungen und Rangfolge; Scores nur mit Toleranz ±0,05 (H-002). Änderungen an Gewichten oder Regeln aktualisieren die Goldfälle bewusst (Diff im PR). Vor dem Einfrieren sind R-001…R-024 abzuarbeiten (Issue 1). |
| AP-NFR-005 | MUST | Observability: `planning.compute {site_key, scope_size, beds, demands, windows, duration_ms, status, score}`, `planning.accepted {proposal_key, allocations, forbidden_beds}`; Metriken `planning_compute_duration_seconds`, `planning_incomplete_total{reason}`; keine Artnamen oder Nutzertexte in Logs. |
| AP-NFR-006 | MUST | `knowledge_version` am Vorschlag; UI zeigt „mit Wissensstand vom … berechnet". |
| AP-NFR-007 | SHOULD | Engine ohne ArangoDB testbar (Dataclasses; keine eifrige Konstruktion). |
| AP-NFR-008 | MUST | Template-Tests für den Erklärsatz: je Kriterium ein Klauselmuster; verbotene Aussagen (F-14) sind als Negativfälle fixiert. |

---

## 15. MVP und Abgrenzung

**MVP (nach REQ-053 Wellen 0–6, Betreiberentscheid 2026-10-04):** AP-FR-001–006, 008, 011, 012, 014–016; AP-UX-001–004, 006–009; AP-API-001–006, 008, 010–012; V-01–V-09; AP-NFR-001–006, 008; **alle fünf Profile**; **Vor-, Haupt-, Nachkultur und Gründüngung/Mulch-Vorschläge**; **Teilplan mit least-bad-Angebot**; **Druckfassung**; Kriterien `rotation`, `pest_risk`, `companion`, `nutrition`, `space`, `timing`, `preference`, `site_fit` (inkl. Rankhilfe), `effort` (inkl. Wasserzugang), `soil_cover`, `root_depth_rotation`, `soil_fit`, `rotation_future`; H-01…H-10.

**Nicht im MVP:** Vergleich (AP-UX-005), Rest-neu-planen (AP-FR-007), Beetkommentare (AP-UX-010), H-11 (wartet auf REQ-001 `pathogen_hosts`), `water_match`, `shading_neighbour`, `care_load`, Ertrag (§7.4), Mehrjahresplanung (AP-FR-009), Solver (AP-FR-010), KI-Prosa (AP-FR-013), Frost-Perzentile.

**Voraussetzungen (Folge-Issues anderer Dokumente):** REQ-053: `water_access`, `soil_hazards`, `usable_fraction`, `greenhouse_offset_days` an Location; Historie-Eingänge (Gründüngung Art/Leguminose/Einarbeitung, Mengen je m², Kalkung, `confirmed`-Flag, Ernterückstände); Seed-Schema: `light_requirement`, `crop_organ`, `plants_per_person`, `harvest_window_days`, vorzeichenbehaftete Frost-Offsets / `growing_periods`-Anker `first_frost`/`calendar`; REQ-001: `soil_persistence_years`, `pathogen_hosts`; REQ-053 §16.3 v0077.

---

## 16. Akzeptanzkriterien

- **AP-ACC-001** (U) Given 3 Beete (je 4 m², `usable_fraction` 1,0; Historie: B1 2025 Fabaceae geerntet, B2 2025 Solanaceae, B3 keine) und Bedarf Tomate 6 Stück `must` (0,48 m²/Pflanze, Solanaceae, Pause 4), When `plan()` mit „Ausgewogen", Then liegt die Tomate in B1 (Breakdown `rotation = +0,4 heavy_after_legume_harvested`), B2 ist in `alternatives` mit `main_difference = rotation_pause_violated`, B3 trägt `history_coverage = none`, And `notes` enthält `history_none` mit `["B3"]`.
- **AP-ACC-002** (U) Given dieselbe Eingabe, When `plan()` 20-mal läuft, Then byte-identische Ergebnisse.
- **AP-ACC-003** (U, F-01) Given Kohl `must`, alle Beete mit Brassicaceae in den letzten 3 Jahren bei Pause 4, und zwei weitere erfüllbare Bedarfe, When `plan()`, Then `status = proposed_incomplete`, zwei Allocations existieren, `unallocated[0].least_bad_candidates[0]` nennt das Beet mit `years_short = 1` und `earliest_year`, And keine Allocation für Kohl.
- **AP-ACC-004** (U) Given Kohl `must` mit `pinned_location_key = B2` (Brassicaceae 2024), When `plan()`, Then Allocation in B2 mit `warnings[0].code = rotation_pause_violated`, `override.kind = pinned_by_user`, Status `proposed`; And bei Annahme trägt der Run `rotation_override_reason`; And der Breakdown enthält **keinen** positiven `preference`-Beitrag für die Fixierung.
- **AP-ACC-005** (U) Given Tomate 20 Stück `in_hand`, `available_from = 2026-05-10`, 3 Beete à 4 m² (7 Pflanzen je Beet), When `plan()`, Then 20 Pflanzen vollständig auf 3 Beete verteilt (7+7+6), jedes `window.from ≥ 2026-05-15` (Frost-Sicherheitsdatum) und `≥ available_from`, `effort` zeigt `split_across_beds {beds: 3}` mit `s = −1,0` (geklemmt), And der Gesamtscore ist **nicht** höher als bei einer hypothetischen Einzelbelegung derselben Fläche (Aggregation nach `share`).
- **AP-ACC-006** (U) Given Bohne und Zwiebel (`severe`) als `must` und ein Beet, Then Bohne oder Zwiebel in `unallocated` mit `reason_code = severe_incompatibility`, Status `proposed_incomplete`; mit zwei Beeten, die `adjacent_to.distance_cm = 60` sind, Then je eins mit `warnings[severe_incompatibility_neighbour]` und `companion = −1,0`; mit `distance_cm = 20`, Then wieder `unallocated`.
- **AP-ACC-007** (U) Given „Boden schonen" vs. „Ausgewogen", ein Beet mit P-Klasse A ohne Düngung und ein Beet mit Klasse C, When beide laufen, Then landet der Starkzehrer unter „Boden schonen" auf dem C-Beet; And ein Beet mit Klasse E erhält in `nutrition` 0, nicht +.
- **AP-ACC-008** (I) Given ein Vorschlag mit 4 Allocations und 1 Cover-Vorschlag, When `POST /accept {all: true, cover_keys: [c1]}`, Then 5 `planting_runs` (`planned`, `source = crop_planner`, `reserved_area_m2` gesetzt, einer mit `plan_role = green_manure`), 5 `CropRotationPlan`-Einträge, Vorschlag `accepted`; When derselbe Aufruf wiederholt wird, Then 200 ohne Duplikate (D-04); And in `GET /plan` (REQ-053) tragen die Beete das Muster „reserviert, ohne Positionen".
- **AP-ACC-009** (I) Given ein Vorschlag, dessen Beet B1 nach `computed_at` eine neue **angenommene** Reservierung bekam, When `POST /accept`, Then 409 `proposal.stale` mit `changed = ["B1"]`; Given stattdessen nur ein weiterer **unangenommener** Vorschlag auf B1, Then 200 (H-04).
- **AP-ACC-010** (I) Given 150 Beete und 60 Bedarfe mit drei Fenstern, When `POST /compute`, Then 202 + Ergebnis ≤ 60 s, alle harten Regeln erfüllt.
- **AP-ACC-011** (E) Given die Ergebnisansicht, When der Nutzer Beet B1 anklickt, Then sieht er den Satz mit deutschen Familiennamen, darunter je Kriterium Symbol + Kurztext **ohne** Spalte „Gewicht", unter „Details für Fortgeschrittene" die Zahlen, „Warum nicht Beet 2?" mit Hauptunterschied, And „Hierhin verschieben" zeigt vor dem Speichern Score-Differenz und Warnung.
- **AP-ACC-012** (E) Given ein `unallocated`-Bedarf, Then steht er in der Seitenleiste mit Grund, least-bad-Angebot „Trotzdem in Beet 2 (Anbaupause fehlt 1 Jahr)" und Historie-Hinweis mit Link; When der Nutzer das Angebot wählt, Then wird neu gerechnet, die Belegung trägt die Warnung, der Rest bleibt.
- **AP-ACC-013** (E, 390 × 844) Given ein Vorschlag mit einer Belegung mit Warnung, Then zeigt die Liste das Warnsymbol mit Text **vor** „Annehmen", „alle annehmen" verlangt die Bestätigung „1 Beet mit Warnung", Alternativen sind aufklappbar, „Gewichte" ist deaktiviert mit Hinweis.
- **AP-ACC-014** (U) Given Tenant B besitzt Beet X, When Tenant A `pinned_location_key = X` sendet, Then 422 `reference.not_found`; Given Beet Y derselben Site außerhalb des Geltungsbereichs, Then 422 `proposal.scope_violation`.
- **AP-ACC-015** (U, Goldfälle) Given die Fixtures (a)–(e) aus dem Agrobiologie-Bericht, When `plan()`, Then entsprechen Belegung, `reason_code`s, Warnungen und Rangfolge der erwarteten Ausgabe; Scores innerhalb ±0,05.
- **AP-ACC-016** (U, F-03) Given Erdbeeren (mehrjährig, `removed_on = null`, Pflanzjahr 2024) auf 2 m² von Beet B3, When `plan()`, Then stehen in B3 nur 2 m² zur Verfügung (H-02/H-04); And „Vorjahr übernehmen" erzeugt keinen Bedarf für Erdbeeren und meldet „1 Dauerkultur nicht übernommen".
- **AP-ACC-017** (U, F-04/K-003) Given Site `last_frost_date_avg = 2026-04-20`, `eisheilige_date = 2026-05-15`, Tomate (`frost_sensitivity = high`, Offset 7 Tage) auf einem Beet ohne Frostschutz, Then `window.from = 2026-05-15`, `window_source = frost_safe_date`; auf einem `greenhouse_bed` mit `greenhouse_offset_days = −21`, Then `window.from = 2026-04-24`.
- **AP-ACC-018** (I, F-05) Given zwei Parzellen, Nutzer A schreibberechtigt nur an P1, ein Vorschlag mit Allocations in P1 und P2, When A `POST /accept {all: true}`, Then Runs nur in P1, P2-Allocation unverändert `proposed`, Antwort `forbidden_beds = [P2]`.
- **AP-ACC-019** (U, F-09) Given Beet mit Frühsalat-Fenster (Asteraceae) bis 15. Juni und Bedarf Buschbohne (Fabaceae), When `plan()`, Then zwei Allocations im selben Beet mit `slot = pre` (Salat, bis 15.06.) und `slot = main` (Bohne, ab ≥ 22.06. — `turnaround_days` 7); Given stattdessen Kohlrabi als Vorkultur und Blumenkohl als Hauptkultur (beide Brassicaceae), Then nicht im selben Beet (H-01 gleiche Familie innerhalb der Saison).
- **AP-ACC-020** (U, W-009) Given ein Beet, das nach der Hauptkultur am 10. September frei wird, und kein weiterer Bedarf, When `plan()`, Then enthält `cover_suggestions` für dieses Beet eine Gründüngung aus `green_manure_suitable`-Arten, die H-01 gegen die Beet-Historie besteht (Senf nicht nach Kohl), oder Mulch; And `soil_cover` des Beets ist +0,3 statt −0,5.
- **AP-ACC-021** (U, F-17) Given ein `planned`-Run aus 2025, der nie gestartet wurde (Solanaceae), When `plan()` für 2026, Then verändert er weder H-01 noch `rotation` für dieses Beet.
- **AP-ACC-022** (U, K-001) Given Beet B1 mit `soil_hazards = [{hazard: clubroot, affected_families: [Brassicaceae], confirmed_at: 2022-07-01}]` und `soil_persistence_years(clubroot) = 15` (Fixture-Setzung), When Kohl geplant wird, Then ist B1 ausgeschlossen (`reason_code = soil_hazard`), auch wenn die Familienpause von 4 Jahren erfüllt wäre; And Fixierung auf B1 erzeugt `warnings[persistent_soil_pathogen]`.
- **AP-ACC-023** (U, K-001) Given Beet mit Historie nur für 2024 und 2025 (2022/2023 ohne Eintrag) und Bedarf mit Pause 4, When `plan()`, Then trägt die Allocation `warnings[history_gap_in_pause_window]`, And der Pause-Bonus in `rotation` ist 0.
- **AP-ACC-024** (U, K-007) Given ein Fenster, in dem die Kulturdauer das Fensterende bis auf 10 Tage ausfüllt, Then `timing = −0,3` mit `reason_code = buffer_below_14_days`; bei 20 Tagen Puffer `timing = 0`.
- **AP-ACC-025** (U, W-005) Given Bedarf Stangenbohne (`support_required = true`) und zwei Beete, eines mit `trellis` in 0,3 m Entfernung, Then liegt die Bohne am Rankhilfe-Beet; das andere trägt in `alternatives` `main_difference = support_missing`.
- **AP-ACC-026** (U, W-005) Given 5 Beete und Bedarfe, bei denen die gierige Belegung das letzte für Brassicaceae im Folgejahr zulässige Beet verbrauchen würde, When `plan()` mit `rotation_future` aktiv, Then wählt der Planer die Variante, die mindestens ein Beet für Brassicaceae 2027 freilässt, sofern der Score-Verlust < 0,5 ist.
- **AP-ACC-027** (I, F-18) Given ein Vorschlag mit 2 Warnungen und 1 `unallocated`, When `GET /print/planting-proposal/{key}`, Then enthält das PDF den Abschnitt „Zu besprechen" zuerst (3 Einträge), danach alle Beete mit Fenster, Art und Satz, keine Scores, keine Nutzernamen.

---

## 17. Offene Fragen — entschieden

Alle Punkte O-01…O-08 (v1.1) und die Review-Entscheidungen (v1.2) sind entschieden; die Tabelle ist Protokoll.

| ID | Frage | Entscheidung | Eingearbeitet |
|----|-------|--------------|---------------|
| O-01 | Quelle `Species.light_requirement` | Steckbrief-Pipeline | §5.5 |
| O-02 | Flächenbedarf je Pflanze | `spacing × row_spacing`, Fallback `spacing²` | §5.5 |
| O-03 | Absicherung der Startwerte | Reviews jetzt (erfolgt), Goldfälle vor P1 | §7.5, AP-NFR-004 |
| O-04 | Reservierung vor Layout | `PlantingRun.reserved_area_m2` + `planned_from/until` | §10.4 |
| O-05 | Lesen durch Beobachter | alle Rollen | §13 |
| O-06 | Fenster in Tagen | frostdaten-basiert, Monats-Fallback — **präzisiert** v1.2: Sicherheitsdatum für frostempfindliche Arten, `growing_periods`-Anker | §5.5 |
| O-07 | Mehrjahresplanung | COULD; `rotation_future` deckt den Alltag | AP-FR-009, §7.2 |
| O-08 | Retention | NFR-011 R-27 | §13 |
| O-09 (neu) | Quelle für `plants_per_person`, `crop_organ`, `harvest_window_days`, `water_demand_class` | Steckbrief-Pipeline (Issue 2); bis dahin: Mengenhilfe ausgeblendet, `crop_organ` aus `harvested_part`, Erntefenster aus Monaten, Wasserbedarf aus `watering_interval_days` | §5.5 |
| F-01/W-003 | Teilplan statt `infeasible` | **`proposed_incomplete` + least-bad** | §8.3 |
| F-09/W-009 | Vor-/Nachkultur, Gründüngung | **voll im MVP** | AP-FR-008 |
| F-10/F-18 | „Wenig Arbeit", Druckfassung | **beides im MVP** | §7.3, AP-UX-009 |
| W-005 | neue Kriterien | **alle vier im MVP** | §7.2 |

---

## 18. Entscheidungsvorlagen

| ID | Entscheidung | Optionen | Empfehlung | Begründung |
|----|--------------|----------|------------|------------|
| **D-01** | Planer-Technologie | LLM · Optimierer · beides | **Optimierer**, LLM nur Prosa | Erklärbarkeit in Zahlen, Reproduzierbarkeit, Goldfälle, lokal ohne Modell |
| **D-02** | Solver | reines Python · OR-Tools · MILP | **reines Python**, Solver COULD | Problemgrößen klein; native Abhängigkeit kostet |
| **D-03** | Härtegrade konfigurierbar | ja · nein | **nein** | weiche Anbaupause = Fehlergenerator; Übersteuerung sichtbar per Fixierung |
| **D-04** | Annahme idempotent | 409 · idempotent | **idempotent** | Netzabbruch im Garten |
| **D-05** | Ausgabe-Modell | eigene Collection dauerhaft · in Runs überführen | **Vorschlag bleibt, Annahme erzeugt Runs + CropRotationPlan** | Nachvollziehbarkeit über Jahre |
| **D-06** | Ergebnisansicht | eigener Canvas · Ebene im Plan | **Ebene** | ein Renderer |
| **D-07** | Unerfüllbarer `must` | Totalausfall · Teilplan | **Teilplan `proposed_incomplete`** (F-01) | ein Konflikt darf 8 richtige Belegungen nicht verwerfen |
| **D-08** | Score-Aggregation | Summe je Belegung · nach Flächenanteil | **nach Flächenanteil, pest max, companion min** (K-005) | Summe belohnt Zerstückelung, Mittel verdünnt Konflikte |
| **D-09** | Frostanker | Mittelwert · Sicherheitsdatum | **Sicherheitsdatum (`eisheilige_date`) für frostempfindliche Arten** (K-003/F-04) | Mittelwert = 50 % Risiko |
| **D-10** | Unangenommene Vorschläge als Reservierung | ja · nein | **nein** (W-001) | sonst blockieren sich Vorschläge gegenseitig |
| **D-11** | `severe` zwischen Nachbarbeeten | hart · weich | **weich ab 30 cm** (W-001) | Datenfehler darf kein Beet sperren |
| **D-12** | Geltungsbereich und Beet-Schreibrechte | Site-weit · Scope + Recht je Beet | **Scope + Recht je Beet** (F-05) | Gemeinschaftsgarten |

---

## 19. Roadmap und Issue-Kandidaten

Abhängig von REQ-053 Wellen 0–6 und den Folge-Issues in §15.

| Welle | Inhalt | Schätzung |
|-------|--------|-----------|
| **P0 — Spec-Abschluss** | ✅ O-01…O-09, Reviews (2026-10-04); Recherche R-001…R-024; fünf Goldfälle als JSON-Fixtures; `TC-REQ-054.md`; Folge-Issues an REQ-053/REQ-001/Schema | 2 Wochen |
| **P1 — Engine** | Dataclasses, `plan()`, H-01…H-10, 13 Kriterien, Zehrer-Matrix, Fensterableitung (Anker, Sicherheitsdatum, Gewächshaus-Offset, Voranzucht, Erntefenster, Turnaround), drei Fenster je Beet, Cover-Vorschläge, Teilplan/least-bad, `rotation_future`, Erklärungsgenerator mit Trivialnamen, Property-/Template-/Gold-/Benchmark-Tests | 5 Wochen |
| **P2 — Daten & API** | Collections, Historie-Aggregation, Service, Endpunkte inkl. Scope/Schreibrecht, Celery, Annahme-Transaktion mit Cover, Stale, Idempotenz, Druck-Endpunkt, Bodengefahren-Pflege, NFR-011 R-27 | 3 Wochen |
| **P3 — Oberfläche** | Bedarfserfassung (Bestand, Mengenhilfe, Vorjahr-Ist), Scope, Readiness, Ergebnis-Ebene, Symbol-Breakdown, Alternativen, Verschieben, least-bad, Annahmedialog, „Zu besprechen", Druck, Mobil-Liste mit Warnungen, i18n, testids, E2E | 4 Wochen |
| **P4 — SHOULD** | Vergleich, Rest-neu-planen, Beetkommentare, `water_match`, H-11 (nach REQ-001), `care_load` | 3 Wochen |

| # | Issue-Kandidat | IDs | Größe |
|---|----------------|-----|-------|
| 1 | spec(REQ-054): research R-001…R-024, freeze heuristics, author five golden fixtures (a–e) from the agrobiology report | §7.5, AP-NFR-004 | M |
| 2 | feat(knowledge): Species.light_requirement, crop_organ, plants_per_person, harvest_window_days, water_demand_class; growing_periods anchors first_frost/calendar + signed offsets; Steckbrief pipeline | O-01, O-09, K-004 | M |
| 3 | spec(REQ-053): Location.water_access, soil_hazards[], usable_fraction, greenhouse_offset_days; history inputs (green manure species/legume/incorporation, amounts per m², liming, confirmed flag, residues); PlantingRun.residues | §5.2, §5.3, W-006 | M |
| 4 | spec(REQ-001): soil_persistence_years per hazard, pathogen_hosts (pathogen → host families), APG IV family names in seeds | K-001, K-002, H-11 | M |
| 5 | feat(engine): planting_planner_engine — H-01…H-10, 13 criteria, matrix, window derivation, three windows per bed, cover suggestions, partial plan + least-bad, rotation_future, explanation generator; property/template/golden/benchmark tests | AP-FR-001–006, 008, 011–016, AP-NFR-001–004, 008 | XL |
| 6 | feat(planning): collections, history aggregation, service, compute (sync/async), scope + per-bed write check on accept, cover acceptance, stale/idempotent, soil-hazard endpoints, print endpoint | AP-API-001–006, 010–012, V-01–V-09 | L |
| 7 | feat(frontend): crop planning pages — demand list (in_hand, keep place, fit with max, succession, per-person helper), scope, readiness, proposal layer, symbol breakdown + details, alternatives, move, least-bad pin, accept dialog, discuss list, print, mobile list | AP-UX-001–004, 006–009 | XL |
| 8 | test(e2e): TC-REQ-054 | AP-ACC-011–013, 027 | M |
| 9 | feat(planning): compare, replan-keeping-accepted, bed comments, water_match, H-11, care_load | AP-FR-007, AP-UX-005/010, §7.2 | L |
| 10 | spec(REQ-002): CropRotationPlan.optimization_goal gets value `yield` and REQ-054 as consumer; REQ-053 §29 rows point to REQ-054 | W-010 | S |
