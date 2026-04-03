```yaml
Titel: Mischkultur & Companion Planting
Kategorie: Pflanzenplanung
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, React
Status: Entwurf
Version: 1.0
Quelle: Konsolidiert aus REQ-001 v5.0, REQ-013 v1.2, Outdoor-Garden-Planner Review G-008
```

## 1. Business Case

**User Story:** "Als Gärtnerin möchte ich bei der Beetplanung wissen, welche Pflanzen sich gegenseitig fördern oder hemmen, damit ich meine Mischkultur-Beete optimal zusammenstellen kann — mit konkreten Empfehlungen, warum bestimmte Partner gut oder schlecht zusammenpassen."

**Problemstellung:**
- Mischkultur-Wissen ist fragmentiert: Gärtner verlassen sich auf Tabellen in Büchern, Apps wie Fryd oder Erfahrungswerte
- Die Wechselwirkungen sind komplex: Allelopathie, Nährstoffkonkurrenz, Schädlingsabwehr, Bestäuberanlockung, Wurzelraumnutzung
- Kamerplanter hat die Graph-Datenstruktur (ArangoDB) als ideale Basis — aber die Empfehlungs-Engine, die Seed-Daten und die UI fehlen noch als integriertes Feature

**Abgrenzung:**
- **REQ-001** (Stammdaten): Definiert die Datenmodell-Grundlagen (Species, BotanicalFamily) — REQ-028 definiert die Mischkultur-spezifischen **Edges**, **Scores** und **Seed-Daten**
- **REQ-013** (Pflanzdurchlauf): Definiert `mixed_culture`-Runs mit Entry-Rollen — REQ-028 definiert die **Empfehlungs-Engine** und **Kompatibilitäts-Validierung**, die REQ-013 konsumiert
- **REQ-002** (Standort): Definiert Beetplanung — REQ-028 liefert die **Kompatibilitäts-Visualisierung** im Beetplan

### 1.1 Szenarien

**Szenario 1: Mischkultur-Empfehlung — "Tomate + was passt dazu?"**
```
1. Gärtnerin Lisa erstellt einen mixed_culture-Run für Beet B:
   primary: Tomate (Solanum lycopersicum)

2. System schlägt aktiv Mischkultur-Partner vor (basierend auf compatible_with-Edges):
   Empfohlen: Basilikum (Ocimum basilicum) — "Weisse-Fliege-Abwehr durch ätherische Öle" (Score: 0.9)
   Empfohlen: Tagetes (Tagetes patula) — "Nematoden-Abwehr" (Score: 0.85)
   Möglich: Petersilie, Salat, Spinat (Score: 0.6–0.7)
   Vermeiden: Fenchel — "Hemmt Tomatenwachstum (Allelopathie)"
   Vermeiden: Kartoffel — "Gleiche Familie (Solanaceae), Krankheitsübertragung"

3. Lisa wählt Basilikum (companion) + Tagetes (trap_crop) per Quick-Add
4. System validiert Gesamtkompatibilität des Runs → OK
```

**Szenario 2: Familien-Level Fallback**
```
1. Nutzer fragt: "Was passt zu Paprika (Capsicum annuum)?"
2. Keine Spezies-Level compatible_with-Kante zu Buschbohne vorhanden
3. Fallback auf Familien-Level: family_compatible_with(Solanaceae, Fabaceae)
4. Empfehlung: "Buschbohne (Familien-Level: Fabaceae↔Solanaceae)"
   Score = 0.85 × 0.8 = 0.68 (20% Familien-Level-Abschlag)
   match_level: "family" wird ausgewiesen
```

**Szenario 3: Kompatibilitäts-Check eines bestehenden Runs**
```
1. Lisa hat einen mixed_culture-Run mit Tomate + Basilikum + Fenchel
2. System prüft alle Spezies-Paare:
   Tomate ↔ Basilikum: compatible (0.9)
   Tomate ↔ Fenchel: incompatible ("Allelopathie")
   Basilikum ↔ Fenchel: unknown (kein Edge)
3. Ergebnis: WARNING — 1 inkompatibles Paar gefunden
4. UI zeigt Warnung mit Empfehlung: "Fenchel durch Petersilie ersetzen"
```

**Szenario 4: Nachbarschafts-Check bei Slot-Zuweisung**
```
1. In Beet B, Slot 3 steht bereits Tomate
2. Nutzer will Fenchel in Slot 4 (Nachbar-Slot) pflanzen
3. CompanionPlantingEngine prüft Adjacent-Slots
4. Warnung: "Inkompatibel mit Tomate in Slot 3 — Allelopathie"
```

**Szenario 5: Zimmerpflanzen-Kompatibilität**
```
1. Nutzer hat Monstera auf Fensterbank
2. Will daneben eine weitere Pflanze stellen
3. System empfiehlt Pflanzen mit ähnlichen Licht-/Feuchtigkeitsansprüchen
4. Kein Allelopathie-Risiko bei Zimmerpflanzen → Empfehlung basiert auf Standortkompatibilität
   (Hinweis: compatible_with/incompatible_with-Edges existieren primär für Freiland-Nutzpflanzen)
```

## 2. Datenmodell

### 2.1 Edge Collections (Graph-Beziehungen)

Alle Mischkultur-Edges werden im Named Graph `kamerplanter_graph` registriert.

<!-- Quelle: Widerspruchsanalyse W-010 — Tenant-Scoping vs. Graph-Traversal -->
**Hinweis: Tenant-Scoping bei Graph-Traversal:**
Companion-Planting-Empfehlungen traversieren **alle globalen** `compatible_with`/`incompatible_with`-Edges, unabhaengig von `TenantSpeciesConfig.hidden` (REQ-001 v4.0). Das `hidden`-Flag filtert nur die direkte Listenansicht der Species. In Empfehlungs-Ergebnissen werden jedoch nur Species angezeigt, fuer die der Tenant `tenant_has_access` besitzt. Eine als `hidden` markierte Species kann daher als Empfehlung erscheinen, solange die `tenant_has_access`-Kante existiert — sie ist lediglich in der Stammdaten-Liste ausgeblendet.

