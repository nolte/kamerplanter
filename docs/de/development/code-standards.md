# Code-Standards

Alle Beiträge zu Kamerplanter müssen die hier beschriebenen Standards einhalten. Die Regeln sind in NFR-003 spezifiziert und durch automatisierte Werkzeuge in der CI-Pipeline durchgesetzt.

---

## Sprachen

Die Trennung zwischen Code-Sprache und Dokumentationssprache ist verbindlich:

| Bereich | Sprache | Begründung |
|---------|---------|-----------|
| Quellcode (Python, TypeScript) | Englisch | NFR-003: internationale Lesbarkeit |
| Variablennamen, Funktionen, Klassen | Englisch | NFR-003 |
| Commit-Messages | Englisch | Einheitlichkeit im Git-Log |
| Inline-Kommentare im Code | Englisch | NFR-003 |
| Spezifikationen (`spec/`) | Deutsch | Fachdomäne, Produktdokumentation |
| Endnutzer-Dokumentation (`docs/`) | Deutsch + Englisch | NFR-005 |
| i18n-Übersetzungsdateien (`src/frontend/src/i18n/`) | DE + EN | Produktsprachen |

!!! warning "Keine deutschen Bezeichner im Code"
    Bezeichner wie `pflanze`, `duenger` oder `standort` sind nicht zulässig. Die englischen Entsprechungen `plant`, `fertilizer`, `location` verwenden.

---

## Backend — Python

### Ruff (Linter + Formatter)

