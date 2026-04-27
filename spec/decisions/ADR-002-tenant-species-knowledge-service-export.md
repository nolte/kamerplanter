# ADR-002: Tenant-eigene Species im Knowledge Service und DSGVO-Export

## Status

**Accepted** — *Entschieden: 2026-04-27, durch nolte*
*Erstellt: 2026-04-27*

## Context

REQ-001 v4.0 hat **drei Schichten von Stammdaten** eingeführt:

```
Schicht 1 — Globale Stammdaten (origin='system' | 'enrichment' | 'import')
            tenant_key=null, sichtbar via tenant_has_access-Edge

Schicht 2 — Tenant-Overlay (tenant_species_config / tenant_cultivar_config)
            Tenant-spezifische Anpassungen an globalen Daten (Notizen, Hidden-Flag)

Schicht 3 — Tenant-eigene Stammdaten (origin='tenant')
            tenant_key gesetzt, NUR im eigenen Tenant sichtbar
```

Schicht 3 löst ein echtes Problem (Tenants brauchen Anpassbarkeit), erzeugt aber Konflikte mit anderen Specs, die implizit nur globale Daten kannten.

### Drei konkrete Subprobleme

#### Subproblem A — DSGVO-Datenexport (REQ-025 Art. 15/20)

Der `DataExportEngine.USER_DATA_MANIFEST` (REQ-025 §3.1) iteriert über User-Daten und exportiert sie als JSON. Pflanzdaten enthalten `species_key`-Referenzen.

```
User Anna fordert Datenexport an
→ Export enthält {plant_instance: { species_key: "tenant-tomato-x" }}
→ Anna lädt Export in ein anderes System hoch
→ Anderes System: "species_key tenant-tomato-x ist unbekannt"
→ Datenmigration scheitert oder ist unvollständig
```

DSGVO Art. 20 (Datenübertragbarkeit) verlangt **strukturierte und maschinenlesbare** Daten — eine bloße ID-Referenz auf einen tenant-internen Datensatz erfüllt das nicht, wenn der Empfänger die Auflösung nicht hat.

#### Subproblem B — KI-Kontext (REQ-031)

Der `AiContextBuilder` (REQ-031 §4.2) baut ein `QuestionContext` mit `species`, `phase`, `substrate`, `ec`, `ph` etc. und schickt es an den externen Knowledge Service. Der Knowledge Service hat seinen pgvector-Index aus **Schicht 1 + 2** (globale Stammdaten + kuratierte YAMLs) — **kennt aber Schicht 3 nicht**.

```
Anwender fragt im KI-Chat: "Wie pflege ich meine Pflanze?"
PlantInstance.species_key = "tenant-tomato-x" (origin='tenant')
→ AiContextBuilder schreibt: { species: "Tenant-Tomate-X", ... }
→ Knowledge Service: keine Embeddings für "Tenant-Tomate-X" gefunden
→ Antwort: generischer "Ich weiß nichts über diese Spezies" oder
            irreführende Hochrechnung aus ähnlichem Klang
```

Selbst wenn die tenant-eigene Species ein `parent_species_key` (auf eine globale Species verweisend) hätte, ist nicht spezifiziert, dass der Knowledge Service diesen Fallback durchführen soll.

#### Subproblem C — Promotion-Race-Condition (REQ-001 §3)

REQ-001 v4.0 §3 spezifiziert eine **Promotion-Operation**: KA-Admin kann eine tenant-eigene Species `in-place` zu einer globalen Species machen (`origin: 'tenant' → 'system'`, `tenant_key → null`).

```
Tag 0   Tenant A erstellt tenant-eigene Species "Sorten-Tomate Kasimir"
Tag 1   KA-Admin entscheidet: das ist gut, soll global werden
Tag 1   Promotion-Job startet:
          1. Liest Species-Datensatz
          2. Ändert origin='system', tenant_key=null
          3. Erstellt tenant_has_access-Edges für alle Tier-1+2-Tenants
          → Während Schritt 2-3: Tenant B legt zufällig eine eigene
            Species "Sorten-Tomate Kasimir" mit identischem _key an?
            Kein Konflikt — Schemas sind anders gescoped, aber
            User-Erwartung: nach Promotion sehen alle dieselbe Species
        → Was, wenn ein Cultivar dabei zwischen den Tenants wandert?
```

Der Workflow ist nicht atomar, hat keinen Lock, keine Race-Condition-Tests. Das ist heute kein akutes Problem (Promotion ist selten), aber muss vor produktivem Mehrtenant-Betrieb geklärt sein.

