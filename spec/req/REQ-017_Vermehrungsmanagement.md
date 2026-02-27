# Spezifikation: REQ-017 - Vermehrungsmanagement

```yaml
ID: REQ-017
Titel: Vermehrungsmanagement & Genetische Rückverfolgbarkeit
Kategorie: Pflanzenvermehrung
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB
Status: Entwurf
Version: 1.2 (Agrarbiologie-Review U+P-Findings)
```

## 1. Business Case

**User Story:** "Als Gärtner möchte ich meine Vermehrungsaktivitäten — Stecklingnahme, Aussaat, Teilung, Veredelung — systematisch planen, dokumentieren und auswerten, um Erfolgsraten zu optimieren, Elite-Phänotypen gezielt zu erhalten und die genetische Herkunft jeder Pflanze lückenlos zurückverfolgen zu können."

**User Story (Mutterpflanzen):** "Als Gärtner möchte ich Mutterpflanzen als besonders wertvolle Individuen kennzeichnen und deren Gesundheit, Vitalität und Stecklingshistorie überwachen, damit ich rechtzeitig erkenne, wann eine Mutterpflanze ersetzt werden sollte, und meine besten Genetiken langfristig erhalte."

**User Story (Genetische Linie):** "Als Züchter möchte ich die Abstammungslinie jeder Pflanze über beliebig viele Generationen nachvollziehen können — wer ist die Mutter, wer der Vater bei Kreuzungen, welche Generation ist es — damit ich fundierte Selektionsentscheidungen treffen kann."

**Beschreibung:**
Das System erweitert die bestehende `PlantInstance`-Verwaltung um ein vollständiges Vermehrungsmodul. Statt Vermehrung als impliziten Nebeneffekt (Pflanze anlegen → fertig) zu behandeln, wird der gesamte Vermehrungsprozess als eigenständiger Workflow abgebildet.

**Kernkonzepte:**

**Mutterpflanzen-Verwaltung (Mother Plant):**
Jede `PlantInstance` kann als Mutterpflanze designiert werden. Die Designation ist ein Status-Flag — keine separate Entität. Mutterpflanzen erhalten zusätzliche Überwachung:

- **Gesundheitsbewertung:** Periodischer Health-Score (0–100) basierend auf Vitalität, Schädlingsfreiheit und Wuchsform
- **Stecklingshistorie:** Wann, wie viele, Erfolgsrate pro Entnahme
- **Erholungszeit:** Mindestens N Tage zwischen Stecklingsentnahmen (spezies-abhängig, konfigurierbar)
- **Generationszähler:** Klonale Generation — zählt vegetative Vermehrungszyklen (somatische Mutationslast-Warnung ab Generation 10+, konfigurierbar). Bei Aussaat (generative Vermehrung) wird die klonale Generation zurückgesetzt (neuer Genotyp)
- **Retirement-Kriterien:** Automatische Warnung bei abnehmender Vitalität, hohem Alter oder sinkender Bewurzelungsrate
- **Erhaltungsprioritäten:** Mutterpflanzen können als `critical` (einzige Quelle einer Genetik), `important` oder `standard` markiert werden

**Vermehrungsmethoden:**
- **Steckling (cutting):** Vegetative Vermehrung — Triebspitze oder Stammsteckling von Mutterpflanze. Siehe auch `CuttingType` für Differenzierung (apikal, nodal, Fersensteckling etc.)
- **Blattsteckling (leaf_cutting):** Vegetativ — ganzes Blatt oder Blattteil bewurzeln (Begonia, Sansevieria, Peperomia, Sukkulenten). Besonders für Zimmerpflanzen relevant.
- **Stammstück (stem_section):** Vegetativ — stammförmige Abschnitte ohne Blätter (Dracaena, Dieffenbachia, Yucca). Horizontal oder vertikal stecken.
- **Aussaat (seed_sowing):** Generative Vermehrung — Saatgut in Substrat/Keimmedium
- **Teilung (division):** Vegetativ — Wurzelstock/Rhizom teilen (Stauden, Gräser, Calathea, Spathiphyllum)
- **Kindel/Ableger (offset):** Vegetativ — natürliche Tochterpflanzen am Fuß der Mutterpflanze abtrennen (Aloe, Haworthia, Agave, Bromeliaceae, Pilea). Einfachste Methode mit höchster Erfolgsrate.
- **Absenker (layering):** Vegetativ — Trieb bewurzeln lassen, dann trennen (Beerensträucher)
- **Abmoosen (air_layering):** Vegetativ — Rinde am Stamm entfernen, mit feuchtem Moos umwickeln und in Folie einschlagen bis Wurzeln erscheinen (Ficus, Monstera, Dracaena). Ideal für große Zimmerpflanzen, die nicht einfach gesteckt werden können.
- **Brutzwiebel/Brutknöllchen (bulbil):** Vegetativ — kleine Tochterzwiebeln oder Brutknollen abtrennen (Lilium, Allium, Chlorophytum). Natürliche asexuelle Vermehrungsorgane.
- **Wasserbewurzelung (water_propagation):** Vegetativ — Stecklinge/Ableger in Wasser bewurzeln statt in Substrat (Pothos, Philodendron, Tradescantia, Basil). Besonders niedrigschwellig für Zimmerpflanzen-Einsteiger. Akklimatisierung beim Übergang zu Substrat beachten.
- **Veredelung (grafting):** Vegetativ — Edelreis auf Unterlage (Obstbäume, Tomaten)
- **Gewebekultur (tissue_culture):** In-vitro-Vermehrung — Meristemkultur (Spezial-Setup)

**Stecklingstyp-Differenzierung (CuttingType):**
Unterschiedliche Stecklingstypen haben verschiedene Bewurzelungscharakteristiken und Hormonbedarfe:
- **Triebspitze (apical):** Oberstes Triebstück mit Vegetationspunkt — höchste natürliche Auxin-Konzentration, schnellste Bewurzelung
- **Nodal (nodal):** Mittlerer Stammabschnitt mit Nodium — benötigt oft mehr Hormon als apikale Stecklinge
- **Fersensteckling (heel):** Seitentrieb mit Stück des Hauptstamms abgerissen — verholzte „Ferse" fördert Kallusbildung
- **Weichholz (softwood):** Junger, grüner Trieb der aktuellen Saison — schnelle Bewurzelung, empfindlich gegen Austrocknung
- **Halbverholzt (semi_hardwood):** Teilweise ausgereifter Trieb — robuster als Weichholz, langsamere Bewurzelung
- **Hartholz (hardwood):** Vollständig verholzter Trieb (Ruhephase) — langsame Bewurzelung, höhere Hormonkonzentration nötig, Long-Soak bevorzugt
- **Blatt mit Stiel (leaf_petiole):** Einzelnes Blatt mit Blattstiel (Peperomia, Begonia Rex) — Adventivknospen bilden sich am Schnitt
- **Blattsegment (leaf_section):** Blattstück mit Rippen (Sansevieria, Begonia) — neue Pflanze bildet sich an der Schnittkante

**Bewurzelungs-Protokolle:**
Standardisierte, wiederverwendbare Protokoll-Vorlagen für verschiedene Vermehrungsmethoden:
- Medium (Steinwolle, Perlit, Wasser, Aeroponik-Kloner, Erde) — mit optionaler Substrat-Integration (REQ-019)
- Bewurzelungshormon (IBA, NAA) mit Konzentration und methodenspezifischen Grenzen
- Umgebungsbedingungen:
  - **Lufttemperatur (air_temperature_celsius):** Umgebungstemperatur um den Steckling. Differenziert von Substrattemperatur.
  - **Substrattemperatur (heat_mat_celsius):** Wärmematte/Bottom-Heat-Temperatur. **Ideal 2–5°C über Lufttemperatur** — wärmeres Substrat fördert Wurzelbildung, während kühlere Luft die Transpiration reduziert. Delta >8°C = Warnung (Stress durch Temperaturgradient).
  - **VPD-Ziel (target_vpd_kpa):** Niedriger VPD (0.3–0.5 kPa) für wurzellose Stecklinge unter Dome
  - **Lichtintensität (light_ppfd):** Max. 150 PPFD unter Dome empfohlen, >150 = Warnung (Photoinhibition bei wurzellosen Stecklingen)
  - **Lichtspektrum (light_spectrum):** Spektrum beeinflusst Bewurzelungsgeschwindigkeit. Blau-dominant fördert kompakten Wuchs, Rot-dominant fördert Streckung, Rot:Blau-Mix optimal für Bewurzelung.
- Erwartete Timeline (Kallus-Bildung, erste Wurzeln, transplant-bereit)
- Bewertungskriterien (Wurzelmasse, Wurzellänge, Triebvitalität)

**IPM-Integration bei Vermehrung (REQ-010):**
Vermehrung ist eine kritische Übertragungsphase für Pathogene und Schädlinge:
- **Werkzeugsterilisation:** Dokumentation der Sterilisationsmethode (Alkohol 70%, Flamme, Bleiche, H2O2) pro Vermehrungsevent
- **Quarantäne:** Neue Vermehrungen optional unter Quarantäne stellen (14–21 Tage) bevor sie in den Bestand integriert werden
- **Virusstatus:** Tracking des Virusstatus der Mutterpflanze (`clean`, `untested`, `infected`, `recovered`) — Vermehrung von infizierten Pflanzen erzeugt Warnung
- **Mutterpflanzen-Hygiene:** Gesundheitscheck (REQ-010 Inspection) vor Stecklingnahme empfohlen

**Genetische Abstammung (Lineage Graph):**
ArangoDB-Graph-Traversal ermöglicht Rückverfolgung über beliebig viele Generationen:
- **Klonlinie:** Mutter → Steckling → Steckling von Steckling (lineare Kette)
- **Kreuzung:** Mutter + Vater → Samen → F1-Pflanze (Verzweigung)
- **Generationszählung:** Automatisch berechnet aus Graph-Tiefe
- **Phänotyp-Notizen:** Pro Generation können beobachtete Eigenschaften dokumentiert werden

**Vermehrungsbatch:**
Mehrere Stecklinge/Samen aus einer Entnahme werden als `PropagationBatch` gruppiert:
- Verknüpfung mit `PlantingRun` (REQ-013) für Batch-Management
- Erfolgsrate wird pro Batch ausgewertet
- Ausfälle werden dokumentiert (Gründe: Fäulnis, Austrocknung, kein Wurzelwachstum)

**Veredelungs-Kompatibilität:**
Das System prüft die Veredelungskompatibilität mehrstufig:
1. **Explizite Graph-Edges (Vorrang):** `graft_compatible_with`-Edges zwischen Species-Knoten für bekannte, praxisbewährte Kombinationen (z.B. Tomate auf Beaufort-Unterlage). Diese Edges haben Attribute wie `success_rate`, `notes`, `source` (Literatur/Erfahrung).
2. **Taxonomie-Heuristik (Fallback):** Nur wenn keine expliziten Edges existieren:
   - Innerhalb derselben Gattung: wahrscheinlich kompatibel (z.B. Solanum lycopersicum auf S. lycopersicum Unterlage)
   - Innerhalb derselben Familie: möglicherweise kompatibel (z.B. Tomate auf Kartoffel-Unterlage)
   - Verschiedene Familien: inkompatibel → System blockiert
3. **Hinweis:** Taxonomische Nähe ist ein Indikator, aber kein Garant — z.B. sind nicht alle Cucurbitaceae als Unterlage füreinander geeignet. Explizite Edges aus der Praxis sind immer vorzuziehen.

## 2. ArangoDB-Modellierung

### Document-Collections:

