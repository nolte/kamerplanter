# Agrarbiologisches Review: REQ-054 v1.1 (Automatische Anbauplanung)

**Erstellt von:** Agrarbiologie-Experte (Subagent, nur Lesezugriff)
**Datum:** 2026-10-04
**Ablage durch Aufrufer:** `spec/analysis/agrobiology-review-req-054.md`

**Einarbeitung (Aufrufer, REQ-054 v1.2, 2026-10-04):** K-001 → H-10 `soil_hazards`, H-01 „nicht prüfbar" bei Lücke, V-01 Fenster ≥ Pause, Jahreskonvention (§5.4, §5.5, §6). K-002 → H-11 (SHOULD, wartet auf REQ-001 `pathogen_hosts`, Issue 4); Gründüngung zählt familienübergreifend (§5.3). K-003 → Sicherheitsdatum `eisheilige_date`, H-05 Klausel 2 gestrichen, Perzentile COULD (§5.5, D-09). K-004 → `growing_periods` mit Ankern hat Vorrang; Schema-Folge-Issue 2. K-005 → Aggregation nach Flächenanteil, Klemmung, `pest_risk` max, `companion` min, `effort` −1,0 (§7.1, D-08). K-006 → Zehrer-Matrix übernommen, Stark→Stark 0 bei geplanter Düngung (§7.2). K-007 → `timing` über Puffertage (§7.2, AP-ACC-024). K-008 → `nutrition` aus schlechtester P/K/Mg-Klasse, E = 0, Humus, geplante Düngung, Hochbeet-Erstjahr, N nur über Vorfrucht (§7.2). W-001 → H-04 nur angenommene Runs, H-06 Nachbar weich ab 30 cm, gleiche Familie innerhalb der Saison hart, pH-Extreme hart, `support_required` in `site_fit`. W-002 → `usable_fraction` je Beettyp ohne Doppelreserve, `turnaround_days` je Übergang. W-003 → Teilplan (Betreiberentscheid F-01). W-004 → Pause-Bonus nur bei erfassten Jahren, `space` ohne Rest-Strafe und mit Site-Ziel, `site_fit` Fruchtgemüse −0,8 / symmetrisches Gewächshaus, `preference` nur Nutzerwünsche. W-005 → `soil_cover`, `root_depth_rotation`, `soil_fit`, `rotation_future`, `support_required` im MVP (Betreiberentscheid); `water_match` SHOULD, `shading_neighbour` COULD. W-006 → Historie-Eingänge als REQ-053-Folge-Issue 3; `history_gap` sichtbar. W-007 → Voranzucht-Vorlauf, Erntefenster, Winterkulturen über Jahreswechsel, Gewächshaus-Offset, GDD/Bodentemperatur als Hinweis (§5.5). W-008 → Lückenstrafe (§5.4). W-009 → Gründüngung/Mulch-Vorschlag als Planergebnis (AP-FR-008, `CoverSuggestion`). W-010 → Profile harmonisiert, `yield` eigener `optimization_goal`-Wert, `space`-Definition, `fit`-Obergrenze. H-001…H-008 → in AP-NFR-004/§7.5/AP-UX-003 übernommen. Goldfälle (a)–(e) → Fixture-Vorlage (AP-NFR-004, Issue 1). R-001…R-024 → **offen**, vor dem Einfrieren der Goldfälle (Issue 1).
**Analysierte Dokumente:** `spec/req/REQ-054_Automatische-Anbauplanung.md` (vollständig gelesen). Abgleich mit `species.schema.yaml`, `_defs.schema.yaml`, `plant_info.schema.yaml` und `botanical_families.schema.yaml` (Stichproben per Grep).
**Fokus:** Freiland, Gewächshaus, Hochbeet und Kübel, Fruchtfolge, Mischkultur.

**Hinweis zur Belegdisziplin:** Ich hatte in dieser Sitzung keinen Zugriff auf externe Quellen. Ich habe deshalb keine agronomische Zahl als „drei Quellen belegt" ausgegeben. Zahlen und Fachbehauptungen, die ich nicht aus dem Dokument selbst oder aus dem Schema ableiten kann, tragen **⚠️ NICHT VERIFIZIERT** und stehen in der Recherche-Tabelle (R-001 ff.).

Die Heuristik-Beträge in §7.2 sind **Modellparameter und keine Fachfakten**. Ich bewerte bei ihnen die *Richtung* (agronomisch begründbar oder nicht) und den *Betrag* (kalibrierbar oder willkürlich) getrennt.

---

## Gesamtbewertung

| Dimension | Bewertung | Kommentar |
|---|---|---|
| Fachliche Korrektheit | ⭐⭐⭐ | Die Struktur ist richtig: Familien-Pause hart, Mischkultur weich. Es fehlen persistente Bodenpathogene, Wirtswechsel über Familiengrenzen und ein tragfähiges Frostmodell. |
| Indoor-Vollständigkeit | n. a. | Der Scope ist Freiland und Gewächshaus. Hydroponik und Zimmerpflanzen sind bewusst nicht Teil von REQ-054. |
| Zimmerpflanzen-Abdeckung | n. a. | wie oben |
| Hydroponik-Tiefe | n. a. | wie oben |
| Messbarkeit der Parameter | ⭐⭐⭐ | Die Kriterien sind numerisch, aber `timing` ist widersprüchlich formuliert (K-007). `Auslastung` und `Fläche` sind nicht eindeutig definiert. |
| Praktische Umsetzbarkeit | ⭐⭐⭐⭐ | Die Engine ist rein, deterministisch und erklärbar. Das ist der richtige Ansatz (D-01). |
| Schema-Spec-Konsistenz | ⭐⭐⭐ | `sowing_outdoor_after_last_frost_days` hat `minimum: 0`. Das passt nicht zu H-03 für Frühkulturen und Gewächshaus. Verwendbare Schema-Felder (`root_depth`, `soil_ph_preference`, `support_required`, `growing_period`) bleiben ungenutzt. |

Die Architektur ist belastbar, die Startwerte sind es noch nicht. Mein Vorschlag lautet: **Gewichte und Beträge nicht einfrieren, bevor K-001 bis K-007 entschieden sind.** Die Goldfälle unten testen deshalb die *Rangfolge* der Belegung und die *Ausschlussgründe* und nicht exakte Scores.

---

## Fachlich Falsch / kritisch (K)

### K-001: Persistente Bodenpathogene — Rückblick und Pause reichen nicht (§5.3, §6 H-01, §7.2 `pest_risk`)
**Anforderung:** H-01 prüft nur `rotation_pause_years(Familie)`. `pest_risk` schaut nur auf die „letzten 2 Jahre". `rotation_window_years` ist 1–8, Standard 4.
**Problem:**
- Dauerstadien von Bodenpathogenen überdauern ein Vielfaches der üblichen Familienpause. Das betrifft Kohlhernie (*Plasmodiophora brassicae*), Zystennematoden (*Globodera*, *Heterodera*), Zwiebelweißfäule (*Sclerotium cepivorum*) und Erbsenmüdigkeit (*Aphanomyces euteiches*). ⚠️ NICHT VERIFIZIERT (R-001: konkrete Jahreszahlen).
- Ein dokumentierter, bestätigter Befall macht die Standardpause fachlich unzureichend.
- Hat ein Beet keine Historie oder ist sie kürzer als die Pause, ist H-01 *vakuös wahr*: Die „harte" Regel prüft nichts, und der Planer sagt es nicht.

**Änderungsvorschlag:**
1. Neue harte Regel **H-10 `soil_hazard`**: Ein Beet mit bestätigtem Befall durch ein persistentes Bodenpathogen (Beet-Attribut `soil_hazards[] {pathogen, family_scope, confirmed_at}`, unabhängig vom Rückblickfenster) ist für die betroffenen Familien gesperrt. Die Sperrdauer kommt aus einem Wissensfeld `soil_persistence_years` am Pathogen oder an der Kante `shares_pest_risk`. Die Werte werden erst nach Recherche R-001 befüllt. Übersteuerung nur per Fixierung mit eigener Warnung `persistent_soil_pathogen`.
2. **H-01 erweitern:** Ist `rotation_window_years < rotation_pause_years(Familie)` oder `history_coverage` für Jahre innerhalb der Pause lückenhaft, gilt die Regel als **nicht prüfbar**. Das Ergebnis ist `warnings[history_gap_in_pause_window]` und kein stilles Bestehen.
3. **V-01:** `rotation_window_years` muss mindestens so groß sein wie die größte Pause der Familien im Bedarf, sonst ein Hinweis.
4. **Konvention festschreiben:** Eine Art ist in Jahr Y erlaubt, wenn `Y − letztes_Jahr ≥ Pause`. Das entspricht dem Beispiel in §10.2 (2023 + 4 = 2027). §6 muss es ausdrücklich sagen. Die Kalenderjahr-Granularität zählt eine Herbst-Kultur 2024 und eine Frühjahrs-Kultur 2025 als „1 Jahr", obwohl nur etwa 6 Monate dazwischen liegen. Das ist ein Hinweis in der Spec.

### K-002: Wirtswechsel über Familiengrenzen fehlt (§6, §7.2)
**Problem:** H-01 und `pest_risk` arbeiten familienweise. Mehrere relevante Erreger haben aber familienübergreifende Wirtskreise:
- Wurzelgallennematoden (*Meloidogyne*): breiter Wirtskreis, u. a. Tomate, Möhre, Salat, Gurke.
- Rübenzystennematode (*Heterodera schachtii*): Amaranthaceae (Beta, Spinat) und Brassicaceae. Das gilt auch für **Senf und Ölrettich als Gründüngung**.
- *Sclerotinia sclerotiorum*: u. a. Salat, Bohne, Möhre, Kohl.
- *Verticillium*: u. a. Tomate, Gurke, Erdbeere.