Kamerplanter verwendet [Ruff](https://docs.astral.sh/ruff/) als einziges Python-Linting-Werkzeug. Die Konfiguration liegt in `src/backend/pyproject.toml`.

**Aktive Regelsets:**

| Kürzel | Beschreibung |
|--------|-------------|
| `E`, `W` | pycodestyle Fehler und Warnungen |
| `F` | Pyflakes (ungenutzte Imports, undefinierte Namen) |
| `I` | isort (Import-Reihenfolge) |
| `N` | pep8-naming (Namenskonventionen) |
| `UP` | pyupgrade (moderne Python-Syntax) |
| `B` | flake8-bugbear (häufige Fehlerquellen) |
| `SIM` | flake8-simplify (vereinfachbare Ausdrücke) |

**Bewusste Ausnahme:**

```toml
[tool.ruff.lint]
ignore = ["B008"]
```

`B008` (Funktionsaufruf als Default-Argument) ist deaktiviert, weil FastAPI `Depends(...)` genau dieses Muster nutzt:

```python
# Korrekt — wird von B008 nicht beanstandet wegen ignore
async def get_species(db: ArangoDatabase = Depends(get_db)) -> list[Species]:
    ...
```

**Linting ausführen:**

```bash
cd src/backend
ruff check .
```

**Automatisch behebbare Probleme korrigieren:**

```bash
ruff check . --fix
```

**Code formatieren (Black-kompatibel, 120 Zeichen Zeilenlänge):**

```bash
ruff format .
```

### Mypy (Statische Typisierung)

```bash
cd src/backend
mypy app/
```

Mypy läuft im `strict`-Modus. Alle öffentlichen Funktionen und Methoden müssen vollständig typisiert sein.

### Docstrings (Google Style)

Alle öffentlichen Klassen, Methoden und Funktionen erhalten Google-Style Docstrings, damit `mkdocstrings` sie in der API-Referenz verarbeiten kann:

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

### Projektstruktur (5-Schichten-Architektur)

Der Code ist strikt in fünf Schichten organisiert. Abhängigkeiten zeigen immer nach innen — äußere Schichten dürfen innere importieren, nicht umgekehrt:

```
app/
├── api/v1/          # Schicht 1: HTTP-Router, Request/Response-Schemas
├── domain/
│   ├── models/      # Schicht 2: Pydantic-Datenmodelle
│   ├── engines/     # Schicht 3: Berechnungslogik (zustandslos)
│   └── services/    # Schicht 3: Orchestrierung (zustandsbehaftet)
├── data_access/     # Schicht 4: Repository-Implementierungen
└── config/          # Schicht 5: Konfiguration, Datenbankverbindung
```

!!! danger "Keine Datenbank-Imports in Services"
    Services importieren ausschließlich Repository-Interfaces. Direkte ArangoDB-Aufrufe (`db.collection(...)`) gehören ausschließlich in `data_access/`.

### Pydantic v2

- Modelle erben von `pydantic.BaseModel`
- Typ-Aliase verwenden das `type`-Schlüsselwort (Python 3.12+), nicht `TypeAlias`
- Validatoren mit `@field_validator` und `@model_validator`

```python
# Korrekt
type PlantKey = str

# Veraltet — nicht verwenden
PlantKey: TypeAlias = str
```

---

## Frontend — TypeScript / React

### ESLint

Die ESLint-Konfiguration liegt in `src/frontend/eslint.config.js` und verwendet den flachen Konfigurationsformat (Flat Config, ESLint 9+).

Aktive Plugins:
- `typescript-eslint` im `recommended`-Preset
- `eslint-plugin-react-hooks` (React-Hook-Regeln)
- `eslint-config-prettier` (deaktiviert Formatierungsregeln, die Prettier übernimmt)

```bash
cd src/frontend
npm run lint          # Prüfen
npm run lint:fix      # Automatisch behebbare Probleme korrigieren
```

**Wichtige Regel:**

```javascript
'@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }]
```

Ungenutzte Variablen sind Fehler. Ausnahme: Präfix `_` signalisiert bewusst ignorierten Parameter.

### Prettier (Formatierung)

```bash
cd src/frontend
npm run format        # Alle .ts/.tsx/.json/.css Dateien formatieren
```

### TypeScript strict

`tsconfig.json` setzt `"strict": true`. Das schließt ein:
- `noImplicitAny` — alle Typen müssen explizit sein
- `strictNullChecks` — `null`/`undefined` müssen explizit behandelt werden
- `noUnusedLocals` und `noUnusedParameters`

Typfehler müssen vor dem Merge behoben sein. `@ts-ignore` ist verboten.

### React Hook-Konventionen

Custom Hooks, die Objekte oder Arrays zurückgeben, müssen `useMemo` verwenden, um stabile Referenzen zu garantieren. Primitive Werte (`string`, `number`, `boolean`) sind davon ausgenommen.

```typescript
// Korrekt — stabile Referenz
function useSpeciesOptions(familyKey: string) {
  const species = useSelector(selectSpeciesByFamily(familyKey));
  return useMemo(() => species.map(s => ({ value: s.key, label: s.scientific_name })), [species]);
}

// Falsch — neue Array-Referenz bei jedem Render
function useSpeciesOptions(familyKey: string) {
  const species = useSelector(selectSpeciesByFamily(familyKey));
  return species.map(s => ({ value: s.key, label: s.scientific_name }));
}
```

### i18n-Schlüssel-Konvention

Übersetzungsschlüssel folgen dem Schema `pages.<section>.<key>` für seitenspezifische Texte und `enums.<enumName>.<value>` für Enum-Werte:

```json
{
  "pages": {
    "plantManagement": {
      "title": "Stammdatenverwaltung",
      "createSpecies": "Art anlegen"
    }
  },
  "enums": {
    "growthHabit": {
      "herb": "Kraut",
      "shrub": "Strauch",
      "tree": "Baum"
    }
  }
}
```

### Komponenten-Struktur

- Jede Seiten-Komponente liegt unter `src/pages/<bereich>/`
- Gemeinsam genutzte Komponenten unter `src/components/common/` oder `src/components/layout/`
- Page-Komponenten sind Standard-Exporte (`export default`)
- Reine Hilfskomponenten als Named Exports

---

## Git-Workflow

### Branch-Namenskonventionen

| Präfix | Zweck | Beispiel |
|--------|-------|---------|
| `feature/` | Neue Funktionalität | `feature/req005-sensor-integration` |
| `fix/` | Fehlerbehebungen | `fix/seed-data-validation` |
| `chore/` | Wartung, CI, Abhängigkeiten | `chore/update-helm-chart` |
| `docs/` | Nur Dokumentation | `docs/add-api-examples` |

### Commit-Messages

Commits folgen [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add species enrichment via GBIF adapter

fix: correct EC delta calculation for RO water sources

docs: add local setup guide for Kind cluster

chore: update ruff to 0.15.4
```

Präfixe: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `perf`.

---

## CI-Checks

In der CI-Pipeline laufen folgende Prüfungen automatisch:

```bash
# Backend
cd src/backend
ruff check .          # Linting
ruff format --check . # Formatierung
mypy app/             # Typen
pytest                # Tests

# Frontend
cd src/frontend
npm run lint          # ESLint
npm run build         # TypeScript-Kompilierung + Vite-Build
npm test              # vitest
```

!!! warning "Alle Checks müssen grün sein"
    Pull Requests werden nur gemergt, wenn alle CI-Checks erfolgreich sind. Lokal vorab prüfen, bevor ein PR geöffnet wird.

## Siehe auch

- [Testen](testing.md)
- [Lokales Setup](local-setup.md)
- [Debugging](debugging.md)