- **`:PropagationEvent`** — Einzelne Vermehrungsaktion (immutable)
  - Collection: `propagation_events`
  - Properties:
    - `event_type: PropagationMethod` (cutting, leaf_cutting, stem_section, seed_sowing, division, offset, layering, air_layering, bulbil, water_propagation, grafting, tissue_culture)
    - `cutting_type: Optional[CuttingType]` (apical, nodal, heel, softwood, semi_hardwood, hardwood, leaf_petiole, leaf_section — nur bei event_type='cutting')
    - `performed_at: datetime`
    - `quantity: int` (Anzahl entnommener Stecklinge / ausgesäter Samen)
    - `survived_count: Optional[int]` (Anzahl überlebender, wird nachgetragen)
    - `success_rate: Optional[float]` (0.0–1.0, berechnet aus survived/quantity)
    - `hormone_type: Optional[Literal['iba', 'naa', 'iba_naa_mix', 'honey', 'willow_water', 'none']]`
    - `hormone_concentration_ppm: Optional[float]` (Obergrenze 10.000 ppm, validiert gegen HORMONE_RANGES)
    - `hormone_application_method: Optional[Literal['quick_dip', 'long_soak', 'powder', 'gel']]` — Applikationsmethode bestimmt Wirkung maßgeblich: Quick-Dip (5s, 1000–3000 ppm IBA für weiche Stecklinge), Long-Soak (12–24h, 50–200 ppm für verholzte Stecklinge), Powder (direkte Applikation), Gel (Kontaktzeit verlängert). Ohne Methode ist die ppm-Angabe nicht reproduzierbar.
    - `medium: Optional[RootingMedium]`
    - `dome_humidity_percent: Optional[int]` (Ziel-Luftfeuchtigkeit unter Haube)
    - `air_temperature_celsius: Optional[float]` (Lufttemperatur — differenziert von Substrattemperatur)
    - `heat_mat_celsius: Optional[float]` (Substrattemperatur/Bottom Heat — ideal 2–5°C über Lufttemperatur)
    - `target_vpd_kpa: Optional[float]` (Ziel-VPD unter Dome, typisch 0.3–0.5 kPa)
    - `light_ppfd: Optional[int]` (Lichtintensität, max. 300 PPFD, Warnung >150 unter Dome)
    - `light_spectrum: Optional[LightSpectrum]` (blue_dominant, red_blue_mix, full_spectrum etc.)
    - `photoperiod_hours: Optional[float]` (Beleuchtungsdauer)
    - `substrate_batch_key: Optional[str]` (Referenz auf SubstrateBatch aus REQ-019)
    - `medium_ph: Optional[float]` (pH des Bewurzelungsmediums)
    - `medium_ec_ms: Optional[float]` (EC des Bewurzelungsmediums)
    - `tool_sterilization_method: Optional[ToolSterilizationMethod]` (IPM: Werkzeugsterilisation)
    - `quarantine_required: bool` (IPM: Quarantäne für Nachkommen)
    - `quarantine_days: Optional[int]` (Quarantäne-Dauer)
    - `callus_observed_at: Optional[datetime]` (Erstes Kallusgewebe)
    - `roots_observed_at: Optional[datetime]` (Erste Wurzeln sichtbar)
    - `transplant_ready_at: Optional[datetime]` (Bereit zum Umtopfen)
    - `failure_reasons: list[Literal['rot', 'desiccation', 'no_roots', 'damping_off', 'contamination', 'mechanical_damage', 'other']]`
    - `failure_count: int` (default: 0)
    - `notes: Optional[str]`
    - `photos: list[str]` (Referenzen auf Foto-Keys)

- **`:PropagationBatch`** — Gruppierung mehrerer gleichzeitiger Vermehrungen
  - Collection: `propagation_batches`
  - Properties:
    - `name: str` (z.B. "GSC-Klone Frühjahr 2026", "Tomaten-Aussaat März")
    - `batch_type: PropagationMethod` (alle 12 Methoden)
    - `started_at: datetime`
    - `completed_at: Optional[datetime]`
    - `status: Literal['in_progress', 'completed', 'failed']`
    - `total_quantity: int` (Summe aller Events)
    - `total_survived: Optional[int]`
    - `overall_success_rate: Optional[float]`
    - `target_planting_run_key: Optional[str]` (Ziel-PlantingRun für überlebende Pflanzen)
    - `notes: Optional[str]`

- **`:RootingProtocol`** — Wiederverwendbare Bewurzelungs-Vorlage
  - Collection: `rooting_protocols`
  - Properties:
    - `name: str` (z.B. "Cannabis Steckling Standard", "Tomate Steinwolle Rapid")
    - `method: PropagationMethod` (alle 12 Methoden)
    - `recommended_cutting_types: list[CuttingType]` (Empfohlene Stecklingstypen, nur bei method='cutting')
    - `recommended_species_keys: list[str]` (Empfohlene Arten)
    - `medium: RootingMedium`
    - `substrate_batch_key: Optional[str]` (Referenz auf SubstrateBatch aus REQ-019)
    - `hormone_type: Optional[HormoneType]`
    - `hormone_concentration_ppm: Optional[float]` (Obergrenze 10.000 ppm)
    - `hormone_application_method: Optional[Literal['quick_dip', 'long_soak', 'powder', 'gel']]`
    - `dome_humidity_percent: int` (z.B. 85)
    - `target_vpd_kpa: Optional[float]` (z.B. 0.4 — niedriger VPD verhindert Austrocknung wurzelloser Stecklinge; REQ-005 Sensor-Feedback)
    - `air_temperature_celsius: Optional[float]` (Lufttemperatur, z.B. 20.0)
    - `heat_mat_celsius: Optional[float]` (Substrattemperatur/Bottom Heat, z.B. 22.0 — ideal 2–5°C über Lufttemperatur)
    - `light_ppfd: int` (z.B. 100 — max. 300, Warnung >150 unter Dome)
    - `light_spectrum: Optional[LightSpectrum]` (Empfohlenes Lichtspektrum)
    - `photoperiod_hours: float` (z.B. 18.0)
    - `expected_callus_days: Optional[int]` (z.B. 5)
    - `expected_root_days: int` (z.B. 10)
    - `expected_transplant_days: int` (z.B. 14)
    - `instructions: str` (Schritt-für-Schritt-Anleitung)
    - `is_template: bool` (Verfügbar als Vorlage)
    - `author: str`

- **`:PhenotypeNote`** — Phänotyp-Beobachtung pro Pflanze
  - Collection: `phenotype_notes`
  - Properties:
    - `recorded_at: datetime`
    - `category: Literal['morphology', 'aroma', 'flavor', 'vigor', 'resistance', 'yield', 'potency', 'other']`
    - `trait: str` (z.B. "Purple Phänotyp", "Zitrus-Terpen-dominant", "Mehltau-resistent")
    - `rating: Optional[int]` (1–10 Skala)
    - `notes: Optional[str]`
    - `photos: list[str]`

### Edge-Collections:
```
# Abstammung (Kernstück — Graph-Traversal)
descended_from:       plant_instances → plant_instances           // Kind → Elternteil (gerichtet)
                      {relationship: Literal['clone', 'seed_mother', 'seed_father', 'rootstock', 'scion', 'division'],
                       generation: int,
                       generation_type: Literal['clonal', 'filial'],  // clonal = vegetativ (Mutationslast), filial = generativ (F1/F2)
                       propagation_event_key: str}

# Vermehrungsevent-Verknüpfungen
propagated_from:      propagation_events → plant_instances        // Event ← Quellpflanze (Mutter)
resulted_in:          propagation_events → plant_instances        // Event → Ergebnis-Pflanze(n)
uses_protocol:        propagation_events → rooting_protocols      // Event nutzt Protokoll
part_of_batch:        propagation_events → propagation_batches    // Event gehört zu Batch
batch_feeds_run:      propagation_batches → planting_runs         // Batch-Ergebnis fließt in PlantingRun

# Phänotyp-Dokumentation
has_phenotype:        plant_instances → phenotype_notes           // Pflanze hat Phänotyp-Beobachtung

# Veredelung (spezielle Abstammung)
grafted_onto:         plant_instances → plant_instances           // Edelreis → Unterlage
                      {grafted_at: datetime, graft_type: Literal['whip', 'cleft', 'approach', 'bud']}

# Veredelungskompatibilität (explizite Erfahrungsdaten — Vorrang vor Taxonomie-Heuristik)
graft_compatible_with: species → species                          // Bekannte Edelreis-Unterlage-Kombinationen
                       {success_rate: float,                      // 0.0-1.0
                        notes: Optional[str],                     // z.B. "Beaufort F1 als Standard-Unterlage"
                        source: Literal['literature', 'experience', 'trial']}
```

**ArangoDB-Graph-Definition:**
```json
{
  "edge_collection": "descended_from",
  "from_vertex_collections": ["plant_instances"],
  "to_vertex_collections": ["plant_instances"]
}
```
```json
{
  "edge_collection": "propagated_from",
  "from_vertex_collections": ["propagation_events"],
  "to_vertex_collections": ["plant_instances"]
}
```
```json
{
  "edge_collection": "resulted_in",
  "from_vertex_collections": ["propagation_events"],
  "to_vertex_collections": ["plant_instances"]
}
```
```json
{
  "edge_collection": "uses_protocol",
  "from_vertex_collections": ["propagation_events"],
  "to_vertex_collections": ["rooting_protocols"]
}
```
```json
{
  "edge_collection": "part_of_batch",
  "from_vertex_collections": ["propagation_events"],
  "to_vertex_collections": ["propagation_batches"]
}
```
```json
{
  "edge_collection": "batch_feeds_run",
  "from_vertex_collections": ["propagation_batches"],
  "to_vertex_collections": ["planting_runs"]
}
```
```json
{
  "edge_collection": "has_phenotype",
  "from_vertex_collections": ["plant_instances"],
  "to_vertex_collections": ["phenotype_notes"]
}
```
```json
{
  "edge_collection": "grafted_onto",
  "from_vertex_collections": ["plant_instances"],
  "to_vertex_collections": ["plant_instances"]
}
```

### AQL-Beispielqueries:

**1. Vollständige Abstammungslinie einer Pflanze (Klonlinie bis zur Ur-Mutter):**
```aql
LET plant = DOCUMENT('plant_instances', @plant_key)

LET lineage = (
    FOR ancestor, edge, path IN 1..20 OUTBOUND plant GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['descended_from'] }
        RETURN {
            plant_key: ancestor._key,
            plant_name: ancestor.name,
            species: ancestor.species_key,
            cultivar: ancestor.cultivar_key,
            relationship: edge.relationship,
            generation: edge.generation,
            propagation_event: edge.propagation_event_key
        }
)

RETURN {
    plant: { key: plant._key, name: plant.name },
    lineage: lineage,
    total_generations: LENGTH(lineage)
}
```

**2. Alle Nachkommen einer Mutterpflanze (Klon-Baum):**
```aql
LET mother = DOCUMENT('plant_instances', @mother_key)

LET descendants = (
    FOR child, edge, path IN 1..20 INBOUND mother GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['descended_from'] }
        RETURN {
            plant_key: child._key,
            plant_name: child.name,
            generation: edge.generation,
            relationship: edge.relationship,
            depth: LENGTH(path.edges)
        }
)

RETURN {
    mother: { key: mother._key, name: mother.name },
    total_descendants: LENGTH(descendants),
    descendants: descendants
}
```

**3. Mutterpflanzen mit Stecklingshistorie und Gesundheitsbewertung:**
```aql
FOR plant IN plant_instances
    FILTER plant.is_mother == true
    LET cutting_events = (
        FOR event IN propagation_events
            FOR edge IN propagated_from
                FILTER edge._to == plant._id AND edge._from == event._id
                FILTER event.event_type == 'cutting'
                SORT event.performed_at DESC
                RETURN {
                    performed_at: event.performed_at,
                    quantity: event.quantity,
                    survived: event.survived_count,
                    success_rate: event.success_rate
                }
    )
    LET latest_health = plant.mother_health_score
    LET avg_success_rate = AVERAGE(cutting_events[*].success_rate)
    LET last_cutting_date = LENGTH(cutting_events) > 0 ? cutting_events[0].performed_at : null
    LET days_since_last = last_cutting_date != null
        ? DATE_DIFF(last_cutting_date, DATE_NOW(), "day")
        : null
    SORT latest_health DESC
    RETURN {
        plant_key: plant._key,
        plant_name: plant.name,
        species_key: plant.species_key,
        cultivar_key: plant.cultivar_key,
        health_score: latest_health,
        mother_priority: plant.mother_priority,
        total_cuttings_taken: SUM(cutting_events[*].quantity),
        total_survived: SUM(cutting_events[*].survived),
        avg_success_rate: avg_success_rate,
        cutting_count: LENGTH(cutting_events),
        days_since_last_cutting: days_since_last,
        recovery_ok: days_since_last == null OR days_since_last >= plant.mother_recovery_days
    }
```