⚠️ NICHT VERIFIZIERT (R-002).
**Änderungsvorschlag:**
- Eine Kante `shares_pest_risk` mit `risk_level = high` zwischen *verschiedenen* Familien wird **hart (H-11)**, wenn im Beet in den letzten 4 Jahren ein `pest_control`- oder `ipm`-Ereignis mit demselben Erreger protokolliert ist. Sonst bleibt sie weich.
- Das Wissensmodell in REQ-001 muss dafür Erreger → Wirtsfamilien-Mengen speichern. Das ist ein Folge-Issue für REQ-001. Bis dahin steht `shares_pest_risk` nur weich in `pest_risk`.
- Die Aussage „Gründüngung zählt mit Familie" in §5.3 gilt auch familienübergreifend (Senf zählt als Wirt für Rübennematoden).
- Nach APG IV sind Chenopodiaceae in Amaranthaceae aufgegangen und Alliaceae in Amaryllidaceae. Das Wissensmodell und die Fixtures müssen APG-IV-Familien verwenden.

### K-003: `last_frost_date_avg` ist ein Mittelwert, kein Sicherheitsdatum (§6 H-03 und H-05)
**Anforderung:** Start = `last_frost_date_avg + sowing_outdoor_after_last_frost_days`. H-05 erlaubt `frost_sensitivity = high` auch „mit Pflanztermin nach `last_frost_date_avg`".
**Problem:** Das mittlere Datum des letzten Frosts wird in etwa der Hälfte der Jahre unterschritten, der Frost kommt also später. Für frostempfindliche Arten (Tomate, Gurke, Bohne, Basilikum, Zucchini) ist ein Pflanztermin direkt am Mittelwert ein 50-%-Risiko. Üblich ist ein Datum mit geringem Restrisiko, in Deutschland oft die Eisheiligen Mitte Mai. ⚠️ NICHT VERIFIZIERT (R-003: DWD-Phänologie, Perzentil-Frostdaten, 10-%-Risiko-Datum).
**Änderungsvorschlag:**
1. H-05, 2. Klausel streichen. Sie ist durch H-03 abgedeckt und mit dem Mittelwert falsch.
2. `Species.sowing_outdoor_after_last_frost_days` für `frost_sensitivity = high` als *Sicherheitsabstand zum Mittelwert* spezifizieren (also ≥ 7–14 Tage) und eine Site-Option `frost_risk_percentile ∈ {50, 25, 10}` (Standard 10) vorsehen, falls REQ-046 Perzentile liefert.
3. Mikroklima (Frostlage, Stadt) als Site-Offset `frost_date_offset_days` zulassen.
4. Schematisch: Die Ableitung ist nur dann ehrlich, wenn die Annahme „Mittelwert + Offset" im Vorschlag als `window_source = frost_avg` mit sichtbarem Restrisiko-Hinweis steht.

### K-004: Schema-Widerspruch zu H-03 — Offset `minimum: 0`, nur Frühjahrsanker (§5.5, H-03)
**Befund:** `species.schema.yaml:120` definiert `sowing_outdoor_after_last_frost_days` mit `minimum: 0`.
**Problem:**
- Frostharte Arten (Spinat, Erbse, Kohlrabi, Möhre, Zwiebelsteckling) werden *vor* dem letzten Frost gesät oder gepflanzt. Das Feld kann das nicht ausdrücken.
- H-03 kennt nur den Anker „letzter Frost". Herbstkulturen (Feldsalat, Herbstspinat, Chinakohl, Rettich, Knoblauch, Winterzwiebel) brauchen einen Anker am *ersten Frost* oder am Kalender.
- Photoperiodisch schossende Arten (Spinat, Salat, Chinakohl als Langtag-Schosser) haben ein *Aussaat-Ende* im Sommer, das aus keiner Frostregel folgt. ⚠️ NICHT VERIFIZIERT (R-004).

**Änderungsvorschlag:** H-03 nutzt primär die vorhandene Liste `growing_periods` (`_defs.schema.yaml#growing_period`, Vorrang vor den Flachfeldern). Die Flachfelder sind nur der Fallback. Das Feld soll vorzeichenbehaftet werden (`minimum` weg) oder um `sowing_windows[] {anchor ∈ {last_frost, first_frost, calendar}, offset_days, latest_calendar?}` ergänzt werden. Das ist ein Folge-Issue für das Schema. Ohne diese Änderung sind Herbst- und Frühkulturen nicht planbar.

### K-005: Summierung der Scores über Belegungen belohnt Zerstückelung (§7.1 gegen `effort`)
**Problem:** `score = Σ_alloc Σ_k w_k·s_k` addiert je Belegung. Eine Aufteilung eines Bedarfs auf 3 Beete erzeugt 3 Summanden mit meist positivem Beitrag (`rotation`, `site_fit`, `preference`). `effort` zieht nur −0,2 · w (balanced: −0,06) je Zusatzbeet ab. Der Planer wird dadurch strukturell zu *mehr* Belegungen getrieben. Das widerspricht AP-ACC-005, wo die Aufteilung nur als Notlösung gedacht ist.
**Änderungsvorschlag:**
- Beiträge je Belegung mit dem Flächenanteil am Bedarf gewichten: `contribution = w_k · s_k · (area_alloc / area_demand)`.
- Alternativ `effort` je Zusatzbeet auf −1,0 anheben.
- Für `pest_risk` festlegen: **Maximum** über die Familien, nicht Summe. Das Kriterium ist auf [−1, +1] zu klemmen. Die zusätzlichen −0,5 bei protokolliertem Ereignis dürfen −1 nicht überschreiten.
- Entsprechend `companion`: den **schlechtesten Partner** statt den Mittelwert bewerten (siehe W-004), sonst verdünnt ein harmloser Nachbar einen echten Konflikt.

### K-006: Zehrer-Zyklus-Heuristik unvollständig und teils entgegen der Praxis (§7.2 `rotation`)
**Anforderung:** Stark nach Leguminose/Gründüngung +0,6. Stark nach Stark −0,6. Schwach nach Stark +0,3. Sonst 0.
**Problem:**
- Die klassische Folge ist Starkzehrer → Mittelzehrer → Schwachzehrer → Leguminose/Gründüngung. Mittelzehrer kommen nicht vor. Mittel nach Stark ist der Normalfall der Vierfelderwirtschaft und bekäme 0. Die Heuristik würde in Goldfall (a) die Möhre nicht nach dem Kohl platzieren.
- Starkzehrer nach Starkzehrer ist mit Düngung gängige Praxis (z. B. Kohl nach Kartoffel). Die Heuristik zieht Zehrer-Wirkung aber doppelt, einmal in `rotation` und einmal in `nutrition` (Düngung im Vorjahr +0,5). Die Doppelzählung ist zu entflechten: `rotation` bildet die *Reihenfolge*, `nutrition` den *Bodenzustand* ab.
- Bei der Gutschrift +0,6 fehlt die Unterscheidung nach Leguminosenform: Eine eingearbeitete Leguminosen-Gründüngung hinterlässt andere Stickstoffmengen als eine abgeerntete Gemüse-Leguminose. Die Spec spricht nur von „Leguminose/Gründüngung". ⚠️ NICHT VERIFIZIERT (R-005: Zahlen; keine Beträge nennen, solange nicht belegt).

**Änderungsvorschlag (Matrix, Startwerte ⚠️, in Goldfällen a, c, d verwendet):**

| Vorfrucht ↓ / Nachfrucht → | Stark | Mittel | Schwach |
|---|---|---|---|
| Leguminose-Gründüngung (eingearbeitet) | +0,6 | +0,3 | 0 |
| Leguminose geerntet | +0,4 | +0,3 | 0 |
| Stark | −0,6 | +0,3 | +0,3 |
| Mittel | 0 | −0,2 | +0,3 |
| Schwach / nicht-leguminose Gründüngung | 0 | 0 | 0 |

Der Stark→Stark-Wert wird nur dann −0,6, wenn für das Beet keine Düngung im aktuellen Jahr als Planungsannahme gesetzt ist. Das ist eine Folge-Entscheidung zu `nutrition` (siehe K-008). Die Richtung der Werte ist begründbar, die Beträge sind kalibrierbar und nicht belegt.

### K-007: `timing`-Kriterium widerspricht H-03 (§7.2 `timing`)
**Anforderung:** „−0,3, wenn ein Fenster nur knapp (< 80 % der Kulturdauer) passt".
**Problem:** H-03 lässt nur Belegungen *innerhalb* des erlaubten Fensters zu. Ein Fenster, das kürzer als 100 % der Kulturdauer ist, ist damit hart ausgeschlossen. Ein Fenster zwischen 80 % und 100 % kann es nicht geben. Das Kriterium löst nie aus. Ob „80 %" eine Toleranz meint, bleibt unklar.
**Änderungsvorschlag:** `timing` über den **Puffer in Tagen** zwischen berechnetem Kulturende und Fensterende definieren. Beispiel: Puffer < 14 Tage → −0,3 (Frost- und Reiferisiko, siehe K-003). Vorkultur/Nachkultur-Kombination, die beide Fenster mit Puffer ≥ 14 Tagen nutzt: +0,3. ⚠️ NICHT VERIFIZIERT (R-006: Reifezeit-Streuung `typical_duration_days` zwischen Jahren; GDD-Bezug, das System kennt GDD).

