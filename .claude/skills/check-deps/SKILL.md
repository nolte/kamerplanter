---
name: check-deps
description: "Prueft alle Python- und Node.js-Abhaengigkeiten auf NFR-009-Konformitaet: CVE-Scanning (pip-audit, npm audit), Version-Pinning-Regeln, Lizenz-Compliance, Renovate-Konfiguration. Nutze diesen Skill regelmaessig oder nach manuellen Dependency-Aenderungen."
argument-hint: "[backend | frontend | all]"
disable-model-invocation: true
---

# Dependency-Check (NFR-009): $ARGUMENTS

## Schritt 1: Dependency-Dateien laden

Lese die relevanten Dateien basierend auf `$ARGUMENTS`:

**Bei `backend` oder `all`:**
- `src/backend/pyproject.toml` oder `requirements.txt`

**Bei `frontend` oder `all`:**
- `src/frontend/package.json`
- `src/frontend/package-lock.json` (erste 30 Zeilen fuer Lock-File-Analyse)

**Immer:**
- `.github/renovate.json` oder `renovate.json` (falls vorhanden) — Renovate-Konfiguration
- `spec/nfr/NFR-009_Dependency-Management.md` erste 60 Zeilen — fuer Update-Strategie

## Schritt 2: Version-Pinning pruefen (NFR-009 §2.1)

**Python (`pyproject.toml`):**
```toml
# ✅ KORREKT — Range mit oberer Grenze
fastapi = ">=0.115.0,<1.0.0"
pydantic = ">=2.0.0,<3.0.0"

# ❌ FALSCH — Keine obere Grenze
fastapi = ">=0.115.0"

# ❌ FALSCH — Exaktes Pin (verhindert Patch-Updates)
fastapi = "==0.115.3"
```

**Node.js (`package.json`):**
```json
// ✅ KORREKT — Caret-Notation
"react": "^19.0.0",

// ❌ FALSCH — Kein Caret
"react": "19.0.0",

// ❌ FALSCH — latest-Tag
"react": "latest"
```

## Schritt 3: CVE-Scan ausfuehren

Fuehre die Scans **parallel** aus (je nach `$ARGUMENTS`):

**Backend:**
```bash
cd src/backend && pip-audit --format=json 2>&1 | head -100; echo "EXIT:$?"
```
Falls `pip-audit` nicht installiert:
```bash
cd src/backend && pip install pip-audit -q && pip-audit 2>&1 | head -50
```

**Frontend:**
```bash
cd src/frontend && npm audit --json 2>&1 | head -100; echo "EXIT:$?"
```

## Schritt 4: Veraltete Pakete pruefen

```bash
# Backend — veraltete Pakete anzeigen
cd src/backend && pip list --outdated --format=columns 2>&1 | head -30

# Frontend — veraltete Pakete anzeigen
cd src/frontend && npm outdated 2>&1 | head -30
```

## Schritt 5: Renovate-Konfiguration pruefen

Prüfe die Renovate-Konfiguration auf NFR-009 §3-Konformitaet:

```json
// ✅ Erwartete Konfiguration:
{
  "automerge": true,                    // Patch/Minor auto-merge
  "automergeType": "pr",
  "packageRules": [
    {
      "matchUpdateTypes": ["major"],
      "automerge": false,               // Major: manuell
      "labels": ["dependency-major"]
    },
    {
      "matchPackagePatterns": ["*"],
      "schedule": ["before 8am on Monday"]  // Wochentag-Fenster
    }
  ]
}
```

## Schritt 6: Lizenz-Check

Suche nach problematischen Lizenzen:
```bash
# Backend
cd src/backend && pip-licenses --format=markdown 2>&1 | grep -E "GPL|AGPL|LGPL" | head -20

# Frontend
cd src/frontend && npx license-checker --summary 2>&1 | grep -E "GPL|AGPL" | head -20
```

Kennzeichne alle `GPL`/`AGPL`-Pakete als pruefungsbeduerftg (koennten Copyleft-Pflichten ausloesen).

## Schritt 7: Report ausgeben

```markdown
# Dependency-Check: {backend/frontend/all}

## CVE-Scan-Ergebnis
| Paket | Version | CVE-ID | Schweregrad | Fix-Version |
|-------|---------|--------|-------------|-------------|
{Tabelle der gefundenen CVEs oder "Keine CVEs gefunden"}

## Version-Pinning-Compliance
{Python: N/M korrekt gepinnt | Node.js: N/M korrekt gepinnt}

## Veraltete Pakete (Auswahl kritischer)
{Tabelle: Paket | Aktuell | Neueste | Update-Typ}

## Renovate-Konfiguration
{Vorhanden: ja/nein | Auto-Merge Patch/Minor: ja/nein | Major-Review: ja/nein}

## Lizenz-Findings
{GPL/AGPL-Pakete: Liste oder "Keine gefunden"}

## Empfehlungen (priorisiert)
1. [KRITISCH] CVEs sofort patchen: ...
2. [HOCH] Major-Updates planen: ...
3. [MITTEL] Version-Pinning korrigieren: ...

## Bewertung
- ✅ NFR-009-konform / ❌ {N} Findings
```