### Compliance- und Architektur-Constraints

- **DSGVO Art. 20**: Datenübertragbarkeit — Export muss self-contained genug sein
- **REQ-031 §1.1 Architektur**: Knowledge Service ist ein **externes Microservice** — wir können ihm nicht einfach beliebige Tenant-Daten reinkippen ohne Tenant-Isolation zu verletzen
- **NFR-001 5-Layer**: Knowledge Service kennt keine ArangoDB-Connection — er fragt den Backend-Adapter an
- **REQ-024 Multi-Tenancy**: Tenant-Daten dürfen unter keinen Umständen in einen Index landen, der von anderen Tenants gelesen wird

### Betroffene Specs

- **REQ-001** Stammdatenverwaltung — Promotion-Workflow
- **REQ-024** Mandantenverwaltung — `tenant_has_access`-Edge-Logik
- **REQ-025** Datenschutz — Export-Manifest
- **REQ-031** KI-Assistent — KnowledgeServiceAdapter, AiContextBuilder

## Decision

Drei zusammenhängende Entscheidungen — eine pro Subproblem:

### A — DSGVO-Export: Inline-Snapshot tenant-eigener Stammdaten

Der `DataExportEngine` exportiert tenant-eigene Species/Cultivars **inline als eingebettete Objekte** im Export-JSON, statt nur die `species_key`-Referenz zu liefern. Globale Species bleiben Referenzen (mit URL zur öffentlichen Stammdaten-Auflösung).

```jsonc
// Export-JSON, plant_instance-Eintrag:
{
  "plant_instances": [{
    "_key": "...",
    "species_ref": {
      "scope": "tenant",                    // 'global' | 'tenant'
      "key": "tenant-tomato-kasimir",
      "snapshot": {                          // NUR bei scope='tenant'
        "scientific_name": "Solanum lycopersicum 'Kasimir'",
        "common_name": "Sorten-Tomate Kasimir",
        "origin": "tenant",
        "created_by": "Anna Schmidt",
        "created_at": "2025-09-15T...",
        "growth_phases": [...],
        "care_profile": {...}
      }
    }
  }]
}
```

Das Export-Manifest in REQ-025 wird um eine neue `DataSourceDefinition` für `tenant_species_config` und `tenant_cultivar_config` ergänzt — beide werden ebenfalls exportiert (Anpassungen, die der User auf globalen Species gemacht hat).

### B — KI-Kontext: Genus/Family-Fallback im Backend, kein eigener Index

Der `AiContextBuilder` (REQ-031 §4.2) erkennt vor dem Knowledge-Service-Aufruf, ob die zugehörige Species `origin='tenant'` hat. Falls ja, wird der Context-`species`-Wert auf die **nächste globale Verwandte** umgemappt:

```
PlantInstance.species_key = "tenant-tomato-kasimir" (origin='tenant')
                            └─ parent_species_key = "solanum-lycopersicum" (global)

AiContextBuilder ruft auf:
  context.species = "Solanum lycopersicum"  (global, im Index)
  context.cultivar_hint = "Kasimir"          (Klartext-Annotation, optional)
```

Der Knowledge Service bekommt also einen **auflösbaren** Species-Wert; die tenant-spezifische Note bleibt als unstrukturierter Hint. Kein eigener Tenant-Index nötig.

Falls keine `parent_species_key` gesetzt ist, fällt der Builder auf das **Genus** (und ggf. Family) zurück; im Worst Case schreibt er eine generische `cultivar_hint`-Antwort und markiert die Antwort als `confidence: low`.

### C — Promotion: Single-Step atomare Operation mit Optimistic Locking

Die Promotion-Operation in REQ-001 §3 wird als **single-AQL-Transaktion** spezifiziert. Während der Transaktion wird der Species-Datensatz mit einem `revision`-Token gelockt; gleichzeitige Modifikationen (Tenant-Edit, andere Promotion) brechen mit HTTP 409 ab.

```python
async def promote_species_to_global(species_key: str, expected_revision: str):
    """Atomare Promotion mit Optimistic Locking."""
    async with db.transaction():
        species = await species_repo.get_for_update(species_key)
        if species.revision != expected_revision:
            raise ConflictError(
                error_code="species.revision_mismatch",
                message="Species wurde während der Promotion modifiziert."
            )
        # 1. origin/tenant_key ändern, revision inkrementieren
        await species_repo.update(species_key, {
            "origin": "system",
            "tenant_key": None,
            "revision": species.revision + 1,
            "promoted_at": now(),
            "promoted_from_tenant": species.tenant_key,
        })
        # 2. tenant_has_access-Edges für Tier-1+2-Tenants erstellen
        await access_repo.bulk_grant_access(species_key=species_key)
```

