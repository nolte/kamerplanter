# Requirements — Frontend-Audit 2026-11 (`chore/frontend-audit`)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
-->

## Bounded context

- **Was:** Ein ausführliches, belegtes Audit von `src/frontend/` (React 19,
  **MUI 9**, TS 6, Vite 8). Jeder Befund hat `file:line`, einen Schweregrad und
  die verletzte Regel. Dazu kommen eine priorisierte Maßnahmenliste und eine
  vollständige Delta-Tabelle gegenüber `spec/analysis/frontend-ui-audit-2026-04.md`.
- **Für wen:** den Betreiber als Entscheidungsgrundlage und die nachgelagerte
  Umsetzung über Issues und Lanes.
- **Explizit außerhalb:**
  - Nicht-triviale Code-Fixes. Sie werden zu Issues und landen nicht in diesem Branch.
  - Backend, Helm, HA-Integration und Docs-Site.
  - Dauerläufe lokaler Tests. Tests laufen auf CI.

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`,
  question budget = `8` (Spec-Defaults; Budget eng gewählt, weil der Plan die
  offenen Fragen bereits vorformuliert hatte)
- `U_gate = min_d c_d` über die Pflichtdimensionen = **0.8**
- Termination: `saturation` (4 von 8 Fragerunden verbraucht, Teach-back bestätigt)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.9 | specification | Antwort „Alle sieben", „Ja, als Zusatzmaßstab" und Teach-back |
| `non_functional` | yes | 0.85 | specification | Antwort Delta-Tabelle „vollständig" und Teach-back; Belegpflicht `file:line` aus dem Plan |
| `constraints` | yes | 0.85 | interpretation | Teach-back bestätigt einen einmaligen lokalen `vite build`; Live-Ziel ist der Dev-Cluster |
| `domain_objects` | yes | 0.85 | interpretation | Maßstäbe FRONTEND.md, UI-NFR-001..022, F1–F11, WCAG 2.2 AA, 3 Zusatz-Skills; k=2: beide Lesarten (Skills ergänzend vs. gleichrangig) per Teach-back auf „ergänzend, Projekt gewinnt" aufgelöst |
| `actors` | yes | 0.9 | specification | Betreiber; Spezialagenten lesend parallel, schreibend sequenziell (Plan-Invariante) |
| `acceptance_criteria` | yes | 0.8 | interpretation | Teach-back Punkte 4–6 |
| `edge_cases` | yes | 0.8 | specification | Plan-Invarianten: Erklärung eines behobenen Defekts ≠ offener Befund; Agenten-Befunde stichprobenartig gegenprüfen; Dev-Cluster nicht erreichbar → siehe Risiken |
| `scope_boundaries` | yes | 0.85 | specification | Antwort Mini-Fix-Grenze „trivial + testgedeckt"; Teach-back Punkt 5 |

## Requirements

- **R1** — Das Audit SHALL alle sieben Dimensionen abdecken: (1) Code-Qualität
  F1–F11, (2) UI-NFR-001..022, (3) A11y WCAG 2.2 AA statisch und live,
  (4) i18n DE/EN, (5) Performance und Bundle, (6) Testbarkeit (data-testid,
  Testpyramide), (7) ein Live-Visual-Audit für Mobile, Tablet und Desktop sowie den Dark Mode.
  - _dimension_: `functional` · _status_: `confirmed` · _source_: „Alle sieben (Recommended)"
- **R2** — Das Audit SHALL zusätzlich die Skills `frontend-design`,
  `vercel-react-best-practices` und `web-design-guidelines` als Maßstab anwenden.
  Befunde daraus SHALL als solche markiert sein. Bei einem Konflikt gelten
  FRONTEND.md und die UI-NFRs.
  - _dimension_: `domain_objects` · _status_: `confirmed` · _source_: „Ja, als Zusatzmaßstab"
- **R3** — Der Live-Anteil (A11y live, Lighthouse, Visual Audit, Dark Mode)
  SHALL gegen den Dev-Cluster (Skaffold, Port-Forward) mit dem Demo-User laufen.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: „Dev-Cluster (Skaffold)"
- **R4** — Für die Bundle-Analyse MAY ein einmaliger lokaler `vite build` laufen.
  Dauer- und Wiederholungsläufe SHALL unterbleiben.
  - _dimension_: `constraints` · _status_: `confirmed` · _source_: Teach-back „Ja, alles korrekt"
- **R5** — Der Report SHALL unter `spec/analysis/frontend-ui-audit-2026-11.md`
  liegen und auf Deutsch geschrieben sein. Jeder Befund SHALL `file:line`
  (bzw. Route und Viewport für Live-Befunde), einen Schweregrad und die verletzte
  Regel tragen. Dazu kommt eine priorisierte Maßnahmenliste.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: „spec/analysis/ (Recommended)"
- **R6** — Der Report SHALL jeden Befund des April-Audits in einer Delta-Tabelle
  als behoben, offen oder obsolet führen, jeweils mit aktuellem Beleg.
  - _dimension_: `non_functional` · _status_: `confirmed` · _source_: „Ja, vollständige Delta-Tabelle"
- **R7** — WHEN ein Befund trivial und verhaltensneutral ist (aria-label,
  fehlender i18n-Key, data-testid), the audit SHALL ihn im Branch beheben und
  im Report als „im Branch behoben" markieren.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: „Report + Mini-Fixes inline", „Trivial + testgedeckt"
- **R8** — WHEN ein Befundbündel den Schweregrad medium oder höher hat und
  kein Mini-Fix ist, the audit SHALL dafür ein englisches GitHub-Issue anlegen.
  Kleinere Befunde bleiben nur im Report.
  - _dimension_: `scope_boundaries` · _status_: `confirmed` · _source_: „Wie oben" in der Option „Report + Mini-Fixes inline" und Teach-back Punkt 5
  - _revisit 2026-11-17_: Nach dem Audit gab es 21 Bündel ab medium. Der Betreiber hat sich für **13 high-Bündel als einzelne Issues und 1 Sammel-Issue für die 8 medium-Bündel** entschieden („13 high einzeln + 1 Sammel-Issue medium").
- **R9** — Das Audit SHALL mit einem PR gegen `develop` abschließen. Commits und
  PR sind auf Englisch.
  - _dimension_: `acceptance_criteria` · _status_: `confirmed` · _source_: Teach-back Punkt 6

## Surviving assumptions / open risks

- **Dev-Cluster erreichbar:** Der Kubernetes-MCP konnte sich nicht verbinden.
  Ist der Dev-Cluster nicht erreichbar, wird der Live-Anteil (R3) blockiert,
  ausgewiesen und dem Betreiber gemeldet, statt ihn stillschweigend auszulassen.
- **Stand des Dev-Clusters:** Der Cluster kann ein anderes Frontend-Image
  als `develop@fe1dd196e` ausliefern. Live-Befunde werden daher gegen den Code
  dieses Worktrees gegengeprüft, bevor sie mit `file:line` belegt werden.
- **Schweregrad-Kalibrierung:** Die Skala (critical, high, medium, low) wird
  aus dem April-Audit übernommen und ist nicht eigens elizitiert.