### K-008: `nutrition` nutzt eine einzelne Gehaltsklasse für N-Bedarf (§7.2 `nutrition`)
**Problem:**
- Bodenanalyse-Gehaltsklassen (VDLUFA A–E) gelten je Nährstoff (P, K, Mg, pH), nicht für Stickstoff. N ist dynamisch (Nmin). Der Starkzehrer-Bedarf ist in erster Linie ein N-Bedarf, den die Klasse nicht abbildet. ⚠️ NICHT VERIFIZIERT (R-007: VDLUFA-Standpunkt, LfL Bayern).
- Hausgartenböden sind häufig mit P und K überversorgt (Klasse D/E). „≥ C → +0,5" belohnt dann gerade überversorgte Beete. Vorschlag: Klasse E für P/K → 0 (kein weiterer Bonus). Das Aggregat soll aus dem *schlechtesten* relevanten Nährstoff (P, K, Mg) und aus dem Humusgehalt gebildet werden.
- „Leguminose auf nährstoffarmem Beet +0,3" ist nur sinnvoll, wenn P und K nicht in Klasse A/B liegen. Leguminosen sind P- und K-bedürftig, nur nicht N-bedürftig.

**Änderungsvorschlag:** `nutrition` aus (a) Gehaltsklasse P/K/Mg (schlechtester Wert, Klasse E → neutral), (b) Humus oder organischer Substanz, (c) geplanter Düngung/Kompost im aktuellen Jahr (Planungsannahme, siehe W-006) zusammensetzen. N nur über Vorfrucht-Gutschrift (K-006). Zusatz für **Hochbeete:** Im ersten Jahr nach Anlage ist der Nährstoffvorrat so hoch, dass Starkzehrer günstig und nitratspeichernde Arten ungünstig sind. Das ist nur ableitbar, wenn `soil_profile` ein Anlage- oder Auffülldatum hat. ⚠️ NICHT VERIFIZIERT (R-008).

---

## Unvollständig / zu ungenau (W)

### W-001: §6 Einteilung hart/weich — Bewertung je Regel

| Regel | Urteil | Begründung / Änderung |
|---|---|---|
| H-01 | hart, richtig | ergänzen um K-001. Zusätzlich: **gleiche Familie innerhalb derselben Saison** (Vorkultur → Nachkultur, z. B. Kohl nach Kohl) ist hart gesperrt. Das Dokument nennt es nur in AP-FR-008 (SHOULD). Es gehört in H-01 und H-03. |
| H-02 | hart, richtig | `usable_fraction = 0,9`: siehe W-002 |
| H-03 | hart, richtig | Ableitung siehe K-003, K-004, W-007 |
| H-04 | hart, aber ein Satz widerspricht AP-UX-005 | „`run_planned_at` anderer **Vorschläge**" blockiert: Ein unangenommener Vorschlag ist keine Reservierung. Sonst können zwei Vorschläge derselben Saison einander blockieren und der Vergleich wird unmöglich. Nur *angenommene* Runs und aktive Runs blockieren. |
| H-05 | teils falsch | 2. Klausel streichen (K-003). `container_suitable = false` nicht in `planter` ist richtig. `light_requirement = full_sun` nicht in `shade` hart: richtig. `support_required` ohne `trellis` ist nicht erwähnt (siehe W-005). |
| H-06 | zu hart für Nachbarbeete | Innerhalb eines Beets hart. Für Nachbarbeete (Beetkante ≤ 50 cm, oft mit Weg dazwischen) ist die Wirkung deutlich schwächer und von der Datenqualität in REQ-028 abhängig. Ein Datenfehler in einer `severe`-Kante würde sonst zum harten Ausschluss. Vorschlag: Nachbarbeet `severe` → weich mit −1,0·w und `warnings[severe_incompatibility_neighbour]`. Ausnahme hart, wenn `adjacent_to.distance_cm ≤ 30` (⚠️ NICHT VERIFIZIERT, R-009). AP-ACC-006 bleibt gültig, denn dort ist die Variante „Nachbarbeet" ohnehin nur mit nicht benachbarten Beeten gelöst. |
| H-07 | richtig | |
| H-08 | hart, aber Folge für den Nutzer schlecht | Siehe W-003. |
| H-09 | richtig | |

**Was hart sein sollte und fehlt:**
- H-10 und H-11 (K-001, K-002).
- **Allelopathie:** Fenchel (*Foeniculum vulgare*) hemmt viele Gemüse. Die Wirkung von Juglon (Walnuss) auf Solanaceae (Tomate) ist gut dokumentiert. Beides ist über REQ-028-`severe`-Kanten erfassbar und braucht keine neue Regel. Das Fehlen von Walnuss als *Standort-Attribut* ist aber eine Lücke: Ein Beet im Wurzel- und Traufbereich einer Walnuss muss `soil_hazards[juglone]` tragen können. ⚠️ NICHT VERIFIZIERT (R-010). Roggen-Gründüngung hemmt die Folgesaat für einige Wochen, ⚠️ NICHT VERIFIZIERT (R-010).
- **Bodenart und pH-Extreme:** `soil_texture` und `ph` werden in §5.2 gelesen, aber in keiner Regel oder keinem Kriterium verwendet. Hart nur bei Extremen: Säurezeiger (Heidelbeere) auf Beet mit pH > 6,5; Beete mit Torf- oder Moorbedarf. ⚠️ NICHT VERIFIZIERT (R-011). Sonst weich (W-005).

**Was hart ist und weich sein sollte:** `must` (H-08) als harte Vorgabe ist fachlich richtig, führt aber zu einer schlechten Ausgabe (W-003). Sonst nichts.

### W-002: `usable_fraction = 0,9` und `turnaround_days = 7`
- **`usable_fraction = 0,9`:** plausibel als Pauschale für Wege und Luftzirkulation innerhalb des Beets. Sie wird aber auf `spacing × row_spacing` angewendet, und dieser Flächenbedarf enthält den Platz zwischen den Pflanzen bereits. Das ist eine **Doppelreserve**, die kleine Beete unnötig kleinrechnet (3,6 statt 4 m² bei 4 m²). Vorschlag: `usable_fraction` je Beettyp (Freiland-Beet 1,0 wenn die Fläche bereits ohne Wege gemessen ist, Gewächshaus-Beet und Hochbeet 0,9, Kübel 1,0) oder als Beet-Attribut. Die Zahl 0,9 ist als Herleitung nicht belegbar. ⚠️ NICHT VERIFIZIERT (R-012). Zusätzlich: Auslastung ist an `area_m2` oder an `area_m2 × usable_fraction` zu messen? `space` definiert es nicht (siehe W-010).
- **`turnaround_days = 7`:** reicht für Ernte, Räumen und Neupflanzen mit Jungpflanzen. Es reicht **nicht** nach Einarbeitung einer Gründüngung, weil Zersetzung und Stickstoffimmobilisierung eine Wartezeit vor Saat und Pflanzung erfordern. Das ist ein verbreiteter Praxisgrundsatz. ⚠️ NICHT VERIFIZIERT (R-013: Dauer). Vorschlag: `turnaround_days` je Übergang: 7 (Ernte → Pflanzung), je Vorkultur-Typ erhöht nach Gründüngungseinarbeitung, Beeteinarbeitung von Ernterückständen oder Kompost. Der Wert muss im Wissensmodell der Vorfrucht stehen, nicht als Konstante.

### W-003: H-08 / AP-ACC-003 — `infeasible` liefert nichts
Ist ein einziger `must`-Bedarf nicht unterzubringen (Kohl, alle Beete gesperrt), existiert laut AP-ACC-003 *keine* Allocation. Der Nutzer erhält für 5 Beete und 9 Bedarfe nichts. Fachlich ist der beste Teilplan hochwertig.
**Änderung:** `status = infeasible` bleibt, aber `allocations` enthält den besten Plan für alle *lösbaren* Bedarfe, `unallocated[]` die unlösbaren `must`-Bedarfe. Die UI kann so beide anzeigen. Goldfall (b) legt dieses Verhalten fest.

### W-004: §7.2 Bewertung jeder Zahl

Einstufung: **Richtung** = fachlich begründbar (j/n), **Betrag** = belegbar oder kalibrierbar (b = belegbar, k = kalibrierbar/Modellparameter, w = willkürlich).