**4. Erfolgsraten pro Bewurzelungs-Protokoll und Species:**
```aql
FOR protocol IN rooting_protocols
    LET events = (
        FOR event IN propagation_events
            FOR edge IN uses_protocol
                FILTER edge._from == event._id AND edge._to == protocol._id
                FILTER event.survived_count != null
                FOR source_edge IN propagated_from
                    FILTER source_edge._from == event._id
                    LET source_plant = DOCUMENT(source_edge._to)
                    RETURN {
                        species_key: source_plant.species_key,
                        quantity: event.quantity,
                        survived: event.survived_count,
                        success_rate: event.success_rate
                    }
    )
    LET by_species = (
        FOR e IN events
            COLLECT species = e.species_key INTO grouped
            RETURN {
                species_key: species,
                event_count: LENGTH(grouped),
                total_quantity: SUM(grouped[*].e.quantity),
                total_survived: SUM(grouped[*].e.survived),
                avg_success_rate: AVERAGE(grouped[*].e.success_rate)
            }
    )
    RETURN {
        protocol_key: protocol._key,
        protocol_name: protocol.name,
        method: protocol.method,
        total_events: LENGTH(events),
        overall_avg_success: AVERAGE(events[*].success_rate),
        by_species: by_species
    }
```

**5. Veredelungs-Kompatibilitätsprüfung:**
```aql
LET scion_plant = DOCUMENT('plant_instances', @scion_key)
LET rootstock_plant = DOCUMENT('plant_instances', @rootstock_key)

LET scion_species = FIRST(
    FOR s IN species
        FILTER s._key == scion_plant.species_key
        RETURN s
)
LET rootstock_species = FIRST(
    FOR s IN species
        FILTER s._key == rootstock_plant.species_key
        RETURN s
)

LET scion_family = FIRST(
    FOR f, e IN 1..1 OUTBOUND scion_species GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['belongs_to_family'] }
        RETURN f
)
LET rootstock_family = FIRST(
    FOR f, e IN 1..1 OUTBOUND rootstock_species GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['belongs_to_family'] }
        RETURN f
)

LET same_genus = scion_species.genus == rootstock_species.genus
LET same_family = scion_family._key == rootstock_family._key

RETURN {
    scion: { species: scion_species.scientific_name, family: scion_family.name, genus: scion_species.genus },
    rootstock: { species: rootstock_species.scientific_name, family: rootstock_family.name, genus: rootstock_species.genus },
    same_genus: same_genus,
    same_family: same_family,
    compatibility: same_genus ? 'compatible' : (same_family ? 'possibly_compatible' : 'incompatible'),
    recommendation: same_genus
        ? "Gleiche Gattung — Veredelung empfohlen"
        : (same_family
            ? "Gleiche Familie — Veredelung möglich, aber Abstoßungsrisiko"
            : "Verschiedene Familien — Veredelung nicht empfohlen")
}
```

**6. PropagationBatch mit allen Events und Ergebnis-Pflanzen:**
```aql
LET batch = DOCUMENT('propagation_batches', @batch_key)

LET events = (
    FOR event IN propagation_events
        FOR edge IN part_of_batch
            FILTER edge._from == event._id AND edge._to == batch._id
            LET source = FIRST(
                FOR plant IN plant_instances
                    FOR se IN propagated_from
                        FILTER se._from == event._id AND se._to == plant._id
                        RETURN { key: plant._key, name: plant.name }
            )
            LET children = (
                FOR plant IN plant_instances
                    FOR re IN resulted_in
                        FILTER re._from == event._id AND re._to == plant._id
                        RETURN { key: plant._key, name: plant.name }
            )
            LET protocol = FIRST(
                FOR p IN rooting_protocols
                    FOR ue IN uses_protocol
                        FILTER ue._from == event._id AND ue._to == p._id
                        RETURN { key: p._key, name: p.name }
            )
            RETURN {
                event_key: event._key,
                event_type: event.event_type,
                performed_at: event.performed_at,
                quantity: event.quantity,
                survived_count: event.survived_count,
                success_rate: event.success_rate,
                source_plant: source,
                result_plants: children,
                protocol: protocol,
                callus_observed_at: event.callus_observed_at,
                roots_observed_at: event.roots_observed_at,
                transplant_ready_at: event.transplant_ready_at
            }
)

LET target_run = batch.target_planting_run_key != null
    ? DOCUMENT('planting_runs', batch.target_planting_run_key)
    : null

RETURN {
    batch: batch,
    events: events,
    total_events: LENGTH(events),
    total_quantity: SUM(events[*].quantity),
    total_survived: SUM(events[*].survived_count),
    target_run: target_run != null ? { key: target_run._key, name: target_run.name } : null
}
```

## 3. Technische Umsetzung

### Domänenmodelle:

