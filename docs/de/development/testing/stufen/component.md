# Component-Tests

Component-Tests prüfen **React-Komponenten im gerenderten DOM** — mit allen nötigen Providern, aber gegen eine gemockte API. Sie prüfen, was der Nutzer sieht und tut (Klicks, Eingaben, Validierung), ohne einen echten Browser zu starten. Damit sitzen sie zwischen Unit- und E2E-Stufe.

## Was diese Stufe prüft

- **Rendering & Interaktion:** dass Formulare, Dialoge und Seiten korrekt anzeigen und auf Nutzeraktionen reagieren.
- **Barrierefreiheit:** kritische Formulare und Dialoge werden mit `vitest-axe` auf Accessibility-Verstöße geprüft.

## Getestete Bereiche im Überblick

| Bereich | Getestete Elemente | Umfang |
|---------|--------------------|--------|
| Komponenten | Formulare, Dialoge und Widgets je Bereich: Admin, Dashboard, Diagnose, Schädlinge, Tanks, Identifikation, Glossar, Layout, Datenschutz, KI | umfangreich |
| Seiten | Seiten-Komponenten inkl. Routing und Datenladen | umfangreich |
| Barrierefreiheit | kritische Formulare/Dialoge (`vitest-axe`) | fokussiert |

## Werkzeug & Ort

| | Wert |
|---|---|
| Werkzeug | vitest + Testing Library, `userEvent`, `vitest-axe` |
| Ort | `src/frontend/src/test/components/`, `…/pages/`, `…/a11y/` |
| API | über [Mock Service Worker (MSW)](https://mswjs.io/) abgefangen |

Alle Component-Tests rendern über `renderWithProviders` aus `src/test/helpers.tsx` — das umschließt die Komponente mit Redux Store, React Router, MUI Theme und `SnackbarProvider`.

!!! warning "userPreferences-Reducer erforderlich"
    Komponenten, die `useExpertiseLevel` verwenden, benötigen den `userPreferences`-Reducer im Test-Store. `createTestStore()` schließt ihn ein; ein manuell gebauter Store muss ihn explizit ergänzen.

## Ausführen

```bash
cd src/frontend
npm test                 # einmaliger Durchlauf
npm run test:watch       # Watch-Modus
npm run test:coverage    # mit Coverage-Report
```

Muster und MSW-Details im [Testkonzept → Frontend-Tests](../index.md#frontend-tests-vitest).

## Konventionen

- Provider nie manuell zusammenstellen — immer `renderWithProviders` nutzen.
- API-Antworten über MSW-Handler mocken; testspezifisches Verhalten mit `server.use(…)` temporär überschreiben.
- Jede neue oder geänderte Komponente braucht einen Component-Test; kritische Formulare zusätzlich einen a11y-Test.