## Alternatives Considered

### Subproblem A — DSGVO-Export

| Alt | Strategie | Verdikt |
|-----|-----------|---------|
| **A.1** Inline-Snapshot (Empfehlung) | Tenant-Species als Embedded-Objekt im Export | ✅ Gewählt |
| A.2 | Pure Referenz wie bisher (Status quo) | ❌ DSGVO Art. 20 nicht erfüllt — Datenübertragbarkeit nicht praktikabel |
| A.3 | Externer Resolver-Service (Tenant-Species-API) | ❌ Datenexport muss self-contained sein, externer Resolver braucht Auth |
| A.4 | Inline + zusätzliche RDF/JSON-LD-Repräsentation | ❌ Overengineered für aktuellen Bedarf |

### Subproblem B — KI-Kontext

| Alt | Strategie | Verdikt |
|-----|-----------|---------|
| **B.1** Genus/Family-Fallback im Backend (Empfehlung) | Tenant-Species → globale Verwandte mappen, Cultivar als Hint | ✅ Gewählt |
| B.2 | Tenant-eigener pgvector-Index pro Tenant | ❌ Tenant-Isolation auf KS-Ebene aufwendig; Embedding-Kosten linear pro Tenant; KS-Architektur (REQ-031 §1.1) explizit Single-Index |
| B.3 | Tenant-Species werden im KS-Index mit `tenant_key`-Filter geführt | ❌ Verstoß gegen KS-Stateless-Architektur; ArangoDB-Sync-Overhead |
| B.4 | Tenant-Species lösen KI-Anfrage mit „nicht unterstützt" 422 ab | ❌ UX-Regression für engagierte Tenants, die eigene Sortennotizen haben |
| B.5 | KS bekommt direkten ArangoDB-Read-Zugriff für Tenant-Lookup | ❌ Verletzt 5-Layer-Architektur (NFR-001); Tenant-Isolation kompromittiert |

### Subproblem C — Promotion

| Alt | Strategie | Verdikt |
|-----|-----------|---------|
| **C.1** Single-AQL-Transaktion + Optimistic Locking (Empfehlung) | Atomar, Race-Conditions explizit erkannt | ✅ Gewählt |
| C.2 | Pessimistic Locking (Species für Dauer der Promotion lock) | ❌ Lange Locks bei Bulk-Tenant-Edge-Erzeugung; Skalierungsproblem |
| C.3 | Soft-Promotion (Species bleibt tenant-scoped, zusätzlich global verfügbar via Alias) | ❌ Datenmodell-Komplikation; doppelte Records; Verwirrung im Export |
| C.4 | Promotion ist nur möglich, wenn keine Referenzen existieren (anderer Workflow) | ❌ Verhindert das Hauptszenario: Tenant probiert Species aus, Admin promoted bewährte → Referenzen existieren bereits |

### Verworfene übergeordnete Alternative

**Q.1 — Tenant-eigene Species als Konzept verwerfen**

Wir könnten Schicht 3 (origin='tenant') ganz fallen lassen und nur Schicht 2 (tenant_species_config) zulassen. Tenants könnten dann nur Anpassungen an globalen Species machen, keine eigenen Species erstellen.

- ✅ Würde alle drei Subprobleme eliminieren
- ❌ Verstößt gegen REQ-001 v4.0 User Story (Tenants haben legitime Use Cases für eigene Sorten — z.B. Hobby-Züchtung, regionale Sorten ohne globale Datenlage)
- ❌ Disempowering: Anwender muss auf KA-Admin warten, um neue Sorte einzutragen
- ❌ Outdoor-Garden-Planner-Review G-001 ff. fordert explizit tenant-eigene Sorten

→ **Verworfen** — die drei Subprobleme sind lösbar; das Konzept ist wertvoll.

## Consequences

### Positive

- **DSGVO-konform:** Self-contained Export erfüllt Art. 20 Datenübertragbarkeit
- **KI-funktional:** Tenant-Species verlieren keinen Mehrwert im Chat — Genus/Family-Fallback ist transparent für den Anwender
- **Promotion-sicher:** Optimistic Locking deckt den seltenen Race-Conditions-Fall, ohne Skalierung zu beeinträchtigen
- **Architektur erhalten:** Knowledge Service bleibt stateless mit single-Index, 5-Layer-Architektur unverletzt

