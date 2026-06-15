# ADR-004: Vermehrung als strukturierte per-Methode-Objekte (propagation_configs)

## Status

**Accepted** — *Entschieden: 2026-06-15, durch nolte*
*Erstellt: 2026-06-15*

## Context

REQ-001 modellierte die Vermehrung einer `Species` zunächst über **drei flache Felder**:

```
propagation_methods: list[PropagationMethod]   # alle Methoden zusammen
propagation_months:  list[int]                 # EIN Zeitfenster für die ganze Art
propagation_notes:   str | None                # EIN Freitext für die ganze Art
propagation_difficulty: str | None             # nie befüllt, als String
```

Die fachliche Referenz `spec/knowledge/PFLANZEN-EIGENSCHAFTEN-REFERENZ.md` (§3.3) und der
Umsetzungsplan `.audits/datenmodell-pflanzeneigenschaften-plan.md` (WP-5) zeigen, dass dieses
Modell **fachlich falsch koppelt**: Zeitfenster und Hinweise gehören an die **Methode**, nicht an
die Art. Beispiel: Bei derselben Pflanze wurzeln Weichholzstecklinge im Mai–Juli, während die
Teilung im Herbst erfolgt. Mit einem gemeinsamen `propagation_months` ist diese Information nicht
abbildbar — sie geht verloren oder landet unstrukturiert im Freitext.

Zusätzlich bestand eine **Spec/Code-Drift**: REQ-017 spezifiziert mehr Vermehrungsmethoden
(`air_layering`, `tissue_culture`, `bulbil`, `water_propagation`) als das `PropagationMethod`-Enum
in `common/enums.py` realisierte.

## Decision

1. **Strukturierte per-Methode-Konfiguration.** Die drei flachen Felder werden durch ein einziges
   Feld ersetzt:

   ```python
   class PropagationConfig(BaseModel):
       method: PropagationMethod
       months: list[int] = []          # 1..12, je Methode unabhängig
       wood_stage: WoodStage | None     # Reifegrad, nur für cutting-Methoden sinnvoll
       difficulty: PropagationDifficulty | None
       notes: str | None

   class Species(...):
       propagation_configs: list[PropagationConfig]
   ```

   `wood_stage` (softwood/semi_hardwood/hardwood/herbaceous) wird bewusst als **Parameter** geführt,
   nicht als zusätzliche `PropagationMethod`-Werte, um eine Enum-Explosion zu vermeiden.

2. **Enum-Drift geschlossen.** `PropagationMethod` realisiert nun alle REQ-017-Methoden
   (17 Werte). `propagation_difficulty` wird vom String zum Enum `PropagationDifficulty`
   (easy/moderate/difficult).

3. **Breaking Change — bewusst akzeptiert.** Die API-Schemas `SpeciesCreate`/`SpeciesResponse` und
   das Frontend (Stammdaten-UI) werden in derselben Änderung umgestellt. Es gibt keinen
   Übergangszeitraum mit beiden Modellen im Domänenmodell.

4. **Seeder als Kompatibilitäts-Adapter.** Das Import-/Seed-Format bleibt rückwärtskompatibel: die
   Seeder (`seed_plant_info*.py`) akzeptieren **sowohl** die native `propagation_configs`-Liste **als
   auch** die alten flachen Felder und adaptieren letztere on-import (eine Config je Methode, geteiltes
   Zeitfenster, Notiz auf der ersten Methode). Die ~200 Bestands-Seed-Einträge müssen damit **nicht**
   manuell migriert werden; die fachliche per-Methode-Aufteilung der Monate ist ein Daten-Qualitäts-
   Folgeschritt (Plan WP-10).

5. **Schemalose Persistenz.** ArangoDB ist schemalos — es ist keine DB-Migration nötig. Bestehende
   Dokumente mit flachen Feldern werden beim nächsten Seeder-Upsert in `propagation_configs` überführt.

## Consequences

- **Positiv:** Zeitfenster, Reifegrad und Hinweise sind je Methode abfragbar; die UI kann pro Methode
  ein eigenes Panel zeigen; REQ-017-Methoden sind vollständig nutzbar; die Spec/Code-Drift ist behoben.
- **Negativ / Kosten:** Breaking Change für API-Konsumenten; Frontend-Formulare mussten von einer
  Mehrfachauswahl auf einen wiederholbaren Config-Editor umgebaut werden; bestehende Daten tragen
  zunächst geteilte Monatsfenster, bis WP-10 sie fachlich aufteilt.
- **Folgearbeiten:** WP-10 (Daten-Backfill) teilt die Monatsfenster pro Methode fachlich auf; native
  `propagation_configs` in den Seed-YAMLs lösen die flachen Felder schrittweise ab.

## Realisierung

- Backend: `common/enums.py` (PropagationMethod erweitert, WoodStage + PropagationDifficulty neu),
  `domain/models/species.py` (PropagationConfig, `propagation_configs`), `api/v1/species/schemas.py`,
  `migrations/seed_plant_info*.py` (Adapter `_build_propagation_configs`),
  `migrations/seed_data/schemas/plant_info.schema.yaml`.
- Frontend: `api/types.ts`, `pages/stammdaten/SpeciesDetailPage.tsx`,
  `pages/stammdaten/GrowingPeriodsSection.tsx`, `config/fieldConfigs.ts`, i18n (de/en).
- Tests: `tests/unit/domain/models/test_species.py`, `tests/unit/migrations/test_seed_propagation_methods.py`, Frontend-Vitest.

## Referenzen

- `spec/knowledge/PFLANZEN-EIGENSCHAFTEN-REFERENZ.md` §3.3 (fachliche Begründung)
- `.audits/datenmodell-pflanzeneigenschaften-plan.md` WP-5 (Umsetzungsplan)
- REQ-001 Stammdatenverwaltung, REQ-017 Vermehrungsmanagement
