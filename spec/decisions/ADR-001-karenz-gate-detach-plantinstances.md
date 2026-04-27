# ADR-001: Karenz-Gate für detachte PlantInstances

## Status

**Accepted** — *Entschieden: 2026-04-27, durch nolte*
*Erstellt: 2026-04-27*

## Context

REQ-013 v2.0 hat den `PlantingRun` als primäre Verwaltungseinheit etabliert. IPM-Behandlungen sind jetzt standardmäßig **Run-Level** angesiedelt: `to_run`-Edge geht von `treatment_applications` zum `planting_runs`-Dokument (vorher: `to_plant` zur einzelnen `plant_instances`).

Das funktioniert sauber, **solange alle Pflanzen im Run bleiben**. Aber REQ-013 §1.1 erlaubt explizit **Detach**: Eine PlantInstance kann jederzeit aus einem Run herausgelöst werden (z.B. weil sie eine Krankheit zeigt) und wird zur standalone Plant mit vollem Management.

### Das Problem

```
Tag 0   Run "Hochbeet A" mit 20 Tomaten, status=active
Tag 5   IPM-Behandlung gegen Echten Mehltau auf Run-Ebene angewendet
        → treatment_applications/T1, to_run-Edge zu Run, safety_interval_days=14
Tag 6   Plant TOM_05 zeigt Symptome, wird detached (REQ-013 §3 detach-Operation)
        → run_contains.detached_at = 2026-04-27, TOM_05 ist jetzt standalone
Tag 10  Anwender will TOM_05 ernten (Direkternte aus Diary heraus)
        → REQ-007 Karenz-Gate prüft SafetyIntervalValidator.can_harvest()
        → Treatment T1 hat to_run-Edge, TOM_05 hat keine to_plant-Edge
        → Validator findet KEINE Treatments
        → can_harvest() = (True, [])
        → Ernte wird freigegeben — OBWOHL Karenzzeit noch 9 Tage läuft

→ Karenz-Bypass über Detach. Lebensmittel-Sicherheit + CanG/PflSchG-Verstoß.
```

Der `SafetyIntervalValidator` in REQ-010 §3 (Zeile 530) iteriert über eine `treatment_applications`-Liste. Heute ist nicht spezifiziert, **wie diese Liste für eine detachte Plant zusammengestellt wird** — der Lookup `requires_harvest_delay` ist polymorph (Run oder Plant), aber kein Code-Pfad löst die historische Run-Mitgliedschaft auf.

### Compliance-Constraints

- **CanG (Cannabisgesetz)** §22: Behandlungen mit Pflanzenschutzmitteln sind über 5 Jahre lückenlos zu dokumentieren — *inkl. Karenzzeit-Einhaltung*.
- **PflSchG (Pflanzenschutzgesetz)** §11: Anwender muss nachweislich die Wartezeit zwischen Behandlung und Ernte einhalten.
- **NFR-011 R-17**: Treatment-Applications werden 3 Jahre aufbewahrt; bei DSGVO-Erasure des Anwenders anonymisiert (`applicator → '[gelöscht]'`), aber nicht gelöscht.

Ein Karenz-Bypass ist nicht nur ein Software-Bug — es ist ein dokumentierbarer Compliance-Verstoß mit Bußgeldrisiko.

### Betroffene Specs

- **REQ-007** Erntemanagement — Karenz-Gate-Implementierung
- **REQ-010** IPM-System — `SafetyIntervalValidator` und `requires_harvest_delay`-Edge
- **REQ-013** Pflanzdurchlauf v2.0 — Detach-Operation
- **NFR-011 R-17** — Treatment-Retention

## Decision

**Snapshot-Strategie beim Detach.**

Wenn eine `PlantInstance` aus einem Run detached wird, werden zum Zeitpunkt des Detach die **karenzwirksamen Run-Level-Treatments** auf die PlantInstance kopiert — als neue `to_plant`-Edges mit zusätzlichem Metadatum `inherited_from_run: <run_key>` und `inherited_at: <detach_timestamp>`.

```python
def detach_plant_instance(
    run_key: str,
    plant_key: str,
    *,
    detach_category: str,
    detach_reason: Optional[str],
) -> None:
    # 1. Bestehende Detach-Logik (REQ-013 §3): run_contains.detached_at setzen
    repo.set_detach(run_key, plant_key, now())

    # 2. NEU (ADR-001): Karenz-relevante Run-Treatments snapshotten
    active_treatments = repo.find_active_run_treatments(
        run_key=run_key,
        as_of=now(),  # Treatments mit safe_date >= now()
    )
    for treatment in active_treatments:
        repo.create_inherited_treatment_edge(
            treatment_key=treatment.key,
            target_plant_key=plant_key,
            inherited_from_run=run_key,
            inherited_at=now(),
            original_applied_at=treatment.applied_at,
            safety_interval_days=treatment.safety_interval_days,
        )
```