| Kriterium / Zahl | Richtung | Betrag | Befund |
|---|---|---|---|
| Zehrer +0,6 / −0,6 / +0,3 | j | k | siehe K-006; Matrix erweitern |
| Pause länger +0,1/Jahr bis +0,3 | j | k | Beete ohne Eintrag im Fenster dürfen den Bonus nicht erhalten, sonst belohnt ein *Datenloch* das Beet (siehe K-001/W-008). Nur belegbar, wenn die Jahre als erfasst gelten. |
| Pest-Strafen −0,2 / −0,5 / −0,9 | j | k | Skala der Abstufung ok; max statt Summe (K-005). 2-Jahres-Fenster ist für Insekten (Möhren-, Kohlfliege überwintern im Boden) plausibel, für Bodenpathogene nicht (K-001). ⚠️ NICHT VERIFIZIERT (R-014) |
| Zusatz −0,5 bei protokolliertem Ereignis | j | k | Gesamtstrafe klemmen (K-005); die Schwere des Befalls (Ereignis vs. Befall bestätigt) muss unterscheiden (W-006) |
| Companion `mild` −0,3 / `moderate` −0,7 | j | k | Mittel über Paare verdünnt Konflikte → **Minimum** statt Mittel (K-005). Die Wirksamkeit vieler Mischkultur-Paare ist wissenschaftlich unterschiedlich belegt. ⚠️ NICHT VERIFIZIERT (R-015) |
| Nachbarbeet-Faktor 0,5 | j (Wirkung nimmt mit Entfernung ab) | w | Willkürlich. Wurzelausscheidungen und Erreger wirken über 30–50 cm anders als Duft- und Schatteneffekte. Eine Unterscheidung nach Wirkungsart (Boden, Luft, Schatten) wäre fachlich besser; als Startwert akzeptabel, aber als Platzhalter kennzeichnen. ⚠️ NICHT VERIFIZIERT (R-016) |
| Space-Optimum 85 % | teils | w | Es gibt keine agronomische Begründung für 85 %. Eine zu hohe Auslastung ist nur bei Dichtpflanzung riskant (Luftzirkulation, Pilzdruck), die ist aber durch `spacing` und `usable_fraction` bereits berücksichtigt. Das Kriterium ist ein Planungskomfort (wenig Reste), kein Fachkriterium. Empfehlung: Gewicht niedrig lassen (0,3), den Zielwert als Site-Einstellung führen. |
| Rest < 0,5 m² −0,2 | n | w | Reststücke sind für Gründüngung, Kräuter oder Untersaat nutzbar. Besser: Reste als Hinweis „Gründüngung/Untersaat möglich" statt Strafe. |
| `timing` ±0,3 | n | — | siehe K-007 |
| `nutrition` ±0,5 / +0,3 | j | k | siehe K-008 |
| `site_fit` ±0,5 / −0,4 | teils | k | Zu schwach und zu undifferenziert: Fruchtgemüse (Tomate, Paprika, Gurke) im Halbschatten verlieren deutlich mehr als Blattgemüse (Salat, Spinat, Kräuter). Vorschlag: −0,4 für Blatt-/Wurzelgemüse, −0,8 für Fruchtgemüse (`Nutzorgan`, falls im Steckbrief). ⚠️ NICHT VERIFIZIERT (R-017). `greenhouse_recommended` in `greenhouse_bed` +0,5, sonst −0,3: asymmetrisch. Das Gewächshaus ist knappe Ressource: Eine Art ohne `greenhouse_recommended` im Gewächshausbeet sollte ebenfalls leicht negativ bewertet werden (Kapazität sichern), z. B. −0,2. Kühle Kulturen im Gewächshaus im Hochsommer (Salat, Spinat) sind fachlich problematisch. ⚠️ NICHT VERIFIZIERT (R-017). |
| `effort` −0,2 | j | w | Zu klein, siehe K-005; zweiter Teil (Bewässerungszone) braucht eine Wasserbedarf-Klasse (siehe W-005). |
| `preference` +1 / −0,5 | teils | k | Der Teil „Wechsel der Dauerkultur / Rankhilfe" hat mit Nutzerwunsch nichts zu tun. Dauerkulturen sind `rotation_exempt` und gehören gepinnt. `support_required` ohne Rankhilfe ist ein Standort-Kriterium (W-005). Aus `preference` herausnehmen. |

### W-005: Fehlende Kriterien (Vorschlag mit Priorität)

| Neues Kriterium | Inhalt | Datengrundlage | Priorität |
|---|---|---|---|
| `root_depth_rotation` | Wechsel Tief- und Flachwurzler im Beet (Bodenlockerung, Nährstoffschichten) | `typical_root_depth` und `root_depth` in `_defs.schema.yaml` existieren (shallow/medium/deep) | mittel, MVP-fähig |
| `soil_cover` | Winterbegrünung und Erosionsschutz: Ein Beet ohne Gründüngung oder Kultur über Winter erhält Abzug. Der Planer soll für unbelegte Beete **Gründüngung oder Mulch vorschlagen**. | `season_state = green_manure`, REQ-053 | mittel |
| `water_match` | Wasserbedarf-Gruppierung im Beet und in der Bewässerungszone: Tomate und Gurke verlangen gleichmäßige Wassergaben, Zwiebel und mediterrane Kräuter (Thymian, Salbei, Rosmarin) abtrocknende Phasen | `effort` nennt „Gießintervall aus Phasenprofil"; besser eine eigene Wasserbedarfs-Klasse je Art | mittel |
| `soil_fit` | Bodenart und pH: Wurzelgemüse (Möhre, Pastinake) in schwerem Ton (Beinigkeit), Kartoffel und pH (Schorf), Kohl und pH | `soil_texture`, `ph` in §5.2, `soil_ph_preference` im Schema | mittel; heute werden die Daten gelesen und nicht genutzt |
| `shading_neighbour` | Hohe Kulturen (Mais, Stangenbohne, Sonnenblume, Tomate) verschatten niedrige Nachbarbeete, je nach Himmelsrichtung. REQ-053 §29 schließt die Sonnenberechnung aus. | grob: `max_height_cm` plus Nachbar-Himmelsrichtung. Ein grober Platzhalter genügt, wenn `max_height_cm` im Schema fehlt (Befund, nicht verifiziert). | niedrig, später |
| `support_required` | Stangenbohne, Gurke, hohe Tomate ohne Rankhilfe | `support_required` in `species.schema.yaml:173`; `trellis` laut §7.2 in REQ-053 | mittel; weich −0,6, als `warnings[support_missing]`, in `site_fit` aufnehmen |
| `rotation_future` | Ein-Jahres-Vorschau: Wie viele Beete bleiben im Folgejahr für die gewählte Familie zulässig? Verhindert, dass der Greedy-Planer das letzte freie Beet verbraucht und ein Jahr später nichts mehr geht. | berechenbar aus H-01 | mittel; bessere Alternative zu AP-FR-009 |
| Mindestfläche und Blockpflanzung | Mais benötigt Blockpflanzung für die Windbestäubung | Bestäubungstyp (`pollination_type` in `plant_info`) | niedrig |
| Sortenresistenz | Resistente Sorten (z. B. gegen Kohlhernie oder Kraut- und Braunfäule) verkürzen oder heben die Pause | Sortenfelder unbekannt (nicht geprüft) | niedrig |

### W-006: §5.3 Historie — Rückblick-Umfang und fehlende Eingänge
Der Rückblick von 4 Jahren (bis 8) reicht für die Familien-Pause meist, für persistente Pathogene nicht (K-001, daher Beet-Attribut außerhalb des Fensters). Fehlend:

| Eingang | Warum | Konsequenz |
|---|---|---|
| **Kalkung** (Datum, Menge, Wirkung auf pH) | pH steuert u. a. Kohlhernie-Druck und Schorf. ⚠️ NICHT VERIFIZIERT (R-018) | `care_events` `soil_amendment` mit `amendment_type = lime`; in `nutrition` und `soil_fit` |
| **Gründüngung** (Art, Einarbeitungsdatum, Leguminose ja/nein) | N-Gutschrift (K-006) und Wartezeit (W-002) | `season_state = green_manure` hat nur Familie. Art, Leguminosen-Flag und Einarbeitungsdatum ergänzen. |
| **Kompost-/Düngemenge** (Liter oder kg je m²) | Überversorgung mit P/K bei häufiger Kompostgabe (K-008) | `feeding`/`soil_amendment` mit Menge |
| **Befallsschwere und Erreger** | „Ereignis protokolliert" unterscheidet nicht zwischen Verdacht und bestätigtem Kohlhernie-Befall | `soil_hazards[]` oder `care_events` mit `pathogen`, `confirmed` |
| **Ernterückstände** (entfernt oder eingearbeitet) | Kohlstrünke und Kartoffelkraut mit Befall verbreiten Erreger | Flag am Run |
| **Bewässerungsart** (Tropf, Gießkanne, Überkopf) | Blattnässe fördert Pilzkrankheiten (Kraut- und Braunfäule, Mehltau). Für Gewächshaus wichtig. | Beet-Attribut, niedrig |
| **Ertragsausfall** mit Ursache | trennt Wetter von Bodenproblem | `harvest_batches`, niedrig |
| **Beet-Anlage-/Auffülldatum** (Hochbeet) | siehe K-008 | `soil_profile` |

Außerdem: **Lücken im Rückblick** müssen sichtbar als `history_gap` markiert sein und dürfen nicht als „frei" zählen (K-001, W-008).

