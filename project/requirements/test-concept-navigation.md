# Requirements — Test-Dokumentation als verschachtelte MkDocs-Navigationsebene

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back
or an authoritative user answer.
-->

## Bounded context

- **Was gebaut wird:** Unter der MkDocs-Navigation `Entwicklung → Testen` wird
  die heutige Einzelseite (`docs/{de,en}/development/testing.md`) zu einer
  **Sektion mit Index** ausgebaut: das *Testkonzept* als Einstieg
  (`testing/index.md`), darunter eine Ebene *Teststufen* mit vier Blättern
  (Unit / Integration / Component / E2E). Testfälle aus `spec/e2e-testcases/`
  erscheinen **nicht je Fall als Nav-Eintrag**, sondern als prosaische/tabellarische
  Übersichten pro Teststufe, damit die Sidebar nicht „explodiert".
- **Für wen:** Leser der Projektdokumentation (Entwickler / Contributor).
  DE-kanonisch, EN gespiegelt.
- **Explizit außerhalb Scope:** kein Umbau der Test-*Infrastruktur* (pytest /
  vitest / Selenium), kein neuer Testcode; keine Änderung an `spec/e2e-testcases/`
  als Quelle; keine je-Testfall-Nav-Einträge; **der Testfall-Tabellen-Generator
  (`gen_testcase_tables.py`) ist auf einen Folge-PR verschoben**.
- **Rahmenbedingungen:** `spec/style-guides/DOCS.md` (informelles „du",
  Admonitions, REQ-ID-Sichtbarkeit, Fact-Table-Konvention); NFR-003 (Doku
  DE-kanonisch / EN-mirror, Quellcode + IDs Englisch); jeder neue Nav-Titel
  braucht einen `nav_translations`-EN-Eintrag; lokaler MkDocs-Strict-Build nur
  im isolierten docs-venv.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `8`
  <!-- spec defaults; unverändert übernommen -->
- `U_gate = min_d c_d` over required dimensions = **0.80**
- Termination: `saturation` — alle erforderlichen Dimensionen ≥ τ_high nach vier
  autoritativen Scope-Entscheidungen; keine verbleibende Frage hat positiven
  Netto-EVPI (weitere Fragen würden die erfasste Menge nicht mehr ändern, nur
  ermüden). 4 von 8 Budget-Zügen genutzt.

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.85 | specification | Autoritative Antworten auf Q2 (4 Teststufen), Q4 (Migration testing.md→index); k=2-Self-Consistency: zwei unabhängige Nav-Skizzen konvergierten auf {Testen-Index + Teststufen-Index + 4 Blätter} |
| `non_functional` | yes | 0.85 | specification | Q1 (expand behalten, Tabellen statt Nav-Fülle) + Bounded-Context-Teach-back (DE/EN-Parität, Strict-Build) unwidersprochen |
| `constraints` | yes | 0.85 | interpretation | Bestätigte Recherche im Plan (mkdocs.yml: `navigation.expand`, `nav_translations`, `plugins.redirects`, `pymdownx.snippets`); NFR-003; DOCS.md |
| `domain_objects` | yes | 0.85 | specification | Q2 fixiert die Entitäten: Testkonzept + 4 Teststufen; Testfälle-Quelle `spec/e2e-testcases/` (TC-REQ-*, TC-NFR-*) |
| `actors` | yes | 0.80 | interpretation | Bounded-Context-Teach-back: Doku-Leser (Entwickler/Contributor); keine Login-/Rollen-Semantik in reiner Doku |
| `acceptance_criteria` | yes | 0.80 | interpretation | Operator-endorsierte Plan-Invarianten (Strict-Build grün, Link-Check, DE/EN-Parität, Redirect funktioniert); im Teach-back unten gespiegelt |
| `edge_cases` | yes | 0.80 | interpretation | Plan benennt: alte URL braucht Redirect; fehlender `nav_translations`-Eintrag bricht EN; ggf. dünne/leere Component-Stufe |
| `scope_boundaries` | yes | 0.90 | specification | Q3 (MVP: Nav+Struktur+Prosa, Generator später) + Bounded-Context-Ausschlüsse; klarste Dimension |

## Requirements

<!-- EARS/CNL-Form, getaggt confirmed/assumed, mit Traceability zur Äußerung. -->

- **R1** — WENN ein Leser in der Doku-Navigation `Entwicklung → Testen` öffnet,
  SOLL die Site eine **Sektion mit Index** zeigen (Testkonzept =
  `docs/de/development/testing/index.md`) statt einer Einzelseite.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Q4 „Nach testing/index.md migrieren + Redirect" + Plan Design-Decision
- **R2** — Die Sektion `Testen` SOLL eine Unterebene **Teststufen** enthalten mit
  einem Übersichts-Index und genau **vier** Blattseiten: Unit, Integration,
  Component, E2E.
  - _dimension_: `domain_objects` · _status_: `confirmed` · _source_: Q2 „4 Stufen: Unit / Integration / Component / E2E"
