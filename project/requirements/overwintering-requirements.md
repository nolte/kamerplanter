# Requirements — Überwinterungs-Cluster: inhaltliche Vertiefung (REQ-047 als Anker)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
Elicited: 2026-07-11. Interview language: German. Artifact language: German
(follows spec/req/ project precedent — see R5).
-->

## Bounded context

- **Was:** Die über mehrere REQ-Dokumente verstreute Überwinterungs-Fachlichkeit
  wird **inhaltlich vertieft und erweitert** — mehr abgedeckte Fälle, präzisere
  Akzeptanzkriterien, geschlossene fachliche Lücken. **Anker:** `REQ-047`
  (Saison-/Überwinterungs-Automatik, SeasonState-Engine). **Cluster:** `REQ-022`
  (Pflegeerinnerungen / OverwinteringProfile / CareProfile), `REQ-039`
  (Winterhärte-Ampel). Berührt lesend/konsumierend: REQ-001/002/003/005/006/013/
  041/046/024.
- **Für wen:** Endnutzer der App (Gelegenheits-Gärtner ohne Fachwissen,
  Nutzer mit/ohne Wetteranbindung, erfahrene Übersteuernde) — vertreten durch die
  bestehenden REQ-047-User-Stories. Nachgelagerter Konsument der Vertiefung:
  Implementierung/Doku.
- **Explizit außerhalb des Scopes:** (a) **Produktivcode** — dies ist reine
  Spec-Arbeit unter `spec/req/`. (b) **Neudefinition** der Wetter-/Frost-
  Datenbeschaffung (REQ-005/046), der Klimanormale (REQ-041) oder der
  Winterhärte-Ampel-Logik (REQ-039) — REQ-047 bleibt deren Konsument.
  (c) **Duplizieren** art-spezifischer Überwinterungs-Werte im REQ-Text — diese
  bleiben SSOT in den Steckbriefen §4.3. (d) EN-Übersetzung der REQ-Dokumente.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `6` (verbraucht: 4 Frage-Turns)
  <!-- spec defaults, unverändert übernommen; kein projektspezifischer Override nötig -->
- `U_gate = min_d c_d` über erforderliche Dimensionen = **0.80**
- Termination: `saturation` (alle erforderlichen Dimensionen ≥ `τ_high` mit Teach-back; keine verbleibende Frage mit positivem Netto-EVPI — die noch offene Feinauflösung ist Design-Discovery beim Grounding, keine nutzerseitige Spezifikationslücke)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.80 | specification | Q1: alle vier Themenblöcke in Scope bestätigt; Teach-back bestätigt Reihenfolge |
| `non_functional` | yes | 0.80 | specification | Q4: volle DoD (Lektorat + Cluster-Konsistenz); Graceful-Degradation/Mobile-First aus Bestand |
| `constraints` | yes | 0.85 | specification | Q2: „erst angleichen, dann vertiefen" + netto-neue Tiefe als „noch nicht implementiert"; CLAUDE.md (Spec≠Code, DE) |
| `domain_objects` | yes | 0.85 | interpretation | Grounding: REQ-047 vollständig gelesen (SeasonState/OverwinteringProfile/CareProfile/§4.3); **k=2 self-consistency** über „Cluster-Reichweite" divergierte → trieb Q3, nach Antwort konvergiert |
| `actors` | yes | 0.80 | interpretation | REQ-047 §1 User Stories (Gelegenheits-Gärtner, Wetter-Nutzer, hardwarelos, erfahren-übersteuernd); Teach-back |
| `acceptance_criteria` | yes | 0.80 | specification | Q4: Cluster-Review grün + EARS-ACs je vertieftem Thema; Teach-back |
| `edge_cases` | yes | 0.80 | specification | Q1: „Automatik-Robustheit" als eigener Themenblock bestätigt; Teach-back (Rest-Enumeration = Design-Discovery, s. Risiken) |
| `scope_boundaries` | yes | 0.85 | specification | Q3 (additiv wo Thema wohnt) + Q5 (DE-only, per Faktencheck spec/req/ verifiziert) + Teach-back |