**Spezies-Level Edges:**

- **`compatible_with`**: `Species → Species`
  - Collection: `compatible_with` (Edge)
  - Properties:
    - `compatibility_score: float` (0.0–1.0, Pflichtfeld)
    - `effect_type: Literal['pest_repellent', 'growth_enhancer', 'soil_improver', 'pollinator_attractor', 'space_optimizer', 'nutrient_fixer', 'general']`
    - `description: str` (Freitext-Erklärung, z.B. "Weisse-Fliege-Abwehr durch ätherische Öle")
    - `source: Optional[str]` (Quellenangabe, z.B. "fryd.app", "Mein schöner Garten", "Erfahrungswert")
    - `bidirectional: bool` (Default: true — die meisten Mischkultur-Beziehungen sind symmetrisch)
  - Semantik: A → B = "A profitiert von / verträgt sich mit B". Bei `bidirectional: true` gilt die Beziehung in beide Richtungen, auch wenn nur eine Edge-Richtung gespeichert ist.

- **`incompatible_with`**: `Species → Species`
  - Collection: `incompatible_with` (Edge)
  - Properties:
    - `reason: str` (Pflichtfeld, z.B. "Allelopathische Hemmung durch Wurzelexsudate")
    - `severity: Literal['mild', 'moderate', 'severe']` (Default: `moderate`)
    - `source: Optional[str]`
    - `bidirectional: bool` (Default: true)
  - Semantik: A → B = "A hemmt / verträgt sich nicht mit B"

**Familien-Level Edges (Fallback):**

- **`family_compatible_with`**: `BotanicalFamily ↔ BotanicalFamily` (bidirektional)
  - Collection: `family_compatible_with` (Edge)
  - Properties:
    - `benefit_type: str` (z.B. "nitrogen_fixation", "pest_deterrent", "pollinator_attraction")
    - `compatibility_score: float` (0.0–1.0)
    - `notes: str`

- **`family_incompatible_with`**: `BotanicalFamily ↔ BotanicalFamily` (bidirektional)
  - Collection: `family_incompatible_with` (Edge)
  - Properties:
    - `reason: str`
    - `severity: Literal['mild', 'moderate', 'severe']`

### 2.2 Species-Attribut

- `allelopathy_score: float` (-1.0 bis 1.0) auf `:Species`-Nodes
  - -1.0 = stark hemmend, 0 = neutral, 1.0 = fördernd
  - Genereller Indikator; die paarspezifischen Edges sind autoritativ
  - Dient als Schnellfilter bei der Empfehlungsgenerierung

### 2.3 Effekt-Typen (Companion Effect Types)

| Effekt-Typ | Priorität | Beschreibung | Beispiel |
|---|---|---|---|
| `pest_repellent` | 1 (höchste) | Schädlingsabwehr durch Duftstoffe/Allelopathie | Tagetes gegen Nematoden |
| `growth_enhancer` | 2 | Wachstumsförderung (Schatten, Windschutz, Aromasteigerung) | Basilikum bei Tomate |
| `soil_improver` | 3 | Bodenverbesserung (N-Fixierung, Auflockerung) | Bohne bei Mais |
| `nutrient_fixer` | 4 | Stickstofffixierung durch Rhizobien | Fabaceae allgemein |
| `pollinator_attractor` | 5 | Bestäuberanlockung | Phacelia bei Kürbis |
| `space_optimizer` | 6 | Raumnutzungs-Synergie (Tiefwurzler + Flachwurzler) | Möhre + Zwiebel |
| `general` | 7 (niedrigste) | Allgemeine Verträglichkeit ohne spezifischen Effekt | Salat + Radieschen |

### 2.4 Scoping

Mischkultur-Edges sind **globale Stammdaten** (nicht tenant-scoped). Sie gelten für alle Nutzer und werden durch Seed-Daten und REQ-011 (Externe Anreicherung) befüllt.

| Entität | Scope | Erstellt durch | Bearbeitet durch |
|---|---|---|---|
| `compatible_with` Edge | Global | Seed / Enrichment | Platform-Admin |
| `incompatible_with` Edge | Global | Seed / Enrichment | Platform-Admin |
| `family_compatible_with` Edge | Global | Seed | Platform-Admin |
| `family_incompatible_with` Edge | Global | Seed | Platform-Admin |

## 3. Empfehlungs-Engine (CompanionPlantingEngine)

### 3.1 Algorithmus: Companion-Empfehlung

Eingabe: `species_key` (Primary-Pflanze), optional `location_key`, `season_month`

**4-Schritt-Algorithmus:**

1. **Spezies-Level Matches laden:**
   - Alle `compatible_with`-Edges der Primary Species laden
   - Alle `incompatible_with`-Edges der Primary Species laden

2. **Familien-Level Fallback** (nur wenn Schritt 1 keine compatible-Matches liefert):
   - Familie der Primary Species bestimmen (via `belongs_to_family`)
   - `family_compatible_with`-Edges der Familie laden
   - Alle Species dieser kompatiblen Familien auflösen
   - Score × 0.8 (20% Abschlag für Familien-Level-Inferenz)
   - `match_level: "family"` ausweisen

3. **Standort-/Saison-Filter** (optional):
   - Wenn `location_key` gegeben: Nur Species empfehlen, die für den Standorttyp (indoor/outdoor/greenhouse) geeignet sind
   - Wenn `season_month` gegeben: Nur Species empfehlen, deren Aussaat-/Pflanzzeit den Monat einschließt

4. **Sortierung nach Effekt-Typ-Priorität:**
   - `pest_repellent` > `growth_enhancer` > `soil_improver` > `nutrient_fixer` > `pollinator_attractor` > `space_optimizer` > `general`
   - Bei gleichem Effekt-Typ: nach `compatibility_score` absteigend

### 3.2 Algorithmus: Run-Kompatibilitäts-Validierung

Eingabe: `planting_run_key` (Run mit Entries)