```python
from datetime import datetime, date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class PropagationMethod(str, Enum):
    CUTTING = "cutting"
    LEAF_CUTTING = "leaf_cutting"       # Blattsteckling (Begonia, Sansevieria, Peperomia)
    STEM_SECTION = "stem_section"       # Stammstück ohne Blätter (Dracaena, Yucca)
    SEED_SOWING = "seed_sowing"
    DIVISION = "division"
    OFFSET = "offset"                   # Kindel/Ableger (Aloe, Haworthia, Pilea)
    LAYERING = "layering"
    AIR_LAYERING = "air_layering"       # Abmoosen (Ficus, Monstera)
    BULBIL = "bulbil"                   # Brutzwiebel/Brutknöllchen (Lilium, Chlorophytum)
    WATER_PROPAGATION = "water_propagation"  # Wasserbewurzelung (Pothos, Philodendron)
    GRAFTING = "grafting"
    TISSUE_CULTURE = "tissue_culture"


class CuttingType(str, Enum):
    """Differenzierung von Stecklingstypen — beeinflusst Hormonbedarf und Bewurzelungscharakteristik."""
    APICAL = "apical"               # Triebspitze — höchste natürliche Auxin-Konzentration
    NODAL = "nodal"                 # Mittlerer Stammabschnitt mit Nodium
    HEEL = "heel"                   # Fersensteckling — mit Stück des Hauptstamms
    SOFTWOOD = "softwood"           # Weichholz — junger, grüner Trieb
    SEMI_HARDWOOD = "semi_hardwood" # Halbverholzt — teilweise ausgereift
    HARDWOOD = "hardwood"           # Hartholz — vollständig verholzt, Ruhephase
    LEAF_PETIOLE = "leaf_petiole"   # Blatt mit Stiel (Peperomia, Begonia Rex)
    LEAF_SECTION = "leaf_section"   # Blattsegment (Sansevieria, Begonia)


class LightSpectrum(str, Enum):
    """Lichtspektrum für Bewurzelung — beeinflusst Wurzelinitiierung und Triebwachstum."""
    BLUE_DOMINANT = "blue_dominant"        # 400–500 nm — kompakter Wuchs, Stomata-Regulation
    RED_DOMINANT = "red_dominant"          # 600–700 nm — Streckungswachstum
    RED_BLUE_MIX = "red_blue_mix"         # Optimal für Bewurzelung (3:1 bis 4:1 R:B)
    FULL_SPECTRUM = "full_spectrum"        # Breitspektrum-LED/Tageslicht
    WARM_WHITE = "warm_white"             # 2700–3000K — hoher Rotanteil
    COOL_WHITE = "cool_white"             # 5000–6500K — hoher Blauanteil
    FLUORESCENT = "fluorescent"           # Leuchtstoffröhre (Standard-Propagation)


class ToolSterilizationMethod(str, Enum):
    """Sterilisationsmethode für Vermehrungswerkzeuge (IPM-Integration)."""
    ALCOHOL_70 = "alcohol_70"             # Isopropanol 70% — Standard
    FLAME = "flame"                       # Abflammen — Skalpell, Messer
    BLEACH_10 = "bleach_10"               # Natriumhypochlorit 10% — 10 Min Einwirkzeit
    H2O2 = "h2o2"                         # Wasserstoffperoxid 3%
    AUTOCLAVE = "autoclave"               # Autoklav — für Gewebekultur
    NONE = "none"                         # Keine Sterilisation dokumentiert


class VirusStatus(str, Enum):
    """Virusstatus einer Mutterpflanze — relevant für Vermehrungsentscheidung."""
    CLEAN = "clean"                       # Getestet und virusfrei
    UNTESTED = "untested"                 # Nicht getestet (Default)
    INFECTED = "infected"                 # Bekannt infiziert — Vermehrung erzeugt Warnung
    RECOVERED = "recovered"               # Symptome abgeklungen, latente Infektion möglich


class HormoneType(str, Enum):
    IBA = "iba"
    NAA = "naa"
    IBA_NAA_MIX = "iba_naa_mix"
    HONEY = "honey"
    WILLOW_WATER = "willow_water"
    NONE = "none"


class RootingMedium(str, Enum):
    ROCKWOOL = "rockwool"
    PERLITE = "perlite"
    VERMICULITE = "vermiculite"
    WATER = "water"
    AEROPONIC = "aeroponic"
    SOIL = "soil"
    COCO = "coco"
    PEAT = "peat"


class FailureReason(str, Enum):
    ROT = "rot"
    DESICCATION = "desiccation"
    NO_ROOTS = "no_roots"
    DAMPING_OFF = "damping_off"
    CONTAMINATION = "contamination"
    MECHANICAL_DAMAGE = "mechanical_damage"
    OTHER = "other"


class PropagationRelationship(str, Enum):
    CLONE = "clone"
    SEED_MOTHER = "seed_mother"
    SEED_FATHER = "seed_father"
    ROOTSTOCK = "rootstock"
    SCION = "scion"
    DIVISION = "division"


class MotherPriority(str, Enum):
    CRITICAL = "critical"       # einzige Quelle einer Genetik
    IMPORTANT = "important"     # wertvoller Phänotyp, Backup existiert
    STANDARD = "standard"       # reguläre Mutterpflanze


class PhenotypeCategory(str, Enum):
    MORPHOLOGY = "morphology"
    AROMA = "aroma"
    FLAVOR = "flavor"
    VIGOR = "vigor"
    RESISTANCE = "resistance"
    YIELD = "yield"
    POTENCY = "potency"
    OTHER = "other"


class GraftType(str, Enum):
    WHIP = "whip"              # Kopulationsschnitt
    CLEFT = "cleft"            # Spaltpfropfen
    APPROACH = "approach"      # Annäherungspfropfen
    BUD = "bud"                # Okulation


class BatchStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# --- Mutterpflanzen-Erweiterung auf PlantInstance ---

class MotherPlantConfig(BaseModel):
    """Zusätzliche Felder auf PlantInstance wenn is_mother=True"""

    is_mother: bool = False
    mother_priority: Optional[MotherPriority] = None
    mother_health_score: Optional[int] = Field(None, ge=0, le=100)
    mother_recovery_days: int = Field(default=14, ge=1, le=90,
        description="Mindestens N Tage Erholung zwischen Stecklingsentnahmen")
    mother_generation: int = Field(default=0, ge=0,
        description="Klonale Generation (0 = Sämling/Ur-Mutter). Zählt nur vegetative "
                    "Vermehrungszyklen. Generative Vermehrung (Aussaat) setzt auf 0 zurück "
                    "(neuer Genotyp, keine akkumulierte somatische Mutationslast).")
    mother_designated_at: Optional[datetime] = None
    mother_retired_at: Optional[datetime] = None
    mother_retire_reason: Optional[str] = None
    virus_status: VirusStatus = Field(
        default=VirusStatus.UNTESTED,
        description="Virusstatus der Mutterpflanze. Vermehrung von 'infected'-Pflanzen "
                    "erzeugt Warnung. Regelmäßige Tests empfohlen für 'critical'-Mütter."
    )

    @model_validator(mode='after')
    def validate_mother_fields(self):
        if self.is_mother:
            if self.mother_priority is None:
                self.mother_priority = MotherPriority.STANDARD
            if self.mother_designated_at is None:
                self.mother_designated_at = datetime.now()
        return self


# --- PropagationEvent ---

class PropagationEvent(BaseModel):
    """Einzelne Vermehrungsaktion — immutable nach Erstellung."""

    key: Optional[str] = Field(None, alias='_key')
    event_type: PropagationMethod
    cutting_type: Optional[CuttingType] = Field(
        None,
        description="Stecklingstyp — nur relevant bei event_type='cutting'. "
                    "Beeinflusst Hormonbedarf und Bewurzelungscharakteristik."
    )
    performed_at: datetime
    quantity: int = Field(ge=1, le=1000)
    survived_count: Optional[int] = Field(None, ge=0)
    success_rate: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Bewurzelungsparameter
    hormone_type: Optional[HormoneType] = None
    hormone_concentration_ppm: Optional[float] = Field(
        None, ge=0, le=10000,
        description="Hormon-Konzentration in ppm. Obergrenze 10.000 ppm (realistisches Maximum "
                    "für Hartholz-Long-Soak). Methodenspezifische Richtwerte: "
                    "Quick-Dip Weichholz: 500–1500 ppm IBA; "
                    "Quick-Dip Halbverholzt: 1000–3000 ppm IBA; "
                    "Long-Soak Hartholz: 50–200 ppm IBA (12–24h); "
                    "Powder: 1000–8000 ppm IBA. "
                    "Siehe HORMONE_RANGES in PropagationEngine für spezifische Validierung."
    )
    hormone_application_method: Optional[Literal['quick_dip', 'long_soak', 'powder', 'gel']] = Field(
        None,
        description="Applikationsmethode — bestimmt effektive Dosis. Quick-Dip 5s (weiche Stecklinge), Long-Soak 12-24h (verholzte), Powder/Gel (direkt)."
    )
    medium: Optional[RootingMedium] = None
    dome_humidity_percent: Optional[int] = Field(None, ge=0, le=100)
    air_temperature_celsius: Optional[float] = Field(
        None, ge=5, le=35,
        description="Lufttemperatur um den Steckling. Differenziert von Substrattemperatur (heat_mat). "
                    "Ideal: 2–5°C unter heat_mat_celsius (wärmeres Substrat fördert Wurzelbildung, "
                    "kühlere Luft reduziert Transpiration). Delta >8°C = Warnung."
    )
    heat_mat_celsius: Optional[float] = Field(
        None, ge=15, le=35,
        description="Substrattemperatur (Bottom Heat). Ideal 2–5°C über air_temperature_celsius."
    )
    target_vpd_kpa: Optional[float] = Field(
        None, ge=0.1, le=1.5,
        description="Ziel-VPD unter Dome — niedrig (0.3–0.5 kPa) für wurzellose Stecklinge. "
                    "Berechnet aus Temperatur + Luftfeuchtigkeit (REQ-005)."
    )
    light_ppfd: Optional[int] = Field(
        None, ge=0, le=300,
        description="Lichtintensität während Bewurzelung. Max 300 PPFD, "
                    "Warnung >150 PPFD unter Dome (Photoinhibition bei wurzellosen Stecklingen)."
    )
    light_spectrum: Optional[LightSpectrum] = Field(
        None,
        description="Lichtspektrum — blue_dominant fördert kompakten Wuchs, "
                    "red_blue_mix optimal für Bewurzelung."
    )
    photoperiod_hours: Optional[float] = Field(None, ge=0, le=24)

    # Substrat-Integration (REQ-019)
    substrate_batch_key: Optional[str] = Field(
        None,
        description="Referenz auf SubstrateBatch (REQ-019) für Rückverfolgbarkeit des Bewurzelungsmediums."
    )
    medium_ph: Optional[float] = Field(
        None, ge=3.0, le=8.0,
        description="pH-Wert des Bewurzelungsmediums (gemessen). "
                    "Steinwolle: 5.5–6.0 (vorgewässert), Torf: 5.5–6.5, Coco: 5.8–6.2."
    )
    medium_ec_ms: Optional[float] = Field(
        None, ge=0, le=5.0,
        description="EC des Bewurzelungsmediums in mS/cm (gemessen). "
                    "Ideal für Stecklinge: <0.5 mS (nährstoffarm)."
    )

    # IPM-Integration (REQ-010)
    tool_sterilization_method: Optional[ToolSterilizationMethod] = Field(
        None,
        description="Sterilisationsmethode der verwendeten Werkzeuge. "
                    "Dokumentation für Pathogen-Rückverfolgbarkeit."
    )
    quarantine_required: bool = Field(
        default=False,
        description="Ob die Vermehrungen unter Quarantäne gestellt werden sollen (14–21 Tage)."
    )
    quarantine_days: Optional[int] = Field(
        None, ge=1, le=90,
        description="Quarantäne-Dauer in Tagen (wenn quarantine_required=True)."
    )

    # Fortschritts-Tracking
    callus_observed_at: Optional[datetime] = None
    roots_observed_at: Optional[datetime] = None
    transplant_ready_at: Optional[datetime] = None

    # Ausfälle
    failure_reasons: list[FailureReason] = Field(default_factory=list)
    failure_count: int = Field(default=0, ge=0)

    notes: Optional[str] = Field(None, max_length=2000)
    photos: list[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def validate_success_rate(self):
        """Berechne Erfolgsrate wenn survived_count gesetzt."""
        if self.survived_count is not None:
            if self.survived_count > self.quantity:
                raise ValueError(
                    f"survived_count ({self.survived_count}) kann nicht "
                    f"größer als quantity ({self.quantity}) sein"
                )
            self.success_rate = round(self.survived_count / self.quantity, 3)
            self.failure_count = self.quantity - self.survived_count
        return self

    @model_validator(mode='after')
    def validate_timeline(self):
        """Zeitliche Reihenfolge: Kallus → Wurzeln → Transplant-Ready."""
        dates = [
            (self.callus_observed_at, "callus"),
            (self.roots_observed_at, "roots"),
            (self.transplant_ready_at, "transplant"),
        ]
        filled = [(d, name) for d, name in dates if d is not None]
        for i in range(len(filled) - 1):
            if filled[i][0] > filled[i + 1][0]:
                raise ValueError(
                    f"{filled[i][1]} ({filled[i][0]}) darf nicht nach "
                    f"{filled[i + 1][1]} ({filled[i + 1][0]}) liegen"
                )
        return self


# --- PropagationBatch ---

class PropagationBatch(BaseModel):
    """Gruppierung gleichzeitiger Vermehrungen."""

    key: Optional[str] = Field(None, alias='_key')
    name: str = Field(min_length=1, max_length=200)
    batch_type: PropagationMethod
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: BatchStatus = BatchStatus.IN_PROGRESS
    total_quantity: int = Field(ge=0, default=0)
    total_survived: Optional[int] = Field(None, ge=0)
    overall_success_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    target_planting_run_key: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=2000)


# --- RootingProtocol ---

class RootingProtocol(BaseModel):
    """Wiederverwendbare Bewurzelungs-Vorlage."""

    key: Optional[str] = Field(None, alias='_key')
    name: str = Field(min_length=1, max_length=200)
    method: PropagationMethod
    recommended_cutting_types: list[CuttingType] = Field(
        default_factory=list,
        description="Empfohlene Stecklingstypen für dieses Protokoll (nur bei method='cutting')."
    )
    recommended_species_keys: list[str] = Field(default_factory=list)
    medium: RootingMedium
    substrate_batch_key: Optional[str] = Field(
        None,
        description="Referenz auf SubstrateBatch (REQ-019) für Substrat-Rückverfolgbarkeit."
    )
    hormone_type: Optional[HormoneType] = None
    hormone_concentration_ppm: Optional[float] = Field(
        None, ge=0, le=10000,
        description="Obergrenze 10.000 ppm. Validierung gegen HORMONE_RANGES in PropagationEngine."
    )
    hormone_application_method: Optional[Literal['quick_dip', 'long_soak', 'powder', 'gel']] = None
    dome_humidity_percent: int = Field(ge=0, le=100)
    target_vpd_kpa: Optional[float] = Field(
        None, ge=0.1, le=1.5,
        description="Ziel-VPD unter Dome — niedrig (0.3-0.5 kPa) für Stecklinge ohne Wurzeln. "
                    "Berechnet aus air_temperature + dome_humidity (Tetens-Formel, REQ-005)."
    )
    air_temperature_celsius: Optional[float] = Field(
        None, ge=5, le=35,
        description="Ziel-Lufttemperatur. Ideal: 2–5°C unter heat_mat_celsius."
    )
    heat_mat_celsius: Optional[float] = Field(
        None, ge=15, le=35,
        description="Substrattemperatur (Bottom Heat). Ideal 2–5°C über air_temperature_celsius. "
                    "Delta >8°C = Warnung im Service."
    )
    light_ppfd: int = Field(
        ge=0, le=300,
        description="Lichtintensität. Max 300 PPFD. Warnung >150 PPFD unter Dome "
                    "(Photoinhibition bei wurzellosen Stecklingen)."
    )
    light_spectrum: Optional[LightSpectrum] = Field(
        None,
        description="Empfohlenes Lichtspektrum. red_blue_mix optimal für Bewurzelung."
    )
    photoperiod_hours: float = Field(ge=0, le=24)
    expected_callus_days: Optional[int] = Field(None, ge=1, le=60)
    expected_root_days: int = Field(ge=1, le=120)
    expected_transplant_days: int = Field(ge=1, le=180)
    instructions: str = Field(min_length=1, max_length=5000)
    is_template: bool = False
    author: str = Field(min_length=1, max_length=100)

    @model_validator(mode='after')
    def validate_timeline_order(self):
        if self.expected_callus_days is not None:
            if self.expected_callus_days >= self.expected_root_days:
                raise ValueError(
                    "expected_callus_days muss vor expected_root_days liegen"
                )
        if self.expected_root_days >= self.expected_transplant_days:
            raise ValueError(
                "expected_root_days muss vor expected_transplant_days liegen"
            )
        return self

    @model_validator(mode='after')
    def validate_bottom_heat_delta(self):
        """Warnung wenn Temperatur-Delta zwischen Substrat und Luft >8°C."""
        if (self.heat_mat_celsius is not None
                and self.air_temperature_celsius is not None):
            delta = self.heat_mat_celsius - self.air_temperature_celsius
            if delta > 8:
                raise ValueError(
                    f"Temperaturgradient Substrat→Luft {delta:.1f}°C ist >8°C — "
                    f"Stress durch extremen Temperaturgradient. Empfohlen: 2–5°C."
                )
            if delta < 0:
                raise ValueError(
                    "Bottom Heat (heat_mat_celsius) sollte gleich oder wärmer "
                    "als Lufttemperatur (air_temperature_celsius) sein."
                )
        return self


# --- PhenotypeNote ---

class PhenotypeNote(BaseModel):
    """Phänotyp-Beobachtung an einer Pflanze."""

    key: Optional[str] = Field(None, alias='_key')
    recorded_at: datetime
    category: PhenotypeCategory
    trait: str = Field(min_length=1, max_length=500)
    rating: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = Field(None, max_length=2000)
    photos: list[str] = Field(default_factory=list)
```

### Engines:

**1. PropagationEngine — Vermehrungs-Logik:**
```python
class PropagationEngine:
    """Fachlogik für Vermehrungsaktionen."""

    # Mindest-Erholungszeit nach Stecklingnahme — methodenspezifisch (Tage)
    # Verschiedene Entnahme-Methoden belasten die Mutterpflanze unterschiedlich stark
    RECOVERY_DAYS_BY_METHOD: dict[str, int] = {
        "cutting": 14,          # Steckling — moderater Stress
        "leaf_cutting": 7,      # Blattsteckling — minimaler Stress
        "stem_section": 21,     # Stammstück — starker Stress (Stamm wird geschnitten)
        "division": 21,         # Teilung — starker Stress (Wurzelstörung)
        "offset": 7,            # Kindel — minimaler Stress (natürlich abgetrennt)
        "layering": 7,          # Absenker — minimaler Stress (an Pflanze bewurzelt)
        "air_layering": 14,     # Abmoosen — moderater Stress (Rindenentfernung)
        "bulbil": 7,            # Brutzwiebel — minimaler Stress
        "water_propagation": 14, # Wasserbewurzelung — wie cutting
        "grafting": 28,         # Veredelung — starker Stress (Wundheilung)
        "tissue_culture": 14,   # Gewebekultur — moderater Stress
        "seed_sowing": 0,       # Aussaat — kein Stress für Mutterpflanze
    }

    # Fallback: Spezies-spezifische Erholungszeiten (wenn method-based nicht differenziert)
    DEFAULT_RECOVERY_DAYS: dict[str, int] = {
        "cannabis": 14,
        "tomato": 10,
        "basil": 7,
        "default": 14,
    }

    # Empfohlene Stecklingsanzahl pro Entnahme (relativ zur Pflanzengröße)
    MAX_CUTTINGS_PER_SESSION: dict[str, int] = {
        "cannabis": 8,
        "tomato": 6,
        "basil": 10,
        "default": 6,
    }

    # Somatische Mutationen akkumulieren bei vegetativer Vermehrung —
    # "genetische Drift" ist populationsgenetisch und hier fachlich inkorrekt.
    SOMATIC_MUTATION_WARNING_GENERATION = 10  # Konfigurierbar pro Spezies

    # Hormon-Konzentrationsbereiche nach Methode und Stecklingstyp (ppm)
    # Validierung: Warnung bei Überschreitung, Fehler bei extremer Überschreitung (>2x obere Grenze)
    HORMONE_RANGES: dict[str, dict[str, tuple[float, float]]] = {
        # method_or_cutting_type: {hormone_application_method: (min_ppm, max_ppm)}
        "softwood": {
            "quick_dip": (500, 1500),
            "powder": (500, 2000),
            "gel": (500, 2000),
        },
        "semi_hardwood": {
            "quick_dip": (1000, 3000),
            "powder": (1000, 4000),
            "gel": (1000, 4000),
        },
        "hardwood": {
            "quick_dip": (2000, 5000),
            "long_soak": (50, 200),  # Niedrige Konzentration, lange Einwirkzeit
            "powder": (3000, 8000),
            "gel": (3000, 8000),
        },
        "apical": {
            "quick_dip": (500, 2000),
            "powder": (500, 2500),
            "gel": (500, 2500),
        },
        "nodal": {
            "quick_dip": (1000, 3000),
            "powder": (1000, 3000),
            "gel": (1000, 3000),
        },
        "heel": {
            "quick_dip": (1000, 3000),
            "powder": (1000, 4000),
            "gel": (1000, 4000),
        },
        "leaf_petiole": {
            "powder": (500, 1500),
            "gel": (500, 1500),
        },
        "leaf_section": {
            "powder": (500, 1500),
            "gel": (500, 1500),
        },
        # Default-Fallback für unbekannte Typen
        "default": {
            "quick_dip": (500, 3000),
            "long_soak": (50, 200),
            "powder": (1000, 5000),
            "gel": (1000, 5000),
        },
    }

    def validate_hormone_concentration(
        self,
        concentration_ppm: float,
        cutting_type: Optional[str],
        application_method: Optional[str],
    ) -> list[str]:
        """
        Validiert Hormon-Konzentration gegen typspezifische Bereiche.
        Returns: Liste von Warnungen.
        """
        warnings: list[str] = []
        if application_method is None:
            return warnings

        ranges = self.HORMONE_RANGES.get(
            cutting_type or 'default',
            self.HORMONE_RANGES['default']
        )
        method_range = ranges.get(application_method)
        if method_range is None:
            return warnings

        min_ppm, max_ppm = method_range
        if concentration_ppm < min_ppm:
            warnings.append(
                f"Hormon-Konzentration {concentration_ppm} ppm unter empfohlenem "
                f"Minimum ({min_ppm} ppm) für {cutting_type or 'Standard'}/{application_method}"
            )
        elif concentration_ppm > max_ppm:
            warnings.append(
                f"Hormon-Konzentration {concentration_ppm} ppm über empfohlenem "
                f"Maximum ({max_ppm} ppm) für {cutting_type or 'Standard'}/{application_method}. "
                f"Toxizitätsrisiko!"
            )
        if concentration_ppm > max_ppm * 2:
            warnings.append(
                f"KRITISCH: {concentration_ppm} ppm ist >2x obere Grenze ({max_ppm} ppm) — "
                f"extreme Toxizitätsgefahr (Kallusnekrose, Stecklingstod)"
            )
        return warnings

    def validate_cutting_from_mother(
        self,
        mother: dict,
        quantity: int,
        last_cutting_event: Optional[dict],
        event_type: str = 'cutting',
    ) -> list[str]:
        """
        Prüft ob Stecklingsnahme von Mutterpflanze zulässig ist.
        Returns: Liste von Warnungen (leer = OK, nicht-leer = Warnungen/Fehler).
        """
        warnings: list[str] = []

        if not mother.get('is_mother'):
            warnings.append(
                "Pflanze ist nicht als Mutterpflanze markiert — "
                "Stecklingsnahme trotzdem möglich, aber empfohlen zuerst zu designieren"
            )

        # Erholungszeit prüfen (methodenspezifisch)
        if last_cutting_event:
            from datetime import datetime
            last_date = last_cutting_event['performed_at']
            # Methodenspezifische Recovery-Zeit hat Vorrang vor Mutterpflanzen-Default
            method_recovery = self.RECOVERY_DAYS_BY_METHOD.get(event_type, 14)
            mother_recovery = mother.get('mother_recovery_days', 14)
            recovery_days = max(method_recovery, mother_recovery)
            days_since = (datetime.now() - last_date).days
            if days_since < recovery_days:
                warnings.append(
                    f"Erholungszeit nicht eingehalten: {days_since} von "
                    f"{recovery_days} Tagen seit letzter Entnahme "
                    f"(Methode '{event_type}': {method_recovery}d, "
                    f"Mutterpflanze: {mother_recovery}d)"
                )

        # Virusstatus prüfen (IPM-Integration)
        virus_status = mother.get('virus_status', 'untested')
        if virus_status == 'infected':
            warnings.append(
                "WARNUNG: Mutterpflanze ist als virusinfiziert markiert. "
                "Vermehrung überträgt Viren auf alle Nachkommen. "
                "Werkzeugsterilisation und Quarantäne dringend empfohlen."
            )
        elif virus_status == 'untested' and mother.get('mother_priority') == 'critical':
            warnings.append(
                "Mutterpflanze mit Priorität 'critical' hat Status 'untested'. "
                "Virustest empfohlen vor weiterer Vermehrung."
            )

        # Gesundheit prüfen
        health = mother.get('mother_health_score')
        if health is not None and health < 50:
            warnings.append(
                f"Mutterpflanzen-Gesundheit kritisch niedrig ({health}/100) — "
                f"Stecklingnahme kann Pflanze weiter schwächen"
            )

        # Generationswarnung
        generation = mother.get('mother_generation', 0)
        if generation >= self.SOMATIC_MUTATION_WARNING_GENERATION:
            warnings.append(
                f"Generation {generation} — somatische Mutationslast erhöht. "
                f"Empfehlung: Neue Mutterpflanze aus Samen ziehen"
            )

        # Menge prüfen
        max_cuttings = self.MAX_CUTTINGS_PER_SESSION.get(
            mother.get('species_common', 'default'), 6
        )
        if quantity > max_cuttings:
            warnings.append(
                f"Empfohlenes Maximum pro Entnahme: {max_cuttings} Stecklinge "
                f"(angefordert: {quantity})"
            )

        # Retirement-Status
        if mother.get('mother_retired_at') is not None:
            warnings.append(
                "Mutterpflanze ist bereits als retired markiert"
            )

        return warnings

    def calculate_generation(
        self,
        mother_generation: int,
        method: str,
    ) -> tuple[int, str]:
        """
        Berechnet die Generation der Nachkommen.

        Vegetative Vermehrung (clone, division, etc.): Inkrementiert die
        Klongeneration — zählt Vermehrungszyklen für somatische Mutationslast.
        Gleicher Genotyp wie Mutter.

        Generative Vermehrung (seed_sowing): Setzt auf F1 (filial generation 1)
        zurück — neuer Genotyp durch Rekombination. Nicht vergleichbar mit
        klonaler Generationszählung.

        Returns:
            (generation, generation_type) — generation_type ist 'clonal' oder 'filial'
        """
        vegetative_methods = (
            'cutting', 'leaf_cutting', 'stem_section', 'division',
            'offset', 'layering', 'air_layering', 'bulbil',
            'water_propagation', 'tissue_culture',
        )
        if method in vegetative_methods:
            return mother_generation + 1, 'clonal'
        elif method == 'seed_sowing':
            # Generative Vermehrung: F1-Generation (neuer Genotyp)
            # Klonale Mutationslast wird zurückgesetzt
            return 1, 'filial'
        elif method == 'grafting':
            # Edelreis behält seine Generation, Unterlage zählt nicht
            return mother_generation, 'clonal'
        return mother_generation + 1, 'clonal'

    def check_graft_compatibility(
        self,
        scion_species: dict,
        rootstock_species: dict,
        scion_family_key: str,
        rootstock_family_key: str,
        explicit_edge: Optional[dict] = None,
    ) -> dict:
        """
        Prüft Veredelungskompatibilität.
        1. Explizite graft_compatible_with-Edge (Vorrang)
        2. Taxonomie-Heuristik (Fallback)
        Returns: {compatible: bool, level: str, message: str, source: str}
        """
        # 1. Explizite Graph-Edge prüfen (praxisbewährte Kombination)
        if explicit_edge is not None:
            success_rate = explicit_edge.get('success_rate', 0)
            return {
                'compatible': success_rate > 0.5,
                'level': 'proven' if success_rate > 0.8 else 'experimental',
                'message': (
                    f"Bekannte Kombination — Erfolgsrate: {success_rate*100:.0f}%. "
                    f"{explicit_edge.get('notes', '')}"
                ),
                'source': 'explicit_edge',
            }

        # 2. Taxonomie-Heuristik (Fallback)
        same_genus = scion_species.get('genus') == rootstock_species.get('genus')
        same_family = scion_family_key == rootstock_family_key

        if same_genus:
            return {
                'compatible': True,
                'level': 'compatible',
                'message': (
                    f"Gleiche Gattung ({scion_species['genus']}) — "
                    f"Veredelung wahrscheinlich kompatibel (taxonomische Heuristik)"
                ),
                'source': 'taxonomy_heuristic',
            }
        elif same_family:
            return {
                'compatible': True,
                'level': 'possibly_compatible',
                'message': (
                    f"Gleiche Familie — Veredelung möglich, "
                    f"aber Abstoßungsrisiko erhöht (keine explizite Erfahrungsdaten)"
                ),
                'source': 'taxonomy_heuristic',
            }
        else:
            return {
                'compatible': False,
                'level': 'incompatible',
                'message': (
                    f"Verschiedene Familien "
                    f"({scion_family_key} vs. {rootstock_family_key}) — "
                    f"Veredelung nicht empfohlen"
                ),
                'source': 'taxonomy_heuristic',
            }

    def suggest_retirement(
        self,
        mother: dict,
        cutting_events: list[dict],
    ) -> Optional[str]:
        """Prüft ob Mutterpflanze zur Ablösung empfohlen wird."""
        health = mother.get('mother_health_score', 100)
        if health < 30:
            return f"Gesundheit kritisch ({health}/100) — Ablösung dringend empfohlen"

        # Sinkende Erfolgsrate über die letzten 5 Entnahmen
        if len(cutting_events) >= 5:
            recent = cutting_events[:5]  # neueste zuerst
            rates = [e['success_rate'] for e in recent if e.get('success_rate') is not None]
            if len(rates) >= 3:
                # Trend: letzte 3 vs. vorherige
                recent_avg = sum(rates[:3]) / 3
                if recent_avg < 0.5:
                    return (
                        f"Durchschnittliche Erfolgsrate der letzten 3 Entnahmen "
                        f"nur {recent_avg:.0%} — Ablösung empfohlen"
                    )

        generation = mother.get('mother_generation', 0)
        if generation >= 15:
            return (
                f"Generation {generation} — hohes Risiko für somatische Mutationslast. "
                f"Neue Mutterpflanze aus Samen empfohlen"
            )

        return None
```