### W-007: §5.5 / H-03 — was für Vorkultur und Herbstkulturen fehlt
- **Voranzucht-Vorlauf:** `sowing_indoor_weeks_before_last_frost` existiert im Schema (`species.schema.yaml:117`), kommt in H-03 aber nicht vor. Tomate, Paprika, Aubergine und Kohl-Jungpflanzen werden 6–8 Wochen vorgezogen. Das Beet ist in dieser Zeit frei. Die *Kulturdauer im Beet* ist die Dauer ab Pflanzung, nicht ab Aussaat. Ohne den Unterschied wird die Beetbelegung zu lang berechnet, und Vorkulturen (AP-FR-008) werden fälschlich blockiert. Dazu gehört ein Hinweis auf **Anzuchtkapazität** (Fensterbank, Anzuchtplatz). Sie ist nicht im Scope (§2.3) und sollte als Hinweis stehen: „60 Jungpflanzen brauchen Anzuchtplatz".
- **Erntefenster:** Das Ende ist der *Ernteende*, nicht der Erntebeginn. Tomate und Zucchini ernten 8–12 Wochen. `typical_duration_days` bis zur Erntephase liefert den Beginn; das Beet bleibt bis zum Ernteende belegt. Es braucht ein `harvest_window_days` oder eine Erntephasendauer. ⚠️ NICHT VERIFIZIERT (R-019).
- **Herbst- und Winterkulturen:** Frostharte Arten (Grünkohl, Rosenkohl, Feldsalat, Pastinake, Lauch) dürfen nach `first_frost_date_avg` stehen. Die Regel „Ende = früher von Kulturdauer und `first_frost`" ist nur für frostempfindliche Arten richtig und gilt dort ausdrücklich so. Die Belegung kann über den Jahreswechsel reichen und sperrt das Beet im Folgejahr (H-04, Folgejahr-Reservierung, mit `season_state`). Das Fenster braucht dafür ein Enddatum im Folgejahr. Goldfall (e) prüft das.
- **Kulturdauer ist temperaturabhängig:** `typical_duration_days` ist ein Einzelwert, Salat braucht im Frühjahr deutlich länger als im Sommer. Das System kennt GDD. Mittelfristig Kulturdauer aus GDD ableiten (Folge-Issue). ⚠️ NICHT VERIFIZIERT (R-020).
- **Gewächshaus:** H-03 kennt keinen Gewächshaus-Offset. Im unbeheizten Gewächshaus werden frostempfindliche Arten Wochen früher gepflanzt. Vorschlag: `greenhouse_offset_days` je Gewächshaus-Typ (unbeheizt/frostfrei/beheizt) als Beet- oder Site-Attribut. Das Schema führt es nicht (nur Frühjahrsfelder). ⚠️ NICHT VERIFIZIERT (R-021).
- **Bodentemperatur-Trigger:** Wenn REQ-046 Bodentemperatur liefert, sollte H-03 eine Bodentemperatur-Schwelle unterstützen (statt nur Frostdatum). Als Hinweis aufnehmen.

### W-008: Fehlende Historie und „neutral 0" (§5.4)
Die Regel „fehlende Historie ist neutral 0, nicht frei" ist richtig. Zwei Lücken: (1) Bei teilweiser Historie fehlt die Behandlung der Jahre *ohne Eintrag* (K-001). (2) „`must`-Bedarfe werden bevorzugt auf Beete mit Historie gelegt" ist nur ein Tie-Break. Für Hochrisiko-Familien (`shares_pest_risk high`, persistente Pathogene) sollte die Lücke eine Strafe tragen (z. B. −0,3 · Anteil unbekannter Jahre / Pause), sonst bekommt ein Beet ohne Daten dieselbe Bewertung wie ein bewährtes. Beträge ⚠️ NICHT VERIFIZIERT, Modellparameter.

### W-009: §2.3 Nicht im Scope — was für sinnvolle Belegung nötig ist
- **Gründüngung und Brache als Planergebnis:** Nicht ausgeschlossen, aber auch nicht gefordert. Ein Beet ohne Bedarf bleibt unbelegt. Die klassische Vierfelderwirtschaft *braucht* das Gründüngungs- oder Leguminosenjahr. **Muss in den Scope:** Der Planer schlägt für unbelegte oder über Winter freie Beete Gründüngung/Mulch vor (W-005 `soil_cover`). Das kostet keinen Solver, nur eine Regel.
- **Mehrjahresplanung (AP-FR-009 COULD):** Vertretbar als COULD, aber der Greedy-Planer kann sich ohne Vorausschau in die Ecke planen. `rotation_future` (W-005) löst das für ein Jahr ohne neuen Scope.
- **Düngeplanung:** Außerhalb des Scopes in Ordnung. `nutrition` setzt aber eine geplante Düngung voraus (K-008), also muss der Planer mindestens einen Hinweis „hier Kompost einplanen" ausgeben.
- **Anzuchtkapazität:** Hinweis, kein Scope (W-007).
- **Ausgeschlossen und in Ordnung:** Positionen im Beet, Sukzession, Ertragsprognose, Beetneuanlage, Sonnenberechnung, LLM als Planer.

### W-010: Weitere Präzisierungen
- **Profile (§7.3):** §3 Begriffe nennt vier Profile (`balanced`, `soil_health`, `yield`, `low_effort`), §7.3 und §15 fünf (zusätzlich `pest_control`). Beide Stellen angleichen. REQ-002 `optimization_goal` wird für `yield` auf `nutrient_balance` abgebildet. Das ist sachlich falsch: Nährstoffausgleich ist nicht Ertrag. Vorschlag: eigener Wert oder Abbildung auf `balanced`.
- **Space-Definition:** `Auslastung` = Σ Flächenbedarf / (`area_m2` × `usable_fraction`). Bei Ansatz auf `area_m2` ist das 85-%-Optimum nicht erreichbar, wenn H-02 bei 90 % kappt. Festlegen.
- **`fit`-Menge ohne Obergrenze:** `quantity_unit = fit` ohne `max_m2` füllt alle freien Flächen mit einer Art (z. B. 40 m² Salat). Obergrenze je Art fordern (z. B. `max_quantity`).
- **Reihenfolge der Konvention:** `rotation` beim Wechsel `Pause länger als Minimum` setzt „länger" ungeklärt gegenüber „nie im Fenster". Mit K-001 definieren: Kein Eintrag im Fenster = Jahre seit letzter Pflanzung `> window`.

---

## Hinweise und Best Practices (H)