```
1. Alle Entries des Runs laden
2. Für jedes Spezies-Paar (N×N/2):
   a. Prüfe compatible_with-Edge → score
   b. Prüfe incompatible_with-Edge → warning
   c. Wenn keine Edge: Prüfe Familien-Level (family_compatible_with / family_incompatible_with)
   d. Wenn keine Edge auf beiden Levels: "unknown"
3. Gesamtbewertung:
   - COMPATIBLE: Keine incompatible-Paare, Durchschnitts-Score > 0.5
   - WARNING: Mindestens 1 incompatible-Paar
   - INCOMPATIBLE: Mehr als 50% der Paare incompatible
```

### 3.3 Algorithmus: Slot-Nachbarschafts-Check

Eingabe: `species_key`, `slot_key`

```
1. Nachbar-Slots laden (via adjacent_to-Edges im Graph)
2. Aktive Pflanzen in Nachbar-Slots laden
3. Für jede Nachbar-Pflanze:
   a. Prüfe incompatible_with → Warnung
   b. Prüfe compatible_with → Benefit-Info
4. Return: (is_compatible, warnings[], benefits[])
```

### 3.4 AQL-Referenzabfragen

**Companion-Empfehlung mit Familien-Fallback:**
```aql
LET species = DOCUMENT("species", @species_key)
LET family = FIRST(FOR v IN 1..1 OUTBOUND species belongs_to_family RETURN v)

// Spezies-Level kompatible Partner
LET species_compatible = (
    FOR v, e IN 1..1 ANY species compatible_with
    RETURN {
        species_key: v._key,
        scientific_name: v.scientific_name,
        common_name_de: v.common_name_de,
        score: e.compatibility_score,
        effect_type: e.effect_type,
        description: e.description,
        match_level: "species"
    }
)

// Spezies-Level inkompatible Partner
LET species_incompatible = (
    FOR v, e IN 1..1 ANY species incompatible_with
    RETURN {
        species_key: v._key,
        scientific_name: v.scientific_name,
        common_name_de: v.common_name_de,
        reason: e.reason,
        severity: e.severity
    }
)

// Familien-Level Fallback (nur wenn keine Spezies-Level Matches)
LET family_compatible = LENGTH(species_compatible) == 0 ? (
    FOR fam, e IN 1..1 ANY family family_compatible_with
    FOR s IN 1..1 INBOUND fam belongs_to_family
    FILTER s._key != @species_key
    RETURN DISTINCT {
        species_key: s._key,
        scientific_name: s.scientific_name,
        common_name_de: s.common_name_de,
        score: ROUND(e.compatibility_score * 0.8 * 100) / 100,
        effect_type: e.benefit_type,
        description: e.notes,
        match_level: "family"
    }
) : []

RETURN {
    primary_species: species.scientific_name,
    recommended_companions: LENGTH(species_compatible) > 0
        ? species_compatible
        : family_compatible,
    incompatible_species: species_incompatible,
    match_level: LENGTH(species_compatible) > 0 ? "species" : "family"
}
```

**Run-Kompatibilitäts-Check (alle Paare):**
```aql
LET run = DOCUMENT("planting_runs", @run_key)
FILTER run.run_type == "mixed_culture"

LET entries = (
    FOR entry IN 1..1 OUTBOUND run has_entry
    LET species = FIRST(FOR s IN 1..1 OUTBOUND entry entry_for_species RETURN s)
    RETURN { entry_key: entry._key, species_key: species._key, species_name: species.scientific_name, role: entry.role }
)

LET pairs = (
    FOR e1 IN entries
        FOR e2 IN entries
            FILTER e1.entry_key < e2.entry_key
            LET compat = FIRST(
                FOR v, edge IN 1..1 OUTBOUND DOCUMENT("species", e1.species_key) compatible_with
                FILTER v._key == e2.species_key
                RETURN edge
            )
            LET incompat = FIRST(
                FOR v, edge IN 1..1 OUTBOUND DOCUMENT("species", e1.species_key) incompatible_with
                FILTER v._key == e2.species_key
                RETURN edge
            )
            // Familien-Level Fallback
            LET f1 = FIRST(FOR f IN 1..1 OUTBOUND DOCUMENT("species", e1.species_key) belongs_to_family RETURN f)
            LET f2 = FIRST(FOR f IN 1..1 OUTBOUND DOCUMENT("species", e2.species_key) belongs_to_family RETURN f)
            LET fam_compat = compat == null AND incompat == null ? FIRST(
                FOR v, edge IN 1..1 ANY f1 family_compatible_with
                FILTER v._key == f2._key
                RETURN edge
            ) : null
            LET fam_incompat = compat == null AND incompat == null ? FIRST(
                FOR v, edge IN 1..1 ANY f1 family_incompatible_with
                FILTER v._key == f2._key
                RETURN edge
            ) : null
            RETURN {
                species_a: e1.species_name,
                species_b: e2.species_name,
                status: incompat != null ? "incompatible"
                    : fam_incompat != null ? "family_incompatible"
                    : compat != null ? "compatible"
                    : fam_compat != null ? "family_compatible"
                    : "unknown",
                score: compat != null ? compat.compatibility_score
                    : fam_compat != null ? ROUND(fam_compat.compatibility_score * 0.8 * 100) / 100
                    : null,
                reason: incompat != null ? incompat.reason
                    : fam_incompat != null ? fam_incompat.reason
                    : null,
                match_level: compat != null OR incompat != null ? "species"
                    : fam_compat != null OR fam_incompat != null ? "family"
                    : "none"
            }
)

LET has_incompatible = LENGTH(FOR p IN pairs FILTER p.status IN ["incompatible", "family_incompatible"] RETURN 1)
LET compatible_pairs = LENGTH(FOR p IN pairs FILTER p.status IN ["compatible", "family_compatible"] RETURN 1)

RETURN {
    run_key: run._key,
    overall_status: has_incompatible > 0 ? "WARNING" : "COMPATIBLE",
    average_score: AVERAGE(FOR p IN pairs FILTER p.score != null RETURN p.score),
    compatible_pairs: compatible_pairs,
    incompatible_pairs: has_incompatible,
    unknown_pairs: LENGTH(FOR p IN pairs FILTER p.status == "unknown" RETURN 1),
    details: pairs
}
```

## 4. Technische Umsetzung (Python)