**2. LineageEngine — Abstammungs-Berechnung:**
```python
class LineageEngine:
    """Berechnet genetische Abstammung und Verwandtschaft."""

    def build_lineage_tree(
        self,
        descendant_edges: list[dict],
        target_plant_key: str,
    ) -> dict:
        """Baut Stammbaum aus descended_from-Edges."""
        tree = {'key': target_plant_key, 'parents': [], 'generation': 0}

        parent_map: dict[str, list[dict]] = {}
        for edge in descendant_edges:
            child = edge['_from'].split('/')[1]
            parent = edge['_to'].split('/')[1]
            parent_map.setdefault(child, []).append({
                'key': parent,
                'relationship': edge.get('relationship'),
                'generation': edge.get('generation', 0),
            })

        def _build(node_key: str, depth: int = 0) -> dict:
            node = {'key': node_key, 'parents': [], 'depth': depth}
            for parent in parent_map.get(node_key, []):
                parent_node = _build(parent['key'], depth + 1)
                parent_node['relationship'] = parent['relationship']
                parent_node['generation'] = parent['generation']
                node['parents'].append(parent_node)
            return node

        return _build(target_plant_key)

    def calculate_relatedness_estimate(
        self,
        lineage_tree: dict,
    ) -> float:
        """
        Schätzt die Verwandtschaftsnähe basierend auf wiederkehrenden
        Vorfahren in der Abstammungslinie. Höherer Wert = mehr gemeinsame Vorfahren.

        HINWEIS: Dies ist eine vereinfachte Heuristik auf Basis der Graph-Struktur,
        KEIN biologisch korrekter Inzuchtkoeffizient (Wright's F). Ein korrekter
        Inzuchtkoeffizient erfordert vollständige Pedigree-Daten mit bekannten
        Allel-Segregationsmustern, die in diesem System nicht vorliegen.
        Der Wert dient als Annäherung für Zuchtentscheidungen.

        Returns:
            float (0.0–1.0): Anteil wiederkehrender Vorfahren an Gesamtvorfahren.
            0.0 = keine gemeinsamen Vorfahren, >0.3 = erhöhte Verwandtschaft.
        """
        ancestors: dict[str, int] = {}

        def _collect(node: dict) -> None:
            for parent in node.get('parents', []):
                key = parent['key']
                ancestors[key] = ancestors.get(key, 0) + 1
                _collect(parent)

        _collect(lineage_tree)
        repeated = sum(1 for count in ancestors.values() if count > 1)
        total = sum(ancestors.values())
        if total == 0:
            return 0.0
        return round(repeated / total, 3)
```

### Datenvalidierung:

```python
class CuttingRequestValidator(BaseModel):
    """Validiert eine Stecklingnahme-Anfrage."""

    mother_plant_key: str
    quantity: int = Field(ge=1, le=100)
    protocol_key: Optional[str] = None

    @model_validator(mode='after')
    def validate_quantity(self):
        if self.quantity > 20:
            # Kein Fehler, aber Service gibt Warnung
            pass
        return self


class GraftRequestValidator(BaseModel):
    """Validiert eine Veredelungs-Anfrage."""

    scion_plant_key: str
    rootstock_plant_key: str
    graft_type: GraftType

    @model_validator(mode='after')
    def validate_different_plants(self):
        if self.scion_plant_key == self.rootstock_plant_key:
            raise ValueError("Edelreis und Unterlage müssen verschiedene Pflanzen sein")
        return self


class SeedSowingRequestValidator(BaseModel):
    """Validiert eine Aussaat-Anfrage."""

    quantity: int = Field(ge=1, le=1000)
    species_key: str
    cultivar_key: Optional[str] = None
    mother_plant_key: Optional[str] = None  # Mutterpflanze, wenn Samen selbst geerntet
    father_plant_key: Optional[str] = None  # Vaterpflanze bei gezielter Kreuzung
    protocol_key: Optional[str] = None
```

### REST-API-Endpunkte:
```
# Vermehrungsevents
POST   /api/v1/propagation/events                            — Vermehrungsaktion dokumentieren
GET    /api/v1/propagation/events                            — Alle Events (Filter: method, status, date range)
GET    /api/v1/propagation/events/{event_key}                — Event-Details mit Quell-/Ergebnis-Pflanzen
PATCH  /api/v1/propagation/events/{event_key}/outcome        — Ergebnis nachtragen (survived_count, failure_reasons)
PATCH  /api/v1/propagation/events/{event_key}/progress       — Fortschritt aktualisieren (callus/roots/transplant dates)

# Vermehrungsbatches
POST   /api/v1/propagation/batches                           — Batch erstellen
GET    /api/v1/propagation/batches                           — Alle Batches (Filter: status, method)
GET    /api/v1/propagation/batches/{batch_key}               — Batch-Details mit allen Events und Ergebnis-Pflanzen
PATCH  /api/v1/propagation/batches/{batch_key}               — Batch aktualisieren (status, completed_at)
POST   /api/v1/propagation/batches/{batch_key}/finalize      — Batch abschließen, Pflanzen an PlantingRun übergeben

# Bewurzelungsprotokolle
POST   /api/v1/propagation/protocols                         — Protokoll erstellen
GET    /api/v1/propagation/protocols                         — Alle Protokolle (Filter: method, is_template)
GET    /api/v1/propagation/protocols/{protocol_key}          — Protokoll-Details mit Erfolgsstatistiken
PUT    /api/v1/propagation/protocols/{protocol_key}          — Protokoll aktualisieren
DELETE /api/v1/propagation/protocols/{protocol_key}          — Protokoll löschen (nur wenn nicht in Verwendung)
GET    /api/v1/propagation/protocols/{protocol_key}/stats    — Erfolgsraten pro Species für dieses Protokoll

# Mutterpflanzen
GET    /api/v1/propagation/mothers                           — Alle Mutterpflanzen mit Gesundheit und Stecklingshistorie
GET    /api/v1/propagation/mothers/{plant_key}               — Mutterpflanzen-Detail (Historie, Erfolgsraten, Retirement-Empfehlung)
PATCH  /api/v1/propagation/mothers/{plant_key}/designate     — Pflanze als Mutterpflanze markieren
PATCH  /api/v1/propagation/mothers/{plant_key}/retire        — Mutterpflanze als retired markieren
PATCH  /api/v1/propagation/mothers/{plant_key}/health        — Gesundheitsbewertung aktualisieren

# Abstammung / Lineage
GET    /api/v1/plant-instances/{plant_key}/lineage           — Abstammungslinie (Vorfahren, Graph-Traversal)
GET    /api/v1/plant-instances/{plant_key}/descendants       — Alle Nachkommen (Klon-Baum)
GET    /api/v1/propagation/graft-compatibility               — Veredelungs-Kompatibilitätsprüfung (Query: scion_key, rootstock_key)

# Phänotyp-Notizen
POST   /api/v1/plant-instances/{plant_key}/phenotypes        — Phänotyp-Notiz hinzufügen
GET    /api/v1/plant-instances/{plant_key}/phenotypes        — Alle Phänotyp-Notizen einer Pflanze
DELETE /api/v1/plant-instances/{plant_key}/phenotypes/{note_key} — Notiz löschen

# Statistiken
GET    /api/v1/propagation/stats                             — Gesamtstatistik (Erfolgsraten per Method, Species, Protocol)
GET    /api/v1/propagation/stats/by-cultivar                 — Erfolgsraten gruppiert nach Cultivar
GET    /api/v1/propagation/stats/by-protocol                 — Erfolgsraten gruppiert nach Protokoll
```