## Requirements

<!-- EARS/CNL, tagged confirmed/assumed, traceable. „System" = das vertiefte
     REQ-Dokumentenset (Deliverable). -->

### Rahmen & Vorgehen

- **R1** — Das vertiefte Anforderungsset SHALL ausschließlich als DE-kanonische
  REQ-Dokumente unter `spec/req/` geliefert werden; es SHALL **keinen**
  Produktivcode ändern.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: Plan (operator-bestätigt 2026-07-11) + „Es ist Spec-Arbeit, keine Code-Implementierung"
- **R2** — WENN REQ-047 vertieft wird, SHALL zuerst der Kern des Dokuments an den
  real implementierten Stand (PR #406/#410) angeglichen werden (Status
  `Entwurf → Umgesetzt`, Versionshistorie gepflegt); netto-neue Fachlichkeit, die
  über den gebauten Stand hinausgeht, SHALL explizit als „noch nicht
  implementiert" markiert werden (DOCS.md-Konvention).
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: Q2 „Erst angleichen, dann vertiefen"
- **R3** — Die Vertiefung SHALL REQ-047 als Anker führen und REQ-022 **additiv**
  dort erweitern, wo die Fachlichkeit dort beheimatet ist (OverwinteringProfile-,
  CareProfile-, ReminderType-Felder); REQ-039 SHALL nur minimal berührt werden.
  Art-spezifische Überwinterungs-Werte SHALL in den Steckbriefen §4.3 verbleiben
  (SSOT) und im REQ-Text **referenziert statt dupliziert** werden.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: Q3 „Additiv wo das Thema dort wohnt" + SSOT-Regel
- **R4** — Bevor die Arbeit als fertig gilt, SHALL (a) `lektorat-apply` auf jedes
  geänderte Dokument laufen und die DOCS.md-Konventionen erfüllt sein, (b) ein
  Cluster-Konsistenz-Review (`spec-readiness-reviewer` + `requirements-
  contradiction-analyzer`) durchlaufen und gefundene Widersprüche aufgelöst sein,
  und (c) Versionshistorie und Status je geändertem REQ gepflegt sein.
  - _dimension_: `non_functional` / `acceptance_criteria` · _status_: `confirmed` · _source_: Q4 „Voll: Lektorat + Cluster-Konsistenz"
- **R5** — Die REQ-Dokumente SHALL DE-kanonisch bleiben, ohne EN-Mirror-Pflicht;
  darin enthaltene UI-Strings SHALL weiterhin DE+EN geführt werden. Da `spec/req/`
  per Faktencheck flach/DE-only ist und kein Spec-Root-Index existiert, SHALL
  keine EN-Übersetzung und keine Index-Regeneration erfolgen.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: Q5 „so wie das Projekt es definiert" → per `ls spec/req/` verifiziert (kein EN-Mirror, kein Index)
- **R6** — REQ-047 SHALL Konsument von REQ-005/046 (Wetter/Frost), REQ-041
  (Klimanormale) und REQ-039 (Ampel) bleiben; die Vertiefung SHALL diese Domänen
  **nicht** neu definieren. WENN die Vertiefung neue Implementierung nahelegt,
  SHALL diese als Folge-REQ/Backlog markiert und **nicht** hier gebaut werden.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: Plan-Invarianten „Abgrenzung wahren" + REQ-047 §1 Abgrenzung; Teach-back
- **R12** — Die Vertiefung SHALL in dieser Reihenfolge erfolgen: (0) REQ-047-Kern
  an gebauten Stand angleichen → (1) Winterquartier & Pfad B → (2) Frühjahr &
  Abhärtung → (3) Arten & Sonderfälle → (4) Automatik-Robustheit.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: Teach-back „Passt — so umsetzen"

### Fachliche Vertiefung (Inhalt = Deliverable)