### 4.1 Enumerationen

```python
from enum import StrEnum


class CompanionEffectType(StrEnum):
    """Typ des Mischkultur-Effekts, nach Priorität sortiert."""
    PEST_REPELLENT = "pest_repellent"
    GROWTH_ENHANCER = "growth_enhancer"
    SOIL_IMPROVER = "soil_improver"
    NUTRIENT_FIXER = "nutrient_fixer"
    POLLINATOR_ATTRACTOR = "pollinator_attractor"
    SPACE_OPTIMIZER = "space_optimizer"
    GENERAL = "general"


# Prioritätsreihenfolge für Sortierung (niedrigerer Wert = höhere Priorität)
EFFECT_TYPE_PRIORITY: dict[CompanionEffectType, int] = {
    CompanionEffectType.PEST_REPELLENT: 1,
    CompanionEffectType.GROWTH_ENHANCER: 2,
    CompanionEffectType.SOIL_IMPROVER: 3,
    CompanionEffectType.NUTRIENT_FIXER: 4,
    CompanionEffectType.POLLINATOR_ATTRACTOR: 5,
    CompanionEffectType.SPACE_OPTIMIZER: 6,
    CompanionEffectType.GENERAL: 7,
}


class IncompatibilitySeverity(StrEnum):
    """Schweregrad einer Unverträglichkeit."""
    MILD = "mild"          # Suboptimal, aber möglich
    MODERATE = "moderate"  # Deutliche Beeinträchtigung
    SEVERE = "severe"      # Stark hemmend, vermeiden
```

### 4.2 Pydantic-Modelle

```python
from pydantic import BaseModel, Field


class CompanionEdge(BaseModel):
    """compatible_with-Edge zwischen zwei Species."""
    _from: str = Field(description="species/{key}")
    _to: str = Field(description="species/{key}")
    compatibility_score: float = Field(ge=0.0, le=1.0)
    effect_type: CompanionEffectType = CompanionEffectType.GENERAL
    description: str = ""
    source: str | None = None
    bidirectional: bool = True


class IncompatibleEdge(BaseModel):
    """incompatible_with-Edge zwischen zwei Species."""
    _from: str = Field(description="species/{key}")
    _to: str = Field(description="species/{key}")
    reason: str
    severity: IncompatibilitySeverity = IncompatibilitySeverity.MODERATE
    source: str | None = None
    bidirectional: bool = True


class CompanionRecommendation(BaseModel):
    """Einzelne Empfehlung aus der Engine."""
    species_key: str
    scientific_name: str
    common_name_de: str | None = None
    score: float
    effect_type: CompanionEffectType
    description: str = ""
    match_level: str = "species"  # "species" oder "family"
    suggested_role: str | None = None  # "companion", "trap_crop", etc.


class IncompatibleSpecies(BaseModel):
    """Einzelne Warnung aus der Engine."""
    species_key: str
    scientific_name: str
    common_name_de: str | None = None
    reason: str
    severity: IncompatibilitySeverity


class CompanionAdvice(BaseModel):
    """Gesamtergebnis der Companion-Empfehlung."""
    primary_species_key: str
    primary_species_name: str
    recommended_companions: list[CompanionRecommendation]
    incompatible_species: list[IncompatibleSpecies]
    match_level: str  # "species" oder "family"


class PairCompatibility(BaseModel):
    """Kompatibilitäts-Ergebnis für ein Spezies-Paar."""
    species_a: str
    species_b: str
    status: str  # "compatible", "incompatible", "family_compatible", "family_incompatible", "unknown"
    score: float | None = None
    reason: str | None = None
    match_level: str  # "species", "family", "none"


class RunCompatibilityResult(BaseModel):
    """Gesamtergebnis der Run-Kompatibilitätsprüfung."""
    run_key: str
    overall_status: str  # "COMPATIBLE", "WARNING", "INCOMPATIBLE"
    average_score: float | None = None
    compatible_pairs: int = 0
    incompatible_pairs: int = 0
    unknown_pairs: int = 0
    details: list[PairCompatibility] = []
```

### 4.3 Engine-Methoden

```python
class CompanionPlantingEngine:
    """Mischkultur-Empfehlungs- und Validierungs-Engine."""

    FAMILY_LEVEL_DISCOUNT = 0.8  # 20% Abschlag für Familien-Level-Inferenz

    def __init__(
        self,
        graph_repo: IGraphRepository,
        plant_repo: IPlantInstanceRepository,
        species_repo: ISpeciesRepository,
    ) -> None:
        self._graph_repo = graph_repo
        self._plant_repo = plant_repo
        self._species_repo = species_repo

    def get_companion_recommendations(
        self,
        species_key: str,
        location_key: str | None = None,
        season_month: int | None = None,
    ) -> CompanionAdvice:
        """Generiert Mischkultur-Empfehlungen für eine Primary-Spezies.

        4-Schritt-Algorithmus:
        1. Spezies-Level compatible_with/incompatible_with laden
        2. Familien-Level Fallback (Score × 0.8)
        3. Standort-/Saison-Filter (optional)
        4. Sortierung nach Effekt-Typ-Priorität
        """
        ...

    def check_compatibility(
        self, species_key: str, slot_key: str
    ) -> tuple[bool, list[str], list[str]]:
        """Prüft Nachbarschafts-Kompatibilität in Adjacent-Slots.

        Returns: (is_compatible, warnings, benefits)
        """
        ...

    def check_or_raise(self, species_key: str, slot_key: str) -> list[str]:
        """Prüft Kompatibilität und wirft CompanionConflictError bei Konflikt.

        Returns: benefits (bei Erfolg)
        """
        ...

    def validate_run_compatibility(
        self, run_entries: list[dict]
    ) -> RunCompatibilityResult:
        """Validiert die Mischkultur-Kompatibilität aller Entries eines Runs.

        Prüft N×N/2 Spezies-Paare mit Familien-Level-Fallback.
        """
        ...

    @staticmethod
    def sort_by_effect_priority(
        recommendations: list[CompanionRecommendation],
    ) -> list[CompanionRecommendation]:
        """Sortiert Empfehlungen nach Effekt-Typ-Priorität, dann Score."""
        return sorted(
            recommendations,
            key=lambda r: (EFFECT_TYPE_PRIORITY.get(r.effect_type, 99), -r.score),
        )
```