- **H-001 Fixtures unabhängig von Seeds halten:** Jeder Goldfall trägt einen `knowledge`-Block (Pausen, Zehrerstufe, Flächenbedarf, Kompatibilität, Frostdaten). Die Konstanten sind **Fixture-Setzungen und keine agronomischen Aussagen**. So bleiben die Goldfälle stabil, wenn Seed-Werte geändert werden.
- **H-002 Rang statt Score:** Goldfälle sollen Belegung, Ausschlussgründe (`reason_code`), Warnungen und die Reihenfolge der getesteten Kriterien prüfen. Exakte Scores nur mit Toleranz (`±0,05`), sonst zwingt jede Gewichtsrevision zu Fixture-Diffs. Das passt zu AP-NFR-004 („bewusst aktualisieren"), aber wo möglich mit Rangvergleich testen.
- **H-003 Score nur im Profil vergleichbar:** Die Gewichtssummen unterscheiden sich je Profil. Vorschläge unterschiedlicher Profile sind nicht über `total_score` vergleichbar. Im Vergleich (AP-UX-005) kennzeichnen.
- **H-004 `must` + Fixierung + Warnung** sind konsistent und gut: AP-ACC-004 ist agronomisch korrekt (Übersteuerung sichtbar, nicht still).
- **H-005 Frostdaten-Fallback:** `window_source = month_fallback` ist ehrlich und sollte in der UI als Genauigkeitshinweis erscheinen.
- **H-006 Gewächshaus-Fruchtfolge:** In der Praxis wird im Tunnel häufig die Pause bei Tomate gebrochen, weil nur 1–2 Beete existieren. Der Planer soll das nicht abschwächen, sondern den Konflikt benennen (Goldfall e). Alternativen (Bodenwechsel, Veredelung, Bodenpflege) sind als Textvorschlag in `suggestion_de` sinnvoll. ⚠️ NICHT VERIFIZIERT (R-022).
- **H-007 Hochbeet-Alter** als Eingang (K-008).
- **H-008 Antwort auf Kompatibilitätsdaten:** REQ-028-Daten haben unterschiedliche Evidenzqualität. `evidence_level` an Kanten nutzen und im Breakdown anzeigen.

---

## Parameter-Übersicht (relevant für REQ-054)

| Parameter | Vorhanden? | Empfohlener Bereich | Priorität |
|---|---|---|---|
| PPFD / DLI / VPD / EC / pH Nährlösung / CO₂ | n. a. (Freiland) | — | — |
| `light_requirement` (O-01) | ❌ noch nicht im Schema | `full_sun`/`partial_shade`/`shade_tolerant`, plus Nutzorgan-Differenzierung (W-004) | hoch |
| Frostdaten-Perzentil statt Mittelwert | ❌ | 10-%-Risikodatum ⚠️ (R-003) | hoch |
| Gewächshaus-Offset | ❌ | je Typ, ⚠️ (R-021) | hoch |
| Bodenart/pH-Nutzung | ⚠️ gelesen, nicht verwendet | `soil_ph_preference`, `soil_texture` | mittel |
| Wurzeltiefe | ✅ Schema | `root_depth` | mittel |
| Wasserbedarf-Klasse | ❌ | 3 Klassen | mittel |
| Gehaltsklasse P/K/Mg statt „Klasse" | ⚠️ unscharf | A–E je Nährstoff (R-007) | mittel |

## Schema-Abgleich (Stichproben)

| Spec-Aussage | Schema | Status |
|---|---|---|
| `sowing_outdoor_after_last_frost_days` ≥ 0 reicht | `minimum: 0` | Widerspruch zu H-03 für frostharte Arten (K-004) |
| `growing_periods` hat Vorrang | `species.schema.yaml` | von H-03 nicht genutzt, nur Monats-Fallback (§5.5) |
| `sowing_indoor_weeks_before_last_frost` | vorhanden | nicht genutzt (W-007) |
| `Species.light_requirement` | fehlt | in O-01 bereits beschlossen |
| `root_depth`, `typical_root_depth`, `soil_ph_preference` | vorhanden | von REQ-054 ungenutzt (W-005) |
| `support_required` | vorhanden | nur in `preference`, falsch zugeordnet (W-004) |
| `rotation_pause_years`, `nitrogen_fixing`, `NutrientDemand` | im Schema-Verzeichnis per Grep **nicht gefunden** (nur `nutrient_demand_level`, `typical_nutrient_demand`) | REQ-053 §16.3 / v0077 sind Voraussetzung (§15). Vor P1 prüfen, ob die Felder im Seed-Schema nachgezogen sind. |

---

## Goldfälle (AP-NFR-004) — 1:1 als Fixture verwendbar

### Gemeinsame Konventionen (in jede Fixture als `knowledge`-Block kopieren)

- Planjahr 2026. Anbaupause: Jahr Y erlaubt, wenn `Y − letztes_Jahr ≥ Pause`.
- Fixture-Pausen (**Setzungen, nicht agronomisch verifiziert**): Brassicaceae 4, Solanaceae 4, Fabaceae 3, Cucurbitaceae 3, Amaryllidaceae 3, Apiaceae 3, Asteraceae 2.
- Zehrerstufe: Kohl, Tomate, Kürbis = Stark. Möhre, Zwiebel = Mittel. Salat, Radies, Basilikum = Schwach. Bohne, Wicke = Leguminose (Schwach). Schnittlauch = Schwach, Dauerkultur.
- Alle Bodenzustände: Gehaltsklasse C, keine Düngung erfasst → `nutrition = 0`, falls nicht anders genannt.
- Beete ohne Nachbarkante = „keine Nachbarn".
- Kompatibilität (Fixture-Setzung): Möhre–Zwiebel +0,8; Salat–Radies +0,6; Basilikum–Tomate +0,8; Bohne–Zwiebel `severe`; alles andere nicht im Graph = neutral 0.
- Zehrer-Matrix: K-006 (v1.2-Vorschlag). Gilt die Matrix nicht, fallen die Folgerungen in (a), (c), (d) entsprechend.
- `usable_fraction = 0,9`; `turnaround_days = 7`.
- Flächenbedarf je Pflanze: Kohl 0,25 m², Tomate 0,48 m², Kürbis 1,00 m², Gurke 0,50 m², Basilikum 0,04 m², Grünkohl 0,25 m². Bedarfe in m² werden direkt gerechnet.

### Goldfall (a) — Hausgarten, 5 Beete, klassische Vierfelder-Rotation

Idee: S → M → W → L (Stark, Mittel, Schwach, Leguminose), fünftes Beet Dauerbeet.

**Beete**

| Beet | Fläche | nutzbar (×0,9) | Typ / Zustand | Nachbarn |
|---|---|---|---|---|
| B1 | 6 m² | 5,4 | Freiland, `full_sun`, Klasse C | B2 |
| B2 | 6 m² | 5,4 | Freiland, `full_sun`, Klasse C | B1, B3 |
| B3 | 6 m² | 5,4 | Freiland, `full_sun`, Klasse C | B2, B4 |
| B4 | 6 m² | 5,4 | Freiland, `full_sun`, Klasse C | B3, B5 |
| B5 | 3 m² | 2,7 | Freiland, `rotation_exempt = true`, Dauerkultur Schnittlauch | B4 |

**Historie (Familie)**

| Beet | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| B1 | Brassicaceae (S) | Apiaceae (M) | Asteraceae (W) | Fabaceae, Buschbohne (L) |
| B2 | Fabaceae (L) | Cucurbitaceae (S) | Amaryllidaceae (M) | Asteraceae (W) |
| B3 | Asteraceae (W) | Fabaceae (L) | Solanaceae (S) | Apiaceae (M) |
| B4 | Amaryllidaceae (M) | Asteraceae (W) | Fabaceae (L) | Brassicaceae (S) |
| B5 | Schnittlauch (Dauer) | Schnittlauch | Schnittlauch | Schnittlauch |

**Bedarf**

| Key | Art (Familie) | Menge | Priorität | Fixierung |
|---|---|---|---|---|
| d1 | Weißkohl (Brassicaceae) | 18 Pflanzen (4,5 m²) | must | — |
| d2 | Möhre (Apiaceae) | 3,0 m² | must | — |
| d3 | Zwiebel (Amaryllidaceae) | 2,0 m² | must | — |
| d4 | Salat (Asteraceae) | 3,0 m² | want | — |
| d5 | Radies (Brassicaceae) | 1,0 m² | want | — |
| d6 | Buschbohne (Fabaceae) | 4,0 m² | must | — |
| d7 | Schnittlauch (Amaryllidaceae) | Bestand | must | pinned B5 |

**Erwartete Belegung**

| Beet | Belegung | Begründung |
|---|---|---|
| B1 | Weißkohl 18 Pfl. (4,5 m²) | Stark nach Leguminose (+0,6). Brassicaceae zuletzt 2022: 2022 + 4 = 2026, Pause genau erfüllt. B4 ist per H-01 gesperrt (2025). B2 und B3 sind erlaubt, aber ohne Vorfruchtvorteil (Schwach/Mittel → Stark = 0). |
| B2 | Buschbohne 4,0 m² | Fabaceae zuletzt 2022 → 2025 erfüllt. B1 gesperrt (2025 + 3), B4 gesperrt (2024 + 3 = 2027). Leguminose nach Schwach: neutral. |
| B3 | Salat 3,0 m² + Radies 1,0 m² (zusammen 4,0 m²) | Schwach nach Mittel (+0,3). Asteraceae zuletzt 2022. Salat–Radies +0,6. B2 für Salat per H-01 gesperrt (2025 + 2 = 2027). |
| B4 | Möhre 3,0 m² + Zwiebel 2,0 m² (5,0 m² ≤ 5,4) | Mittel nach Stark (+0,3). Möhre–Zwiebel +0,8. Zwiebel in B2 per H-01 gesperrt (2024 + 3 = 2027). Der Rest von 0,4 m² löst `space −0,2` aus. |
| B5 | Schnittlauch (Bestand) | `rotation_exempt`, Dauerkultur; Kohl in B5 ausgeschlossen (nur Dauerkultur erlaubt). |

**Prüft harte Regeln:** H-01 (Familien-Pausen, Grenzfall 2022 + 4 = 2026; `rotation_exempt`), H-02, H-06 (Bohne in B2 und Zwiebel in B4 sind nicht benachbart; B3 trennt sie).
**Prüft Kriterien:** `rotation` (Zehrer-Matrix, v1.2-Vorschlag), `companion` (Möhre–Zwiebel, Salat–Radies), `space`.
**Hinweis:** Mit der heutigen Heuristik in §7.2 (ohne Mittelzehrer) würde die Möhre in B4 keinen Vorteil erhalten. Der Fall belegt die Notwendigkeit von K-006.

### Goldfall (b) — Kohlhernie, zu kurze Pause

**Beete**

| Beet | Fläche | nutzbar | Zustand |
|---|---|---|---|
| B1 | 8 m² | 7,2 | `full_sun`, Klasse C, pH 6,0; `soil_hazards: kohlhernie confirmed 2023` |
| B2 | 8 m² | 7,2 | `full_sun`, Klasse C |
| B3 | 8 m² | 7,2 | `full_sun`, Klasse C |

**Historie**

| Beet | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| B1 | Fabaceae | Brassicaceae (Kohl; Befall Kohlhernie bestätigt) | Cucurbitaceae | Asteraceae |
| B2 | Apiaceae | Fabaceae | Brassicaceae (Kohl) | Amaryllidaceae |
| B3 | Asteraceae | Brassicaceae, Gründüngung Senf | Fabaceae | Apiaceae |

**Bedarf**

| Key | Art | Menge | Priorität |
|---|---|---|---|
| d1 | Weißkohl (Brassicaceae) | 20 Pflanzen (5,0 m²) | must |
| d2 | Zucchini (Cucurbitaceae, 1,0 m²/Pfl.) | 2 Pflanzen (2,0 m²) | want |

**Erwartete Ergebnisse**

| Variante | Eingabe | Erwartung |
|---|---|---|
| b1 | ohne Fixierung | `status = infeasible`. `unallocated[d1].reason_code = no_bed_without_rotation_conflict` mit `detail.earliest_year`: B1 2027, B2 2028, B3 2027 (Senf-Gründüngung zählt mit Familie). Kohl bleibt unbelegt. Zucchini wird belegt (nach W-003 als Teilplan): Zucchini in B2 (B1 hat Cucurbitaceae 2024 + 3 = 2027, gesperrt; B2 und B3 frei, B2 bevorzugt: Cucurbit nach Amaryllidaceae). Bleibt die Spec bei AP-ACC-003 (keine Allocation), lautet die Erwartung `allocations = []`. |
| b2 | `d1.pinned = B2` | `status = proposed`, Allocation in B2, `warnings[0].code = rotation_pause_violated` (2024 + 4 = 2028). Bei Annahme `rotation_override_reason` am Run. |
| b3 | `d1.pinned = B1` | `proposed`, zusätzlich `warnings[].code = persistent_soil_pathogen` (kohlhernie) mit Hinweis zur Gegenmaßnahme. Nur mit H-10 aus K-001. Ohne H-10 nur `rotation_pause_violated` (2023 + 4 = 2027), und der Test verlangt diesen Code. |

**Prüft harte Regeln:** H-01 (inkl. Gründüngung derselben Familie), H-07 (Fixierung übersteuert), H-08, H-10 (neu).
**Prüft Kriterien:** `pest_risk` (Zusatz für protokolliertes Ereignis), `rotation`.

### Goldfall (c) — Leguminosen-Vorfrucht-Gutschrift

**Beete**

| Beet | Fläche | nutzbar | Zustand |
|---|---|---|---|
| B1 | 5 m² | 4,5 | `full_sun`, Klasse C |
| B2 | 5 m² | 4,5 | `full_sun`, Klasse C, Kompost 2025 |
| B3 | 5 m² | 4,5 | `full_sun`, Klasse C |

**Historie**

| Beet | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| B1 | Brassicaceae | Apiaceae | Asteraceae | Fabaceae, Buschbohne geerntet |
| B2 | Fabaceae | Brassicaceae | Asteraceae | Solanaceae, Kartoffel (S) |
| B3 | Apiaceae | Asteraceae | Brassicaceae | `green_manure`, Wicke (Fabaceae), eingearbeitet Okt. 2025 |

**Bedarf**

| Key | Art | Menge | Priorität |
|---|---|---|---|
| d1 | Kürbis (Cucurbitaceae, Stark) | 3 Pflanzen (3,0 m²) | must |
| d2 | Salat (Asteraceae, Schwach) | 3,0 m² | want |

**Erwartete Belegung**

| Beet | Belegung | Begründung |
|---|---|---|
| B3 | Kürbis 3 Pfl. | Stark nach eingearbeiteter Leguminosen-Gründüngung (+0,6). Höhere Gutschrift als geerntete Bohne (+0,4, B1). Das zeigt, dass die Heuristik zwischen beiden unterscheiden muss (K-006). Fabaceae-Gründüngung zählt in H-01 mit Familie, betrifft Kürbis nicht. Turnaround nach Gründüngung ≥ 7 Tage; die Fixture setzt `turnaround_days = 14` für Übergänge nach Gründüngung (Vorschlag W-002), das Planfenster beginnt ausreichend später. |
| B2 | Salat 3,0 m² | Schwach nach Stark (+0,3). Kürbis in B2 wäre Stark nach Stark (−0,6) und ist dort schlechter. Asteraceae in B2 zuletzt 2024 → 2026 erfüllt (Pause 2). |
| B1 | unbelegt | Alternative für Kürbis: +0,4, also zweitbester Platz; als `alternatives[0]` mit `main_difference = lower_legume_credit`. |

**Prüft harte Regeln:** H-01 (Asteraceae-Grenzfall 2024 + 2 = 2026), H-02, H-03 (Turnaround nach Gründüngung).
**Prüft Kriterien:** `rotation` (Gutschriftstufen), `nutrition` (B2 mit Kompost: Starkzehrer dort +, Salat neutral).
**Tipp:** Kein `fit`-Bedarf verwenden (W-010 `fit` ohne Obergrenze).

### Goldfall (d) — Mischkultur-Konflikt `severe`, nur zwei Beete

**Beete**

| Beet | Fläche | nutzbar | Historie 2023 / 2024 / 2025 |
|---|---|---|---|
| B1 | 4 m² | 3,6 | Brassicaceae / Solanaceae / Cucurbitaceae |
| B2 | 4 m² | 3,6 | Asteraceae / Brassicaceae / Apiaceae |

**Bedarf**

| Key | Art | Menge | Priorität |
|---|---|---|---|
| d1 | Buschbohne (Fabaceae) | 3,0 m² | must |
| d2 | Zwiebel (Amaryllidaceae) | 3,0 m² | must |

**Varianten**

| Variante | Layout | Erwartung |
|---|---|---|
| d1 | B1 und B2 benachbart (Kante ≤ 30 cm) | Nach §6 H-06 (v1.1, Nachbarbeet hart): `status = infeasible`, `reason_code = severe_incompatibility`, `detail.conflicting_demand_keys = [d1, d2]`, keine Allocation. Nach W-001 (Nachbarbeet weich): beide belegt, `warnings[severe_incompatibility_neighbour]`, Score −1,0·w. Die Fixture hält die Variante fest, die die Spec beschließt. |
| d2 | B1 und B2 nicht benachbart (keine Kante) | Bohne in B1 (Leguminose nach Stark +0,3 nach Matrix), Zwiebel in B2. Beide zulässig, keine Warnung. |
| d3 | nur B1 | `infeasible`, `reason_code = severe_incompatibility`, kein Beet für den zweiten `must`. |

**Prüft harte Regeln:** H-06 (innerhalb Beet und Nachbarbeet), H-08.
**Prüft Kriterien:** `companion`, `rotation` (Bohne nach Starkzehrer). Entspricht AP-ACC-006, ergänzt um die Rotation als Tie-Break, damit Variante d2 deterministisch ist.

### Goldfall (e) — Gewächshaus + Freiland mit frostempfindlicher Art

**Site-Konstanten (Fixture):** `last_frost_date_avg = 2026-05-10`, `first_frost_date_avg = 2026-10-15`. Frostempfindliche Arten pflanzen ab Mittelwert + 7 Tage (Fixture-Setzung, siehe K-003; keine agronomische Aussage), also ab 2026-05-17. Gewächshaus, unbeheizt: Offset −14 Tage (Setzung, Feld im Schema nicht vorhanden, siehe W-007), also ab 2026-04-26.

**Beete**

| Beet | Typ | Fläche | nutzbar | Zustand |
|---|---|---|---|---|
| G1 | `greenhouse_bed`, unbeheizt | 6 m² | 5,4 | Klasse C |
| F1 | Freiland, `full_sun` | 8 m² | 7,2 | Klasse C, Nachbar K1 |
| F2 | Freiland, `sun_exposure = shade` | 8 m² | 7,2 | Klasse C |
| K1 | `planter`, `full_sun` | 2 m² | 1,8 | Nachbar F1 (Kante ≤ 50 cm) |

**Historie**

| Beet | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| G1 | Fabaceae | Cucurbitaceae (Gurke) | Asteraceae | Solanaceae (Tomate) |
| F1 | Apiaceae | Brassicaceae | Fabaceae | Amaryllidaceae |
| F2 | Apiaceae | Fabaceae | Amaranthaceae | Asteraceae |
| K1 | keine Historie | | | |

**Bedarf**

| Key | Art | Eigenschaften | Menge | Priorität |
|---|---|---|---|---|
| d1 | Tomate (Solanaceae) | `frost_sensitivity = high`, `greenhouse_recommended = true`, Kulturdauer bis Ernteende 150 d | 4 Pfl. (1,92 m²) | must |
| d2 | Gurke (Cucurbitaceae) | `frost_sensitivity = high`, `greenhouse_recommended = true`, 120 d | 3 Pfl. (1,5 m²) | want |
| d3 | Basilikum (Lamiaceae) | `frost_sensitivity = high`, `container_suitable = true`, 100 d | 6 Pfl. (0,24 m²) | nice |
| d4 | Grünkohl (Brassicaceae) | frostfest, `partial_shade`, Pflanzung ab 2026-06-15, 160 d | 6 Pfl. (1,5 m²) | want |

**Erwartete Belegung**

| Beet | Belegung | Fenster | Begründung |
|---|---|---|---|
| G1 | Gurke 3 Pfl. | 2026-04-26 bis 2026-08-24 | Gewächshaus-Offset. `site_fit +0,5` (`greenhouse_recommended` erfüllt). Cucurbitaceae zuletzt 2023 → 2026 erfüllt (Grenzfall). **Tomate in G1 per H-01 gesperrt (Solanaceae 2025 + 4 = 2029).** |
| F1 | Tomate 4 Pfl. + Basilikum 6 Pfl. | 2026-05-17 bis 2026-10-14 (Tomate) | Tomate frostempfindlich, Freiland erst ab 2026-05-17 (H-03/H-05). Kulturende 2026-10-14 vs. `first_frost_date_avg` 2026-10-15: Puffer 1 Tag → `timing −0,3` (Puffer < 14 Tage, K-007). `site_fit −0,3` (`greenhouse_recommended` im Freiland nicht erfüllt) und `warnings[greenhouse_recommended_not_met]`. Basilikum im selben Beet: Tomate–Basilikum +0,8. |
| F2 | Grünkohl 6 Pfl. | 2026-06-15 bis 2027-01-31 | Brassicaceae in F1 bis 2027 gesperrt (2023 + 4); F2 hat keine Brassicaceae im Fenster. Frostfeste Art: Ende darf nach `first_frost_date_avg` liegen. `light_requirement = partial_shade` in `shade`: zulässig. Die Reservierung reicht in 2027 hinein und sperrt F2 im Folgejahr (H-04). |
| K1 | unbelegt | — | Basilikum wäre dort möglich (Kübel, Pflanztermin nach 2026-05-17), liegt aber im selben Beet wie die Tomate (voller Kompatibilitätsfaktor 1,0 statt Nachbarbeet 0,5). `alternatives[]` von d3 nennt K1 mit `main_difference = neighbour_factor_half`. |

**Zusatzvariante e2:** `d1.pinned = G1` → `proposed`, `warnings[rotation_pause_violated]` (2025 + 4 = 2029) und kein Hinweis auf Freilandrisiko; `site_fit +0,5`, `timing` ohne Abzug.

**Prüft harte Regeln:** H-01 (Tunnelrotation), H-03 (Frostanker, Gewächshaus-Offset, Ende bei frostfestem Grünkohl über den Jahreswechsel), H-04 (Folgejahr-Reservierung), H-05 (Frostschutz, Kübel, Licht).
**Prüft Kriterien:** `site_fit`, `timing` (Puffer), `companion` (Basilikum), `rotation`.
**Voraussetzung:** K-003 (Frostmodell), K-004 (Schema-Felder) und W-007 (Gewächshaus-Offset) sind vor dem Einfrieren der Fixture zu entscheiden.

---

## Gewichtssätze (§7.3) — interne Konsistenz mit dem Namen

| Profil | Befund | Änderung |
|---|---|---|
| `balanced` | passt, aber `effort 0,3` wirkungslos (K-005) und `preference 0,7` hoch gegenüber `rotation 1,0` | `preference` auf 0,5; `effort` nach K-005 anpassen |
| `soil_health` | `rotation 1,5`, `nutrition 1,0`, `pest_risk 1,0` passen. Es fehlen Gründüngung, Bodenbedeckung und Wurzeltiefe, die dieses Profil im Kern ausmachen. | neue Kriterien `soil_cover` (1,0) und `root_depth_rotation` (0,6) ergänzen |
| `pest_control` | `rotation 1,0` ist gleich wie in `balanced`. Fruchtfolge ist der wichtigste phytosanitäre Hebel. `pest_risk 1,5` und `companion 0,9` passen. | `rotation` auf mindestens 1,3 |
| `yield` | `space 1,0`, `timing 0,8`, `site_fit 0,8`, `nutrition 0,9` passen. `rotation 0,8` und `pest_risk 0,6` sind niedriger als in `balanced`: Ertrag leidet unter Fruchtfolgefehlern, nicht darunter. Die Abbildung auf `optimization_goal = nutrient_balance` ist falsch (W-010). | `rotation` und `pest_risk` wie in `balanced` lassen; `space` auf 0,6 (siehe W-004) |
| `low_effort` | `effort 1,0` passt. `preference 0,9` ist inhaltlich kein Arbeitsaufwand. Pflegeleichte Arten (Schwachzehrer, keine Rankhilfe, geringe Schädlingsanfälligkeit) fehlen als Kriterium. | `preference` auf 0,5; Kriterium `care_load` je Art ergänzen (neue Daten nötig, daher später) |

Die Gewichte sind ⚠️ **Modellparameter ohne Quelle** (Aussage nur über Richtung). Vergleich nur innerhalb eines Profils (H-003).

---

## 🔍 Offene Recherchepunkte — Verifizierung ausstehend

| Nr. | Aussage | Verfügbare Quellen | Fehlend | Empfohlene Recherche |
|---|---|---|---|---|
| R-001 | Dauerstadien persistenter Bodenpathogene (Kohlhernie, Zystennematoden, Zwiebelweißfäule, Erbsenmüdigkeit) überdauern viele Jahre; konkrete Jahre je Erreger | im Review nicht abrufbar | alle 3 | JKI, LfL Bayern, CABI Compendium, EPPO Global Database, universitäre Phytopathologie |
| R-002 | Familienübergreifende Wirtskreise (Meloidogyne, Heterodera schachtii inkl. Senf/Ölrettich, Sclerotinia, Verticillium) | wie R-001 | alle 3 | EPPO Global Database, CABI, JKI-Erregersteckbriefe |
| R-003 | Mittel des letzten Frosts hat ca. 50 % Überschreitungsrisiko; 10-%-Risikodatum; Eisheilige | Statistik-Grundsatz | 3 Quellen | DWD Klimadaten und Phänologie, Meteorologie-Fachbuch |
| R-004 | Photoperiodisches Schossen (Spinat, Salat, Chinakohl) und Herbstanker | wie R-001 | alle 3 | Hartmann's Plant Science, Taiz & Zeiger, Gemüsebau-Lehrbuch, Sortenprüfungen |
| R-005 | N-Gutschrift verschiedener Leguminosenformen (eingearbeitete Gründüngung vs. geerntete Gemüse-Leguminose); Starkzehrer-Folge | wie R-001 | alle 3 | KTBL, LfL, Bioland/Naturland Gemüsebau, Fachbuch Gemüsebau |
| R-006 | Reifezeit-Streuung und GDD-Bezug; Puffer von 14 Tagen gegenüber Frost | wie R-001 | alle 3 | Gemüsebau-Anbauberatung, Hochschule Geisenheim |
| R-007 | VDLUFA-Gehaltsklassen je Nährstoff; N nicht über Klassen abbildbar | VDLUFA-Standpunkt (nicht im Review geprüft) | 2 weitere | VDLUFA, LfL Bayern, Landwirtschaftskammern |
| R-008 | Hochbeet-Nährstoffzyklus (Starkzehrer im ersten Jahr) | wie R-001 | alle 3 | Gartenbau-Beratung der Landesanstalten, Fachbuch |
| R-009 | Wirkabstand von Allelopathie über Beetgrenzen (30 cm als Schwelle) | wie R-001 | alle 3 | Allelopathie-Fachliteratur, REQ-028-Quellen |
| R-010 | Fenchel-Allelopathie; Juglon/Walnuss und Solanaceae; Roggen-Hemmung der Folgesaat | wie R-001 | alle 3 | Universitäre Extension, Fachliteratur Allelopathie |
| R-011 | pH-Grenzen für Säurezeiger (Heidelbeere) und Schorf/Kohlhernie-pH | wie R-001 | alle 3 | LfL, RHS, Fachliteratur |
| R-012 | Wegeanteil und Reserve bei `usable_fraction` je Beettyp | REQ-002 | 3 Quellen | Gartenbau-Beratung, Fachbuch |
| R-013 | Wartezeit nach Gründüngungseinarbeitung bis Saat/Pflanzung | wie R-001 | alle 3 | Fachbuch, LfL, Bioland |
| R-014 | Dauer des Insektenrisikos im Boden (Möhren-, Kohlfliege) | wie R-001 | alle 3 | JKI, EPPO |
| R-015 | Evidenz der Mischkultur-Wirkung je Paar | wie R-001 | alle 3 | Peer-reviewed Reviews zu Mischkultur |
| R-016 | Wirkradius Nachbarbeet-Faktor 0,5 | — | alle 3 | wie R-015 |
| R-017 | Lichtbedarf Fruchtgemüse vs. Blattgemüse; Hitzeschäden kühler Kulturen im Gewächshaus | wie R-001 | alle 3 | Gemüsebau-Lehrbuch, RHS |
| R-018 | Einfluss von Kalkung auf Kohlhernie und Schorf | wie R-001 | alle 3 | JKI, Universitäre Studien |
| R-019 | Erntedauer von Tomate und Zucchini (Beetbelegung bis Ernteende) | wie R-001 | alle 3 | Sortenprüfungen, Anbauberatung |
| R-020 | Kulturdauer in Abhängigkeit von Temperatur (GDD) | wie R-001 | alle 3 | Hartmann's Plant Science, Gemüsebau |
| R-021 | Pflanzzeitpunkt im unbeheizten Gewächshaus relativ zum letzten Frost | wie R-001 | alle 3 | Anbauberatung Gewächshaus, LfL |
| R-022 | Tomatenwechsel im Tunnel: Bodenwechsel, Veredelung als Maßnahmen | wie R-001 | alle 3 | Gartenbau-Versuchsanstalten |
| R-023 | Familien-Pausen (Brassicaceae, Solanaceae, Fabaceae, Apiaceae, Amaranthaceae, Cucurbitaceae, Amaryllidaceae, Asteraceae) | REQ-001 Seeds | je 3 | JKI, Bioland, LfL, Fachbuch Gemüsebau |
| R-024 | Zehrerstufen der Arten in den Goldfällen | REQ-053 §16.3 | je 3 | KTBL, Fachbuch |

Alle Zahlen in den Goldfällen sind Fixture-Setzungen und tragen keine agronomische Aussage. Die Heuristik-Beträge in §7.2/§7.3 sind Modellparameter und nicht belegbar; belegbar ist nur ihre Richtung.

---

## Empfohlene Datenquellen

| Bereich | Quelle |
|---|---|
| Schaderreger, Wirtskreise | EPPO Global Database, JKI, CABI |
| Taxonomie (APG IV) | POWO, GBIF |
| Frost- und Phänologiedaten | DWD |
| Nährstoffklassen | VDLUFA, LfL |
| Gemüsebau-Praxis | KTBL, Bioland/Naturland, Hochschule Geisenheim |

---

## Empfohlene nächste Schritte

1. **K-001 bis K-007 entscheiden** und in REQ-054 v1.2 einarbeiten, danach erst die Gewichte und Goldfälle einfrieren.
2. **Folge-Issues:** Schema (`sowing_windows`, vorzeichenbehafteter Offset, Gewächshaus-Offset, `soil_hazards`), REQ-001 (Erreger → Wirtsfamilien, Persistenz), REQ-053 (Historie-Eingänge W-006).
3. **Goldfälle (a) bis (e)** als JSON-Fixtures anlegen. Für (b3), (d1) und (e) die Varianten festlegen, die die Entscheidung zu H-10 und H-06 (Nachbarbeet) ergibt.
4. **Recherche R-001 bis R-024** abarbeiten, bevor Zahlen als „fachlich geprüft" gelten.

**Go/no-go: FAIL für die Startwerte** (Frostmodell, `timing`-Kriterium, Score-Aggregation und Zehrer-Matrix sind noch nicht tragfähig). **PASS für Architektur und Verfahren** (deterministische, erklärbare Engine, harte/weiche Trennung, Vorschlag statt Ausführung).

Datei: `/home/nolte/repos/github/kamerplanter/spec/req/REQ-054_Automatische-Anbauplanung.md`
