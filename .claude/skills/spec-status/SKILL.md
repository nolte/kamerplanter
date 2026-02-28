---
name: spec-status
description: "Zeigt den Implementierungsstatus aller REQ-Dokumente als Uebersichtstabelle an. Gleicht Spec-Versionen mit Backend, Frontend, Tests und HA-Integration ab. Nutze diesen Skill fuer einen schnellen Projektstatus-Ueberblick."
disable-model-invocation: true
---

# Implementierungsstatus-Uebersicht

## Schritt 1: Datenquellen laden

Lade folgende Quellen **parallel**:

1. **Alle REQ-Dokumente:** Glob `spec/req/REQ-*.md` — lies jeweils die ersten 20 Zeilen fuer Titel und Versionsnummer
2. **MEMORY.md:** Die auto-memory Datei `MEMORY.md` (aus dem persistenten Memory-Verzeichnis) — fuer den bekannten Implementierungsstatus
3. **HA-Integration-Dokumente:** Glob `spec/ha-integration/HA-REQ-*.md` — fuer HA-Status
4. **Backend-Verzeichnis:** Glob `src/backend/app/api/v1/*/router.py` — fuer vorhandene API-Router
5. **Frontend-Verzeichnis:** Glob `src/frontend/src/pages/*/` — fuer vorhandene Pages
6. **E2E-Tests:** Glob `tests/e2e/test_req*.py` — fuer vorhandene Tests

## Schritt 2: Status bestimmen

Fuer jedes REQ-Dokument bestimme den Status in 4 Kategorien:

### Status-Werte:
- **Implementiert** — Code existiert und ist funktional
- **Teilweise** — Teilimplementierung vorhanden (z.B. Backend ja, Frontend nein)
- **Spezifiziert** — Spec-Dokument existiert, aber keine Implementierung
- **Offen** — Weder Spec noch Implementierung vollstaendig

### Kategorien:
- **Backend:** Pruefe ob API-Router, Models, Services existieren
- **Frontend:** Pruefe ob Pages, Redux Slices, API-Endpoints existieren
- **Tests:** Pruefe ob E2E-Tests oder Backend-Tests existieren
- **HA-Integration:** Pruefe ob HA-REQ-Dokument existiert

## Schritt 3: Tabelle ausgeben

```markdown
# Kamerplanter — Implementierungsstatus

| REQ | Titel | Spec | Backend | Frontend | Tests | HA |
|-----|-------|------|---------|----------|-------|----|
| REQ-001 | Stammdatenverwaltung | v5.0 | Impl. | Impl. | Impl. | — |
| REQ-002 | Standortverwaltung | v4.1 | Impl. | Impl. | Impl. | — |
| ... | ... | ... | ... | ... | ... | ... |

**Legende:**
- Impl. = Implementiert
- Teil. = Teilweise
- Spec. = Nur spezifiziert
- Offen = Noch nicht spezifiziert
- — = Nicht anwendbar
```

## Schritt 4: Zusammenfassung

Gib eine kurze Zusammenfassung:
- Anzahl vollstaendig implementierter REQs
- Anzahl teilweise implementierter REQs
- Anzahl nur spezifizierter REQs
- Naechste Kandidaten fuer Implementierung (basierend auf Abhaengigkeiten)
