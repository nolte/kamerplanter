# Spezifikation: REQ-054 - Automatische Anbauplanung

```yaml
ID: REQ-054
Titel: Automatische Anbauplanung — aus einer Pflanzenliste und der Beet-Historie eine erklärbare, optimierte Beetbelegung je Saison ableiten
Kategorie: Planung & Empfehlung
Fokus: Nutzpflanze (Freiland, Gewächshaus, Hochbeet, Kübel)
Technologie: Python 3.14+, FastAPI, Celery, ArangoDB, React 19, TypeScript 6, MUI 9
Status: Entwurf
Priorität: Mittel (nach REQ-053 MVP)
Version: 1.1 (alle offenen Punkte O-01…O-08 entschieden)
Datum: 2026-10-04
Tags: [crop-planning, optimisation, crop-rotation, companion-planting, explainability, proposal]
Abhängigkeit: REQ-053 v1.2 (Beete mit Geometrie und Fläche, `care_events`, `season_state`, Zeitfenster-Reservierung `run_planned_at`, Beet-Validator GP-FR-131, `NutrientDemand`/`nitrogen_fixing`/`PlanRole` §16.3, `rotation_exempt`, Layout-Rechner GP-FR-062), REQ-001 v4.x (`rotation_after.benefit_score`, `shares_pest_risk`, BotanicalFamily), REQ-002 v4.4 (`CropRotationPlan`, `optimization_goal`), REQ-013 v2.7 (PlantingRun `planned`, Entries, Sukzession), REQ-028 (`compatible_with`/`incompatible_with` mit Score/Severity, `adjacent_to`), REQ-015/REQ-015-A (Aussaatkalender: Saat-/Pflanz-/Erntefenster je Art und Site), REQ-046/REQ-039 (Frostdaten, Klimazone), REQ-007 (Ertrags-Historie `yield_per_m2_g`), REQ-024 v1.7 (Mandant), REQ-049 v1.4 (Rollenvokabular), REQ-042 (Modul-Sichtbarkeit), REQ-031 (KI-Assistent — nur als optionale Erklärschicht), NFR-006 (Fehlerformat), NFR-007 (Observability)
Wird benötigt von: —
```