## 5. API-Endpunkte

### 5.1 Companion-Planting-Router

Prefix: `/api/v1/companion-planting`

| Methode | Pfad | Beschreibung | Auth |
|---|---|---|---|
| `GET` | `/species/{species_key}/recommendations` | Mischkultur-Empfehlungen für eine Species | Mitglied |
| `GET` | `/species/{species_key}/compatible` | Kompatible Partner (Spezies-Level) | Mitglied |
| `GET` | `/species/{species_key}/incompatible` | Inkompatible Partner (Spezies-Level) | Mitglied |
| `POST` | `/compatible` | Neue compatible_with-Edge anlegen | Platform-Admin |
| `DELETE` | `/compatible/{edge_key}` | compatible_with-Edge entfernen | Platform-Admin |
| `POST` | `/incompatible` | Neue incompatible_with-Edge anlegen | Platform-Admin |
| `DELETE` | `/incompatible/{edge_key}` | incompatible_with-Edge entfernen | Platform-Admin |

### 5.2 PlantingRun-Integration

| Methode | Pfad | Beschreibung | Auth |
|---|---|---|---|
| `POST` | `/api/v1/t/{slug}/planting-runs/{key}/validate-compatibility` | Mischkultur-Kompatibilitäts-Check eines Runs | Mitglied |

### 5.3 Request/Response-Beispiele

**GET `/api/v1/companion-planting/species/solanum_lycopersicum/recommendations`:**
```json
{
    "primary_species_key": "solanum_lycopersicum",
    "primary_species_name": "Solanum lycopersicum",
    "recommended_companions": [
        {
            "species_key": "tagetes_patula",
            "scientific_name": "Tagetes patula",
            "common_name_de": "Studentenblume",
            "score": 0.85,
            "effect_type": "pest_repellent",
            "description": "Nematoden-Abwehr durch Thiophene in den Wurzeln",
            "match_level": "species",
            "suggested_role": "trap_crop"
        },
        {
            "species_key": "ocimum_basilicum",
            "scientific_name": "Ocimum basilicum",
            "common_name_de": "Basilikum",
            "score": 0.9,
            "effect_type": "growth_enhancer",
            "description": "Weisse-Fliege-Abwehr durch ätherische Öle, traditionelle Aromaförderung",
            "match_level": "species",
            "suggested_role": "companion"
        },
        {
            "species_key": "petroselinum_crispum",
            "scientific_name": "Petroselinum crispum",
            "common_name_de": "Petersilie",
            "score": 0.7,
            "effect_type": "general",
            "description": "Gute Standortgemeinschaft, Bodenbeschattung",
            "match_level": "species",
            "suggested_role": "companion"
        }
    ],
    "incompatible_species": [
        {
            "species_key": "foeniculum_vulgare",
            "scientific_name": "Foeniculum vulgare",
            "common_name_de": "Fenchel",
            "reason": "Allelopathische Hemmung durch Wurzelexsudate",
            "severity": "moderate"
        },
        {
            "species_key": "solanum_tuberosum",
            "scientific_name": "Solanum tuberosum",
            "common_name_de": "Kartoffel",
            "reason": "Gleiche Familie (Solanaceae) — gemeinsame Krankheiten (Phytophthora, Alternaria)",
            "severity": "severe"
        }
    ],
    "match_level": "species"
}
```

**POST `/api/v1/t/{slug}/planting-runs/{key}/validate-compatibility`:**
```json
{
    "run_key": "mischkultur_beet_b_2025",
    "overall_status": "COMPATIBLE",
    "average_score": 0.72,
    "compatible_pairs": 2,
    "incompatible_pairs": 0,
    "unknown_pairs": 1,
    "details": [
        {
            "species_a": "Solanum lycopersicum",
            "species_b": "Ocimum basilicum",
            "status": "compatible",
            "score": 0.9,
            "reason": null,
            "match_level": "species"
        },
        {
            "species_a": "Solanum lycopersicum",
            "species_b": "Tagetes patula",
            "status": "compatible",
            "score": 0.85,
            "reason": null,
            "match_level": "species"
        },
        {
            "species_a": "Ocimum basilicum",
            "species_b": "Tagetes patula",
            "status": "unknown",
            "score": null,
            "reason": null,
            "match_level": "none"
        }
    ]
}
```

## 6. Seed-Daten: Spezies-Level Mischkultur-Matrix

### 6.1 Datenquelle

Die Seed-Daten werden aus den 185 plant-info Dokumenten (`spec/knowledge/plants/*.md`) extrahiert. Jedes Dokument enthält eine Sektion "6. Fruchtfolge & Mischkultur" mit strukturierten Tabellen für gute und schlechte Nachbarn inkl. Kompatibilitäts-Score und KA-Edge-Typ.

### 6.2 compatible_with-Edges (Auswahl der wichtigsten Paare)

Die folgende Tabelle enthält die kanonischen Spezies-Level-Paare. Bidirektional = jeweils eine Edge-Richtung gespeichert, beide Richtungen gelten.

