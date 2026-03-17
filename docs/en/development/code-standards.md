# Code Standards

All contributions to Kamerplanter must follow the standards described here. The rules are specified in NFR-003 and enforced by automated tools in the CI pipeline.

---

## Languages

The separation between code language and documentation language is mandatory:

| Area | Language | Reason |
|------|----------|--------|
| Source code (Python, TypeScript) | English | NFR-003: international readability |
| Variable names, functions, classes | English | NFR-003 |
| Commit messages | English | Consistency in git log |
| Inline code comments | English | NFR-003 |
| Specifications (`spec/`) | German | Domain language, product documentation |
| End-user documentation (`docs/`) | German + English | NFR-005 |
| i18n translation files (`src/frontend/src/i18n/`) | DE + EN | Product languages |

!!! warning "No German identifiers in code"
    Identifiers such as `pflanze`, `duenger`, or `standort` are not permitted. Use the English equivalents `plant`, `fertilizer`, `location`.

---

## Backend — Python

### Ruff (Linter + Formatter)

Kamerplanter uses [Ruff](https://docs.astral.sh/ruff/) as the sole Python linting tool. The configuration lives in `src/backend/pyproject.toml`.

**Active rule sets:**

| Code | Description |
|------|-------------|
| `E`, `W` | pycodestyle errors and warnings |
| `F` | Pyflakes (unused imports, undefined names) |
| `I` | isort (import ordering) |
| `N` | pep8-naming (naming conventions) |
| `UP` | pyupgrade (modern Python syntax) |
| `B` | flake8-bugbear (common error patterns) |
| `SIM` | flake8-simplify (simplifiable expressions) |

**Intentional exception:**

```toml
[tool.ruff.lint]
ignore = ["B008"]
```

`B008` (function call as default argument) is disabled because FastAPI `Depends(...)` uses exactly this pattern:

```python
# Correct — not flagged by B008 due to ignore
async def get_species(db: ArangoDatabase = Depends(get_db)) -> list[Species]:
    ...
```

**Run linting:**

```bash
cd src/backend
ruff check .
```

**Fix auto-correctable issues:**

```bash
ruff check . --fix
```

**Format code (Black-compatible, 120-character line length):**

```bash
ruff format .
```

### Mypy (Static Typing)

```bash
cd src/backend
mypy app/
```

Mypy runs in `strict` mode. All public functions and methods must be fully typed.

### Docstrings (Google Style)

All public classes, methods, and functions must have Google-style docstrings so that `mkdocstrings` can process them for the API reference:

```python
def calculate_ec_target(
    base_water_ec: float,
    target_nutrient_ec: float,
) -> float:
    """Calculate the net nutrient EC to reach a target solution EC.

    The net EC accounts for the mineral content already present in the
    source water, following the formula: EC_net = EC_target - EC_base.

    Args:
        base_water_ec: Measured EC of the source water in mS/cm.
        target_nutrient_ec: Desired total solution EC in mS/cm.

    Returns:
        Net nutrient EC to add in mS/cm. Returns 0.0 if base_water_ec
        exceeds target_nutrient_ec.

    Raises:
        ValueError: If either EC value is negative.

    Example:
        >>> calculate_ec_target(0.3, 1.8)
        1.5
    """
```

### Project Structure (5-Layer Architecture)

Code is strictly organized into five layers. Dependencies always point inward — outer layers may import inner ones, not the reverse:

```
app/
├── api/v1/          # Layer 1: HTTP routers, request/response schemas
├── domain/
│   ├── models/      # Layer 2: Pydantic data models
│   ├── engines/     # Layer 3: Calculation logic (stateless)
│   └── services/    # Layer 3: Orchestration (stateful)
├── data_access/     # Layer 4: Repository implementations
└── config/          # Layer 5: Configuration, database connection
```

!!! danger "No database imports in services"
    Services only import repository interfaces. Direct ArangoDB calls (`db.collection(...)`) belong exclusively in `data_access/`.

### Pydantic v2

- Models inherit from `pydantic.BaseModel`
- Type aliases use the `type` keyword (Python 3.12+), not `TypeAlias`
- Validators use `@field_validator` and `@model_validator`

```python
# Correct
type PlantKey = str

# Outdated — do not use
PlantKey: TypeAlias = str
```

---

## Frontend — TypeScript / React

### ESLint

The ESLint configuration is in `src/frontend/eslint.config.js` and uses the flat configuration format (ESLint 9+).

Active plugins:
- `typescript-eslint` with the `recommended` preset
- `eslint-plugin-react-hooks` (React hook rules)
- `eslint-config-prettier` (disables formatting rules handled by Prettier)

```bash
cd src/frontend
npm run lint          # Check
npm run lint:fix      # Fix auto-correctable issues
```

**Key rule:**

```javascript
'@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }]
```

Unused variables are errors. Exception: the `_` prefix signals an intentionally ignored parameter.

### Prettier (Formatting)

```bash
cd src/frontend
npm run format        # Format all .ts/.tsx/.json/.css files
```

### TypeScript strict

`tsconfig.json` sets `"strict": true`, which includes:
- `noImplicitAny` — all types must be explicit
- `strictNullChecks` — `null`/`undefined` must be handled explicitly
- `noUnusedLocals` and `noUnusedParameters`

Type errors must be fixed before merging. `@ts-ignore` is prohibited.

### React Hook Conventions

Custom hooks that return objects or arrays must use `useMemo` to guarantee stable references. Primitive values (`string`, `number`, `boolean`) are exempt.

```typescript
// Correct — stable reference
function useSpeciesOptions(familyKey: string) {
  const species = useSelector(selectSpeciesByFamily(familyKey));
  return useMemo(() => species.map(s => ({ value: s.key, label: s.scientific_name })), [species]);
}

// Incorrect — new array reference on every render
function useSpeciesOptions(familyKey: string) {
  const species = useSelector(selectSpeciesByFamily(familyKey));
  return species.map(s => ({ value: s.key, label: s.scientific_name }));
}
```

### i18n Key Convention

Translation keys follow the pattern `pages.<section>.<key>` for page-specific texts and `enums.<enumName>.<value>` for enum values:

```json
{
  "pages": {
    "plantManagement": {
      "title": "Master Data",
      "createSpecies": "Create species"
    }
  },
  "enums": {
    "growthHabit": {
      "herb": "Herb",
      "shrub": "Shrub",
      "tree": "Tree"
    }
  }
}
```

### Component Structure

- Each page component lives under `src/pages/<section>/`
- Shared components under `src/components/common/` or `src/components/layout/`
- Page components are default exports (`export default`)
- Pure utility components as named exports

---

## Git Workflow

### Branch Naming Conventions

| Prefix | Purpose | Example |
|--------|---------|---------|
| `feature/` | New functionality | `feature/req005-sensor-integration` |
| `fix/` | Bug fixes | `fix/seed-data-validation` |
| `chore/` | Maintenance, CI, dependencies | `chore/update-helm-chart` |
| `docs/` | Documentation only | `docs/add-api-examples` |

### Commit Messages

Commits follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add species enrichment via GBIF adapter

fix: correct EC delta calculation for RO water sources

docs: add local setup guide for Kind cluster

chore: update ruff to 0.15.4
```

Prefixes: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `perf`.

---

## CI Checks

The following checks run automatically in CI on every push to `main` and every pull request:

```bash
# Backend
cd src/backend
ruff check .          # Linting
ruff format --check . # Formatting
mypy app/             # Types
pytest                # Tests

# Frontend
cd src/frontend
npm run lint          # ESLint
npm run build         # TypeScript compilation + Vite build
npm test              # vitest
```

!!! warning "All checks must be green"
    Pull requests are only merged when all CI checks pass. Run checks locally before opening a PR.

## See also

- [Testing](testing.md)
- [Local Setup](local-setup.md)
- [Debugging](debugging.md)