### Negative / Risiken

- **Export-Größe wächst:** Inline-Snapshot statt Referenz — bei vielen tenant-eigenen Species pro User wird der Export größer. Mitigation: Snapshot-Format ist kompakt (kein doppeltes Speichern globaler Species, die als Referenz bleiben)
- **KI-Antworten sind „verschwommen" für tenant-eigene Sorten:** Der Anwender bekommt Genus-Antworten, nicht sortenspezifische. Mitigation: UI-Indikator „Antwort basiert auf allgemeiner Solanum-Lycopersicum-Datenlage, nicht spezifisch für deine Sorte"
- **Promotion erfordert UI-Anpassung:** Anwender muss `expected_revision` mitschicken; bei 409 Retry-Dialog. Mitigation: Standard-Pattern, vom Frontend bereits für andere Operationen genutzt
- **`parent_species_key`-Pflichtfeld?** Wenn Tenant-Species keine `parent_species_key` hat, ist der KI-Fallback schwächer. Open Question für den Workshop.

### Folgemaßnahmen

| Spec | Änderung |
|------|----------|
| **REQ-001** §3 Promotion | Atomare Operation + Optimistic Locking spezifizieren; `revision`-Feld auf Species/Cultivar einführen |
| **REQ-001** §1 Species-Modell | `parent_species_key` als optionales Feld dokumentieren, mit Empfehlung „bei origin='tenant' setzen für KI-Kontext" |
| **REQ-025** §3.1 Export-Manifest | `species_ref`-Wrapper-Struktur; Inline-Snapshot für tenant-eigene Species; `tenant_species_config` + `tenant_cultivar_config` als neue `DataSourceDefinition`s |
| **REQ-031** §4.2 AiContextBuilder | Genus/Family-Fallback-Logik dokumentieren; `cultivar_hint` als optionales Feld im QuestionContext |
| **REQ-031** §6.X UI | `confidence: low`-Badge bei Genus-Fallback-Antworten anzeigen |
| **REQ-024** §1a Permission-Matrix | Promotion-Permission auf KA-Admin (Platform-Admin) beschränken; Token-Generierung dokumentieren |
| AKs | Pro Spec: Tests für die drei Subprobleme |

## References

- **Widerspruchsbericht:** `spec/analysis/requirements-contradictions-2026-04-26.md` — W-006
- **REQ-001** v4.0 §1, §3 — Stammdaten-Origin und Promotion
- **REQ-024** v1.3 §1a, §1b — `tenant_has_access`, Tier-1+2-Auto-Assign
- **REQ-025** §3.1 — `USER_DATA_MANIFEST`
- **REQ-031** v2.0 §1.1, §2.1, §4.2 — Knowledge Service Architektur, Wissensquellen, AiContextBuilder
- **DSGVO Art. 20** Datenübertragbarkeit
- **NFR-001** 5-Layer-Architektur

## Resolved Decisions (Workshop 2026-04-27)

| # | Frage | Entscheidung | Begründung |
|---|-------|--------------|-----------|
| 1 | `parent_species_key`-Pflichtigkeit bei `origin='tenant'` | **Empfohlen, nicht erzwungen** | Echte Neuentdeckungen ohne globale Verwandte sollen möglich bleiben; bei fehlender Angabe markiert die KI-Antwort `confidence: low` |
| 2 | Cultivar-Inheritance bei Species-Promotion | **Cultivars NICHT automatisch mitpromoten** | Sortenrechte und Datenqualität oft tenant-spezifisch; KA-Admin kann jedes Cultivar separat prüfen und einzeln promoten |
| 3 | Reverse-Import (Tenant→Tenant) jetzt? | **Phase 2 (später)** | Heute reicht DSGVO-Export-Konformität (Art. 20); Re-Import-Tooling wird als REQ-012-Erweiterung in einer späteren Iteration spezifiziert |
| 4 | Promotion-Audit | **Eigene Collection `promotion_audit_log`, nur Platform-Admin, 5 Jahre Retention** | Bei Sortenrechts-Streitigkeiten relevant; konsistent mit harvest_batches-Retention (NFR-011 R-16) |
| 5 | UX bei Genus-Fallback-Antworten | **Sichtbarer „confidence: low"-Badge + Tooltip** | Kein Blocker — nur Information, damit Anwender weiß, dass die Antwort nicht sortenspezifisch ist |