## Versionshistorie

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.1 | 2026-10-04 | **Alle offenen Punkte entschieden** (Betreiber, §17): `Species.light_requirement` über die Steckbrief-Pipeline (O-01); Flächenbedarf `spacing × row_spacing`, Fallback `spacing²` (O-02); Reviews jetzt, fünf Goldfälle vor Welle P1 (O-03); `PlantingRun.reserved_area_m2`, Positionen erst im Dialog (O-04); Lesen für alle Rollen (O-05); Zeitfenster frostdaten-basiert mit Monats-Fallback (O-06); Mehrjahresplanung bleibt COULD (O-07); Retention: mit dem Request, verworfene Vorschläge 1 Jahr — NFR-011 R-27 (O-08). |
| 1.0 | 2026-10-04 | Erstfassung. Beantwortet die Frage, ob eine automatische Beetbelegung vorgesehen ist (bisher: nein — REQ-053 §29 führt „Automatische Fruchtfolge-/Mischkulturplanung" als WON'T, REQ-002 trägt ein `optimization_goal` ohne Algorithmus, REQ-001 §2.4 empfiehlt eine Rotationsfolge nur für **ein** Beet). Definiert das Planungsproblem als Zuordnung Pflanzenbedarf × Beete × Zeitfenster mit harten Restriktionen (§6), gewichteter Zielfunktion (§7), deterministischem Verfahren mit Erklärung je Zuordnung (§8), Vorschlag-statt-Ausführung (§9) und der Historie der letzten Jahre als Pflichteingang (§5). |

---

## 0. Verhältnis zu bestehenden Spezifikationen

| Dokument | Liefert | Verhältnis zu REQ-054 |
|----------|---------|-----------------------|
| **REQ-053** | Beete mit Fläche, Historie je Beet (`care_events`, Pflanzungen, `season_state` je Jahr), Beet-Validator mit Anbaupausen, Zeitfenster-Reservierungen, Layout-Rechner | **Datengrundlage und Ausgabeziel.** REQ-054 liest, was REQ-053 persistiert, und schreibt seine Vorschläge als geplante Runs mit `run_planned_at` (REQ-053 GP-FR-065). Ohne REQ-053-MVP ist REQ-054 nicht implementierbar. |
| **REQ-001 / REQ-002** | Rotationsgraph (`rotation_after` mit `benefit_score`), `shares_pest_risk`, `CropRotationPlan` mit `optimization_goal` | Der Graph ist die **Wissensquelle** der Fruchtfolge-Bewertung. `CropRotationPlan` wird zum **Ausgabeformat** des akzeptierten Vorschlags (§10.4); `optimization_goal` bekommt hier erstmals einen Konsumenten (§7.3). |
| **REQ-028** | Kompatibilität Art × Art, Familie × Familie, `adjacent_to` | **Wissensquelle** der Mischkultur-Bewertung; REQ-054 erzeugt Nachbarschaften erst durch seine Zuordnung und bewertet sie vorab über Beet-Nachbarschaft (§7.2). |
| **REQ-015 / REQ-015-A** | Saat-, Pflanz- und Erntefenster je Art, Site und Klimazone | **Wissensquelle** der zeitlichen Machbarkeit: ein Zeitfenster, das REQ-015-A nicht zulässt, ist für REQ-054 unzulässig (§6). |
| **REQ-013** | Runs, Entries, Sukzession | Ausgabeformat (geplante Runs); Sukzession bleibt REQ-013 — REQ-054 plant **Belegungen**, keine Staffelung innerhalb einer Belegung (§2.3). |
| **REQ-031** | KI-Assistent, LLM-Adapter (lokal/Cloud, Einwilligung) | **Nicht** die Planungs-Engine. Optional nur als Erklärschicht, die eine bereits berechnete Begründung in Prosa fasst (§8.5, D-01). |

---

## 1. Business Case

### 1.1 User Stories

- *Als Freilandgärtnerin (Sabine, ZG-002) möchte ich im Januar meine Wunschliste eingeben — Tomaten, Zucchini, Bohnen, Salat, Möhren, Kräuter — und einen Vorschlag bekommen, welches Beet was bekommt, der die letzten drei Jahre berücksichtigt, damit ich nicht wieder Kohl nach Kohl setze und die Starkzehrer dorthin kommen, wo letztes Jahr Bohnen standen.*
- *Als Leitung eines Gemeinschaftsgartens (Tom, ZG-004) möchte ich für die gemeinsam bewirtschafteten Beete einen Plan vorschlagen lassen und ihn vor der Mitgliederversammlung durchgehen, damit die Diskussion bei den strittigen Beeten beginnt und nicht bei null.*
- *Als Gärtnermeister (Jonas, UZG-005) möchte ich dem Planer sagen, dass Tomaten im Tunnel bleiben und Beet 7 brach liegt, und für den Rest einen Vorschlag bekommen, der die Reihenkapazität ausnutzt.*
- *Als Nutzer ohne Fruchtfolge-Wissen (Aisha, ZG-004) möchte ich bei jedem Vorschlag lesen, **warum** eine Pflanze in dieses Beet soll, damit ich etwas lerne und dem Plan vertraue.*

### 1.2 Warum eine eigene Anforderung

Die Bausteine existieren verstreut: ein Validator, der eine gewählte Art gegen ein Beet prüft; eine Empfehlung, welche Familie in **einem** Beet als nächstes sinnvoll wäre; ein Kompatibilitäts-Check für gewählte Nachbarn; ein Layout-Rechner innerhalb eines Beets. Keiner beantwortet die Frage „ich habe diese Pflanzen und diese Beete — wie belege ich sie?". Das ist ein **Zuordnungsproblem** mit Restriktionen und Zielkonflikten (Fruchtfolge gegen Mischkultur gegen Flächenausnutzung gegen Nutzerwunsch), und seine Entscheidungen — welche Regel hart ist, welche weich, was gewichtet wird — sind fachlich, nicht technisch. Sie gehören in eine Spezifikation, nicht in einen Algorithmus-Kommentar.

### 1.3 Leitplanken

1. **Vorschlag, nie Ausführung.** Der Planer legt nichts an, bevor der Nutzer nicht je Beet akzeptiert hat. Akzeptierte Zuordnungen werden geplante Runs (REQ-053 §11).
2. **Erklärbar je Zuordnung.** Jede Zuordnung nennt die Beiträge zur Bewertung (Fruchtfolge, Nachbarn, Fläche, Zeit, Wunsch) und die Alternativen, die verworfen wurden — in Zahlen und in einem Satz.
3. **Deterministisch.** Dieselbe Eingabe ergibt denselben Vorschlag (Seed für Tie-Breaks). Der Nutzer kann einen Vorschlag reproduzieren, vergleichen und als Testfall einfrieren.
4. **Historie ist Pflichteingang.** Ohne Beet-Historie läuft der Planer, sagt aber, dass er blind plant (§5.4). Nacherfasste Vorjahre (REQ-053 GP-FR-131) zählen wie gemessene.
5. **Fachregeln bleiben in ihren Quellen.** Anbaupausen in `BotanicalFamily.rotation_pause_years`, Kompatibilität in REQ-028, Zeitfenster in REQ-015-A. REQ-054 **kombiniert**, es definiert keine Agronomie neu.

---

## 2. Ziel und Scope

### 2.1 Ziel

Aus einer Bedarfsliste (Arten/Sorten mit Menge), einem Planungszeitraum und den Beeten einer Site eine Belegung berechnen, die alle harten Restriktionen erfüllt und die gewichtete Zielfunktion maximiert — und sie so präsentieren, dass der Nutzer sie beetweise annehmen, ändern oder verwerfen kann.

### 2.2 Im Scope

- Bedarfsliste mit Mengenangabe in Stück, m² oder „wie es passt"; Fixierungen und Ausschlüsse je Beet.
- Planungszeitraum: eine Saison (Hauptkultur), optional mit Vor- und Nachkultur je Beet (zwei Zeitfenster).
- Harte Restriktionen (§6) und gewichtete Ziele (§7) mit drei Standardprofilen und manueller Gewichtung.
- Historie der letzten `rotation_window_years` (Standard 4, bis 8) je Beet aus REQ-053.
- Deterministischer Optimierer (§8) mit Alternativen je Beet und Begründung.
- Vorschlag als Dokument (`planting_proposals`) mit Status, Annahme je Zuordnung, Umwandlung in geplante Runs.
- Mehrere Vorschläge je Saison vergleichen.

### 2.3 Nicht im Scope

- Positionen **innerhalb** eines Beets (das macht REQ-053 `compute_layout` nach der Annahme).
- Sukzessions-Staffelung innerhalb einer Belegung (REQ-013 `SuccessionPlan`).
- Ertrags-**Prognose** in kg (nur Flächenbedarf aus Stückzahl; Ertrag als Ziel erst mit genügend Historie, §7.4 COULD).
- Automatisches Anlegen neuer Beete („du bräuchtest 4 m² mehr") — nur ein Hinweis auf nicht unterbringbaren Bedarf.
- Sonnen-/Schattenberechnung (REQ-053 §29); `sun_exposure` wird als manuell gepflegte Beeteigenschaft gelesen.
- LLM als Planer. Ein LLM darf die berechnete Begründung umformulieren, nie die Zuordnung bestimmen (D-01).

---

## 3. Begriffe

| Begriff | Definition |
|---------|------------|
| **Bedarf** (`DemandItem`) | Eine Art/Sorte mit Menge und optionalen Vorgaben (bevorzugte/ausgeschlossene Beete, Zeitfenster, Priorität). |
| **Belegungseinheit** (`Allocation`) | Die Zuordnung eines Bedarfs (ganz oder anteilig) zu einem Beet in einem Zeitfenster; Ergebnis des Planers. |
| **Vorschlag** (`PlantingProposal`) | Menge aller Belegungseinheiten einer Planung plus nicht unterbringbarer Rest, Bewertung und Begründungen. |
| **Zeitfenster** | `[from, until]` in Kalenderdaten; für Hauptkultur aus REQ-015-A (Pflanz-/Saatfenster bis Ernteende), für Vor-/Nachkultur daraus abgeleitet. |
| **Profil** | Vordefinierter Gewichtssatz der Zielfunktion (§7.3): `balanced`, `soil_health`, `yield`, `low_effort`. |
| **Härtegrad** | Hart (nie verletzt) oder weich (Strafterm). Die Zuordnung Regel → Härtegrad steht in §6/§7 und ist nicht konfigurierbar. |

---

## 4. Fachliches Modell

```
PlanningRequest ──has_demand──▶ DemandItem (1..n)
PlanningRequest ──for_site──▶ Site
PlanningRequest ──produced──▶ PlantingProposal (0..n, je Lauf)
PlantingProposal ──has_allocation──▶ Allocation (0..n) ──targets──▶ Location (Beet)
Allocation ──fulfils──▶ DemandItem
Allocation (accepted) ──materialised_as──▶ PlantingRun (status planned, run_planned_at mit Zeitfenster)
PlantingProposal (accepted) ──summarised_as──▶ CropRotationPlan (Beet × Jahr, plan_role, planned_species_keys)
```

Ein `PlanningRequest` ist wiederverwendbar: Der Nutzer ändert Gewichte oder Fixierungen und lässt erneut rechnen; jeder Lauf erzeugt einen neuen `PlantingProposal` (Vergleich §9.4).

---

## 5. Eingangsdaten

### 5.1 Bedarf (Nutzereingabe)

| Feld | Regel |
|------|-------|
| `species_key`, `cultivar_key?` | Stammdaten (REQ-001); Sorte optional, beeinflusst nur Zeitfenster/Abstände, wenn die Sorte Werte überschreibt |
| `quantity`, `quantity_unit ∈ {plants, m2, fit}` | `fit` = „so viel wie passt" (wird zuletzt zugeteilt, füllt Rest) |
| `priority ∈ {must, want, nice}` | `must` darf nie unerfüllt bleiben, sonst ist der Vorschlag `infeasible` mit Begründung |
| `preferred_location_keys[]`, `excluded_location_keys[]` | weiche Präferenz bzw. harter Ausschluss |
| `pinned_location_key?` | harte Fixierung („Tomaten in Beet 2") — der Planer prüft nur noch die Machbarkeit und warnt |
| `window_override?` | explizites Zeitfenster statt REQ-015-A-Ableitung |

### 5.2 Beete (REQ-053)

Je Beet mit `bed_status = active` und `supports_layout`: Fläche (`area_m2`), `sun_exposure`, `soil_profile` (`growing_medium_kind`, `soil_texture`, `ph`, `rotation_exempt`, `rotation_reset_at`), Beettyp (`greenhouse_bed`, `planter` …), geplante/aktive Reservierungen (`run_planned_at`, aktive Runs mit erwartetem Ende), Nachbarschaft Beet ↔ Beet (Beetkanten ≤ 50 cm, REQ-053 GP-FR-130 SHOULD; fehlt sie, gilt „keine Nachbarn" und die Mischkultur-Bewertung ist neutral).

### 5.3 Historie (REQ-053) — Pflichteingang

Je Beet und Jahr im Rückblick `rotation_window_years`: Familien und Arten der Hauptkultur, Vor-/Nachkulturen, `season_state` (`green_manure` zählt **mit Familie**, `fallow` als Pause), `plan_role`, Düngegaben mit Nährstoffwirkung (`care_events` `feeding`/`soil_amendment`), letzte Bodenanalyse (Gehaltsklassen), Ertragsereignisse (`harvest_batches` → `yield_per_m2_g`, REQ-007) und Probleme (`care_events` `category ∈ {pest_control, ipm}` oder Tagebuch-`problem` mit Familienbezug). Quelle sind gemessene Daten **und** nacherfasste Vorjahre (REQ-053 GP-FR-131); nacherfasste Einträge tragen `source = backfill`.

### 5.4 Fehlende Historie

Hat ein Beet keine Historie im Rückblick, bewertet der Planer die Fruchtfolge dort als **unbekannt** (neutral 0, nicht als „frei"), markiert die Zuordnung mit `history_coverage = none` und der Vorschlag trägt den Hinweis „n von m Beeten ohne Historie — Vorjahre nacherfassen verbessert den Plan". `must`-Bedarfe werden bevorzugt auf Beete **mit** Historie gelegt, wenn die Bewertung sonst gleich ist.

### 5.5 Wissensquellen (global)

- Anbaupause: `BotanicalFamily.rotation_pause_years`, Spezies-Override (REQ-053 K-004).
- Rotationsnutzen: `rotation_after.benefit_score` (−1 … +1) und `benefit_reason` (REQ-001).
- Schädlingsrisiko: `shares_pest_risk.risk_level` zwischen Familien (REQ-001).
- Kompatibilität: `compatible_with.compatibility_score` (0–1), `incompatible_with.severity` (`mild|moderate|severe`), Familien-Fallback (REQ-028).
- Zehrerstufe: `Species.nutrient_demand`, `nitrogen_fixing` (REQ-053 §16.3).
- Zeitfenster: REQ-015-A je Site/Klimazone (Frostdaten REQ-046).
- Flächenbedarf (O-02, entschieden): m² je Pflanze = `spacing_cm × row_spacing_cm / 10 000`; fehlt `row_spacing_cm`, gilt `spacing_cm²`; Rechner ist `slot_capacity_calculator.calculate_plants_per_m2(spacing, row_spacing, strategy)` aus REQ-053 GP-FR-073 — der Planer führt keine eigene Flächenformel.
- Standortansprüche: `Species.light_requirement ∈ {full_sun, partial_shade, shade_tolerant}` (**neu**, O-01 entschieden: Schema `species.schema.yaml` + `plant_info.schema.yaml`, Steckbrief-Abschnitt „Standort/Licht", `plant-info-to-seed-yaml` extrahiert, `seed-data-validator` prüft; bis zur Befüllung ist `site_fit` für die Lichtkomponente neutral und der Vorschlag nennt `notes[species_missing_light_requirement]`), `greenhouse_recommended`, `container_suitable`, `frost_sensitivity`, `hardiness_zones` (vorhanden).

---

## 6. Harte Restriktionen (nie verletzt)

| ID | Restriktion | Quelle | Verhalten bei Konflikt |
|----|-------------|--------|------------------------|
| H-01 | **Anbaupause:** Im Beet stand in den letzten `rotation_pause_years(Familie)` Jahren keine Art derselben Familie (inkl. Gründüngung derselben Familie); `rotation_reset_at` setzt die Historie zurück; `rotation_exempt`-Beete sind für Hauptkulturen gesperrt, außer die Art ist dort bereits die Dauerkultur | REQ-053 GP-FR-131, K-004 | Beet für diese Art ausgeschlossen |
| H-02 | **Fläche:** Σ Flächenbedarf der Belegungen eines Beets im selben Zeitfenster ≤ `area_m2 × usable_fraction` (Standard 0,9, REQ-002 Luftzirkulation) | REQ-053, REQ-002 | Bedarf wird geteilt (mehrere Beete) oder bleibt Rest |
| H-03 | **Zeitfenster:** Belegung liegt innerhalb des für Site und Art erlaubten Pflanz-/Saat- bis Erntefensters. Ableitung in Tagen (O-06, entschieden): **frostdaten-basiert** — Start = `Site.last_frost_date_avg + Species.sowing_outdoor_after_last_frost_days` (bzw. Vorkultur-Pflanztermin), Ende = Kulturdauer aus den Phasenprofilen (`typical_duration_days` bis zur Erntephase) oder `Site.first_frost_date_avg` für frostempfindliche Arten, je nachdem was früher liegt; fehlen Frostdaten, gelten Monatsanfang/-ende aus `direct_sow_months`/`harvest_months` (REQ-015-A) mit Kennzeichnung `window_source = month_fallback`; zwei Belegungen eines Beets überlappen nicht (Vor-/Nachkultur mit ≥ `turnaround_days` 7 Tage Abstand) | REQ-015-A, REQ-053 GP-FR-065 | Fenster verschieben oder Beet ausschließen |
| H-04 | **Bestehende Reservierungen:** aktive Runs und `run_planned_at` anderer Vorschläge/Runs blockieren überlappende Fenster | REQ-053 V-08 | wie H-03 |
| H-05 | **Standort-Eignung:** `frost_sensitivity = high` nur in Beeten mit Frostschutz (`greenhouse_bed`, `cold_frame`) oder mit Pflanztermin nach `last_frost_date_avg`; `greenhouse_recommended = true` **weich** (§7); `container_suitable = false` nicht in `planter`; `light_requirement = full_sun` nicht in `sun_exposure = shade` (bei `unknown` weich) | REQ-001, REQ-046, REQ-053 | Beet ausgeschlossen |
| H-06 | **Inkompatibilität `severe`:** keine zwei Arten mit `incompatible_with.severity = severe` im selben Beet oder in benachbarten Beeten im selben Fenster | REQ-028 | Beet ausgeschlossen |
| H-07 | **Nutzer-Fixierungen:** `pinned_location_key` und `excluded_location_keys` | §5.1 | Fixierung, die H-01…H-06 verletzt → Vorschlag `infeasible` mit Nennung der Regel; der Nutzer löst auf |
| H-08 | **`must`-Bedarfe** vollständig untergebracht | §5.1 | sonst `infeasible` mit Liste der Gründe je Bedarf |
| H-09 | **Beetstatus:** nur `active`-Beete; `planned`-Beete nur, wenn der Nutzer „geplante Beete einbeziehen" wählt | REQ-053 §7.4 | — |

Härtegrade sind **nicht** konfigurierbar (eine „weiche Anbaupause" ist genau der Fehler, den der Planer verhindern soll). Was der Nutzer kann: eine Regel durch eine Fixierung bewusst übersteuern — das erzeugt dann den Hinweis, nicht die Verletzung im Stillen.

---

## 7. Zielfunktion (weiche Kriterien)

### 7.1 Form

`score(proposal) = Σ_allocations Σ_k w_k · s_k(allocation)` mit `s_k ∈ [−1, +1]` je Kriterium; der Planer **maximiert**. Jede Belegung trägt ihre `ScoreBreakdown {k: s_k, w_k, contribution}` (§10.2) — das ist die Erklärung.

### 7.2 Kriterien

| k | Kriterium | Berechnung `s_k` | Quelle |
|---|-----------|------------------|--------|
| `rotation` | Fruchtfolge-Nutzen | `benefit_score(vorjahr_familie → neue_familie)` aus `rotation_after`; fehlt die Kante: Zehrer-Zyklus-Heuristik (Starkzehrer nach Leguminose/Gründüngung +0,6; Starkzehrer nach Starkzehrer −0,6; Schwachzehrer nach Starkzehrer +0,3; sonst 0); Pause länger als Minimum: +0,1 je Jahr bis +0,3 | REQ-001, REQ-053 §16.3 |
| `pest_risk` | Schädlings-/Krankheitsdruck | −`risk_level` (`low` −0,2, `medium` −0,5, `high` −0,9) zwischen neuer Familie und jeder Familie der letzten 2 Jahre im Beet (`shares_pest_risk`); zusätzlich −0,5, wenn im Beet in den letzten 2 Jahren ein `pest_control`/`ipm`-Ereignis mit derselben Familie protokolliert ist | REQ-001, REQ-053 `care_events` |
| `companion` | Mischkultur im Beet und zu Nachbarbeeten | Mittel über Paare: `compatibility_score` (+), `incompatible_with` `mild` −0,3 / `moderate` −0,7 (`severe` ist hart H-06); Nachbarbeete mit Faktor 0,5 | REQ-028 |
| `nutrition` | Nährstoffpassung | Zehrerstufe gegen Bodenzustand: Starkzehrer auf Beet mit Gehaltsklasse ≥ C oder Düngung/Kompost im Vorjahr +0,5; Starkzehrer auf Beet mit Klasse A/B ohne Düngung −0,5; Leguminose auf nährstoffarmem Beet +0,3; `insufficient_data` → 0 | REQ-053 §15, GP-FR-125 |
| `space` | Flächenausnutzung | `1 − abs(Auslastung − 0,85) / 0,85` (Optimum bei 85 %); Reste < 0,5 m² −0,2 | REQ-002 Kapazität |
| `timing` | Zeitliche Passung | +0,3 bei Vor-/Nachkultur-Kombination, die beide Fenster voll nutzt; −0,3, wenn ein Fenster nur knapp (< 80 % der Kulturdauer) passt | REQ-015-A |
| `preference` | Nutzerwunsch | +1 bei `preferred_location_keys`, −0,5 bei Wechsel einer Art in ein anderes Beet als im Vorjahr **wenn** die Art eine Dauerkultur oder ein Beet mit Rankhilfe braucht (`support_required` und `trellis` vorhanden, REQ-053) | §5.1 |
| `site_fit` | Weiche Standort-Eignung | `greenhouse_recommended` in `greenhouse_bed` +0,5, sonst −0,3; `light_requirement = full_sun` in `partial_shade` −0,4; `sun_exposure = unknown` 0 | REQ-001, REQ-053 |
| `effort` | Arbeitsaufwand | −0,2 je zusätzlichem Beet, auf das ein Bedarf verteilt wird (Zersplitterung); −0,2, wenn gleiche Pflegebedürfnisse (Gießintervall aus Phasenprofil) in einer Bewässerungszone gemischt werden | REQ-053 §14, REQ-022 |

### 7.3 Profile (Gewichte `w_k`)

| Profil | rotation | pest_risk | companion | nutrition | space | timing | preference | site_fit | effort | Bezug |
|--------|----------|-----------|-----------|-----------|-------|--------|------------|----------|--------|-------|
| `balanced` (Standard) | 1,0 | 0,8 | 0,6 | 0,6 | 0,5 | 0,4 | 0,7 | 0,6 | 0,3 | — |
| `soil_health` | 1,5 | 1,0 | 0,5 | 1,0 | 0,3 | 0,3 | 0,4 | 0,5 | 0,2 | REQ-002 `optimization_goal = soil_health` |
| `pest_control` | 1,0 | 1,5 | 0,9 | 0,4 | 0,3 | 0,3 | 0,4 | 0,5 | 0,2 | REQ-002 `optimization_goal = pest_control` |
| `yield` | 0,8 | 0,6 | 0,5 | 0,9 | 1,0 | 0,8 | 0,4 | 0,8 | 0,2 | REQ-002 `optimization_goal = nutrient_balance` + Fläche |
| `low_effort` | 0,8 | 0,6 | 0,4 | 0,4 | 0,4 | 0,4 | 0,9 | 0,5 | 1,0 | ZG-004 Gießdienst |

Die Gewichte sind Startwerte (O-03: Agrobiologie-Review) und als Site-Einstellung überschreibbar (`planning_weights`, Schieberegler in der UI). Das Profil wird am Vorschlag gespeichert, damit zwei Vorschläge vergleichbar bleiben.

### 7.4 Ertrag (COULD)

Liegen für eine Art ≥ 3 Ertragsereignisse auf Beeten der Site vor (REQ-007 `yield_per_m2_g`), kann das Profil `yield` ein Kriterium `expected_yield` (normierter Mittelwert je Beet) hinzuziehen. Vorher ist Ertrag nur Flächenbedarf. Keine Prognose in kg an der Oberfläche vor dieser Schwelle.

---

## 8. Verfahren

### 8.1 Anforderungen an das Verfahren

| ID | Prio | Anforderung |
|----|------|-------------|
| AP-FR-001 | MUST | Das Verfahren ist **deterministisch**: gleiche Eingabe (Request-Snapshot, Wissensstand, `seed`) → identischer Vorschlag. Der Snapshot aller Eingaben wird am Vorschlag gespeichert (`inputs_hash`, `knowledge_version`). |
| AP-FR-002 | MUST | Es findet, wenn eine zulässige Belegung existiert, in ≤ 10 s (klein/mittel) bzw. ≤ 60 s (groß, §14) eine Belegung, die alle harten Restriktionen erfüllt, und meldet sonst `infeasible` mit den verletzten Regeln je `must`-Bedarf — nie einen Vorschlag, der eine harte Regel bricht. |
| AP-FR-003 | MUST | Zwei Phasen: (1) **Konstruktion** — Bedarfe in Reihenfolge `must` → `want` → `nice`, innerhalb nach fallender Restriktivität (wenige zulässige Beete zuerst), gierig auf das bestbewertete zulässige Beet; (2) **Verbesserung** — lokale Suche (Tausch zweier Belegungen, Verschiebung einer Belegung, Teilen/Zusammenlegen) bis keine Verbesserung > 0,01 oder Zeitbudget; Tie-Breaks über `seed`. Reines Python, keine Solver-Abhängigkeit im MVP (D-02). |
| AP-FR-004 | MUST | Je Belegung werden die **drei besten verworfenen Alternativen** (Beet, Score, Hauptgrund für den Unterschied) gespeichert, damit der Nutzer „warum nicht Beet 5?" sofort sieht. |
| AP-FR-005 | MUST | Das Verfahren ist eine **reine Funktion** `plan(request_snapshot, beds, history, knowledge, weights, seed) → Proposal` in `domain/engines/planting_planner_engine.py` ohne I/O; Daten lädt der Service. Property-Tests: kein Vorschlag verletzt H-01…H-09; Score monoton in den Gewichten; Determinismus. |
| AP-FR-006 | MUST | Große Läufe (> 30 Beete oder > 40 Bedarfe) laufen als Celery-Task mit Fortschritt; kleine synchron. Die API entscheidet anhand der Größe (`mode = sync \| async` in der Antwort). |
| AP-FR-007 | SHOULD | Nutzer-Fixierungen und bereits angenommene Belegungen eines früheren Vorschlags werden beim Neurechnen als fest übernommen („Rest neu planen"). |
| AP-FR-008 | SHOULD | Vor-/Nachkultur: Der Planer darf je Beet zwei Fenster belegen (z. B. Salat bis Juni, dann Buschbohne), wenn REQ-015-A beide Fenster erlaubt und H-03 eingehalten ist; Vorkultur zählt in der Fruchtfolge als eigenes Jahr-Ereignis mit Familie. |
| AP-FR-009 | COULD | Mehrjahresplanung: drei aufeinanderfolgende Saisons in einem Lauf (Rotationsfolge je Beet), spätere Jahre nur als Familien-Empfehlung, nicht als Arten. (O-07, entschieden: bleibt COULD; Entscheidung nach einer Saison Nutzung — bis dahin deckt REQ-053 GP-FR-133 den Bedarf.) |
| AP-FR-010 | COULD | Solver-Backend (z. B. OR-Tools CP-SAT, Apache-2.0) hinter derselben `plan()`-Schnittstelle, wenn die Belastungsgrenze (§14) in der Messung gerissen wird. |

### 8.2 Erklärung

| ID | Prio | Anforderung |
|----|------|-------------|
| AP-FR-011 | MUST | Jede Belegung trägt `explanation { breakdown[], sentence_de, sentence_en, alternatives[] }`. Der Satz wird **regelbasiert** aus dem Breakdown erzeugt (Vorlagen je Kriterium, z. B. „Starkzehrer nach Bohnen (+0,6 Fruchtfolge), gute Nachbarn zu Beet 3 (+0,4), Vorjahr: Solanaceae vor 3 Jahren — Pause 4 Jahre eingehalten"). Kein LLM nötig. |
| AP-FR-012 | MUST | Nicht untergebrachter Bedarf (`unallocated[]`) nennt je Bedarf die Gründe (`no_bed_without_rotation_conflict`, `insufficient_area {missing_m2}`, `no_window`, `excluded_by_user`, `frost_risk`) und, wenn möglich, einen Vorschlag („2,4 m² fehlen — Beet 6 im Nachkultur-Fenster wäre frei, wenn Salat vorgezogen wird"). |
| AP-FR-013 | COULD | Optionale Prosa-Erklärung über den KI-Assistenten (REQ-031): Eingabe ist **ausschließlich** das Breakdown-JSON, Ausgabe ein Absatz; mit Einwilligung, lokal-first, als „KI-Formulierung" gekennzeichnet; nie Grundlage der Zuordnung (D-01). |

---

## 9. Ablauf und Oberfläche

### 9.1 Ablauf

1. **Planung starten** (Site → Gartenplan → „Saison planen" oder Beetliste → „Automatisch belegen"): Zeitraum (Jahr/Saison), Profil, Rückblick-Jahre, Schalter „Vor-/Nachkultur zulassen", „geplante Beete einbeziehen".
2. **Bedarf erfassen:** Pflanzenliste (Favoriten, Vorjahr übernehmen, Suche), je Zeile Menge/Einheit, Priorität, optional Beet-Wunsch/-Ausschluss/-Fixierung. „Vorjahr übernehmen" lädt die Arten des Vorjahres mit gleicher Menge als `want`.
3. **Beete prüfen:** Liste der aktiven Beete mit Historie-Abdeckung (Ampel: Rückblick vollständig / teilweise / fehlt) und Link „Vorjahre nacherfassen" (REQ-053 GP-FR-131).
4. **Rechnen** → Ergebnisansicht.
5. **Ergebnis:** Gartenplan (REQ-053 Gartenübersicht) mit Beeten in Artfarbe, je Beet Kurzerklärung; Seitenleiste: Gesamtscore, Profil, `unallocated[]`, Hinweise (Historie-Lücken, Fixierungs-Warnungen). Klick auf ein Beet: Breakdown-Tabelle, Satz, Alternativen mit „Hierhin verschieben".
6. **Bearbeiten:** Belegung per Drag auf anderes Beet (Planer prüft H-01…H-09 sofort, zeigt Score-Differenz), Bedarf ändern, „Rest neu planen".
7. **Annehmen:** je Beet oder „alle annehmen" → geplante Runs mit Zeitfenster (REQ-053 GP-FR-065), `CropRotationPlan`-Einträge je Beet/Jahr, Vorschlag `accepted`. Positionen innerhalb des Beets entstehen danach im Bepflanzen-Dialog (REQ-053 §11) — vorbelegt aus dem Vorschlag.

### 9.2 UX-Anforderungen

| ID | Prio | Anforderung |
|----|------|-------------|
| AP-UX-001 | MUST | Die Ergebnisansicht ist die bestehende Gartenübersicht (REQ-053) mit einer Ebene „Vorschlag"; kein zweiter Canvas. Beete ohne Belegung bleiben neutral; `unallocated` steht sichtbar in der Seitenleiste, nie nur in einem Tab. |
| AP-UX-002 | MUST | Die Begründung je Beet ist in **einem Satz** sichtbar (Tooltip/Sheet), das Breakdown in einer Tabelle (Kriterium, Beitrag, Gewicht) darunter; Zahlen nie ohne Wort. |
| AP-UX-003 | MUST | Warnhinweise, die der Nutzer durch Fixierung erzeugt hat (z. B. Anbaupause verletzt), stehen an der Belegung und werden bei Annahme als `rotation_override_reason` am Run gespeichert (REQ-053 GP-FR-132). |
| AP-UX-004 | MUST | Annehmen ist je Beet reversibel, solange der Run `planned` ist (Reservierung freigeben, REQ-053 GP-API-022); der Vorschlag bleibt als Dokument erhalten. |
| AP-UX-005 | SHOULD | Vergleich zweier Vorschläge derselben Saison nebeneinander (Beet-für-Beet-Diff, Score-Differenz je Kriterium). |
| AP-UX-006 | MUST | Leerzustand erklärt in zwei Sätzen, was der Planer braucht (Beete mit Fläche, Pflanzenliste) und dass er ohne Historie „blind" plant; Fachbegriffe mit Glossar (UI-NFR-011). |
| AP-UX-007 | MUST | Mobil: Ergebnis lesbar und annehmbar (Liste statt Karte als Standard < 600 px); Bedarfserfassung und Gewichte sind Desktop-/Tablet-Funktionen (Hinweis auf xs). |
| AP-UX-008 | MUST | `data-testid`: `planning-request-page`, `planning-demand-row-<key>`, `planning-run-button`, `planning-proposal-page`, `proposal-allocation-<location_key>`, `proposal-accept-button`, `proposal-unallocated-list`; i18n `pages.cropPlanning.*`, `enums.planningProfile.*`, `enums.unallocatedReason.*`. |

---

## 10. Datenmodell

### 10.1 PlanningRequest (Collection `planning_requests`)

```json
{
  "_key": "pr_2026_main",
  "tenant_key": "t_garten_sabine", "site_key": "site_7f3a",
  "name": "Saison 2026",
  "season": { "year": 2026, "period": "main", "allow_pre_post_culture": true },
  "profile": "balanced",
  "weights": null,
  "rotation_window_years": 4,
  "include_planned_beds": false,
  "usable_fraction": 0.9,
  "demands": [
    { "key": "d1", "species_key": "sp_solanum_lycopersicum", "cultivar_key": "cv_harzfeuer", "quantity": 8, "quantity_unit": "plants", "priority": "must", "pinned_location_key": "loc_gh1", "preferred_location_keys": [], "excluded_location_keys": [] },
    { "key": "d2", "species_key": "sp_phaseolus_vulgaris", "quantity": 3, "quantity_unit": "m2", "priority": "want" },
    { "key": "d3", "species_key": "sp_lactuca_sativa", "quantity": 0, "quantity_unit": "fit", "priority": "nice" }
  ],
  "created_by": "u_sabine", "created_at": "…", "updated_at": "…"
}
```

### 10.2 PlantingProposal (Collection `planting_proposals`)

```json
{
  "_key": "pp_7c1e",
  "tenant_key": "t_garten_sabine", "site_key": "site_7f3a", "request_key": "pr_2026_main",
  "status": "proposed",
  "engine_version": "1.0.0", "knowledge_version": "2026-10-01", "inputs_hash": "sha256:…", "seed": 42,
  "profile": "balanced", "weights_used": { "rotation": 1.0, "pest_risk": 0.8, "…": 0 },
  "total_score": 14.6,
  "history_coverage": { "beds_total": 6, "beds_with_history": 4, "years": 4 },
  "allocations": [
    {
      "key": "a1", "demand_key": "d1", "location_key": "loc_gh1",
      "window": { "from": "2026-05-10", "until": "2026-10-15", "slot": "main" },
      "quantity_plants": 8, "area_m2": 3.84, "utilisation": 0.86,
      "score": 2.9,
      "breakdown": [
        { "k": "rotation", "s": 0.6, "w": 1.0, "contribution": 0.6, "reason_code": "heavy_after_legume", "detail": { "previous_family": "Fabaceae", "years_since_same_family": 3, "pause_required": 4 } },
        { "k": "pest_risk", "s": 0.0, "w": 0.8, "contribution": 0.0, "reason_code": "no_shared_risk" },
        { "k": "companion", "s": 0.4, "w": 0.6, "contribution": 0.24, "reason_code": "compatible_neighbours", "detail": { "neighbours": ["loc_b02:Ocimum basilicum"] } },
        { "k": "site_fit", "s": 0.5, "w": 0.6, "contribution": 0.3, "reason_code": "greenhouse_recommended_met" },
        { "k": "preference", "s": 1.0, "w": 0.7, "contribution": 0.7, "reason_code": "pinned_by_user" }
      ],
      "warnings": [],
      "history_coverage": "full",
      "explanation": { "de": "Tomaten ins Gewächshausbeet: Starkzehrer nach Bohnen (+0,6), Basilikum nebenan ist ein guter Nachbar (+0,4), Solanaceae zuletzt vor 3 Jahren — Pause von 4 Jahren wäre erst 2027 erfüllt, aber durch deine Fixierung übersteuert.", "en": "…" },
      "alternatives": [ { "location_key": "loc_b04", "score": 2.1, "main_difference": "no_greenhouse" } ],
      "accepted": false, "materialised_run_key": null
    }
  ],
  "unallocated": [
    { "demand_key": "d3", "reason_code": "insufficient_area", "detail": { "missing_m2": 1.2 }, "suggestion_de": "Beet 6 wird im Juli frei, wenn der Salat als Vorkultur läuft." }
  ],
  "notes": [ { "code": "history_partial", "detail": { "beds_without_history": ["loc_b05", "loc_b06"] } } ],
  "computed_at": "…", "computed_by": "u_sabine", "duration_ms": 1830,
  "accepted_at": null, "accepted_by": null
}
```

`status ∈ {proposed, partially_accepted, accepted, discarded, infeasible}`. `reason_code`-Werte sind ein geschlossenes Enum (i18n-fähig); `detail` ist strukturiert, nie Freitext.

### 10.3 Edges und Indizes

`has_planning_request` (sites → planning_requests), `request_produced` (planning_requests → planting_proposals), `allocation_targets` (planting_proposals → locations, mit `allocation_key`), `allocation_materialised_as` (planting_proposals → planting_runs). Indizes: `planting_proposals(tenant_key, site_key, status)`, `planning_requests(tenant_key, site_key)`. `belongs_to_tenant` wird um beide Collections erweitert.

### 10.4 Annahme → bestehende Modelle

| Erzeugt | Felder | Quelle |
|---------|--------|--------|
| `PlantingRun` (`planned`) je Belegung | `location_key`, `planned_start_date = window.from`, `plan_role = main_crop`, `source = crop_planner`, `proposal_key`, `rotation_override_reason` bei Warnung | REQ-013, REQ-053 |
| `PlantingRunEntry` | `species_key`, `cultivar_key`, `quantity`, `spacing_cm`/`row_spacing_cm` aus Steckbrief, `layout_strategy = rows` (Standard) | REQ-053 GP-FR-060 |
| `run_planned_at` | nach `compute_layout` beim ersten Öffnen des Bepflanzen-Dialogs (Positionen gehören nicht zum Planer). **Bis dahin (O-04, entschieden)** reserviert der Run das Beet **flächig**: neue Felder `PlantingRun.reserved_area_m2`, `planned_from`, `planned_until`; REQ-053 V-08 und H-02/H-04 dieses Dokuments zählen eine flächige Reservierung wie belegte Slots derselben Fläche. Beim Layout im Dialog wird `reserved_area_m2` durch die erzeugten Slots ersetzt (`reserved_area_m2 = null`). | REQ-053 GP-FR-065, REQ-013 |
| `CropRotationPlan` je Beet/Jahr | `plan_role`, `planned_species_keys`, `nutrient_demand` (aus Arten), `optimization_goal` ← Profil, `proposal_key` | REQ-002 |

---

## 11. API

Alle Pfade unter `/api/v1/t/{tenant_slug}`; Standardregel Lesen „Alle Rollen", Anlegen/Ändern „Ab Gärtner", Löschen „Nur Leitung".

| ID | Methode & Pfad | Zweck | Rolle |
|----|----------------|-------|-------|
| AP-API-001 | `GET\|POST /sites/{key}/planning-requests`, `GET\|PATCH\|DELETE /planning-requests/{key}` | Bedarfslisten | Alle / Ab Gärtner / Nur Leitung |
| AP-API-002 | `POST /planning-requests/{key}/compute` `{seed?, profile?, weights?}` → 200 `{mode: sync, proposal}` oder 202 `{mode: async, task_id}` | Rechnen | Ab Gärtner |
| AP-API-003 | `GET /planning-requests/{key}/compute/{task_id}` | Fortschritt/Ergebnis (async) | Alle Rollen |
| AP-API-004 | `GET /sites/{key}/planting-proposals?season=&status=`, `GET /planting-proposals/{key}` | Vorschläge | Alle Rollen |
| AP-API-005 | `POST /planting-proposals/{key}/allocations/{akey}/move` `{location_key, window?}` → neu bewertete Belegung + Warnungen (ohne Persistenz, Vorschau) ; `PATCH …/allocations/{akey}` persistiert | Bearbeiten | Ab Gärtner |
| AP-API-006 | `POST /planting-proposals/{key}/accept` `{allocation_keys[] \| all: true}` → geplante Runs + CropRotationPlan, transaktional; 409 `proposal.stale` wenn `inputs_hash` nicht mehr zu Beeten/Reservierungen passt | Annehmen | Ab Gärtner |
| AP-API-007 | `POST /planting-proposals/{key}/replan` `{keep_accepted: true}` | Rest neu planen | Ab Gärtner |
| AP-API-008 | `POST /planting-proposals/{key}/discard` | Verwerfen | Ab Gärtner (eigene), Nur Leitung (fremde) |
| AP-API-009 | `GET /planting-proposals/compare?a=&b=` | Vergleich (SHOULD) | Alle Rollen |
| AP-API-010 | `GET /sites/{key}/planning-readiness` → `{beds_active, beds_with_history, beds_missing_area, species_missing_fields[]}` | Vorabprüfung für Schritt 3 | Alle Rollen |

Referenzen in Request-Bodies (`species_key`, `location_key`, `*_location_keys`) unterliegen REQ-053 GP-NFR-058 (Tenant-Auflösung, 422 `reference.not_found`). Rate-Limit: `compute` 6/min je Nutzer, 20/min je Tenant; `move` 60/min.

---

## 12. Validierung

| Regel | Ebene | Code | Inhalt |
|-------|-------|------|--------|
| V-01 | API | `validation_error` | ≤ 100 Bedarfe je Request; `quantity > 0` außer bei `fit`; `rotation_window_years` 1–8; Gewichte 0–2 |
| V-02 | Domain | `planning.site_not_ready` | keine aktiven Beete mit Fläche > 0 → 422 mit `readiness` |
| V-03 | Domain | `planning.pinned_conflict` | Fixierung verletzt H-01…H-06 → Vorschlag `infeasible`, kein 4xx (das Ergebnis ist die Information) |
| V-04 | Domain | `proposal.stale` | Annahme, wenn sich Beete/Reservierungen seit `computed_at` geändert haben (`inputs_hash` neu berechnet ≠ gespeichert) → 409 mit `changed[]` |
| V-05 | Domain | `proposal.allocation_conflict` | Verschieben auf ein Beet, das H-01…H-06 verletzt → 422 mit Regel; Fixierung über den Konflikt nur mit `override_reason` |
| V-06 | Domain | `planning.too_large` | > 500 Beete oder > 100 Bedarfe → 422 (Belastungsgrenze §14) |
| V-07 | Domain | `reference.not_found` | fremde/fehlende Keys (GP-NFR-058) |

Prüfreihenfolge wie REQ-053 §22.1.

---

## 13. Berechtigungen, Datenschutz, Modul

| Ressource | Lesen | Anlegen | Ändern | Löschen | Sonderaktionen |
|-----------|-------|---------|--------|---------|----------------|
| Bedarfsliste | Alle Rollen | Ab Gärtner | Ab Gärtner | Nur Leitung | Rechnen: Ab Gärtner |
| Vorschlag | Alle Rollen | (durch Rechnen) | Ab Gärtner (Belegung verschieben) | Nur Leitung | Annehmen: Ab Gärtner; Verwerfen: eigene ab Gärtner, fremde Nur Leitung |

- Lesen ist für **alle Rollen** offen (O-05, entschieden): Entwürfe sind im Gemeinschaftsgarten Diskussionsgrundlage, keine Geheimsache; angenommene Pläne sind ohnehin als Runs sichtbar.
- Vorschläge enthalten keine personenbezogenen Daten außer `created_by`/`computed_by`/`accepted_by` (Kaskade → `_anonymized`). **Retention (O-08, entschieden, NFR-011 R-27):** Bedarfslisten und ihre Vorschläge werden mit dem Request gelöscht; verworfene Vorschläge (`discarded`, `infeasible`) nach 1 Jahr hart gelöscht; angenommene Vorschläge bleiben als Begründung der Runs 5 Jahre (wie `care_events` R-25), danach werden Nutzer-Keys anonymisiert und das Dokument bleibt.
- Optionale KI-Erklärung (AP-FR-013) nur mit Einwilligung `ai_cloud_processing` (REQ-031) bzw. lokal; Eingabe ist das Breakdown ohne Nutzerfelder.
- Modul `crop_planner` in REQ-042; Navigation unter „Standorte → Gartenplan → Saison planen" (kein eigener Hauptmenüpunkt); abhängig vom Modul `garden_planner`.

---

## 14. Nichtfunktionale Anforderungen

| ID | Prio | Anforderung |
|----|------|-------------|
| AP-NFR-001 | MUST | Größenklassen wie REQ-053 §25.1: klein (5 Beete, 10 Bedarfe) ≤ 1 s sync; mittel (20/30) ≤ 10 s sync; groß (150/60) ≤ 60 s async; Belastungsgrenze 500/100. Gemessen als pytest-Benchmark mit synthetischen Sites. |
| AP-NFR-002 | MUST | Determinismus-Test: 20 Läufe derselben Eingabe → byte-identischer Vorschlag. |
| AP-NFR-003 | MUST | Property-Tests (Hypothesis): keine harte Regel verletzt; `must` erfüllt oder `infeasible`; Score steigt nicht, wenn eine Belegung auf ein per H-01 gesperrtes Beet verschoben würde (Sanity). |
| AP-NFR-004 | MUST | Goldene Testfälle: ≥ 5 handgeprüfte Szenarien (Agrobiologie-Review, O-03) als Fixtures `spec/e2e-testcases/fixtures/crop-planning-golden/*.json` mit erwarteter Belegung; Änderungen an Gewichten oder Regeln müssen die Goldfälle bewusst aktualisieren (Diff im PR). |
| AP-NFR-005 | MUST | Observability: `planning.compute {site_key, beds, demands, duration_ms, status, score}`, `planning.accepted {proposal_key, allocations}`; Metriken `planning_compute_duration_seconds`, `planning_infeasible_total{reason}`. Keine Artnamen in Logs nötig, keine Nutzertexte. |
| AP-NFR-006 | MUST | Wissensversion: der Vorschlag speichert `knowledge_version` (Stand der globalen Graph-Seeds); ein Vorschlag mit älterer Version zeigt „mit Wissensstand vom … berechnet". |
| AP-NFR-007 | SHOULD | Engine ohne ArangoDB testbar: Eingabe als Dataclasses, Repository liefert sie; Unit-Tests laufen ohne DB (Memory „localhost:8529 ist lokal erreichbar" — eifrige Konstruktion vermeiden). |

---

## 15. MVP und Abgrenzung

**MVP (nach REQ-053 Wellen 0–6):** AP-FR-001–006, 011, 012; AP-UX-001–004, 006–008; AP-API-001–008, 010; V-01–V-07; AP-NFR-001–006; Profile `balanced`, `soil_health`, `pest_control`; Hauptkultur-Fenster; Beet-Nachbarschaft nur, wenn REQ-053 sie liefert (sonst neutral).

**Nicht im MVP:** Vor-/Nachkultur (AP-FR-008, braucht REQ-015-A-Fenster je Site stabil), Vergleich (AP-UX-005), Rest-neu-planen mit Übernahme (AP-FR-007), Ertrag (§7.4), Mehrjahresplanung (AP-FR-009), Solver-Backend (AP-FR-010), KI-Prosa (AP-FR-013), Profile `yield`/`low_effort`.

**Voraussetzungen aus REQ-053:** Beete mit `area_m2`, `season_state`-Ableitung, Beet-Validator mit `rotation_pause_years`, Nacherfassung der Vorjahre, Zeitfenster-Reservierung, `NutrientDemand`-Split (v0077). Ohne diese ist REQ-054 nicht sinnvoll startbar; die Roadmap (§19) hängt REQ-054 deshalb an REQ-053 Welle 8.

---

## 16. Akzeptanzkriterien

- **AP-ACC-001** (U) Given 3 Beete (je 4 m², Historie: B1 2025 Fabaceae, B2 2025 Solanaceae, B3 keine) und Bedarf Tomate 6 Stück `must` (0,48 m²/Pflanze, Solanaceae, Pause 4), When `plan()` mit Profil `balanced`, Then liegt die Tomate in B1 (Breakdown `rotation = +0,6 heavy_after_legume`), B2 ist in `alternatives` mit `main_difference = rotation_pause_violated`, B3 trägt `history_coverage = none`, And der Vorschlag hat `notes[history_partial]` mit `["B3"]`.
- **AP-ACC-002** (U) Given dieselbe Eingabe, When `plan()` 20-mal läuft, Then sind alle Ergebnisse byte-identisch (`inputs_hash` gleich, Allocations gleich).
- **AP-ACC-003** (U) Given Bedarf Kohl `must` und alle Beete mit Brassicaceae in den letzten 3 Jahren bei Pause 4, When `plan()`, Then ist `status = infeasible`, `unallocated[0].reason_code = no_bed_without_rotation_conflict` mit `detail.earliest_year = 2027` je Beet, And keine Allocation existiert.
- **AP-ACC-004** (U) Given Kohl `must` mit `pinned_location_key = B2` (Brassicaceae 2024), When `plan()`, Then entsteht die Allocation in B2 mit `warnings[0].code = rotation_pause_violated` und `status = proposed` (Fixierung übersteuert), And bei Annahme trägt der Run `rotation_override_reason`.
- **AP-ACC-005** (U) Given Bedarf Tomate 20 Stück bei 3 Beeten à 4 m² (`usable_fraction 0,9` → 7 Pflanzen je Beet), When `plan()`, Then wird der Bedarf auf 3 Beete verteilt (7+7+6), `effort` trägt −0,4 (zwei zusätzliche Beete), And kein Beet überschreitet 3,6 m² Belegung.
- **AP-ACC-006** (U) Given Bohne und Zwiebel (`incompatible_with severity = severe`) als `must`, When `plan()` mit nur einem Beet, Then `infeasible` mit `reason_code = severe_incompatibility`; mit zwei nicht benachbarten Beeten, Then je eins.
- **AP-ACC-007** (U) Given Profil `soil_health` vs. `balanced` auf derselben Eingabe mit einem Beet Gehaltsklasse A ohne Düngung, When beide laufen, Then landet der Starkzehrer unter `soil_health` nicht auf diesem Beet (nutrition −0,5 × 1,0), unter `balanced` ist es als Alternative gelistet.
- **AP-ACC-008** (I) Given ein Vorschlag mit 4 Allocations, When `POST /accept {all: true}`, Then existieren 4 `planting_runs` (`planned`, `source = crop_planner`, `proposal_key`), 4 `CropRotationPlan`-Einträge für 2026 mit `plan_role = main_crop`, der Vorschlag ist `accepted`; When derselbe Aufruf wiederholt wird, Then 409 `proposal.stale` oder idempotent 200 ohne Duplikate (D-04).
- **AP-ACC-009** (I) Given ein Vorschlag, dessen Beet B1 nach `computed_at` eine neue Reservierung bekam, When `POST /accept`, Then 409 `proposal.stale` mit `changed = ["B1"]`, And nichts ist angelegt.
- **AP-ACC-010** (I) Given 150 Beete und 60 Bedarfe (synthetisch), When `POST /compute`, Then 202 mit `task_id`, And das Ergebnis liegt in ≤ 60 s vor und erfüllt alle harten Regeln (Property-Check über das Ergebnis).
- **AP-ACC-011** (E) Given die Ergebnisansicht, When der Nutzer Beet B1 anklickt, Then sieht er einen Begründungssatz und eine Tabelle mit Kriterium/Beitrag/Gewicht, darunter „Warum nicht Beet 2?" mit dem Hauptunterschied, And „Hierhin verschieben" auf Beet 2 zeigt vor dem Speichern die Score-Differenz und die Warnung.
- **AP-ACC-012** (E) Given ein `unallocated`-Bedarf, Then steht er in der Seitenleiste mit Grund und Vorschlag, nicht in einem Tab, And die Seitenleiste nennt „2 von 6 Beeten ohne Historie" mit Link zur Nacherfassung.
- **AP-ACC-013** (E, 390 × 844) Given ein Vorschlag, When die Seite auf dem Smartphone geöffnet wird, Then erscheint die Belegung als Liste (Beet → Arten → Satz) mit „Annehmen" je Beet ≥ 48 px, And der Button „Gewichte" ist deaktiviert mit Hinweis auf Desktop.
- **AP-ACC-014** (U) Given Tenant B besitzt Beet X, When Tenant A einen Request mit `pinned_location_key = X` sendet, Then 422 `reference.not_found`.
- **AP-ACC-015** (U, Goldfall) Given Goldfall `sabine_2026.json` (6 Beete, 4 Jahre Historie, 9 Bedarfe, von Agrobiologie geprüft), When `plan()`, Then entspricht die Belegung dem erwarteten Ergebnis; eine Abweichung schlägt fehl, bis der Goldfall bewusst aktualisiert ist.

---

## 17. Offene Fragen — entschieden am 2026-10-04

| ID | Frage | Entscheidung | Eingearbeitet |
|----|-------|--------------|---------------|
| O-01 | Quelle für `Species.light_requirement` | **Steckbrief-Pipeline erweitern**; bis dahin Lichtkomponente neutral + Hinweis | §5.5, Issue 2 |
| O-02 | Flächenbedarf je Pflanze | **`spacing × row_spacing`, Fallback `spacing²`**, über den REQ-053-Kapazitätsrechner | §5.5 |
| O-03 | Absicherung der Gewichte/Heuristiken | **Agrobiologie- und Outdoor-Review jetzt; fünf Goldfälle vor Welle P1** | §7, AP-NFR-004, Issue 1 |
| O-04 | Reservierung vor Positionsberechnung | **`PlantingRun.reserved_area_m2` + `planned_from/until`; Positionen erst im Dialog** | §10.4, REQ-013-Änderung |
| O-05 | Lesen durch Beobachter | **Ja, alle Rollen** | §13 |
| O-06 | Zeitfenster in Tagen | **Frostdaten-basiert, Fallback Monatsgrenzen** (`window_source`) | H-03 |
| O-07 | Mehrjahresplanung | **COULD, Entscheidung nach einer Saison** | AP-FR-009 |
| O-08 | Retention | **Mit dem Request; verworfene 1 Jahr; angenommene 5 Jahre** — NFR-011 R-27 | §13 |

Es gibt keine offenen Fragen mehr, die die Umsetzung blockieren; die fachliche Prüfung der Startwerte (O-03) läuft als Review und mündet in v1.2.

---

## 18. Entscheidungsvorlagen

| ID | Entscheidung | Optionen | Empfehlung | Begründung |
|----|--------------|----------|------------|------------|
| **D-01** | Planer-Technologie | LLM-gestützt (REQ-031) · deterministischer Optimierer · beides | **Deterministischer Optimierer**, LLM höchstens als Prosa-Schicht | Erklärbarkeit in Zahlen, Reproduzierbarkeit, Testbarkeit (Goldfälle), lokal ohne Modell lauffähig, keine Einwilligungsfrage für die Kernfunktion |
| **D-02** | Solver | reines Python (greedy + lokale Suche) · OR-Tools CP-SAT · PuLP/MILP | **reines Python im MVP**, Solver hinter `plan()` als COULD | Problemgrößen der Zielgruppen sind klein; eine Abhängigkeit mit nativem Build (OR-Tools) kostet Container-Größe und Wartung; die Schnittstelle erlaubt den späteren Tausch |
| **D-03** | Härtegrade konfigurierbar? | ja · nein | **nein** | Eine weiche Anbaupause macht den Planer zum Generator von Fehlern, die er verhindern soll; Übersteuerung nur per sichtbarer Fixierung |
| **D-04** | Annahme idempotent? | 409 bei Wiederholung · idempotent | **idempotent** (zweiter Aufruf liefert dieselben Run-Keys) | Netzabbruch im Garten darf keine Duplikate erzeugen |
| **D-05** | Ausgabe-Modell | eigene Belegungs-Collection dauerhaft · in Runs/CropRotationPlan überführen | **Vorschlag bleibt als Dokument, Annahme erzeugt Runs + CropRotationPlan** | Nachvollziehbarkeit („warum stand das hier") über Jahre; Runs bleiben das operative Modell |
| **D-06** | Vorschlag-Ergebnisansicht | eigener Canvas · Ebene im REQ-053-Plan | **Ebene im Plan** | ein Canvas, ein Renderer, eine Mobil-Logik |

---

## 19. Roadmap und Issue-Kandidaten

Abhängig von REQ-053 Wellen 0–6 (MVP) **und** Welle 8 (Beet-Validator mit Anbaupausen ist dort nur SHOULD-Erweiterung; die MVP-Hinweise reichen) sowie v0077 (`NutrientDemand`).

| Welle | Inhalt | Schätzung |
|-------|--------|-----------|
| **P0 — Spec-Abschluss** | O-01…O-08; Agrobiologie- und Outdoor-Review auf REQ-054 (Gewichte, Heuristiken, Goldfälle); `TC-REQ-054.md` | 1 Woche |
| **P1 — Engine** | Dataclasses, `planting_planner_engine.plan()`, Restriktionen H-01…H-09, Kriterien §7.2, Profile, lokale Suche, Erklärungsgenerator, Property-Tests, Goldfälle, Benchmarks | 3 Wochen |
| **P2 — Daten & API** | Collections, Repository (Historie-Aggregation aus REQ-053), Service, Endpunkte AP-API-001–008/010, Celery-Task, Annahme-Transaktion, Stale-Prüfung, Kaskade/NFR-011 R-27 | 2 Wochen |
| **P3 — Oberfläche** | Bedarfserfassung, Readiness, Ergebnis-Ebene im Gartenplan, Breakdown/Alternativen, Verschieben, Annehmen, Mobil-Liste, i18n, testids, E2E | 3 Wochen |
| **P4 — SHOULD** | Vor-/Nachkultur, Vergleich, Rest-neu-planen, Profile `yield`/`low_effort` | 2 Wochen |

| # | Issue-Kandidat | IDs | Größe |
|---|----------------|-----|-------|
| 1 | spec(REQ-054): operator decisions O-01…O-08 + agrobiology/outdoor reviews of weights and heuristics; five golden scenarios | §17, O-03 | M |
| 2 | feat(knowledge): Species.light_requirement in schema + Steckbrief pipeline | O-01 | S |
| 3 | feat(engine): planting_planner_engine — hard constraints, criteria, profiles, greedy construction + local search, explanation generator, property tests, golden tests, benchmarks | AP-FR-001–005, 011, 012, AP-NFR-001–004 | L |
| 4 | feat(planning): planning_requests/planting_proposals collections, history aggregation repository, service, compute endpoints (sync/async), Celery task | AP-API-001–004, 010, AP-FR-006 | L |
| 5 | feat(planning): accept transaction → planned runs + CropRotationPlan, stale check, idempotency, move/preview, discard, DSGVO cascade + NFR-011 R-27 | AP-API-005–008, V-04/V-05, D-04/D-05 | M |
| 6 | feat(frontend): crop planning pages — demand list, readiness, proposal layer on garden plan, breakdown + alternatives, move, accept, mobile list, i18n, testids | AP-UX-001–008 | L |
| 7 | test(e2e): TC-REQ-054 scenarios | AP-ACC-011–013 | M |
| 8 | feat(planning): pre/post culture windows, proposal compare, replan-keeping-accepted, yield and low_effort profiles | AP-FR-007/008, AP-UX-005, §7.4 | L |
| 9 | spec(REQ-002/REQ-053): CropRotationPlan.optimization_goal gets REQ-054 as consumer; REQ-053 §29 WON'T rows point to REQ-054 | §0 | S |