- **R3** — Testfälle aus `spec/e2e-testcases/` SOLLEN je Teststufe als
  **prosaische/tabellarische Übersicht** dargestellt werden, NICHT als
  je-Testfall-Nav-Eintrag.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Bounded Context „Sidebar nicht sprengen" + Q3
- **R4** — Die globale MkDocs-Option `navigation.expand` SOLL **unverändert**
  bleiben; die Sidebar-Fülle SOLL allein über Tabellen (statt Nav-Tiefe) begrenzt
  werden.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: Q1 „expand behalten, Fülle über Tabellen zähmen"
- **R5** — WENN die bestehende `testing.md` nach `testing/index.md` migriert wird,
  SOLL die öffentliche URL erhalten bleiben und dürfen keine internen Quell-Links
  brechen.
  - _dimension_: `edge_cases` · _status_: `confirmed` · _source_: Q4 „+ Redirect" + Plan-Invariante
  - **Umsetzungsbefund (Build-verifiziert):** Wegen `use_directory_urls` rendern
    `testing.md` UND `testing/index.md` auf **dieselbe** URL `/development/testing/` —
    die URL ändert sich also nicht. Ein `redirect_maps`-Eintrag ist deshalb nicht nur
    überflüssig, sondern **schädlich**: `mkdocs-redirects` überschreibt die echte
    `index.html` mit einem Self-Redirect (`url=./` → Endlosschleife). Der Redirect
    wurde daher wieder entfernt; stattdessen wurden die 8 eingehenden Quell-Links
    (`testing.md` → `testing/index.md`) in den Geschwisterseiten korrigiert.
- **R6** — Für **jeden** neuen deutschen Nav-Titel SOLL ein `nav_translations`-EN-Eintrag
  ergänzt werden, damit der EN-Build vollständig und einheitlich bleibt.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: Plan-Invariante (mkdocs.yml:90–202) + NFR-003
- **R7** — Alle neuen Seiten SOLLEN DE-kanonisch verfasst und EN gespiegelt werden,
  konform zu `spec/style-guides/DOCS.md` (informelles „du", Admonitions,
  REQ-ID-Sichtbarkeit).
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: Bounded Context + NFR-003
- **R8** — WENN die Änderung abgeschlossen ist, SOLL der lokale MkDocs-**Strict-Build**
  im isolierten docs-venv fehlerfrei durchlaufen, der Link-Check sauber sein und
  DE/EN-Parität bestehen (Definition of Done).
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: Operator-endorsierte Plan-Invarianten (Teach-back unten)
- **R9** — Der Testfall-Tabellen-**Generator** (`scripts/docs/gen_testcase_tables.py`)
  SOLL NICHT Teil dieses Arbeitspakets sein, sondern als Folge-PR erfolgen.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: Q3 „MVP: nur Nav + Struktur + Prosa (Generator später)"
- **R10** — Jede Teststufen-Seite SOLL eine **handkuratierte, thematische
  Übersichtstabelle** („Getestete Bereiche im Überblick") enthalten, die einen
  Eindruck vermittelt, welche Elemente auf dieser Ebene getestet werden — mit
  qualitativem Umfang (umfangreich/mittel/fokussiert) statt driftanfälliger
  Zahlen, faktenbasiert aus dem realen Test-Baum erhoben.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: Revisit „ich vermisse noch eine übersicht der existierenden testfälle für die jeweilige stufe … welche elemente auf welcher ebene getestet werden" + Zuschnitt-Entscheidung „Kompakt-thematische Tabelle"
  - _Abgrenzung zu R9:_ statische Tabellen, KEIN Generator — R9 bleibt gültig.

## Surviving assumptions / open risks

- **AC-Teach-back (R8):** Die Akzeptanzkriterien (Strict-Build grün, Link-Check
  sauber, DE/EN-Parität, funktionierender Redirect) sind aus den Operator-endorsierten
  Plan-Invarianten abgeleitet, nicht in einem separaten expliziten Teach-back-Zug
  einzeln bestätigt. `c_d = 0.80` genau an der Schwelle — falls zusätzliche DoD-Kriterien
  (z. B. Screenshot-Abnahme der Sidebar) gewünscht sind, hier nachtragen.
- **Component-Teststufe (R2):** Falls das Projekt real keine dedizierten
  Component-Tests führt, könnte diese Seite dünn/konzeptionell bleiben. Beim
  Schreiben verifizieren; ggf. als „geplant"-Admonition kennzeichnen statt leere Stufe.
- **`assumed`-Einträge:** keine — alle R1–R10 sind `confirmed`. Restrisiken sind
  ausschließlich die obigen an-der-Schwelle-Punkte.
- **Drift der Übersichtstabellen (R10):** Die kuratierten „Getestete Bereiche"-Tabellen
  sind handgepflegt und können vom realen Test-Baum abweichen, wenn neue Testbereiche
  entstehen. Bewusst gegen Zahlen-Drift gehärtet (qualitativer Umfang), aber neue
  fachliche Bereiche müssen manuell nachgetragen werden — der verschobene Generator (R9)
  wäre die dauerhafte Lösung.