| Species A | Species B | Score | effect_type | Beschreibung |
|---|---|---|---|---|
| Solanum lycopersicum | Ocimum basilicum | 0.9 | pest_repellent | Weisse-Fliege-Abwehr durch ätherische Öle |
| Solanum lycopersicum | Tagetes patula | 0.85 | pest_repellent | Nematoden-Abwehr durch Thiophene |
| Solanum lycopersicum | Petroselinum crispum | 0.7 | general | Gute Standortgemeinschaft, Bodenbeschattung |
| Solanum lycopersicum | Lactuca sativa | 0.65 | space_optimizer | Flacher Bodendecker zwischen Tomatenpflanzen |
| Solanum lycopersicum | Spinacia oleracea | 0.6 | space_optimizer | Bodenbeschattung, schnelle Ernte vor Tomaten-Wachstum |
| Solanum lycopersicum | Allium cepa | 0.7 | pest_repellent | Zwiebelduft gegen Tomatenkrankheiten |
| Daucus carota | Allium cepa | 0.85 | pest_repellent | Möhrenfliege ↔ Zwiebelfliege wechselseitige Abwehr |
| Daucus carota | Allium porrum | 0.8 | pest_repellent | Möhrenfliege-Abwehr durch Lauch |
| Daucus carota | Raphanus sativus | 0.7 | space_optimizer | Radieschen als Markierungssaat und Bodenlockerer |
| Cucumis sativus | Anethum graveolens | 0.75 | pollinator_attractor | Bestäuber anlocken, ähnliche Feuchtigkeitsansprüche |
| Cucumis sativus | Phaseolus vulgaris | 0.7 | nutrient_fixer | N-Fixierung durch Bohnen |
| Phaseolus vulgaris | Satureja hortensis | 0.8 | pest_repellent | Bohnenkraut gegen Schwarze Bohnenlaus |
| Fragaria x ananassa | Allium sativum | 0.8 | pest_repellent | Knoblauch gegen Grauschimmel und Erdbeermilbe |
| Fragaria x ananassa | Allium porrum | 0.75 | pest_repellent | Lauch gegen Erdbeerkrankheiten |
| Capsicum annuum | Ocimum basilicum | 0.8 | pest_repellent | Blattlaus-Abwehr durch ätherische Öle |
| Brassica oleracea var. italica | Tagetes patula | 0.75 | pest_repellent | Kohlweissling-Verwirrung, Nematoden-Abwehr |
| Brassica oleracea var. italica | Allium schoenoprasum | 0.7 | pest_repellent | Schnittlauch gegen Kohlschädlinge |
| Cucurbita pepo | Phaseolus vulgaris | 0.85 | nutrient_fixer | Drei-Schwestern-Prinzip: N-Fixierung |
| Cucurbita pepo | Tropaeolum majus | 0.75 | pest_repellent | Kapuzinerkresse als Blattlaus-Fangpflanze |
| Pisum sativum | Daucus carota | 0.7 | nutrient_fixer | N-Fixierung, Bodenlockerung durch Erbsenwurzeln |
| Solanum lycopersicum | Calendula officinalis | 0.7 | pest_repellent | Ringelblume gegen Nematoden und Blattläuse |
| Beta vulgaris | Phaseolus vulgaris | 0.7 | nutrient_fixer | N-Fixierung für Starkzehrer Mangold |
| Lactuca sativa | Raphanus sativus | 0.75 | space_optimizer | Schnelle Radieschen-Ernte zwischen Salat |
| Allium schoenoprasum | Rosa spp. | 0.7 | pest_repellent | Schnittlauch gegen Sternrußtau und Mehltau |
| Lavandula angustifolia | Rosa spp. | 0.75 | pest_repellent | Lavendel gegen Blattläuse bei Rosen |

### 6.3 incompatible_with-Edges (Auswahl der wichtigsten Paare)

| Species A | Species B | Reason | Severity |
|---|---|---|---|
| Solanum lycopersicum | Foeniculum vulgare | Allelopathische Hemmung durch Wurzelexsudate | moderate |
| Solanum lycopersicum | Solanum tuberosum | Gleiche Familie — Phytophthora/Alternaria-Übertragung | severe |
| Solanum lycopersicum | Brassica oleracea var. sabellica | Nährstoffkonkurrenz Starkzehrer vs. Starkzehrer | mild |
| Phaseolus vulgaris | Allium cepa | Zwiebel hemmt Knöllchenbakterien-Aktivität | moderate |
| Phaseolus vulgaris | Allium porrum | Lauch hemmt Knöllchenbakterien der Bohne | moderate |
| Pisum sativum | Allium cepa | Allium-Exsudate hemmen Rhizobien | moderate |
| Pisum sativum | Allium sativum | Knoblauch hemmt Erbsen-Wachstum | moderate |
| Cucumis sativus | Solanum lycopersicum | Unterschiedliche Klima-Ansprüche (Gurke feucht-warm, Tomate trocken-warm) | mild |
| Daucus carota | Anethum graveolens | Apiaceae-Selbstinkompatibilität, Kreuzbestäubung möglich | moderate |
| Fragaria x ananassa | Brassica oleracea var. gemmifera | Rosenkohl beschattet Erdbeeren, Nährstoffkonkurrenz | moderate |
| Foeniculum vulgare | Phaseolus vulgaris | Fenchel hemmt viele Nachbarn durch ätherische Öle | moderate |
| Ocimum basilicum | Salvia officinalis | Gegensätzliche Wasser-/Nährstoffbedürfnisse (feucht vs. trocken) | moderate |
| Ocimum basilicum | Thymus vulgaris | Gegensätzliche Wasserbedürfnisse | mild |
| Brassica oleracea var. botrytis | Fragaria x ananassa | Nährstoffkonkurrenz, Beschattung | moderate |
| Lactuca sativa | Petroselinum crispum | Petersilie hemmt Salatkeimung | mild |

### 6.4 Familien-Level Seed-Daten

**family_compatible_with-Kanten (~8 bidirektionale Paare):**

| Familie A | Familie B | benefit_type | compatibility_score | notes |
|---|---|---|---|---|
| Fabaceae | Solanaceae | nitrogen_fixation | 0.85 | N-Fixierung verbessert Starkzehrer-Versorgung |
| Fabaceae | Brassicaceae | nitrogen_fixation | 0.80 | N-Fixierung nach Starkzehrer |
| Fabaceae | Cannabaceae | nitrogen_fixation | 0.85 | N-Fixierung verbessert Starkzehrer-Versorgung |
| Lamiaceae | Solanaceae | pest_deterrent | 0.75 | Ätherische Öle wirken abschreckend |
| Lamiaceae | Brassicaceae | pest_deterrent | 0.70 | Basilikum/Minze gegen Kohlweissling |
| Lamiaceae | Cannabaceae | pest_deterrent | 0.70 | Ätherische Öle gegen Spinnmilben und Thripse |
| Asteraceae | Cucurbitaceae | pollinator_attraction | 0.65 | Blüten locken Bestäuber an |
| Apiaceae | Asteraceae | pollinator_attraction | 0.60 | Komplementäre Blütenbesucher |

