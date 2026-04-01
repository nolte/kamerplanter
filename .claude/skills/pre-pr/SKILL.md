---
name: pre-pr
description: "Fuehrt alle Pre-PR-Checks aus: Quality-Gate (Linting + Tests), Security-Review, i18n-Vollstaendigkeit, Dokumentations-Aktualitaet. Nutze diesen Skill bevor ein Pull Request erstellt wird, um sicherzustellen dass der Code merge-faehig ist."
disable-model-invocation: true
---

# Pre-PR Check

Fuehre alle Checks in der richtigen Reihenfolge aus. Brich ab sobald ein kritischer Check fehlschlaegt.

## Schritt 1: Quality-Gate (parallel)

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

Warte auf alle Ergebnisse. Zaehle TC001-Warnings bei ruff NICHT als Fehler (bekanntes Pattern).

## Schritt 2: i18n-Vollstaendigkeit

Starte den `i18n-completeness-checker` Agent:

Prompt: "Pruefe die i18n-Uebersetzungsdateien auf Vollstaendigkeit und erstelle einen Report."

## Schritt 3: Security-Review (nur bei Backend-Aenderungen)

Pruefe mit `git diff --name-only develop...HEAD` (oder `main...HEAD` falls develop nicht existiert) ob Backend-Dateien geaendert wurden:

- `src/backend/app/api/**`
- `src/backend/app/domain/**`
- `src/backend/app/data_access/**`
- `src/backend/app/common/**`
- `src/backend/app/tasks/**`

Falls ja, starte den `code-security-reviewer` Agent:

Prompt: "Pruefe die folgenden geaenderten Backend-Dateien auf Sicherheitsprobleme: {liste der geaenderten Dateien}"

Falls keine Backend-Aenderungen: Ueberspringe diesen Schritt mit Hinweis "Kein Security-Review noetig — keine Backend-Aenderungen."

## Schritt 4: Dokumentations-Aktualitaet (nur bei relevanten Aenderungen)

Pruefe mit `git diff --name-only develop...HEAD` (oder `main...HEAD`) ob Dateien geaendert wurden die Doku-Relevanz haben:

- `src/backend/app/api/**` — API-Endpoints geaendert
- `src/backend/app/domain/models/**` — Domain-Models geaendert
- `src/frontend/src/pages/**` — Frontend-Seiten geaendert
- `docs/**` — Dokumentation direkt geaendert
- `spec/**` — Spezifikationen geaendert

Falls ja, starte den `docs-freshness-checker` Agent:

Prompt: "Pruefe die Dokumentation auf Aktualitaet und Vollstaendigkeit. Fokussiere auf die folgenden geaenderten Bereiche: {liste der geaenderten Verzeichnisse}"

Falls keine relevanten Aenderungen: Ueberspringe mit Hinweis "Kein Doku-Check noetig — keine doku-relevanten Aenderungen."

## Schritt 5: Ergebnis-Report

Fasse alle Ergebnisse in einer Tabelle zusammen:

```markdown
# Pre-PR Report

| Check               | Status    | Details                     |
|---------------------|-----------|-----------------------------|
| Backend Linting     | Pass/Fail | {n} errors, {m} warnings    |
| Backend Tests       | Pass/Fail | {passed}/{total} passed     |
| Frontend Linting    | Pass/Fail | {n} errors, {m} warnings    |
| Frontend TypeScript | Pass/Fail | {n} type errors             |
| Frontend Tests      | Pass/Fail | {passed}/{total} passed     |
| i18n Completeness   | Pass/Warn | {n} fehlende Keys           |
| Security Review     | Pass/Warn/Skip | {n} Findings            |
| Docs Freshness      | Pass/Warn/Skip | {n} veraltete/{m} fehlende |

## Gesamtbewertung: MERGE-READY / NICHT MERGE-READY
```

**MERGE-READY** wenn:
- Alle 5 Quality-Gate-Checks bestanden
- i18n hat keine kritischen Findings (fehlende Keys im Code)
- Security-Review hat keine kritischen Findings

**NICHT MERGE-READY** wenn:
- Mindestens ein Quality-Gate-Check fehlgeschlagen
- ODER Security-Review hat kritische Findings (Injection, Auth-Bypass, Tenant-Isolation)

i18n-Warnungen (verwaiste Keys, identische Werte) blockieren NICHT den Merge.
Docs-Warnungen (fehlende Seiten, DE/EN-Paritaet) blockieren NICHT den Merge — nur kritische Findings (veraltete API-Doku, tote Links) werden als Blocker gewertet.

## Hinweise

- Timeout fuer Backend-Tests: 5 Minuten
- Timeout fuer Frontend-Tests: 3 Minuten
- Security-Review und i18n-Check koennen parallel zu Schritt 1 laufen
- Bei fehlenden Dependencies (`node_modules`, venv) melde dies als separates Problem