Der `SafetyIntervalValidator` (REQ-010) wird so erweitert, dass er für eine Plant **alle relevanten Treatments** sammelt:

- Direkte `to_plant`-Edges (Standalone-Behandlungen)
- Aktive `to_run`-Edges (während Plant Run-Mitglied ist, `run_contains.detached_at = null`)
- Geerbte `to_plant`-Edges mit `inherited_from_run != null` (nach Detach)

```aql
// SafetyIntervalValidator-Lookup (alle relevanten Treatments)
FOR plant IN plant_instances FILTER plant._key == @plant_key
    LET direct = (
        FOR t IN treatment_applications
            FOR e IN to_plant FILTER e._from == t._id AND e._to == plant._id
            RETURN t
    )
    LET active_run = FIRST(
        FOR r IN run_contains
            FILTER r._to == plant._id AND r.detached_at == null
            FOR run IN planting_runs FILTER run._id == r._from
            RETURN run
    )
    LET run_treatments = active_run == null ? [] : (
        FOR t IN treatment_applications
            FOR e IN to_run FILTER e._from == t._id AND e._to == active_run._id
            RETURN t
    )
    RETURN UNION_DISTINCT(direct, run_treatments)
```

Geerbte `to_plant`-Edges werden im obigen `direct`-Block automatisch erfasst, weil sie nach dem Detach reguläre `to_plant`-Edges sind.

## Alternatives Considered

### Alternative 1 — Lookup über Phase-History (kein Snapshot)

Bei jeder Karenz-Prüfung wird via `phase_history` der frühere Run-Aufenthalt rekonstruiert und alle Run-Level-Treatments während dieser Mitgliedschaft mit eingerechnet.

- ✅ Keine Datenredundanz
- ✅ Spätere Run-Korrekturen (z.B. Treatment-Edit) wirken automatisch auf detachte Plants
- ❌ Komplexere AQL — Phase-History muss traversiert werden, dann Run-Treatments im Zeitfenster der Mitgliedschaft gefiltert
- ❌ Performance: Karenz-Gate wird bei jeder Ernte-Erstellung getriggert → potenziell teurer Cross-Collection-Lookup
- ❌ **Compliance-Risiko:** Wenn der Run später gelöscht oder umbenannt wird, ist der historische Bezug verloren — die detachte Plant kann ihre eigene Behandlungshistorie nicht mehr rekonstruieren

### Alternative 2 — Detach blockieren bei aktiver Karenz

Solange auf Run-Ebene eine Karenz läuft, kann keine Plant detached werden. Der Anwender muss warten, bis die Karenzzeit abgelaufen ist.

- ✅ Triviale Implementierung
- ❌ Verhindert legitime Detaches in genau dem Szenario, das Detach motiviert: kranke Plant aus dem Run rausnehmen, um den Rest zu schützen
- ❌ Pflanzenschutz-Praxis-untauglich

### Alternative 3 — Karenz-Vererbung als virtueller Edge / Service-Layer

Eine Service-Methode `effective_treatments(plant)` abstrahiert den Lookup. Die Logik kann austauschbar sein: heute via Phase-History, morgen via Snapshot, der Aufrufer (REQ-007) ist davon entkoppelt.

- ✅ Trennung von Wissen und Speicherform
- ❌ Verschiebt das Problem nur — die zugrundeliegende Strategie muss trotzdem entschieden werden
- ❌ Spec wird abstrakter — schwerer zu verifizieren, ob die Compliance erfüllt ist

### Alternative 4 — Hybrid Snapshot + Phase-History-Fallback

Beim Detach wird ein Snapshot erstellt; der Lookup nutzt primär den Snapshot, fällt aber zur Phase-History zurück, falls der Snapshot fehlt (z.B. bei Migration-Daten).

- ✅ Robust gegen Schema-Migrationen
- ❌ Doppelte Code-Pfade — beide müssen parallel maintainen werden
- ❌ Compliance schwerer auditierbar (zwei Quellen der Wahrheit)

### Verworfene Alternativen — Begründung kompakt

| Alt | Verworfen weil |
|-----|----------------|
| 1 | Performance + historische Robustheit |
| 2 | Praxis-untauglich, blockt legitime Workflows |
| 3 | Verschiebt Entscheidung statt sie zu treffen |
| 4 | Doppelter Code-Pfad ohne klaren Mehrwert über Snapshot allein |

## Consequences

### Positive

