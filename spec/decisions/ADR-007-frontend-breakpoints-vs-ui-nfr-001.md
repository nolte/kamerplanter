# ADR-007: Eigene Frontend-Breakpoints vs. MUI-Defaults (UI-NFR-001 R-001)

## Status

Proposed — 2026-07-26

Aufgedeckt während der E2E-Full-Run-Stabilisierung (Issue #768, Branch
`fix/e2e-full-run-stabilization`). **Es wurde bewusst nichts geändert**: weder das
Theme noch die Spec. Dieses ADR bringt den Widerspruch zur Entscheidung.

## Context

`spec/ui-nfr/UI-NFR-001_Responsive-Design.md` R-001 (Stufe **MUSS**) schreibt fünf
Breakpoints vor und benennt sie ausdrücklich als „die MUI-Standard-Breakpoints":

| Breakpoint | UI-NFR-001 R-001 | `src/frontend/src/theme/tokens.ts` |
|---|---|---|
| `xs` | 0 | 0 |
| `sm` | 600 | 600 |
| `md` | 900 | **768** |
| `lg` | 1200 | **1024** |
| `xl` | 1536 | **1440** |

Die Implementierung weicht ab `md` ab. Die Abweichung ist nicht kosmetisch,
sondern **tragend**:

- Die Navigations-Seitenleiste (`src/frontend/src/layouts/Sidebar.tsx`) schaltet über
  `useMediaQuery(theme.breakpoints.down('md'))` zwischen `variant="temporary"`
  (Overlay-Modal) und `variant="persistent"` (im Fluss liegende 240-px-Spalte). Mit
  `md = 768` statt `900` wird die Seitenleiste bereits bei 768 px dauerhaft angedockt —
  also auf Geräten, die R-001 als „Tablet" (`sm`) führt.
- Genau daraus entstand der Defekt, den Commit `39cc9ef96` behoben hat: Bei
  Tablet-Breiten war das gesamte Dokument um exakt die Seitenleistenbreite (240 px)
  breiter als der Viewport (gemessen bei 820 px: Dokument 1060 px, primäre
  Aktionen außerhalb des Bildschirms) — ein Verstoß gegen UI-NFR-001 R-005/R-006
  („keine horizontalen Scrollbars"). Der Fix beseitigt den Überlauf, **nicht** die
  Ursache der Breakpoint-Divergenz.
- Rund 120 Frontend-Dateien binden an `theme.breakpoints` bzw. `useMediaQuery`,
  außerdem die responsiven Kurzschreibweisen in `sx`-Props (`{ xs: …, md: … }`).
  Jede Änderung an den Werten verschiebt daher praktisch jedes responsive Layout
  der Anwendung.
- Die E2E-Profile `mobile`, `tablet`, `full-mobile` und `full-tablet` fahren feste
  Viewport-Breiten. Welches Layout ein „Tablet"-Lauf erwartet, hängt direkt an
  dieser Entscheidung.

## Decision

**Offen.** Zu entscheiden ist, welche der beiden Seiten die Wahrheit ist.

## Alternatives Considered

| Option | Inhalt | Konsequenz |
|---|---|---|
| **A — Theme an die Spec angleichen** | `md → 900`, `lg → 1200`, `xl → 1536` in `theme/tokens.ts` | Spec-konform, aber ein anwendungsweiter Layout-Shift: Seitenleiste wird erst ab 900 px persistent, jedes `sx`-Objekt mit `md`/`lg`-Schwelle verschiebt sich, alle Tablet-E2E-Erwartungen und Screenshot-Referenzen müssen neu bewertet werden. Hohes Regressionsrisiko, breite Test-Neuabnahme. |
| **B — Spec an das Theme angleichen** | UI-NFR-001 R-001 auf `sm=600, md=768, lg=1024, xl=1440` umschreiben, Referenztabelle in §2.1 mitziehen, Begründung für die Abweichung von den MUI-Defaults ergänzen | Kein Code-Risiko, aber eine bewusste Abkehr vom MUI-Standard, die begründet werden muss (z.B. „768 px trifft die verbreitete Tablet-Hochkant-Breite besser als 900 px"). Betrifft außerdem die Flutter-Mobile-Zielplattform, die R-001 ebenfalls adressiert. |
| **C — Status quo dokumentieren, ohne zu entscheiden** | Abweichung als bekannte Ausnahme in R-001 vermerken | Verschiebt das Problem nur; künftige Analysen laufen weiter in die Divergenz. Nicht empfohlen. |

**Tendenz (nicht entschieden):** Option B, weil die Divergenz seit Langem gelebt
wird, die Anwendung um `md = 768` herum entworfen ist und Option A ein
anwendungsweites Layout-Risiko für einen rein formalen Gewinn einginge. Die
Entscheidung ist jedoch eine Architektur-/Produktentscheidung und wird hier
ausdrücklich nicht vorweggenommen.

## Consequences

Solange die Entscheidung offen ist:

- UI-NFR-001 R-001 ist eine **MUSS**-Regel, die die Implementierung verletzt. Jede
  Konformitätsprüfung gegen UI-NFR-001 meldet diesen Verstoß erneut.
- Layout-Analysen bei Tablet-Breiten müssen wissen, dass die effektive
  `md`-Schwelle 768 px ist und nicht die in der Spec genannten 900 px — sonst
  wird die falsche Layout-Variante angenommen (genau das ist während der
  E2E-Stabilisierung passiert).

Nach der Entscheidung ist nachzuziehen:

- Bei **A**: `src/frontend/src/theme/tokens.ts`; erneute Abnahme der E2E-Profile
  `tablet` / `full-tablet`; Sichtprüfung der Seiten mit `md`/`lg`-gebundenen
  `sx`-Werten.
- Bei **B**: UI-NFR-001 §2.1 (R-001 + Breakpoint-Referenztabelle) mit
  Changelog-Zeile und Verweis auf dieses ADR; Abgleich mit der Flutter-Zielplattform.

## References

- `spec/ui-nfr/UI-NFR-001_Responsive-Design.md` §2.1 R-001, R-005, R-006
- `src/frontend/src/theme/tokens.ts` (`breakpoints.values`)
- `src/frontend/src/layouts/Sidebar.tsx` (`breakpoints.down('md')` → Drawer-Variante)
- `src/frontend/src/layouts/MainLayout.tsx` und
  `src/frontend/src/test/layouts/MainLayout.responsive.test.tsx`
- Commit `39cc9ef96` — „fix(frontend): stop the layout overflowing beside the persistent drawer"
- Issue #768 (E2E-Full-Run-Stabilisierung), Arbeitspaket P9
