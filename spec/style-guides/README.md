# Source Code Style Guides

Verbindliche Style Guides fuer alle Code-Bereiche des Kamerplanter-Projekts.
Diese Dokumente definieren Konventionen die durch automatische statische Analyse erzwungen werden.

## Dokumente

| Guide | Scope | Statische Analyse |
|-------|-------|-------------------|
| [BACKEND.md](BACKEND.md) | `src/backend/` — Python / FastAPI | Ruff, MyPy strict, pytest |
| [FRONTEND.md](FRONTEND.md) | `src/frontend/` — React / TypeScript / MUI | ESLint, TypeScript strict, Vitest |
| [HELM.md](HELM.md) | `helm/`, `skaffold.yaml` — Kubernetes / Helm | helm lint, helm template, skaffold diagnose |
| [HA-INTEGRATION.md](HA-INTEGRATION.md) | `src/ha-integration/` — Home Assistant Custom Component | Ruff, MyPy, hassfest |

## Zweck

1. **Einheitlichkeit** — Agents und Entwickler erzeugen konsistenten Code
2. **Nachvollziehbarkeit** — Jede Konvention ist begruendet und referenziert bestehende Patterns
3. **Automatisierung** — Alle Regeln werden durch Tooling erzwungen, nicht nur dokumentiert

## Pruefkette (CI/CD)

```
Pull Request
    │
    ├─→ Backend:     ruff check + ruff format + mypy --strict + pytest
    ├─→ Frontend:    eslint + tsc --noEmit + vitest run
    ├─→ Helm:        helm lint + helm template + skaffold diagnose
    └─→ HA:          ruff check + ruff format + mypy
```

## Fuer Agents

Die Style Guides sind so verfasst, dass Umsetzungs-Agents (fullstack-developer, ha-integration-sync, etc.)
die Konventionen direkt anwenden koennen:

- **Namenskonventionen** mit konkreten Beispielen
- **Code-Patterns** mit Copy-Paste-faehigen Templates
- **Anti-Patterns** (FALSCH-Beispiele) wo noetig
- **Tooling-Befehle** zur Selbstpruefung