- **Self-contained Plant:** Eine detachte Plant trägt ihre vollständige Behandlungshistorie selbst — auch wenn der ursprüngliche Run später gelöscht wird
- **Performance:** Karenz-Lookup bleibt bei zwei direkten Edge-Traversals (`to_plant` direct + `to_plant` inherited), kein historisches Walken
- **Compliance auditierbar:** `inherited_from_run` + `inherited_at` dokumentieren explizit, woher die Treatments stammen — CanG/PflSchG-konform
- **Migration-stabil:** Ein einmaliges Migrations-Skript für bestehende detachte Plants kann den Snapshot rückwirkend erzeugen

### Negative / Risiken

- **Datenredundanz:** Run-Level-Treatments existieren als zusätzliche `to_plant`-Edges auf detachten Plants. Bei Run mit 20 Plants und 3 aktiven Karenzen: bis zu 60 zusätzliche Edges beim Detach (1 pro Plant × 3 Treatments). Für Kamerplanter-Skalen (max. ~100k aktive Pflanzen) unkritisch.
- **Stichtag der Erfassung:** Treatments, die *nach* dem Detach auf Run-Ebene hinzukommen, werden nicht mehr auf die detachte Plant kopiert. Das ist beabsichtigt — die Plant ist ja nicht mehr im Run. Aber: Wenn der Anwender erwartet, dass „spätere Korrekturen am Run auch detachte Plants betreffen", ist das nicht der Fall. Mitigation: Klare UI-Doku.
- **Detach-Operation wird etwas teurer:** O(n) Run-Treatments × O(1) Edge-Insert. Bei typisch 0–5 aktiven Karenzen pro Run praktisch unkritisch.

### Folgemaßnahmen

| Spec | Änderung |
|------|----------|
| **REQ-013** §3 detach-Operation | Snapshot-Schritt im Pseudocode + Engine-Pflicht ergänzen |
| **REQ-010** §3 SafetyIntervalValidator | Lookup-Logik um geerbte Treatments erweitern, AQL-Beispiel ergänzen |
| **REQ-010** §2 Edge Collections | `to_plant`-Edge bekommt optionale Felder `inherited_from_run`, `inherited_at` |
| **REQ-007** §6 Karenz-Gate | Verweis auf REQ-010-Validator, der die geerbten Treatments einschließt |
| **NFR-011 R-17** | Klarstellung: Geerbte `to_plant`-Edges teilen die Aufbewahrungsfrist des Original-Treatments |
| Migration | Einmaliger Celery-Task für bestehende detachte PlantInstances: Snapshot rückwirkend erzeugen |
| AKs | DoD-Punkte in REQ-007/010/013: „Karenz-Detach-Bypass-Test" erforderlich |

## References

- **Widerspruchsbericht:** `spec/analysis/requirements-contradictions-2026-04-26.md` — W-009
- **REQ-007** §6 Karenzzeit-Gate (Zeile 1943)
- **REQ-010** §3 SafetyIntervalValidator (Zeile 530)
- **REQ-013** §1.1 Dual-Modell, §3 detach-Operation
- **NFR-011** R-17 Treatment-Retention
- **CanG** §22 Anbau-Dokumentationspflicht
- **PflSchG** §11 Anwendungsdokumentation

## Resolved Decisions (Workshop 2026-04-27)

| # | Frage | Entscheidung | Begründung |
|---|-------|--------------|-----------|
| 1 | Snapshot-Cutoff | **Nur aktive Treatments** (`safe_date >= now()`) | Karenz-Schutz ist die einzige zwingende Anforderung für den Snapshot. Historische Behandlungs-Doku läuft über `treatment_applications`-Collection (NFR-011 R-17, 3 Jahre) und ist über Phase-History rekonstruierbar — keine Datenredundanz nötig. |
| 2 | Edit nach Detach | **Snapshot bleibt unverändert** | Audit-Trail-Integrität: Snapshot dokumentiert, was zum Detach-Zeitpunkt galt. Nachträgliche Korrekturen am Run-Treatment werden nicht automatisch übertragen — der Anwender muss die geerbte `to_plant`-Edge der detachten Plant separat editieren, beide Edits sind dann separat im Audit-Log. |
| 3 | Re-attach | **Geerbte Edges bleiben** (DISTINCT im Validator) | Historischer Audit-Trail bleibt vollständig. Doppelte Treatments durch Re-attach werden im `SafetyIntervalValidator` via DISTINCT/Set-Logik dedupliziert. |
| 4 | Migration | **Hard Cutover** beim REQ-013-v2.0-Rollout | Migration ist Bestandteil des v2.0-Migrations-Tasks (REQ-013-v2.0 ist selbst noch nicht implementiert). Einmaliger sauberer Zustand statt permanentem Mischbetrieb. |