- **R7** — Der „Verlagern"-Pfad (Pfad B / Winterquartier) SHALL fachlich vertieft
  werden: Quartier-Typen (kalt / frostfrei / temperiert / dunkel), Licht-/
  Temperatur-/Feuchte-Bedingungen je Art (per Steckbrief-Verweis), Einräum-/
  Ausräum-Prozess sowie Fäulnis-/Schimmel-/Schädlingskontrolle im Lager — heute
  nur dünn über `quarter_climate_check` abgedeckt.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q1 „Winterquartier & Pfad B"
- **R8** — Der Frühjahrs-Rückhol-Prozess (`pre_spring`) SHALL vertieft werden:
  gestaffelte Abhärtung (`harden_off`, Tag-für-Tag), Knollen-Vorziehen
  (`pre_sprouting`), Abhäufeln (`uncover`), Spätfrost-Schutz und schrittweises
  Rausstellen (`move_outdoors`) — heute als grobe Checkliste skizziert.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q1 „Frühjahr & Abhärtung"
- **R9** — Die Artenabdeckung SHALL erweitert werden um: immergrüne/wintergrüne
  Arten, grenzwertig-winterharte (Ampel-Grenzfälle), Kübel vs. Beet, geheiztes vs.
  kaltes Gewächshaus (heute `outdoor`/`greenhouse` identisch behandelt) sowie
  zwei-/mehrjährige Sonderfälle.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q1 „Arten & Sonderfälle"
- **R10** — Die Saison-Zustandsmaschine SHALL an ihren Edge Cases gehärtet werden:
  Mehrjahres-Hysterese, Mildwinter-/Kahlfrost-Ausnahmen, Quellen-Hochstufung
  mitten in der Saison, fehlende/veraltete Daten, Override-Konflikte und
  Idempotenz-Grenzfälle — je als prüfbares Kriterium.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: Q1 „Automatik-Robustheit"
- **R11** — WENN ein Themenblock (R7–R10) vertieft wird, SHALL die Vertiefung in
  neue/erweiterte, EARS-normalisierte Akzeptanzkriterien in der AC-Liste des
  jeweiligen REQ münden (nicht nur Fließtext).
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: Q4 + REQ-047 §7 als Muster; Teach-back

## Surviving assumptions / open risks

- **A1 (Design-Discovery, edge_cases/functional):** Die *konkrete* Enumeration der
  fehlenden Fälle je Themenblock (welche Arten-Klassen, welche exakten Edge Cases,
  welche Quartier-Parameter) ist beim Grounding gegen den gebauten Code + die
  Steckbriefe §4.3 zu ermitteln. Bestätigt ist die *Verpflichtung* zu vertiefen,
  nicht die fertige Liste. `assumed` bis zum jeweiligen Vertiefungs-Schritt.
- **A2 (Drift-Umfang):** Wie groß die Spec↔Code-Divergenz von REQ-047 real ist,
  ist erst nach Lesen des implementierten Stands (Backend/Frontend zu
  SeasonState/Overwintering) belastbar. R2 legt die *Haltung* fest, nicht den
  Umfang. Divergenzen werden beim Angleichen bewusst als „angleichen vs. bewusst
  voraus-spezifizieren" entschieden und im REQ markiert.
- **A3 (GWH-Sonderfall, R9):** Ob „geheiztes vs. kaltes Gewächshaus" eine echte
  Modell-/Feld-Erweiterung nahelegt (die dann per R6 Backlog-Folge-REQ würde) oder
  rein textlich/kriterienbasiert bleibt, entscheidet sich beim Vertiefen von R9.
- **A4 (Restrisiko unter Reflexion):** Keine erforderliche Dimension liegt unter
  `τ_high`; es besteht kein budgetbedingter Stopp. Einziges strukturelles Risiko
  ist A1/A2 (Discovery-Natur der Inhaltsarbeit), das methodisch nicht per Interview
  schließbar ist, sondern beim Grounding.
