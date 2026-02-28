---
name: check-quality
description: "Fuehrt ein vollstaendiges Quality-Gate aus: Backend-Linting (ruff), Backend-Tests (pytest), Frontend-Linting (ESLint), TypeScript-Check (tsc), Frontend-Tests (vitest). Nutze diesen Skill wenn die Code-Qualitaet vor einem Commit oder Release geprueft werden soll."
disable-model-invocation: true
---

# Quality-Gate ausfuehren

## Schritt 1: Alle Checks parallel starten

Fuehre die folgenden 5 Checks **parallel** via Bash-Tool aus:

1. **Backend Linting:**
   ```bash
   cd src/backend && ruff check . 2>&1; echo "EXIT:$?"
   ```

2. **Backend Tests:**
   ```bash
   cd src/backend && python -m pytest tests --tb=short -q 2>&1; echo "EXIT:$?"
   ```

3. **Frontend Linting:**
   ```bash
   cd src/frontend && npm run lint 2>&1; echo "EXIT:$?"
   ```

4. **Frontend TypeScript:**
   ```bash
   cd src/frontend && npx tsc -b 2>&1; echo "EXIT:$?"
   ```

5. **Frontend Tests:**
   ```bash
   cd src/frontend && npm test -- --run 2>&1; echo "EXIT:$?"
   ```

## Schritt 2: Ergebnisse als Tabelle zusammenfassen

Warte auf alle Checks und stelle die Ergebnisse in folgender Tabelle dar:

```markdown
| Check              | Status | Details                    |
|--------------------|--------|----------------------------|
| Backend Linting    | Pass/Fail | {n} errors, {m} warnings |
| Backend Tests      | Pass/Fail | {passed}/{total} passed  |
| Frontend Linting   | Pass/Fail | {n} errors, {m} warnings |
| Frontend TypeScript| Pass/Fail | {n} type errors          |
| Frontend Tests     | Pass/Fail | {passed}/{total} passed  |
```

## Schritt 3: Gesamtbewertung

- **Alles gruen:** "Quality-Gate bestanden. Alle 5 Checks erfolgreich."
- **Fehler vorhanden:** Liste die fehlgeschlagenen Checks mit den wichtigsten Fehlermeldungen auf. Schlage konkrete Fixes vor, falls offensichtlich.

## Hinweise

- Timeout fuer Backend-Tests: 5 Minuten
- Timeout fuer Frontend-Tests: 3 Minuten
- Bei fehlenden Dependencies (`node_modules`, venv) melde dies als separates Problem
- Zaehle TC001-Warnings bei ruff NICHT als Fehler (bekanntes Pattern im Projekt)