**family_incompatible_with-Kanten (~3 bidirektionale Paare):**

| Familie A | Familie B | reason | severity |
|---|---|---|---|
| Solanaceae | Solanaceae | Selbstinkompatibilität: gemeinsame Krankheiten und Schädlinge | severe |
| Brassicaceae | Brassicaceae | Kohlhernie-Risiko bei wiederholtem Anbau | severe |
| Cucurbitaceae | Cucurbitaceae | Fusarium-Akkumulation im Boden | moderate |

## 7. UI-Integration

### 7.1 Mischkultur-Partner-Panel (PlantingRun-Create-Dialog)

**Trigger:** Nach Auswahl einer Primary-Pflanze in einem `mixed_culture`-Run.

**Darstellung:**
- Panel "Mischkultur-Partner" erscheint unterhalb der Primary-Auswahl
- Zwei Bereiche: "Empfohlene Partner" (grün) und "Vermeiden" (rot)
- Empfehlungen zeigen: Pflanzenname (DE + wiss.), Score-Badge, Effekt-Icon, Kurzbeschreibung
- Quick-Add-Button pro Empfehlung: Fügt Species als Entry mit vorgeschlagener Rolle hinzu
- Bei Familien-Level-Match: Badge "Familien-Empfehlung" zur Transparenz

**Expertise-Level (REQ-021):**
- **Beginner:** Zeigt nur Top-3 Empfehlungen + alle Warnungen, vereinfachte Sprache
- **Intermediate:** Zeigt Top-5 + Warnungen + Effekt-Typen
- **Expert:** Zeigt alle Empfehlungen + Scores + Match-Level + Quellen

### 7.2 Kompatibilitäts-Indikator im Run-Detail

- Farbiger Badge am Run-Header: Grün (COMPATIBLE), Gelb (WARNING), Rot (INCOMPATIBLE)
- Tooltip zeigt Kurzfassung: "2 kompatible, 1 inkompatibles Paar"
- Klick öffnet Detail-Dialog mit allen Paaren und Empfehlungen

### 7.3 Beetplan-Visualisierung (REQ-002)

- Farbliche Markierung von Kompatibilitäten wenn Pflanzen nebeneinander platziert werden:
  - Grüne Linie zwischen kompatiblen Nachbarn
  - Rote Linie zwischen inkompatiblen Nachbarn
  - Graue Linie bei unbekannter Beziehung
- Hover auf Linie zeigt Grund/Score

### 7.4 i18n-Keys

```
companion.panel.title = "Mischkultur-Partner" / "Companion Plants"
companion.panel.recommended = "Empfohlene Partner" / "Recommended Partners"
companion.panel.avoid = "Vermeiden" / "Avoid"
companion.panel.quickAdd = "Als Partner hinzufügen" / "Add as Companion"
companion.badge.familyLevel = "Familien-Empfehlung" / "Family-Level Match"
companion.effect.pest_repellent = "Schädlingsabwehr" / "Pest Repellent"
companion.effect.growth_enhancer = "Wachstumsförderung" / "Growth Enhancer"
companion.effect.soil_improver = "Bodenverbesserung" / "Soil Improver"
companion.effect.nutrient_fixer = "Stickstofffixierung" / "Nitrogen Fixation"
companion.effect.pollinator_attractor = "Bestäuberanlockung" / "Pollinator Attractor"
companion.effect.space_optimizer = "Raumoptimierung" / "Space Optimizer"
companion.effect.general = "Allgemein verträglich" / "Generally Compatible"
companion.severity.mild = "Suboptimal" / "Suboptimal"
companion.severity.moderate = "Unverträglich" / "Incompatible"
companion.severity.severe = "Stark hemmend" / "Strongly Inhibiting"
companion.validation.compatible = "Alle Kombinationen verträglich" / "All combinations compatible"
companion.validation.warning = "{count} inkompatible(s) Paar(e)" / "{count} incompatible pair(s)"
```

## 8. Verknüpfung mit anderen REQs

| REQ | Beziehung |
|---|---|
| **REQ-001** | Stellt Datenmodell bereit (Species, BotanicalFamily, allelopathy_score). REQ-028 definiert die Mischkultur-Edges und Seed-Daten. |
| **REQ-002** | Liefert Beetplan-Visualisierung. REQ-028 liefert die Kompatibilitätsdaten für farbliche Markierungen. |
| **REQ-011** | Externe Anreicherung kann compatible_with/incompatible_with-Edges automatisch aus Quellen importieren. |
| **REQ-013** | Konsumiert Empfehlungs-Engine für mixed_culture-Runs. Entry-Rollen (companion, trap_crop etc.) und Validierung bleiben in REQ-013. |
| **REQ-020** | Onboarding-Wizard kann im "Erstbepflanzung"-Schritt Mischkultur-Vorschläge anzeigen. |
| **REQ-021** | Expertise-Level steuert Detailtiefe der Mischkultur-Empfehlungen. |

## 9. Definition of Done (DoD)

### Datenmodell & Seed-Daten:
- [ ] **Edge-Collections:** `compatible_with`, `incompatible_with`, `family_compatible_with`, `family_incompatible_with` im Named Graph `kamerplanter_graph` registriert
- [ ] **Edge-Properties:** `effect_type`, `description`, `source`, `bidirectional` auf `compatible_with`; `severity` auf `incompatible_with`
- [ ] **Spezies-Level Seed-Daten:** Mindestens 25 `compatible_with`-Paare und 15 `incompatible_with`-Paare aus plant-info Dokumenten geladen
- [ ] **Familien-Level Seed-Daten:** 8 `family_compatible_with`-Paare und 3 `family_incompatible_with`-Paare
- [ ] **CompanionEffectType Enum:** 7 Effekt-Typen implementiert mit Prioritätsreihenfolge