### Seed-Daten:
```json
// rooting_protocols collection (10 Protokolle für verschiedene Pflanzenkategorien)

// --- Nutzpflanzen / Grow ---
{ "_key": "proto_cannabis_std", "name": "Cannabis Steckling Standard", "method": "cutting", "recommended_cutting_types": ["apical", "nodal"], "recommended_species_keys": ["cannabis_sativa"], "medium": "rockwool", "hormone_type": "iba", "hormone_concentration_ppm": 1000, "hormone_application_method": "powder", "dome_humidity_percent": 85, "target_vpd_kpa": 0.4, "air_temperature_celsius": 20.0, "heat_mat_celsius": 22.0, "light_ppfd": 100, "light_spectrum": "cool_white", "photoperiod_hours": 18.0, "expected_callus_days": 5, "expected_root_days": 10, "expected_transplant_days": 14, "instructions": "1. Triebspitze mit 2-3 Nodien schneiden (45° Winkel, steriles Skalpell)\n2. Untere Blätter entfernen, obere halbieren (Transpirationsreduktion)\n3. Schnittstelle in IBA-Pulver (1000 ppm) tauchen\n4. In vorgewässerten Steinwollwürfel stecken\n5. Unter Dome bei 85% RLF, 20°C Luft / 22°C Substrat, 100 PPFD\n6. Täglich lüften (2 Min), ab Tag 5 Dome-Öffnung vergrößern\n7. Ab Tag 7 RLF schrittweise auf 70% senken\n8. Wurzeln sichtbar → 2 Tage akklimatisieren → transplant", "is_template": true, "author": "system" }

{ "_key": "proto_tomato_rockwool", "name": "Tomate Steinwolle Rapid", "method": "cutting", "recommended_cutting_types": ["apical", "softwood"], "recommended_species_keys": ["solanum_lycopersicum"], "medium": "rockwool", "hormone_type": "none", "hormone_concentration_ppm": null, "dome_humidity_percent": 80, "target_vpd_kpa": 0.5, "air_temperature_celsius": 22.0, "heat_mat_celsius": 24.0, "light_ppfd": 150, "light_spectrum": "full_spectrum", "photoperiod_hours": 16.0, "expected_callus_days": 3, "expected_root_days": 7, "expected_transplant_days": 10, "instructions": "1. Seitentrieb (Geiztrieb) mit 10-15 cm abschneiden\n2. Untere Blätter entfernen\n3. Direkt in Steinwolle — kein Hormon nötig (Tomaten bilden leicht Adventivwurzeln)\n4. Unter Dome bei 80% RLF, 22°C Luft / 24°C Substrat\n5. Ab Tag 3 Dome öffnen\n6. Tag 7: Wurzeln sichtbar → transplant", "is_template": true, "author": "system" }

{ "_key": "proto_basil_water", "name": "Basilikum Wasserglas", "method": "water_propagation", "recommended_species_keys": ["ocimum_basilicum"], "medium": "water", "hormone_type": "none", "hormone_concentration_ppm": null, "dome_humidity_percent": 70, "air_temperature_celsius": 22.0, "heat_mat_celsius": null, "light_ppfd": 200, "light_spectrum": "full_spectrum", "photoperiod_hours": 16.0, "expected_callus_days": null, "expected_root_days": 5, "expected_transplant_days": 10, "instructions": "1. Triebspitze oberhalb eines Nodiums schneiden\n2. Untere Blätter entfernen\n3. In Glas mit Wasser stellen (Stängel 3-4 cm unter Wasser)\n4. Wasser alle 2 Tage wechseln\n5. Bei Raumtemperatur und hellem Standort\n6. Tag 5: Wurzeln 2-3 cm → 2 Tage in Erde akklimatisieren (anfangs feucht halten)", "is_template": true, "author": "system" }

// --- Zimmerpflanzen ---
{ "_key": "proto_pothos_water", "name": "Pothos/Philodendron Wasserbewurzelung", "method": "water_propagation", "recommended_species_keys": ["epipremnum_aureum", "philodendron_hederaceum"], "medium": "water", "hormone_type": "none", "hormone_concentration_ppm": null, "dome_humidity_percent": 60, "air_temperature_celsius": 22.0, "heat_mat_celsius": null, "light_ppfd": 100, "light_spectrum": "warm_white", "photoperiod_hours": 12.0, "expected_callus_days": null, "expected_root_days": 7, "expected_transplant_days": 21, "instructions": "1. Steckling mit mindestens 1 Nodium und Luftwurzel abschneiden\n2. In Glas mit Wasser stellen, Nodium unter Wasser\n3. Wasser wöchentlich wechseln, heller Standort ohne direkte Sonne\n4. Wurzeln ab ca. Tag 7, transplant wenn Wurzeln 5-8 cm lang\n5. Beim Einpflanzen: Erde anfangs feucht halten (Akklimatisierung Water→Soil)", "is_template": true, "author": "system" }

{ "_key": "proto_sansevieria_leaf", "name": "Sansevieria Blattsteckling", "method": "leaf_cutting", "recommended_species_keys": ["sansevieria_trifasciata"], "medium": "perlite", "hormone_type": "iba", "hormone_concentration_ppm": 500, "hormone_application_method": "powder", "dome_humidity_percent": 50, "air_temperature_celsius": 22.0, "heat_mat_celsius": 24.0, "light_ppfd": 80, "light_spectrum": "warm_white", "photoperiod_hours": 12.0, "expected_callus_days": 14, "expected_root_days": 30, "expected_transplant_days": 60, "instructions": "1. Gesundes Blatt nahe der Basis abschneiden\n2. In 8-10 cm Segmente teilen, Polarität markieren (unten/oben)!\n3. 24h antrocknen lassen (Wundverschluss)\n4. Unteres Ende in IBA-Pulver (500 ppm) tauchen\n5. Aufrecht in feuchtes Perlit stecken (3 cm tief)\n6. Sparsam gießen — Fäulnis ist Hauptausfallursache\n7. Geduld: Wurzeln nach 4 Wochen, Baby-Pflanze nach 8-12 Wochen\nHINWEIS: Variegate Sorten verlieren bei Blattstecklingen ihre Musterung — Teilung bevorzugen!", "is_template": true, "author": "system" }

{ "_key": "proto_monstera_airlayer", "name": "Monstera Abmoosen", "method": "air_layering", "recommended_species_keys": ["monstera_deliciosa"], "medium": "peat", "hormone_type": "iba", "hormone_concentration_ppm": 1000, "hormone_application_method": "powder", "dome_humidity_percent": 80, "air_temperature_celsius": 22.0, "heat_mat_celsius": null, "light_ppfd": 100, "light_spectrum": "full_spectrum", "photoperiod_hours": 12.0, "expected_callus_days": 7, "expected_root_days": 21, "expected_transplant_days": 35, "instructions": "1. Stelle mit Luftwurzel und Nodium wählen\n2. Unterhalb des Nodiums Rinde ringförmig entfernen (2 cm)\n3. Optional: IBA-Pulver auf freiliegendes Kambium auftragen\n4. Mit feuchtem Sphagnum-Moos umwickeln (Tennisball-Größe)\n5. In transparente Frischhaltefolie einwickeln, oben+unten verschließen\n6. Wöchentlich kontrollieren, Moos nachfeuchten wenn nötig\n7. Bei sichtbaren Wurzeln durch die Folie: unterhalb abschneiden und einpflanzen", "is_template": true, "author": "system" }

{ "_key": "proto_aloe_offset", "name": "Aloe/Haworthia Kindel-Abtrennung", "method": "offset", "recommended_species_keys": ["aloe_vera", "haworthia_fasciata"], "medium": "soil", "hormone_type": "none", "hormone_concentration_ppm": null, "dome_humidity_percent": 40, "air_temperature_celsius": 22.0, "heat_mat_celsius": null, "light_ppfd": 150, "light_spectrum": "full_spectrum", "photoperiod_hours": 12.0, "expected_callus_days": null, "expected_root_days": 3, "expected_transplant_days": 7, "instructions": "1. Mutterpflanze austopfen und vorsichtig Erde entfernen\n2. Kindel mit eigenen Wurzeln identifizieren (mind. 3-4 cm groß)\n3. Mit sauberer Klinge abtrennen, möglichst mit eigenen Wurzeln\n4. Schnittstelle 24h antrocknen lassen\n5. In durchlässiges Substrat (50% Kakteenerde, 50% Perlit) pflanzen\n6. Erst nach 3-5 Tagen vorsichtig angießen\n7. Heller Standort ohne direkte Sonne bis etabliert", "is_template": true, "author": "system" }

// --- Verholzte Pflanzen ---
{ "_key": "proto_rose_hardwood", "name": "Rose Hartholz-Steckling Winter", "method": "cutting", "recommended_cutting_types": ["hardwood", "heel"], "recommended_species_keys": ["rosa_spp"], "medium": "soil", "hormone_type": "iba", "hormone_concentration_ppm": 3000, "hormone_application_method": "powder", "dome_humidity_percent": 70, "air_temperature_celsius": 10.0, "heat_mat_celsius": 15.0, "light_ppfd": 50, "light_spectrum": "cool_white", "photoperiod_hours": 8.0, "expected_callus_days": 30, "expected_root_days": 60, "expected_transplant_days": 90, "instructions": "1. Im Spätherbst/Winter ausgereifte, bleistiftdicke Triebe schneiden (20-25 cm)\n2. Schrägschnitt unten unter einem Auge, gerader Schnitt oben über einem Auge\n3. Unterste 3 cm in IBA-Pulver (3000 ppm) tauchen\n4. In sandige Erde stecken (2/3 unter der Oberfläche)\n5. Frostfrei, aber kühl überwintern (5-10°C)\n6. Im Frühjahr: langsam ans Licht gewöhnen\n7. Bewurzelung dauert 2-3 Monate — Geduld!", "is_template": true, "author": "system" }

{ "_key": "proto_strawberry_runner", "name": "Erdbeere Ableger/Ausläufer", "method": "layering", "recommended_species_keys": ["fragaria_ananassa"], "medium": "soil", "hormone_type": "none", "hormone_concentration_ppm": null, "dome_humidity_percent": 60, "air_temperature_celsius": 20.0, "heat_mat_celsius": null, "light_ppfd": 200, "light_spectrum": "full_spectrum", "photoperiod_hours": 14.0, "expected_callus_days": null, "expected_root_days": 14, "expected_transplant_days": 21, "instructions": "1. Ausläufer (Stolon) mit Kindel-Rosette identifizieren\n2. Kleinen Topf mit feuchter Erde neben Mutterpflanze stellen\n3. Kindel auf den Topf drücken und mit Drahtbügel fixieren\n4. Nicht von Mutterpflanze trennen!\n5. Feucht halten, nach 2 Wochen Wurzeln prüfen\n6. Wenn gut bewurzelt: Ausläufer-Nabelschnur durchtrennen\n7. 1 Woche an Originalstandort akklimatisieren, dann umsetzen", "is_template": true, "author": "system" }

// --- Generisch ---
{ "_key": "proto_seed_general", "name": "Standard-Aussaat Indoor", "method": "seed_sowing", "recommended_species_keys": [], "medium": "peat", "hormone_type": "none", "hormone_concentration_ppm": null, "dome_humidity_percent": 90, "air_temperature_celsius": 22.0, "heat_mat_celsius": 22.0, "light_ppfd": 50, "light_spectrum": "warm_white", "photoperiod_hours": 18.0, "expected_callus_days": null, "expected_root_days": 5, "expected_transplant_days": 21, "instructions": "1. Saatgut 12h in lauwarmem Wasser vorquellen (optional)\n2. In feuchtes Anzuchtsubstrat drücken (Tiefe: 2x Samendurchmesser)\n3. Dome schließen, 90% RLF\n4. Wärmematte auf 22°C\n5. Kein direktes Licht bis Keimung\n6. Nach Keimung: Dome schrittweise öffnen, Licht auf 50 PPFD\n7. Erste echte Blätter → transplant", "is_template": true, "author": "system" }

// propagation_batches collection
{ "_key": "batch_gsc_spring26", "name": "GSC-Klone Frühjahr 2026", "batch_type": "cutting", "started_at": "2026-02-15T10:00:00Z", "completed_at": null, "status": "in_progress", "total_quantity": 10, "total_survived": null, "overall_success_rate": null, "target_planting_run_key": null, "notes": "Elite-Phänotyp #3 vermehren für nächsten Zyklus" }

// propagation_events collection
{ "_key": "prop_evt_001", "event_type": "cutting", "performed_at": "2026-02-15T10:30:00Z", "quantity": 10, "survived_count": null, "success_rate": null, "hormone_type": "iba", "hormone_concentration_ppm": 1000, "medium": "rockwool", "dome_humidity_percent": 85, "heat_mat_celsius": 22.0, "light_ppfd": 100, "photoperiod_hours": 18.0, "callus_observed_at": "2026-02-20T08:00:00Z", "roots_observed_at": null, "transplant_ready_at": null, "failure_reasons": [], "failure_count": 0, "notes": "10 Stecklinge von GSC Mutter #1", "photos": [] }

// part_of_batch edge
{ "_from": "propagation_events/prop_evt_001", "_to": "propagation_batches/batch_gsc_spring26" }

// propagated_from edge (Event ← Mutterpflanze)
{ "_from": "propagation_events/prop_evt_001", "_to": "plant_instances/gsc_mother_1" }

// uses_protocol edge
{ "_from": "propagation_events/prop_evt_001", "_to": "rooting_protocols/proto_cannabis_std" }
```

## 4. Abhängigkeiten

**Erforderliche Module:**
- REQ-001 (Stammdaten): Species, Cultivar, BotanicalFamily für Veredelungs-Kompatibilität und Spezies-spezifische Defaults
- REQ-002 (Standort): Location/Slot für Platzierung von Stecklingen und Mutterpflanzen
- REQ-003 (Phasensteuerung): Vermehrung erzeugt PlantInstances in `germination`-Phase; Stecklinge starten in `seedling`
- REQ-010 (IPM): Virusstatus-Tracking, Werkzeugsterilisation, Quarantäne-Empfehlungen
- REQ-013 (Pflanzdurchlauf): PropagationBatch übergibt Ergebnis-Pflanzen an PlantingRun
- REQ-019 (Substratverwaltung): SubstrateBatch-Referenz für Bewurzelungsmedium-Rückverfolgbarkeit

**Wird benötigt von:**
- REQ-003 (Phasensteuerung): **MITTEL** — Phase-Start hängt von Vermehrungsmethode ab (Samen = Germination, Steckling = Seedling)
- REQ-006 (Aufgabenplanung): **MITTEL** — Stecklingnahme-Tasks basierend auf Mutterpflanzen-Erholungszeit
- REQ-007 (Erntemanagement): **NIEDRIG** — Samen-Ernte für Saatgut-Gewinnung (REQ-008 seed_saving)
- REQ-009 (Dashboard): **NIEDRIG** — Mutterpflanzen-Status-Widget, aktive Batches
- REQ-013 (Pflanzdurchlauf): **HOCH** — Klon-Run-Typ nutzt PropagationBatch als Quelle

**Celery-Tasks:**
- `check_mother_plant_health` — Wöchentlich: Prüft alle Mutterpflanzen auf Retirement-Kriterien
- `check_propagation_progress` — Täglich: Prüft aktive Events auf überfällige Bewurzelungs-Meilensteine

