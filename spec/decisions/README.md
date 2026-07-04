# Architecture Decision Records (ADRs)

Diese Verzeichnis enthält **persistente Architektur-Entscheidungen** für Kamerplanter. Ein ADR dokumentiert eine bewusste Entscheidung samt Kontext, Alternativen und Konsequenzen — damit in 2 Jahren nachvollziehbar ist, *warum* eine bestimmte Architektur gewählt wurde.

## Wann ein ADR geschrieben wird

- **Architektur-Entscheidungen mit Folgewirkung** über mehrere Specs (z.B. „Wer besitzt die Phase — Run oder Plant?")
- **Safety-/Compliance-relevante Entscheidungen** (CanG, PflSchG, DSGVO)
- **Tech-Stack-Wahlen mit Lifecycle-Implikationen** (z.B. Valkey vs. Redis)
- **Trade-offs zwischen NFR-Zielen** (z.B. Performance vs. Datenschutz)

**Kein ADR nötig** für: Rein redaktionelle Korrekturen, Bug-Fixes, kleine Refactorings.

## Format

Wir verwenden das **Michael-Nygard-Format** — kompakt und etabliert. Jedes ADR enthält:

```markdown
# ADR-NNN: <Titel>

## Status
[Proposed | Accepted | Superseded by ADR-MMM | Deprecated]

## Context
Was ist das Problem? Welche Specs/Anforderungen sind betroffen?
Welche Constraints (Recht, Tech-Stack, NFRs) gelten?

## Decision
Welche Entscheidung wurde getroffen? In einem Satz, dann ausführlicher.

## Alternatives Considered
Welche anderen Optionen wurden geprüft? Warum wurden sie verworfen?

## Consequences
- Positive Folgen
- Negative Folgen / Risiken
- Folgemaßnahmen (welche Specs werden wie aktualisiert?)

## References
- Verweise auf Specs, externe Quellen, vorherige Entscheidungen
```

## Lifecycle eines ADRs

```
1. Proposed   → Decision-Brief mit Optionen + Empfehlung
2. Accepted   → Entscheidung getroffen, Datum + Entscheider eingetragen
3. Implemented → Verlinkte Specs sind aktualisiert (Changelog-Verweis auf ADR)
```

Status `Superseded` wird gesetzt, wenn eine spätere Entscheidung das ADR überstimmt — der alte ADR bleibt als historisches Dokument erhalten, mit Verweis auf den Nachfolger.

## Naming Convention

`ADR-NNN-<kurz-beschreibung>.md` mit fortlaufender Nummerierung ab `001`.

Beispiel:
- `ADR-001-karenz-gate-detach-plantinstances.md`
- `ADR-002-tenant-species-knowledge-service.md`

## Verbindung zu REQ-/NFR-Changelogs

Wenn ein ADR `Accepted` wird, werden die betroffenen Specs aktualisiert. Die Spec-Changelog-Zeile verweist explizit auf den ADR:

```markdown
| 2.5 | 2026-04-30 | **ADR-001:** Karenz-Gate für detachte PlantInstances spezifiziert. ... |
```

So ist die Verknüpfung Entscheidung ↔ Spec-Änderung dauerhaft nachvollziehbar.

## Index

| ID | Titel | Status | Datum |
|----|-------|--------|-------|
| ADR-001 | Karenz-Gate für detachte PlantInstances (W-009) | Accepted | 2026-04-27 |
| ADR-002 | Tenant-eigene Species im Knowledge Service (W-006) | Accepted | 2026-04-27 |
| ADR-003 | Sensor-Retention für Perennials (W-014) | Accepted | 2026-04-27 |
| ADR-004 | Vermehrung als strukturierte per-Methode-Objekte (propagation_configs) | Accepted | 2026-06-15 |
| ADR-005 | Versioniertes Datenbank-Migrations-Framework | Accepted | 2026-07-04 |