### Empfehlungs-Engine:
- [ ] **4-Schritt-Algorithmus:** Species-Level → Family-Fallback (×0.8) → Standort/Saison-Filter → Effekt-Prioritäts-Sortierung
- [ ] **get_companion_recommendations:** Liefert sortierte Empfehlungen + Warnungen für eine Species
- [ ] **validate_run_compatibility:** Prüft alle N×N/2 Paare eines mixed_culture-Runs inkl. Familien-Fallback
- [ ] **check_compatibility (Slot):** Prüft Adjacent-Slot-Nachbarn auf Kompatibilität
- [ ] **Bidirektionale Edge-Traversierung:** `ANY`-Richtung in AQL für symmetrische Beziehungen

### API:
- [ ] **7 Companion-Planting-Endpoints:** GET recommendations, GET compatible, GET incompatible, POST/DELETE compatible, POST/DELETE incompatible
- [ ] **Run-Validierung:** POST `/planting-runs/{key}/validate-compatibility` liefert RunCompatibilityResult
- [ ] **Auth:** GET-Endpoints für alle Mitglieder; POST/DELETE nur für Platform-Admin

### UI:
- [ ] **Mischkultur-Partner-Panel:** Erscheint nach Primary-Auswahl im PlantingRun-Create-Dialog
- [ ] **Quick-Add:** 1-Klick-Hinzufügen eines empfohlenen Partners als Entry
- [ ] **Kompatibilitäts-Badge:** Farbiger Badge am Run-Header (grün/gelb/rot)
- [ ] **Expertise-Level-Anpassung:** Beginner sieht Top-3, Intermediate Top-5, Expert alle Empfehlungen
- [ ] **i18n:** Alle Labels in DE und EN

## 10. Testszenarien

**Szenario 1: Empfehlung — Spezies-Level Match**
```
GIVEN: Species "Solanum lycopersicum" hat 3 compatible_with-Edges und 2 incompatible_with-Edges
WHEN: GET /companion-planting/species/solanum_lycopersicum/recommendations
THEN:
  - recommended_companions enthält 3 Einträge, sortiert nach Effekt-Priorität
  - incompatible_species enthält 2 Einträge
  - match_level: "species"
```

**Szenario 2: Empfehlung — Familien-Level Fallback**
```
GIVEN: Species "Capsicum annuum" hat KEINE Spezies-Level compatible_with-Edge zu "Phaseolus vulgaris"
       BotanicalFamily "Solanaceae" hat family_compatible_with zu "Fabaceae" (Score 0.85)
WHEN: GET /companion-planting/species/capsicum_annuum/recommendations
THEN:
  - recommended_companions enthält Phaseolus vulgaris
  - Score: 0.85 × 0.8 = 0.68
  - match_level: "family"
```

**Szenario 3: Run-Kompatibilitäts-Check — COMPATIBLE**
```
GIVEN: PlantingRun (mixed_culture) mit Entries:
       - Solanum lycopersicum (primary)
       - Ocimum basilicum (companion)
       - Tagetes patula (trap_crop)
WHEN: POST /planting-runs/{key}/validate-compatibility
THEN:
  - overall_status: "COMPATIBLE"
  - compatible_pairs: 2 (Tomate-Basilikum: 0.9, Tomate-Tagetes: 0.85)
  - incompatible_pairs: 0
  - unknown_pairs: 1 (Basilikum-Tagetes: kein Edge)
```

**Szenario 4: Run-Kompatibilitäts-Check — WARNING**
```
GIVEN: PlantingRun (mixed_culture) mit Entries:
       - Solanum lycopersicum (primary)
       - Foeniculum vulgare (companion)
WHEN: POST /planting-runs/{key}/validate-compatibility
THEN:
  - overall_status: "WARNING"
  - incompatible_pairs: 1
  - details[0].reason: "Allelopathische Hemmung durch Wurzelexsudate"
```

**Szenario 5: Slot-Nachbarschafts-Check**
```
GIVEN: Slot 3 enthält aktive Solanum lycopersicum
       Slot 4 ist Nachbar-Slot (adjacent_to-Edge)
WHEN: check_compatibility("foeniculum_vulgare", "slot_4")
THEN:
  - is_compatible: false
  - warnings: ["Incompatible neighbor: Foeniculum vulgare in slot slot_3"]
```

**Szenario 6: Bidirektionale Edge-Traversierung**
```
GIVEN: compatible_with-Edge: Solanum lycopersicum → Ocimum basilicum (Score: 0.9)
WHEN: GET /companion-planting/species/ocimum_basilicum/recommendations
THEN:
  - recommended_companions enthält Solanum lycopersicum mit Score 0.9
  - (AQL-Traversierung mit ANY-Richtung findet Edge in beide Richtungen)
```

**Szenario 7: Quick-Add in UI**
```
GIVEN: Nutzer erstellt mixed_culture-Run, Primary: Solanum lycopersicum
WHEN: Mischkultur-Partner-Panel zeigt Empfehlungen
  AND: Nutzer klickt "Als Partner hinzufügen" bei Ocimum basilicum
THEN:
  - Neuer Entry wird angelegt: species=Ocimum basilicum, role=companion
  - Partner-Panel aktualisiert sich (zeigt Basilikum nicht mehr als Vorschlag)
```

---

**Hinweise für RAG-Integration:**
- Keywords: Mischkultur, Companion Planting, Allelopathie, Kompatibilität, Inkompatibilität, Begleitpflanze, Fangpflanze, Ammenpflanze, Gründüngung, Bestäuberanlockung, Familien-Fallback, Effekt-Typ, Schädlingsabwehr, Wachstumsförderung, Bodenverbesserung, Stickstofffixierung
- Botanische Konzepte: Allelopathie (chemische Pflanzenwechselwirkung), Rhizobien (N-fixierende Bakterien), Thiophene (Tagetes-Wurzelsubstanzen gegen Nematoden), Drei-Schwestern-Prinzip (Mais-Bohne-Kürbis)
- Verknüpfung: Baut auf REQ-001 (Species + BotanicalFamily), REQ-002 (Beetplan-Visualisierung), REQ-013 (mixed_culture-Runs, Entry-Rollen); liefert an REQ-011 (Anreicherungsquelle), REQ-020 (Onboarding-Vorschläge), REQ-021 (Expertise-Level-Filter)