## 5. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **PropagationEvent-CRUD:** Erstellen und Lesen von Vermehrungsaktionen (12 Methoden inkl. Zimmerpflanzen-Methoden)
- [ ] **Zimmerpflanzen-Methoden:** leaf_cutting, stem_section, offset, air_layering, bulbil, water_propagation als PropagationMethod unterstützt
- [ ] **Stecklingstyp-Differenzierung:** CuttingType-Enum (apical, nodal, heel, softwood, semi_hardwood, hardwood, leaf_petiole, leaf_section) auf PropagationEvent bei event_type='cutting'
- [ ] **Ergebnis-Nachtragung:** survived_count und failure_reasons nachträglich erfassbar
- [ ] **Fortschritts-Tracking:** callus/roots/transplant Zeitpunkte aktualisierbar
- [ ] **PropagationBatch:** Gruppierung mehrerer Events, Batch-Finalisierung
- [ ] **RootingProtocol:** Vorlagen-CRUD, Template-System, Erfolgsstatistiken pro Protokoll
- [ ] **Temperaturzonen-Differenzierung:** air_temperature_celsius + heat_mat_celsius auf RootingProtocol und PropagationEvent, Bottom-Heat-Validierung (Delta 2–5°C empfohlen, >8°C = Fehler)
- [ ] **VPD-Ziel:** target_vpd_kpa auf RootingProtocol und PropagationEvent für Dome-Bewurzelungs-Bedingungen
- [ ] **Lichtspektrum:** LightSpectrum-Enum auf RootingProtocol und PropagationEvent
- [ ] **PPFD-Obergrenze:** light_ppfd max. 300, Warnung >150 unter Dome (Photoinhibition)
- [ ] **Hormon-Konzentrationsbereiche:** HORMONE_RANGES in PropagationEngine mit methoden-/typspezifischer Validierung, Obergrenze 10.000 ppm
- [ ] **Methodenspezifische Erholungszeit:** RECOVERY_DAYS_BY_METHOD (cutting: 14d, division: 21d, offset: 7d, layering: 7d etc.)
- [ ] **Mutterpflanzen-Designation:** PlantInstance als Mutterpflanze markieren/entmarkieren
- [ ] **Mutterpflanzen-Monitoring:** Health-Score, Stecklingshistorie, Erholungszeit-Prüfung
- [ ] **Virusstatus-Tracking:** virus_status auf MotherPlantConfig (clean, untested, infected, recovered), Warnung bei Vermehrung infizierter Pflanzen
- [ ] **IPM-Integration:** tool_sterilization_method, quarantine_required, quarantine_days auf PropagationEvent
- [ ] **Substrat-Integration:** substrate_batch_key (REQ-019), medium_ph, medium_ec_ms auf PropagationEvent
- [ ] **Retirement-Empfehlung:** Automatische Warnung bei niedriger Gesundheit oder sinkender Erfolgsrate
- [ ] **Genetische Abstammung:** descended_from-Graph mit beliebig tiefer Traversierung
- [ ] **Klon-Baum:** Alle Nachkommen einer Mutterpflanze abrufbar
- [ ] **Generationszählung:** Automatisch berechnet aus Graph-Tiefe
- [ ] **Veredelungs-Kompatibilität:** Mehrstufig: explizite graft_compatible_with-Edges > Taxonomie-Heuristik
- [ ] **Phänotyp-Notizen:** CRUD für Beobachtungen pro Pflanze
- [ ] **Somatische Mutationslast:** Warnung ab konfigurierbarer Generationsschwelle (Default: 10)
- [ ] **Verwandtschaftsschätzung:** calculate_relatedness_estimate (Heuristik, nicht Wright's F) in LineageEngine
- [ ] **PlantingRun-Integration:** Batch-Ergebnis kann an PlantingRun (REQ-013) übergeben werden
- [ ] **Statistiken:** Erfolgsraten pro Methode, Cultivar, Protokoll
- [ ] **Seed-Daten:** 10 Bewurzelungsprotokolle (Nutzpflanzen, Zimmerpflanzen, verholzte Pflanzen, generisch)
- [ ] **Celery-Beat:** `check_mother_plant_health` (wöchentlich), `check_propagation_progress` (täglich)

### Testszenarien:

**Szenario 1: Stecklingnahme von Mutterpflanze mit Erholungszeit-Prüfung**
```
GIVEN: Mutterpflanze "GSC Mother #1" (Cannabis, is_mother=true, health_score=85,
       mother_recovery_days=14), letzte Stecklingnahme vor 10 Tagen
WHEN: POST /api/v1/propagation/events
      Body: { event_type: "cutting", quantity: 8,
              mother_plant_key: "gsc_mother_1", protocol_key: "proto_cannabis_std" }
THEN:
  - PropagationEvent wird erstellt
  - Warnung: "Erholungszeit nicht eingehalten: 10 von 14 Tagen"
  - Event wird NICHT blockiert (Warnung, kein Fehler)
  - propagated_from-Edge zur Mutterpflanze
  - uses_protocol-Edge zum Protokoll
```

**Szenario 2: Bewurzelungs-Fortschritt und Erfolgs-Nachtragung**
```
GIVEN: PropagationEvent "prop_evt_001" (10 Cannabis-Stecklinge, Tag 12)
WHEN: PATCH /api/v1/propagation/events/prop_evt_001/progress
      Body: { roots_observed_at: "2026-02-25T08:00:00Z" }
THEN:
  - roots_observed_at aktualisiert
  - Liegt nach callus_observed_at (2026-02-20) → Validierung OK

WHEN: PATCH /api/v1/propagation/events/prop_evt_001/outcome
      Body: { survived_count: 8, failure_reasons: ["rot", "no_roots"] }
THEN:
  - success_rate automatisch berechnet: 0.8 (80%)
  - failure_count: 2
  - 8 neue PlantInstances angelegt (in seedling-Phase)
  - resulted_in-Edges zu allen 8 Pflanzen
  - descended_from-Edges (relationship: "clone", generation: Mutter+1)
```

**Szenario 3: Abstammungslinie über 3 Generationen**
```
GIVEN: Pflanze "GSC-Clone-A1" abstammt von "GSC-Mother-1" (Steckling),
       "GSC-Mother-1" abstammt von "GSC-Seed-Original" (Samen/Sämling)
WHEN: GET /api/v1/plant-instances/gsc_clone_a1/lineage
THEN:
  - Lineage: GSC-Clone-A1 → GSC-Mother-1 → GSC-Seed-Original
  - total_generations: 2
  - Relationships: clone → clone (oder seed_mother)
  - Generation-Counter: A1=2, Mother-1=1, Seed-Original=0
```

**Szenario 4: Veredelungs-Kompatibilitätsprüfung**
```
GIVEN: Edelreis: Tomate "San Marzano" (Solanum lycopersicum, Solanaceae)
       Unterlage 1: Tomate "Beaufort F1" (Solanum lycopersicum, Solanaceae)
       Unterlage 2: Gurke (Cucumis sativus, Cucurbitaceae)
WHEN: GET /api/v1/propagation/graft-compatibility?scion_key=tomato_sm&rootstock_key=tomato_beaufort
THEN:
  - compatibility: "compatible"
  - message: "Gleiche Gattung (Solanum) — Veredelung empfohlen"

WHEN: GET /api/v1/propagation/graft-compatibility?scion_key=tomato_sm&rootstock_key=cucumber_1
THEN:
  - compatibility: "incompatible"
  - message: "Verschiedene Familien (Solanaceae vs. Cucurbitaceae) — Veredelung nicht empfohlen"
```

**Szenario 5: Mutterpflanzen-Retirement-Empfehlung**
```
GIVEN: Mutterpflanze "Old Mother" (Cannabis, health_score=35, generation=12),
       letzte 5 Stecklingnahmen: Erfolgsraten 90%, 85%, 60%, 45%, 40%
WHEN: GET /api/v1/propagation/mothers/old_mother
THEN:
  - retirement_suggestion: "Gesundheit kritisch (35/100) — Ablösung dringend empfohlen"
  - Zusätzlich: "Generation 12 — hohes Risiko für somatische Mutationslast"
  - avg_success_rate der letzten 3: 48%
```

**Szenario 6: Aussaat mit Kreuzungs-Dokumentation**
```
GIVEN: Mutterpflanze "Haze Mother" (Cannabis, Samen-Trägerin),
       Vaterpflanze "Kush Father" (Cannabis, Pollenspender)
WHEN: POST /api/v1/propagation/events
      Body: { event_type: "seed_sowing", quantity: 20,
              mother_plant_key: "haze_mother",
              father_plant_key: "kush_father",
              protocol_key: "proto_seed_general" }
THEN:
  - PropagationEvent erstellt
  - propagated_from-Edge zu "Haze Mother"
  - 2 descended_from-Edges vorbereitet:
    - relationship: "seed_mother" → "Haze Mother"
    - relationship: "seed_father" → "Kush Father"
  - Ergebnis-Pflanzen erhalten beide Eltern im Lineage-Graph
```

**Szenario 7: Batch-Finalisierung mit PlantingRun-Übergabe**
```
GIVEN: PropagationBatch "GSC-Klone Frühjahr 2026" (10 Stecklinge, 8 überlebt),
       PlantingRun "GSC Grow Cycle #5" existiert (status: planned)
WHEN: POST /api/v1/propagation/batches/batch_gsc_spring26/finalize
      Body: { target_planting_run_key: "gsc_cycle_5" }
THEN:
  - Batch-Status → "completed"
  - total_survived: 8, overall_success_rate: 0.8
  - 8 PlantInstances werden zu PlantingRun "GSC Grow Cycle #5" hinzugefügt
  - batch_feeds_run-Edge erstellt
  - PlantingRun enthält nun 8 Einträge
```

**Szenario 8: Bewurzelungsprotokoll-Statistiken**
```
GIVEN: Protokoll "Cannabis Steckling Standard" wurde in 15 Events verwendet,
       davon: Cannabis (10 Events, avg 82%), Tomate (3 Events, avg 90%), Basilikum (2 Events, avg 95%)
WHEN: GET /api/v1/propagation/protocols/proto_cannabis_std/stats
THEN:
  - total_events: 15
  - overall_avg_success: 85.3%
  - by_species:
    - Cannabis: 10 Events, avg 82%
    - Tomate: 3 Events, avg 90%
    - Basilikum: 2 Events, avg 95%
```

**Szenario 9: Generationswarnung bei Klon-von-Klon**
```
GIVEN: Pflanze "Clone-Gen-11" ist Generation 11 in einer Klonlinie
WHEN: POST /api/v1/propagation/events
      Body: { event_type: "cutting", quantity: 5, mother_plant_key: "clone_gen_11" }
THEN:
  - Warnung: "Generation 11 — somatische Mutationslast erhöht. Empfehlung: Neue Mutterpflanze aus Samen ziehen"
  - Ergebnis-Pflanzen erhalten generation: 12
```

**Szenario 10: Phänotyp-Dokumentation für Selektion**
```
GIVEN: 4 Pflanzen aus Samen-Batch (F1-Generation, Haze × Kush)
WHEN: POST /api/v1/plant-instances/f1_plant_3/phenotypes
      Body: { category: "aroma", trait: "Zitrus-Terpen-dominant mit Kiefer-Untertönen",
              rating: 9, notes: "Auffällig starke Terpen-Produktion ab Woche 5 Blüte" }
THEN:
  - PhenotypeNote erstellt, has_phenotype-Edge zur Pflanze
  - Pflanze "F1 #3" hat nun dokumentierten Phänotyp
  - Kann als Grundlage für Mutterpflanzen-Selektion dienen
```

---

**Hinweise für RAG-Integration:**
- Keywords: Vermehrung, Steckling, Blattsteckling, Stammstück, Aussaat, Klon, Mutterpflanze, Bewurzelung, Veredelung, Unterlage, Edelreis, Absenker, Abmoosen, Teilung, Kindel, Ableger, Brutzwiebel, Wasserbewurzelung, Gewebekultur, Hormon, IBA, NAA, Hormonkonzentration, Steinwolle, Perlit, Aeroponik, Kloner, Dome, Haube, Wärmematte, Bottom Heat, Lufttemperatur, Substrattemperatur, Temperaturgradient, Kallus, Bewurzelungsrate, Erfolgsrate, Phänotyp, Selektion, Abstammung, Lineage, Generation, Somatische Mutationslast, Verwandtschaft, Kreuzung, F1, Samen, Pheno-Hunting, VPD, Veredelungskompatibilität, graft_compatible_with, Stecklingstyp, Triebspitze, Fersensteckling, Weichholz, Hartholz, Halbverholzt, Lichtspektrum, Blaulicht, Rotlicht, PPFD, Photoinhibition, Quarantäne, Virusstatus, Werkzeugsterilisation, IPM, Substrat-pH, Substrat-EC, Zimmerpflanze, Pothos, Monstera, Sansevieria, Aloe, Haworthia, Begonia, Ficus, Dracaena, Pilea, Philodendron
- Technische Begriffe: PropagationEvent, PropagationBatch, RootingProtocol, PhenotypeNote, MotherPlantConfig, PropagationEngine, LineageEngine, CuttingType, LightSpectrum, ToolSterilizationMethod, VirusStatus, HORMONE_RANGES, RECOVERY_DAYS_BY_METHOD, calculate_relatedness_estimate, descended_from, propagated_from, resulted_in, grafted_onto, has_phenotype, batch_feeds_run, CuttingRequestValidator, GraftRequestValidator, air_temperature_celsius, heat_mat_celsius, target_vpd_kpa, light_spectrum, substrate_batch_key, medium_ph, medium_ec_ms, tool_sterilization_method, quarantine_required, virus_status
- Verknüpfung: REQ-001 (Species/Cultivar/BotanicalFamily), REQ-003 (GrowthPhase — Start-Phase), REQ-010 (IPM — Virusstatus, Werkzeugsterilisation, Quarantäne), REQ-013 (PlantingRun), REQ-006 (Aufgaben), REQ-007/008 (Samenernte), REQ-019 (Substratverwaltung — Bewurzelungsmedium)
