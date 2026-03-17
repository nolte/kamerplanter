# Spezifikation: REQ-014 - Tankmanagement

```yaml
ID: REQ-014
Titel: Tank-Verwaltung für Nährstofflösungen & Bewässerung
Kategorie: Bewässerung & Düngung
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, Celery
Status: Entwurf
Version: 1.5 (HA-Sensor-Binding & Bulk-Endpoints)
```

## 1. Business Case

**User Story:** "Als Gärtner möchte ich meine Nährstoff-/Gießwasser-Tanks als eigenständige Objekte verwalten — mit Zuordnung zu einem Bereich, lückenloser Pflegehistorie, nachvollziehbarer Befüllungshistorie und automatisierter Aufgabenplanung — damit ich den Überblick über Wasserwechsel, Reinigungen, Düngerzusammensetzungen und Reservoirzustand behalte und die Bewässerung meiner Pflanzen zuverlässig läuft."

**User Story (Befüllungshistorie):** "Als Gärtner möchte ich bei jedem Befüllen meines Tanks dokumentieren, welche Lösung ich in welcher Menge und nach welchem Rezept eingefüllt habe — damit ich nachvollziehen kann, was meine Pflanzen wann bekommen haben, und meine Düngeprogramme über die Zeit optimieren kann."

**Beschreibung:**
Das System führt den **Tank (Reservoir)** als zentrale Infrastruktur-Entität ein. Ein Tank versorgt genau einen Bereich (Location) mit Nährstofflösung oder Gießwasser und ist der zentrale Knotenpunkt zwischen Bewässerung, Düngung und Standort-Verwaltung.

**Kernkonzepte:**

**Tank als Infrastruktur-Objekt:**
- Jeder Tank hat ein festes Volumen, einen Typ und einen aktuellen Zustand (Füllstand, EC, pH, Wassertemperatur)
- Tanks werden genau einer Location zugeordnet — die Location bestimmt, welche Slots/Pflanzen über diesen Tank versorgt werden
- Bei automatischer Bewässerung (`irrigation_system != 'manual'`) ist ein zugeordneter Tank **Pflicht** für die Location
- Bei manueller Bewässerung ist der Tank optional (Gießkanne statt Reservoir)

**Tank-Typen:**
- **Nährstofflösung (nutrient):** Fertig gemischte Lösung für Hydro-/Drip-Systeme
- **Gießwasser (irrigation):** Aufbereitetes Wasser (ggf. mit pH-Korrektur) für Erde/Coco
- **Reservoir (reservoir):** Vorratstank für Rohwasser (Regenwasser, Osmose, Leitungswasser)
- **Rezirkulation (recirculation):** Rücklauftank bei geschlossenen Hydro-Systemen (NFT, Ebb&Flow)
- **Stammlösung (stock_solution):** Konzentrierte A/B-Tanks (100x–200x) für automatisierte Dosierung (REQ-018). EC 50–200+ mS/cm, extrem niedriger pH. A+B niemals im Konzentrat mischen! Muss über `feeds_from`-Kaskade in Mischtank dosiert werden.

**Tankpflege & Wartungsaufgaben:**
Die Pflege des Tanks erzeugt direkte Auswirkungen auf die Aufgabenplanung (REQ-006):

- **Wasserwechsel (water_change):** Kompletter Austausch der Nährstofflösung — Intervall abhängig vom Tank-Typ und System (z.B. alle 7 Tage bei DWC, 14 Tage bei Drip)
- **Reinigung (cleaning):** Tankinneres + Leitungen von Algen, Biofilm und Ablagerungen befreien — z.B. bei sichtbarem Bewuchs oder nach jeder Ernte
- **Desinfektion (sanitization):** Sterile Reinigung mit H2O2 oder Enzymen — pflichtmäßig zwischen Grow-Zyklen
- **Kalibrierung (calibration):** EC-/pH-Sonden im Tank kalibrieren — Intervall abhängig von Tank-Typ und Sondenplatzierung:
  - **Rezirkulation (inline-Sonden, Dauerkontakt):** Alle 7–14 Tage — permanenter Kontakt mit Nährlösung beschleunigt Drift und Membranverschleiß
  - **Nährstofftank (intermittierende Messung):** Alle 14 Tage
  - **Irrigation/Reservoir (seltene Nutzung):** Alle 21–28 Tage
  - **Generell:** Nach jedem Wasserwechsel mit Reinigungsmitteln (H2O2, Enzyme) neu kalibrieren, da Chemikalien Sondenoberfläche angreifen
- **Filterwechsel (filter_change):** Vorfilter, Inline-Filter, UV-Lampen austauschen
- **Pumpeninspektion (pump_inspection):** Umwälzpumpe, Druckpumpe, Dosierperistaltik prüfen

**Befüllungshistorie (Tank Fill Events):**
Jede Tankbefüllung — ob Vollwechsel, Auffüllen oder Korrektur — wird als eigenständiges, unveränderliches Event historisiert. Damit entsteht eine lückenlose Nachvollziehbarkeit, *welche* Lösung *wann* in *welcher Menge* und nach *welchem Rezept* in den Tank eingefüllt wurde.

- **Befüllungstypen:** Vollwechsel (full_change), Auffüllen (top_up), Korrektur/Nachdosierung (adjustment)
- **Rezept-Verknüpfung:** Optionale Referenz auf ein MixingResult (REQ-004), um das exakte Mischrezept mit Düngern und Dosierungen zu verknüpfen
- **Plan-Verknüpfung:** Optionale Referenz auf den NutrientPlan (REQ-004), nach dem dosiert wurde
- **Soll/Ist-Vergleich:** Ziel-EC/pH aus dem Plan vs. gemessene Werte nach Befüllung
- **Dünger-Snapshot:** Kopie der verwendeten Dünger + Dosierungen (unveränderlich, auch wenn das Quell-Rezept später geändert wird)
- **Wasserquelle:** Herkunft des Wassers (Osmose, Leitungswasser, Regenwasser) oder Referenz auf einen Quell-Tank bei Kaskaden

**Wasserquellen-Defaults (Kaskade):**

Beim Erfassen eines TankFillEvent müssen `base_water_ec_ms`, `alkalinity_ppm`, `chlorine_ppm`, `chloramine_ppm` und das Mischverhältnis Osmose/Leitungswasser nicht jedes Mal manuell eingegeben werden. Das System löst fehlende Felder über eine 4-stufige Kaskade auf:

1. **Explizit im TankFillEvent** (höchste Priorität) — vom Nutzer direkt eingegebene Werte überschreiben alle Defaults
2. **NutrientPlan-Default** — wenn ein `nutrient_plan_key` auf dem Fill-Event gesetzt ist, wird `water_mix_ratio_ro_percent` des Plans als Default verwendet; die effektiven Wasserparameter werden daraus per `WaterMixCalculator` (REQ-004) berechnet
3. **Site-WaterSource-Profil** — wenn die Location des Tanks einer Site mit `water_source` (REQ-002) zugeordnet ist, werden die `TapWaterProfile`-Daten als Fallback genutzt; bei gesetztem `has_ro_system` und bekanntem Mischverhältnis (aus NutrientPlan oder Default) wird der `WaterMixCalculator` angewendet
4. **Manuelle Eingabe** (Fallback) — wenn keine der obigen Quellen Daten liefert, muss der Nutzer die Werte manuell eingeben (wie bisher)

Die Kaskade ist transparent: In der API-Response wird ein `water_defaults_source`-Feld mitgeliefert, das angibt, woher die Werte stammen (`'explicit'`, `'nutrient_plan'`, `'site_profile'`, `'manual'`).

- **Automatische TankState-Erstellung:** Nach Erfassung eines Fill-Events wird ein TankState-Record mit den gemessenen Werten erzeugt

**Ergänzende manuelle Bewässerung (WateringEvent):**
Auch bei Locations mit automatischer Bewässerung (`irrigation_system != 'manual'`) kann es notwendig sein, einzelne Pflanzen oder Slots **zusätzlich per Hand** zu gießen — z.B. um organische Dünger auszubringen, die Tropfer verstopfen oder Biofilm im Tank verursachen würden. Das System modelliert dies über **WateringEvents** auf Slot-/Pflanzenebene:

- **Abgrenzung TankFillEvent vs. WateringEvent vs. FeedingEvent (REQ-004):**

| Aspekt | TankFillEvent | WateringEvent (REQ-014) | FeedingEvent (REQ-004) |
|--------|--------------|---------------|---------------|
| Ebene | Tank (Infrastruktur) | Slot(s) (Gießvorgang) | PlantInstance (Pflanzenlevel) |
| Was wird dokumentiert? | Was geht IN den Tank | Was wird auf Slot(s) ausgebracht | Was bekommt die EINZELNE Pflanze |
| Granularität | 1 pro Tankbefüllung | 1 pro Gießvorgang (kann mehrere Slots umfassen) | 1 pro Pflanze pro Düngung |
| Typischer Anlass | Wasserwechsel, Auffüllung | Gießen, Blattdüngung, Top-Dressing | Automatisch aus WateringEvent abgeleitet |
| Verknüpfung | → MixingResult, NutrientPlan | → FeedingEvent (REQ-004), optional → TankFillEvent | ← WateringEvent, → Fertilizer |
| Erstellt durch | Nutzer (manuell/API) | Nutzer (manuell/API) | System (automatisch pro betroffener Pflanze im Slot) |

**Beziehung WateringEvent → FeedingEvent:** Ein `WateringEvent` erzeugt automatisch `FeedingEvents` (REQ-004) für jede `PlantInstance` in den betroffenen Slots. Das WateringEvent dokumentiert den physischen Gießvorgang (Volumen, EC, Methode), das FeedingEvent dokumentiert die Düngeraufnahme pro Pflanze (für Nährstoffbilanzierung und NutrientPlan-Tracking). Bei `application_method='fertigation'` und Tank-Verknüpfung werden die Dünger-Daten aus dem `TankFillEvent.mixing_result` übernommen.

- **Applikationsmethoden:** Fertigation (Tank/Tropfer), Drench (Gießkanne), Foliar (Blattdüngung), Top Dress (Feststoffe auf Substrat) — siehe REQ-004 ApplicationMethod
- **Hybride Versorgung:** Eine Location kann gleichzeitig Tank-basiert (mineralisch via Drip) UND manuell (organisch via Gießkanne) versorgt werden. Das `irrigation_system` in REQ-002 beschreibt das primäre System, nicht die einzige Methode.
- **Tank-Safety-Warnung:** Wenn ein Nutzer einen Dünger mit `tank_safe=false` (REQ-004) in ein TankFillEvent einfügen möchte, warnt das System und schlägt manuelles Gießen per WateringEvent vor

**Zustandsüberwachung:**
- Kontinuierliches Tracking von pH, EC, Wassertemperatur, Gelöstsauerstoff (DO), ORP und Füllstand (manuell oder via REQ-005 Sensorik)
- Automatische Alerts bei Grenzwert-Überschreitung — Schwellenwerte nach Tank-Typ differenziert:
  - **pH:** Tank-Typ-abhängig (Hydroponik: 5.5–6.5, Rezirkulation: 5.5–6.3, Bewässerung: 5.8–6.8), pH-Drift relativ zum letzten Wasserwechsel (>0.5, Rezirkulation >0.3)
  - **EC:** Relativ zum Ziel-EC des aktiven NutrientPlans (Warnung >20%, Alarm >30%), Fallback auf absolute Obergrenze ohne Plan
  - **Temperatur:** Differenziert nach Tank-Typ — Nährstoff/Rezirkulation: Warnung >22°C (Pythium), kritisch >25–26°C; Kälte-Warnung <15°C, kritisch <10–12°C (Wurzelschock)
  - **Gelöstsauerstoff (DO):** Kritisch <4 mg/L (anaerob), suboptimal <6 mg/L (Hydroponik-Pflicht)
  - **ORP:** Für Rezirkulation mit Sterilisation — <250 mV = Pathogen-Risiko, <650 mV = Sterilisation unzureichend
  - **Lösungsalter:** Temperaturkorrigierte Warnung (Q10-Regel: 5 Tage organisch / 10 Tage mineralisch bei 20°C Referenz; bei 30°C halbe Haltbarkeit) — Chelat-Degradation
- Füllstandswarnung bei < 20% Restvolumen
- Algenrisiko-Score (multifaktoriell: Lichteinfall als Primärtreiber, Temperatur, Nährstoffgehalt)
- Chlor/Chloramin-Warnung bei >0.5 ppm im Ausgangswasser + biologischen Additiven — differenzierte Entchlorungsempfehlung (freies Chlor: Abstehen reicht; Chloramin: Ascorbinsäure/Aktivkohle zwingend)

## 2. ArangoDB-Modellierung

### Nodes:

- **`:Tank`** — Physischer Tank/Reservoir
  - Collection: `tanks`
  - Properties:
    - `name: str` (z.B. "Haupttank Zelt 1", "Regenwasser Garten")
    - `tank_type: TankType` (nutrient | irrigation | reservoir | recirculation)
    - `volume_liters: float` (Nennvolumen)
    - `material: Optional[Literal['plastic', 'stainless_steel', 'glass', 'ibc']]`
    - `has_lid: bool` (Deckel vorhanden — Algenrisiko ohne Deckel)
    - `is_light_proof: bool` (Lichtdicht — primärer Algenrisikofaktor; transparente Materialien sind NICHT lichtdicht)
    - `has_air_pump: bool` (Belüftung — wichtig für DWC)
    - `has_circulation_pump: bool` (Umwälzpumpe)
    - `has_heater: bool` (Heizstab für Winterbetrieb)
    - `has_uv_sterilizer: bool` (UV-C Entkeimung — relevant für Rezirkulation)
    - `has_ozone_generator: bool` (Ozon-Desinfektion — effektiv gegen Pythium/Fusarium)
    - `installed_on: date` (Installationsdatum)
    - `notes: Optional[str]`
    - **Sensor-Binding:** Erfolgt über `monitors_tank`-Edge (REQ-005 `:Sensor` → `:Tank`). Ein Sensor kann `ha_entity_id`, `mqtt_topic` oder `modbus_address` tragen — damit werden **alle Datenquellen** (Home Assistant, ESPHome/MQTT direkt, Modbus/I2C) gleichwertig unterstützt. Kein HA-spezifisches Feld auf dem Tank selbst nötig.
    <!-- Quelle: HA-REVIEW-CORE CF-006 — Über monitors_tank Edge statt ha_*_entity_id auf Tank. Nutzt REQ-005 Sensor-Infrastruktur mit ha_entity_id, mqtt_topic, modbus_address. Unterstützt alle Datenkanäle (HA, ESPHome, Modbus) gleichwertig. -->

- **`:TankState`** — Momentaufnahme des Tank-Zustands (immutable)
  - Collection: `tank_states`
  - Properties:
    - `recorded_at: datetime`
    - `fill_level_liters: Optional[float]`
    - `fill_level_percent: Optional[float]`
    - `ph: Optional[float]`
    - `ec_ms: Optional[float]`
    - `water_temp_celsius: Optional[float]`
    - `dissolved_oxygen_mgl: Optional[float]` (Gelöstsauerstoff — kritisch für Hydroponik: >6 mg/L optimal, <4 mg/L kritisch)
    - `orp_mv: Optional[int]` (Oxidation-Reduction-Potential — Rezirkulation: >700 mV steril, <250 mV Pathogen-Risiko)
    - `tds_ppm: Optional[int]`
    - `source: Literal['manual', 'ha_auto', 'mqtt_auto', 'modbus_auto']` (Datenherkunft — identisch mit REQ-005 `Observation.source`. `manual` = Nutzereingabe, Rest = automatisch via Sensor-Webhook)

- **`:TankFillEvent`** — Einzelne Tankbefüllung (immutable)
  - Collection: `tank_fill_events`
  - Properties:
    - `filled_at: datetime`
    - `fill_type: Literal['full_change', 'top_up', 'adjustment']` (Vollwechsel | Auffüllen | Korrektur)
    - `volume_liters: float` (eingefülltes Volumen)
    - `mixing_result_key: Optional[str]` (Referenz auf MixingResult aus REQ-004)
    - `nutrient_plan_key: Optional[str]` (Referenz auf NutrientPlan aus REQ-004)
    - `target_ec_ms: Optional[float]` (Ziel-EC laut Plan/Rezept)
    - `target_ph: Optional[float]` (Ziel-pH laut Plan/Rezept)
    - `measured_ec_ms: Optional[float]` (gemessen nach Befüllung)
    - `measured_ph: Optional[float]` (gemessen nach Befüllung)
    - `water_source: Optional[Literal['tap', 'osmose', 'rainwater', 'distilled', 'well', 'mixed']]` (Wasserherkunft; `'mixed'` = Osmose/Leitungswasser-Mischung mit definierbarem Verhältnis)
    - `water_mix_ratio_ro_percent: Optional[int]` (ge=0, le=100) — Osmose-Anteil in Prozent bei `water_source='mixed'`. Überschreibt den NutrientPlan-Default (REQ-004) und den Site-Default (REQ-002) für diese einzelne Befüllung. `null` = Default aus Kaskade (NutrientPlan → Site).
    - `source_tank_key: Optional[str]` (Quell-Tank bei Kaskade, z.B. Reservoir)
    - `fertilizers_used: Optional[list[FertilizerSnapshot]]` (Dünger-Snapshot: [{name, ml_per_liter, product_key}])
    - `base_water_ec_ms: Optional[float]` (EC des Ausgangswassers — kann automatisch aus Mischverhältnis und Site-WaterSource-Profil berechnet werden, siehe Wasserquellen-Kaskade)
    - `chlorine_ppm: Optional[float]` (Freies Chlor im Ausgangswasser — verflüchtigt sich durch 24h Abstehen)
    - `chloramine_ppm: Optional[float]` (Chloramin im Ausgangswasser — erfordert Ascorbinsäure/Aktivkohle, NICHT flüchtig)
    - `is_organic_fertilizers: bool` (Enthält organische Dünger — kürzeres Lösungsalter)
    - `alkalinity_ppm: Optional[float]` (Karbonathärte CaCO₃-Äquivalent — bestimmt pH-Drift)
    - `performed_by: Optional[str]` (Benutzer)
    - `notes: Optional[str]`

- **`:WateringEvent`** — Einzelner Gießvorgang auf Slot-/Pflanzenebene (immutable)
  - Collection: `watering_events`
  - Properties:
    - `watered_at: datetime`
    - `application_method: Literal['fertigation', 'drench', 'foliar', 'top_dress']` (Art der Ausbringung — analog REQ-004 ApplicationMethod)
    - `is_supplemental: bool` (Ergänzend zur automatischen Bewässerung — z.B. organische Düngung per Gießkanne bei Drip-versorgten Pflanzen)
    - `volume_liters: float` (Gesamtvolumen)
    - `slot_keys: list[str]` (Betroffene Slots — mindestens 1)
    - `task_key: Optional[str]` (Rückreferenz auf den Gießplan-Task aus REQ-006, wenn das WateringEvent aus einem bestätigten Task erzeugt wurde. Ermöglicht Rückverfolgbarkeit: Task → WateringEvent → FeedingEvents)
    - `tank_fill_event_key: Optional[str]` (Referenz auf TankFillEvent, wenn aus dokumentierter Tankbefüllung)
    - `nutrient_plan_key: Optional[str]` (Referenz auf NutrientPlan aus REQ-004)
    - `fertilizers_used: Optional[list[FertilizerSnapshot]]` (Dünger-Snapshot mit Dosierungen)
    - `target_ec_ms: Optional[float]`
    - `target_ph: Optional[float]`
    - `measured_ec_ms: Optional[float]` (gemessen im Substrat/Runoff nach Gießen)
    - `measured_ph: Optional[float]`
    - `runoff_ec_ms: Optional[float]` (Drain-Messung bei Drain-to-Waste)
    - `runoff_ph: Optional[float]`
    - `water_source: Optional[Literal['tank', 'tap', 'osmose', 'rainwater', 'distilled', 'well']]`
    - `performed_by: Optional[str]`
    - `notes: Optional[str]`

- **`:MaintenanceLog`** — Einzelne Wartungsaktion (immutable)
  - Collection: `maintenance_logs`
  - Properties:
    - `maintenance_type: MaintenanceType` (water_change | cleaning | sanitization | calibration | filter_change | pump_inspection)
    - `performed_at: datetime`
    - `performed_by: Optional[str]` (Benutzer)
    - `duration_minutes: Optional[int]`
    - `products_used: Optional[list[str]]` (z.B. ["H2O2 3%", "Enzym-Reiniger"])
    - `notes: Optional[str]`
    - `next_due_at: Optional[datetime]` (Nächste Fälligkeit, berechnet aus Intervall)

- **`:MaintenanceSchedule`** — Wiederkehrender Wartungsplan pro Tank
  - Collection: `maintenance_schedules`
  - Properties:
    - `maintenance_type: MaintenanceType`
    - `interval_days: int` (z.B. 7 für wöchentlichen Wasserwechsel)
    - `reminder_days_before: int` (z.B. 1 Tag vorher erinnern)
    - `is_active: bool`
    - `priority: Literal['low', 'medium', 'high', 'critical']`
    - `auto_create_task: bool` (Task in REQ-006 automatisch anlegen)
    - `instructions: Optional[str]` (Spezielle Anweisungen)

### Edge-Collections:
```
has_tank:          locations → tanks                   // Location besitzt Tank
supplies:          tanks → locations                   // Tank versorgt Location (kann gleiche oder andere sein)
feeds_from:        tanks → tanks                       // Tankkaskade: Reservoir → Nährstofftank
has_state:         tanks → tank_states                 // Zeitserie von Zustandsmessungen
has_fill_event:    tanks → tank_fill_events            // Befüllungshistorie
has_maintenance:   tanks → maintenance_logs            // Wartungshistorie
has_schedule:      tanks → maintenance_schedules       // Geplante Wartungsintervalle
watered_slot:      watering_events → slots              // Gießvorgang betrifft Slot(s)
watering_from:     watering_events → tank_fill_events   // Gießvorgang stammt aus dokumentierter Tankbefüllung (optional)
generated_task:    maintenance_logs → tasks            // Verknüpfung zu REQ-006 Tasks
mixed_into:        mixing_results → tank_fill_events   // Nährstofflösung aus REQ-004 verknüpft mit Befüllungs-Event
monitors_tank:     sensors → tanks                     // Sensor überwacht Tank-Parameter (REQ-005). Attribute: parameter (ec, ph, fill_level, water_temp, dissolved_oxygen, orp)
```

> **Sensor-Binding via `monitors_tank`:** Ein REQ-005 `:Sensor` mit `parameter: 'ec'` und `ha_entity_id: 'sensor.tank1_ec'` (oder `mqtt_topic: 'esphome/tank1/ec'`, oder `modbus_address: 42`) wird über einen `monitors_tank`-Edge mit dem Tank verknüpft. Das System erkennt anhand des `parameter`-Feldes, welches TankState-Feld befüllt wird (ec → `ec_ms`, ph → `ph`, etc.). Damit sind **alle REQ-005-Datenkanäle** (Home Assistant, MQTT direkt, Modbus, manuell) für Tank-Monitoring nutzbar.

**ArangoDB-Graph-Definition:**
```json
{
  "edge_collection": "has_tank",
  "from_vertex_collections": ["locations"],
  "to_vertex_collections": ["tanks"]
}
```
```json
{
  "edge_collection": "supplies",
  "from_vertex_collections": ["tanks"],
  "to_vertex_collections": ["locations"]
}
```
```json
{
  "edge_collection": "feeds_from",
  "from_vertex_collections": ["tanks"],
  "to_vertex_collections": ["tanks"]
}
```

### AQL-Beispielqueries:

**1. Alle Tanks einer Location inkl. aktuellstem Zustand:**
```aql
FOR tank IN tanks
    FOR edge IN has_tank
        FILTER edge._to == tank._id
        FILTER edge._from == CONCAT('locations/', @location_key)
        LET latest_state = FIRST(
            FOR state IN tank_states
                FOR se IN has_state
                    FILTER se._from == tank._id AND se._to == state._id
                    SORT state.recorded_at DESC
                    LIMIT 1
                    RETURN state
        )
        RETURN {
            tank: tank,
            current_state: latest_state
        }
```

**2. Fällige Wartungen über alle Tanks:**
```aql
FOR tank IN tanks
    FOR edge IN has_schedule
        FILTER edge._from == tank._id
        LET schedule = DOCUMENT(edge._to)
        FILTER schedule.is_active == true
        LET last_maintenance = FIRST(
            FOR log IN maintenance_logs
                FOR me IN has_maintenance
                    FILTER me._from == tank._id AND me._to == log._id
                    FILTER log.maintenance_type == schedule.maintenance_type
                    SORT log.performed_at DESC
                    LIMIT 1
                    RETURN log
        )
        LET days_since = last_maintenance != null
            ? DATE_DIFF(last_maintenance.performed_at, DATE_NOW(), "day")
            : 999
        FILTER days_since >= schedule.interval_days - schedule.reminder_days_before
        RETURN {
            tank_name: tank.name,
            tank_key: tank._key,
            maintenance_type: schedule.maintenance_type,
            interval_days: schedule.interval_days,
            days_since_last: days_since,
            days_overdue: days_since - schedule.interval_days,
            priority: schedule.priority,
            last_performed: last_maintenance.performed_at
        }
```

**3. Tank-Kaskade auflösen (Reservoir → Mischtank → Location):**
```aql
FOR v, e, p IN 1..3 OUTBOUND CONCAT('tanks/', @tank_key)
    GRAPH 'kamerplanter_graph'
    OPTIONS { uniqueVertices: "global" }
    FILTER IS_SAME_COLLECTION('feeds_from', e) OR IS_SAME_COLLECTION('supplies', e)
    RETURN {
        vertex: v,
        edge_type: PARSE_IDENTIFIER(e).collection,
        depth: LENGTH(p.edges)
    }
```

**4. Befüllungshistorie eines Tanks (chronologisch, mit Rezept-Details):**
```aql
FOR tank IN tanks
    FILTER tank._key == @tank_key
    FOR edge IN has_fill_event
        FILTER edge._from == tank._id
        LET fill_event = DOCUMENT(edge._to)
        SORT fill_event.filled_at DESC
        LIMIT @offset, @limit
        LET mixing_result = fill_event.mixing_result_key != null
            ? DOCUMENT(CONCAT('mixing_results/', fill_event.mixing_result_key))
            : null
        LET nutrient_plan = fill_event.nutrient_plan_key != null
            ? DOCUMENT(CONCAT('nutrient_plans/', fill_event.nutrient_plan_key))
            : null
        LET source_tank = fill_event.source_tank_key != null
            ? DOCUMENT(CONCAT('tanks/', fill_event.source_tank_key))
            : null
        RETURN {
            fill_event: fill_event,
            mixing_result: mixing_result ? { name: mixing_result.name, total_ec: mixing_result.total_ec } : null,
            nutrient_plan: nutrient_plan ? { name: nutrient_plan.name } : null,
            source_tank: source_tank ? { name: source_tank.name, tank_type: source_tank.tank_type } : null,
            ec_deviation: fill_event.target_ec_ms != null AND fill_event.measured_ec_ms != null
                ? ABS(fill_event.target_ec_ms - fill_event.measured_ec_ms)
                : null
        }
```

**5. Befüllungsstatistik pro Tank (Aggregation über Zeitraum):**
```aql
FOR tank IN tanks
    FILTER tank._key == @tank_key
    LET fill_events = (
        FOR edge IN has_fill_event
            FILTER edge._from == tank._id
            LET fe = DOCUMENT(edge._to)
            FILTER fe.filled_at >= @start_date AND fe.filled_at <= @end_date
            RETURN fe
    )
    RETURN {
        tank_key: tank._key,
        tank_name: tank.name,
        period: { start: @start_date, end: @end_date },
        total_fills: LENGTH(fill_events),
        full_changes: LENGTH(fill_events[* FILTER CURRENT.fill_type == 'full_change']),
        top_ups: LENGTH(fill_events[* FILTER CURRENT.fill_type == 'top_up']),
        adjustments: LENGTH(fill_events[* FILTER CURRENT.fill_type == 'adjustment']),
        total_volume_liters: SUM(fill_events[*].volume_liters),
        avg_ec_deviation: AVERAGE(
            fill_events[* FILTER CURRENT.target_ec_ms != null AND CURRENT.measured_ec_ms != null
                RETURN ABS(CURRENT.target_ec_ms - CURRENT.measured_ec_ms)]
        )
    }
```

**6. Gießhistorie eines Slots (alle Applikationsmethoden):**
```aql
FOR slot IN slots
    FILTER slot._key == @slot_key
    LET watering_events = (
        FOR edge IN watered_slot
            FILTER edge._to == slot._id
            LET we = DOCUMENT(edge._from)
            SORT we.watered_at DESC
            LIMIT @offset, @limit
            LET fill_event = we.tank_fill_event_key != null
                ? DOCUMENT(CONCAT('tank_fill_events/', we.tank_fill_event_key))
                : null
            RETURN {
                event: we,
                application_method: we.application_method,
                is_supplemental: we.is_supplemental,
                fertilizers: we.fertilizers_used,
                from_tank_fill: fill_event ? {
                    filled_at: fill_event.filled_at,
                    fill_type: fill_event.fill_type
                } : null
            }
    )
    RETURN {
        slot_key: slot._key,
        total_events: LENGTH(watering_events),
        events: watering_events
    }
```

**7. Vergleich: Tank-Fertigation vs. manuelle Ergänzungsdüngung pro Location:**
```aql
FOR loc IN locations
    FILTER loc._key == @location_key
    LET all_slots = (
        FOR edge IN has_slot
            FILTER edge._from == loc._id
            RETURN DOCUMENT(edge._to)
    )
    LET all_watering = (
        FOR slot IN all_slots
            FOR edge IN watered_slot
                FILTER edge._to == slot._id
                LET we = DOCUMENT(edge._from)
                FILTER we.watered_at >= @start_date AND we.watered_at <= @end_date
                RETURN we
    )
    RETURN {
        location: loc.name,
        period: { start: @start_date, end: @end_date },
        total_waterings: LENGTH(all_watering),
        fertigation_count: LENGTH(all_watering[* FILTER CURRENT.application_method == 'fertigation']),
        drench_count: LENGTH(all_watering[* FILTER CURRENT.application_method == 'drench']),
        foliar_count: LENGTH(all_watering[* FILTER CURRENT.application_method == 'foliar']),
        top_dress_count: LENGTH(all_watering[* FILTER CURRENT.application_method == 'top_dress']),
        supplemental_count: LENGTH(all_watering[* FILTER CURRENT.is_supplemental == true]),
        total_volume: SUM(all_watering[*].volume_liters)
    }
```

**8. Locations ohne zugeordneten Tank bei automatischer Bewässerung:**
```aql
FOR loc IN locations
    FILTER loc.irrigation_system != 'manual' AND loc.irrigation_system != null
    LET tank_count = LENGTH(
        FOR edge IN has_tank
            FILTER edge._from == loc._id
            RETURN 1
    )
    FILTER tank_count == 0
    RETURN {
        location_key: loc._key,
        location_name: loc.name,
        irrigation_system: loc.irrigation_system,
        warning: "Automatische Bewässerung konfiguriert, aber kein Tank zugeordnet"
    }
```

## 3. Technische Umsetzung (Python)

### Logik-Anforderungen:

**1. Tank-Pydantic-Modelle:**
```python
from datetime import date, datetime
from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, Field, model_validator

class TankType(str, Enum):
    NUTRIENT = "nutrient"           # Nährstofflösung
    IRRIGATION = "irrigation"       # Gießwasser
    RESERVOIR = "reservoir"         # Vorratstank (Regen/Osmose/Leitung)
    RECIRCULATION = "recirculation" # Rücklauftank (geschlossene Systeme)
    STOCK_SOLUTION = "stock_solution"  # Konzentrierte Stammlösung (A/B-Tanks, 100x-200x)
    # stock_solution: EC 50-200+ mS/cm, pH extrem (A: 2-3, B: 4-5), typisch 5-25L.
    # A+B NIEMALS im Konzentrat mischen (Ausfällung)! Muss über feeds_from-Kaskade laufen.

class MaintenanceType(str, Enum):
    WATER_CHANGE = "water_change"
    CLEANING = "cleaning"
    SANITIZATION = "sanitization"
    CALIBRATION = "calibration"
    FILTER_CHANGE = "filter_change"
    PUMP_INSPECTION = "pump_inspection"

class TankDefinition(BaseModel):
    """Stammdaten eines physischen Tanks"""

    name: str = Field(min_length=1, max_length=100)
    tank_type: TankType
    volume_liters: float = Field(gt=0, le=10000)
    material: Optional[Literal['plastic', 'stainless_steel', 'glass', 'ibc']] = None
    has_lid: bool = Field(default=True)
    is_light_proof: bool = Field(default=True, description="Lichtdicht — primärer Treiber für Algenrisiko. Transparente/transluzente Materialien (weißes Plastik, Glas) sind NICHT lichtdicht.")
    has_air_pump: bool = Field(default=False)
    has_circulation_pump: bool = Field(default=False)
    has_heater: bool = Field(default=False)
    has_uv_sterilizer: bool = Field(default=False, description="UV-C Entkeimung inline — relevant für Rezirkulation")
    has_ozone_generator: bool = Field(default=False, description="Ozon-Desinfektion — effektiv gegen Pythium/Fusarium")
    installed_on: date = Field(default_factory=date.today)
    notes: Optional[str] = Field(None, max_length=1000)

class TankStateRecord(BaseModel):
    """Einzelne Zustandsmessung (immutable)"""

    recorded_at: datetime = Field(default_factory=datetime.now)
    fill_level_liters: Optional[float] = Field(None, ge=0)
    fill_level_percent: Optional[float] = Field(None, ge=0, le=100)
    ph: Optional[float] = Field(None, ge=0, le=14)
    ec_ms: Optional[float] = Field(None, ge=0, le=250, description="Bis 10 mS für Gebrauchslösung, bis 250 mS für stock_solution")
    water_temp_celsius: Optional[float] = Field(None, ge=0, le=50)
    dissolved_oxygen_mgl: Optional[float] = Field(
        None, ge=0, le=20,
        description="Gelöstsauerstoff in mg/L. Kritisch für Hydroponik: "
                    "optimal >6 mg/L (>75% Sättigung), kritisch <4 mg/L (anaerobe Bedingungen). "
                    "Sättigung sinkt mit steigender Temperatur UND steigendem EC "
                    "(Salting-Out-Effekt): Reinwasser 20°C: ~9.1 mg/L; "
                    "Nährlösung EC 2.0 bei 25°C: ~7.2–7.5 mg/L."
    )
    orp_mv: Optional[int] = Field(
        None, ge=-500, le=1000,
        description="Oxidation-Reduction-Potential in mV. "
                    "Relevant für Rezirkulation: >700 mV = effektive Sterilisation, "
                    "<250 mV = reduzierende Bedingungen (Pathogen-Risiko)."
    )
    tds_ppm: Optional[int] = Field(None, ge=0)
    source: Literal['manual', 'sensor', 'home_assistant'] = 'manual'

    @model_validator(mode='after')
    def validate_fill_level_consistency(self):
        """Wenn beide Füllstands-Werte gegeben, müssen sie konsistent sein."""
        if self.fill_level_liters is not None and self.fill_level_percent is not None:
            # Konsistenz-Check wird im Service mit tank.volume_liters durchgeführt
            pass
        return self

class FillType(str, Enum):
    FULL_CHANGE = "full_change"     # Kompletter Lösungswechsel
    TOP_UP = "top_up"               # Auffüllen (Verdunstung/Verbrauch ausgleichen)
    ADJUSTMENT = "adjustment"       # Korrektur/Nachdosierung (pH/EC anpassen)

class FertilizerSnapshot(BaseModel):
    """Unveränderliche Kopie der Dünger-Dosierung zum Zeitpunkt der Befüllung"""

    product_key: Optional[str] = Field(None, description="ArangoDB _key des Fertilizer-Dokuments")
    product_name: str = Field(min_length=1, max_length=200)
    ml_per_liter: Optional[float] = Field(None, gt=0, le=50.0, description="Flüssigdünger-Dosierung")
    g_per_liter: Optional[float] = Field(None, gt=0, le=100.0, description="Feststoff-Dosierung (Top-Dress, Trockendünger)")
    is_organic: bool = Field(default=False, description="Konsistent mit REQ-004 Fertilizer.is_organic")

class TankFillEvent(BaseModel):
    """Einzelne Tankbefüllung (immutable) — historisiert Rezept, Menge und Messwerte"""

    filled_at: datetime = Field(default_factory=datetime.now)
    fill_type: FillType
    volume_liters: float = Field(gt=0, le=10000, description="Eingefülltes Volumen in Litern")

    # Rezept-Verknüpfung (REQ-004)
    mixing_result_key: Optional[str] = Field(None, description="Referenz auf MixingResult aus REQ-004")
    nutrient_plan_key: Optional[str] = Field(None, description="Referenz auf NutrientPlan aus REQ-004")

    # Soll/Ist-Vergleich
    target_ec_ms: Optional[float] = Field(None, ge=0, le=10)
    target_ph: Optional[float] = Field(None, ge=0, le=14)
    measured_ec_ms: Optional[float] = Field(None, ge=0, le=10)
    measured_ph: Optional[float] = Field(None, ge=0, le=14)

    # Wasserherkunft
    water_source: Optional[Literal['tap', 'osmose', 'rainwater', 'distilled', 'well', 'mixed']] = None
    water_mix_ratio_ro_percent: Optional[int] = Field(
        None, ge=0, le=100,
        description="Osmose-Anteil bei 'mixed' water_source (0-100%). "
                    "Überschreibt NutrientPlan- und Site-Defaults für diese Befüllung. "
                    "null = Default aus Kaskade (NutrientPlan → Site)."
    )
    source_tank_key: Optional[str] = Field(None, description="Quell-Tank bei Kaskade")
    base_water_ec_ms: Optional[float] = Field(
        None, ge=0, le=5,
        description="EC des Ausgangswassers. Kann automatisch aus Mischverhältnis "
                    "und Site-WaterSource-Profil (REQ-002) berechnet werden — "
                    "siehe Wasserquellen-Kaskade."
    )
    chlorine_ppm: Optional[float] = Field(
        None, ge=0, le=10,
        description="Freies Chlor (Cl₂/HOCl) im Ausgangswasser (ppm). "
                    "Verflüchtigt sich durch 24h Abstehen oder Belüftung. "
                    "Alternativ: Ascorbinsäure (1g pro 400L bei 1 ppm Cl). "
                    "Leitungswasser: typisch 0.2–2.0 ppm."
    )
    chloramine_ppm: Optional[float] = Field(
        None, ge=0, le=10,
        description="Gebundenes Chlor/Chloramin (NH₂Cl) im Ausgangswasser (ppm). "
                    "NICHT flüchtig — Abstehen ist NICHT ausreichend! "
                    "Entfernung: Ascorbinsäure (1g pro 400L bei 1 ppm) oder Aktivkohle-Filter. "
                    ">0.5 ppm tötet Mykorrhiza und Nützlinge ab (REQ-004 Inkompatibilitäten)."
    )
    alkalinity_ppm: Optional[float] = Field(
        None, ge=0, le=500,
        description="Karbonathärte/Alkalinität (CaCO₃-Äquivalent) in ppm. "
                    "Bestimmt pH-Pufferkapazität und pH-Drift-Geschwindigkeit. "
                    "Konsistent mit REQ-004 base_water_alkalinity_ppm."
    )

    # Nachfüllwasser-Temperatur (Wurzelschock-Prävention)
    water_temperature_celsius: Optional[float] = Field(
        None, ge=0, le=50,
        description="Temperatur des Nachfüllwassers. Delta >5°C zur Tanklösung = Wurzelschock-Risiko."
    )

    # Dünger-Snapshot (unveränderliche Kopie)
    fertilizers_used: list[FertilizerSnapshot] = Field(default_factory=list)

    performed_by: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode='after')
    def validate_full_change_has_volume(self):
        """Bei Vollwechsel sollte das Volumen dem Tankvolumen nahekommen (Warnung im Service)."""
        return self

    @model_validator(mode='after')
    def validate_adjustment_has_target(self):
        """Bei Korrektur muss mindestens ein Zielwert (EC oder pH) angegeben sein."""
        if self.fill_type == FillType.ADJUSTMENT:
            if self.target_ec_ms is None and self.target_ph is None:
                raise ValueError(
                    "Bei einer Korrektur (adjustment) muss mindestens "
                    "target_ec_ms oder target_ph angegeben werden"
                )
        return self

class ApplicationMethod(str, Enum):
    """Art der Ausbringung — identisch mit REQ-004 ApplicationMethod"""
    FERTIGATION = "fertigation"   # Über Tank/Tropfer/Pumpe
    DRENCH = "drench"             # Manuelles Gießen per Gießkanne
    FOLIAR = "foliar"             # Blattdüngung per Sprüher
    TOP_DRESS = "top_dress"       # Feststoff auf Substratoberfläche

class WateringEvent(BaseModel):
    """Einzelner Gießvorgang auf Slot-/Pflanzenebene (immutable)"""

    watered_at: datetime = Field(default_factory=datetime.now)
    application_method: ApplicationMethod
    is_supplemental: bool = Field(
        default=False,
        description="Ergänzend zur automatischen Tank-Bewässerung — "
                    "z.B. organische Düngung per Gießkanne bei Drip-System"
    )
    volume_liters: float = Field(gt=0, le=1000, description="Gesamtvolumen in Litern")
    slot_keys: list[str] = Field(min_length=1, description="Betroffene Slot-Keys")

    # Rückreferenz auf Gießplan-Task (REQ-006)
    task_key: Optional[str] = Field(
        None,
        description="Referenz auf den Gießplan-Task, wenn WateringEvent aus "
                    "Bestätigungsflow (confirm/quick-confirm) erzeugt wurde"
    )

    # Verknüpfung zu Tank/Rezept
    tank_fill_event_key: Optional[str] = Field(
        None, description="Referenz auf TankFillEvent, wenn aus Tank gegossen"
    )
    nutrient_plan_key: Optional[str] = Field(
        None, description="Referenz auf NutrientPlan (REQ-004)"
    )

    # Dünger-Snapshot
    fertilizers_used: list[FertilizerSnapshot] = Field(default_factory=list)

    # Soll/Ist
    target_ec_ms: Optional[float] = Field(None, ge=0, le=10)
    target_ph: Optional[float] = Field(None, ge=0, le=14)
    measured_ec_ms: Optional[float] = Field(None, ge=0, le=10)
    measured_ph: Optional[float] = Field(None, ge=0, le=14)
    runoff_ec_ms: Optional[float] = Field(
        None, ge=0, le=10,
        description="Drain-Messung. Interpretation substrat-abhängig: "
                    "Coco: Runoff-EC sollte <0.5 mS über Input liegen; "
                    "Steinwolle: Schwankt im Tagesverlauf; "
                    "Erde: Stark gepuffert durch CEC; "
                    "Hydro (NFT/DWC): Kein Drain-Konzept. "
                    "Substrattyp wird über Slot → SubstrateBatch → Substrate aufgelöst."
    )
    runoff_ph: Optional[float] = Field(None, ge=0, le=14)

    # Wasserherkunft
    water_source: Optional[Literal['tank', 'tap', 'osmose', 'rainwater', 'distilled', 'well']] = None

    performed_by: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode='after')
    def validate_supplemental_not_fertigation(self):
        """Ergänzende Handdüngung ist per Definition nicht fertigation."""
        if self.is_supplemental and self.application_method == ApplicationMethod.FERTIGATION:
            raise ValueError(
                "Ergänzende Handdüngung (is_supplemental=true) kann nicht "
                "application_method='fertigation' sein — verwende 'drench', "
                "'foliar' oder 'top_dress'"
            )
        return self

class MaintenanceLogEntry(BaseModel):
    """Dokumentation einer durchgeführten Wartung"""

    maintenance_type: MaintenanceType
    performed_at: datetime = Field(default_factory=datetime.now)
    performed_by: Optional[str] = Field(None, max_length=100)
    duration_minutes: Optional[int] = Field(None, ge=0, le=1440)
    products_used: Optional[list[str]] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=2000)

class MaintenanceScheduleDefinition(BaseModel):
    """Wiederkehrender Wartungsplan"""

    maintenance_type: MaintenanceType
    interval_days: int = Field(ge=1, le=365)
    reminder_days_before: int = Field(ge=0, le=30)
    is_active: bool = True
    priority: Literal['low', 'medium', 'high', 'critical'] = 'medium'
    auto_create_task: bool = True
    instructions: Optional[str] = Field(None, max_length=2000)

    @model_validator(mode='after')
    def validate_reminder_before_interval(self):
        if self.reminder_days_before >= self.interval_days:
            raise ValueError(
                f"Erinnerung ({self.reminder_days_before}d) muss vor "
                f"dem Intervall ({self.interval_days}d) liegen"
            )
        return self
```

**2. Tank-Service-Logik:**
```python
from datetime import datetime, timedelta

class TankService:
    """Zentrale Geschäftslogik für Tank-Verwaltung"""

    def validate_tank_assignment(
        self,
        location_key: str,
        location_irrigation_system: str,
        existing_tanks: list[dict],
    ) -> tuple[bool, Optional[str]]:
        """
        Validiert Tank-Zuordnung zu einer Location.
        Bei automatischer Bewässerung ist ein Tank Pflicht.
        """
        is_automated = location_irrigation_system not in ('manual', None)

        if is_automated and len(existing_tanks) == 0:
            return False, (
                f"Location '{location_key}' hat Bewässerungssystem "
                f"'{location_irrigation_system}' konfiguriert — "
                f"ein Tank muss zugeordnet werden."
            )
        return True, None

    # pH-Grenzen nach Tank-Typ (engere Bereiche als das universelle 5.0–7.0)
    PH_RANGES: dict[str, tuple[float, float]] = {
        'nutrient':      (5.5, 6.5),   # Hydroponik-Standard; >6.5 = Fe-Lockout, <5.5 = Ca/Mg-Lockout
        'recirculation': (5.5, 6.3),   # Enger, da pH-Drift in Rezirkulation schneller
        'irrigation':    (5.8, 6.8),   # Default für Erde/Coco — kann substratspezifisch überschrieben werden
        'reservoir':     (5.0, 8.0),   # Rohwasser — weiter Bereich akzeptabel
        'stock_solution': (1.0, 14.0), # Keine pH-Limits für Konzentrate
    }

    # Substratspezifische pH-Bereiche für Irrigation-Tanks
    # Wird verwendet wenn die versorgte Location einen bekannten Substrattyp hat
    PH_RANGES_BY_SUBSTRATE: dict[str, tuple[float, float]] = {
        'coco':         (5.8, 6.2),   # Engerer Bereich — pH 6.8 führt zu Fe/Mn-Lockout bei Coco
        'soil':         (6.0, 6.8),   # Standard-Erde
        'living_soil':  (6.2, 6.8),   # Zu sauer (<6.0) schädigt Mikrobiom
        'perlite':      (5.5, 6.3),   # Wie Hydroponik
        'rockwool_slab': (5.5, 6.3),  # Wie Hydroponik
    }

    # Temperatur-Schwellenwerte nach Tank-Typ
    TEMP_THRESHOLDS: dict[str, dict] = {
        'nutrient': {
            'cold_warning': 15.0,      # Nährstoffaufnahme verlangsamt sich
            'cold_critical': 10.0,     # Wurzelschock
            'warm_warning': 22.0,      # DO sinkt, Pythium-Risiko steigt
            'warm_critical': 26.0,     # Akute Wurzelfäule-Gefahr
        },
        'recirculation': {
            'cold_warning': 16.0,
            'cold_critical': 12.0,
            'warm_warning': 22.0,      # Wie nutrient — Pathogen-Ausbreitung über Kreislauf
            'warm_critical': 25.0,     # Strenger wegen systemweitem Infektionsrisiko
        },
        'irrigation': {
            'cold_warning': 10.0,
            'cold_critical': 5.0,
            'warm_warning': 28.0,      # Weniger kritisch (kein Dauerkontakt mit Wurzeln)
            'warm_critical': 35.0,
        },
        'reservoir': {
            'cold_warning': 5.0,       # Frost-Risiko
            'cold_critical': 1.0,
            'warm_warning': 30.0,      # Algenrisiko, aber nicht wurzelkritisch
            'warm_critical': 40.0,
        },
    }

    def check_alerts(
        self,
        tank: dict,
        current_state: dict,
        last_fill_event: Optional[dict] = None,
    ) -> list[dict]:
        """
        Prüft Tank-Zustand gegen Grenzwerte und erzeugt Alerts.
        Schwellenwerte sind nach tank_type differenziert.
        last_fill_event: Letzter Vollwechsel für EC-Zielvergleich und Lösungsalter.
        """
        alerts = []
        tank_type = tank.get('tank_type', 'nutrient')

        # --- pH: Tank-Typ-abhängige Grenzen ---
        if current_state.get('ph') is not None:
            ph = current_state['ph']
            ph_min, ph_max = self.PH_RANGES.get(tank_type, (5.0, 7.0))
            if ph < ph_min or ph > ph_max:
                severity = 'critical' if (ph < ph_min - 0.5 or ph > ph_max + 0.5) else 'high'
                alerts.append({
                    'type': 'ph_out_of_range',
                    'severity': severity,
                    'message': f"pH {ph:.1f} außerhalb Zielbereich ({ph_min}–{ph_max}) "
                               f"für Tank-Typ '{tank_type}'",
                    'value': ph,
                })

            # pH-Drift relativ zum letzten Wasserwechsel
            if last_fill_event and last_fill_event.get('measured_ph') is not None:
                drift = abs(ph - last_fill_event['measured_ph'])
                drift_threshold = 0.3 if tank_type == 'recirculation' else 0.5
                if drift > drift_threshold:
                    alerts.append({
                        'type': 'ph_drift',
                        'severity': 'medium',
                        'message': f"pH-Drift {drift:.1f} seit letzter Befüllung "
                                   f"(war {last_fill_event['measured_ph']:.1f}, jetzt {ph:.1f})",
                        'value': drift,
                    })

        # --- EC: Relativ zum Ziel-EC des letzten Fill-Events ---
        if current_state.get('ec_ms') is not None:
            ec = current_state['ec_ms']
            target_ec = (last_fill_event or {}).get('target_ec_ms')

            if target_ec is not None and target_ec > 0:
                deviation_pct = abs(ec - target_ec) / target_ec * 100
                if deviation_pct > 30:
                    direction = "gestiegen" if ec > target_ec else "gefallen"
                    alerts.append({
                        'type': 'ec_deviation_critical',
                        'severity': 'high',
                        'message': f"EC {ec:.2f} mS — {deviation_pct:.0f}% vom Ziel "
                                   f"({target_ec:.2f} mS) abgewichen ({direction}). "
                                   f"{'Salzakkumulation?' if ec > target_ec else 'Pflanzen nehmen mehr auf als verfügbar.'}",
                        'value': ec,
                    })
                elif deviation_pct > 20:
                    alerts.append({
                        'type': 'ec_deviation_warning',
                        'severity': 'medium',
                        'message': f"EC {ec:.2f} mS — {deviation_pct:.0f}% Abweichung vom Ziel ({target_ec:.2f} mS)",
                        'value': ec,
                    })
            elif tank_type in ('nutrient', 'recirculation') and ec > 3.5:
                # Fallback ohne Ziel-EC: absolute Obergrenze
                alerts.append({
                    'type': 'ec_too_high',
                    'severity': 'high',
                    'message': f"EC {ec:.1f} mS zu hoch — Salzakkumulation?",
                    'value': ec,
                })

        # --- EC-Trend bei Rezirkulation (letzten 3+ Messungen) ---
        # EC-Drift-Richtung ist diagnostisches Signal für Korrekturmaßnahme:
        # Steigend = mehr Wasser nachfüllen, Fallend = Nährstoffe nachdosieren
        if (tank_type == 'recirculation'
                and hasattr(self, '_recent_states') and len(self._recent_states) >= 3):
            ec_values = [s['ec_ms'] for s in self._recent_states if s.get('ec_ms')]
            if len(ec_values) >= 3:
                ec_trend = ec_values[-1] - ec_values[0]
                if ec_trend > 0.3:
                    alerts.append({
                        'type': 'ec_trend_rising',
                        'severity': 'medium',
                        'message': "EC steigt — Pflanzen nehmen mehr Wasser als Nährstoffe auf. "
                                   "Mit Reinstwasser auffüllen, NICHT mit Nährlösung.",
                    })
                elif ec_trend < -0.3:
                    alerts.append({
                        'type': 'ec_trend_falling',
                        'severity': 'medium',
                        'message': "EC sinkt — Pflanzen nehmen mehr Nährstoffe als Wasser auf. "
                                   "Konzentrierte Stammlösung nachdosieren.",
                    })

        # --- Temperatur: Tank-Typ-differenzierte Schwellenwerte ---
        if current_state.get('water_temp_celsius') is not None:
            temp = current_state['water_temp_celsius']
            thresholds = self.TEMP_THRESHOLDS.get(tank_type, self.TEMP_THRESHOLDS['nutrient'])

            if temp <= thresholds['cold_critical']:
                alerts.append({
                    'type': 'temperature_cold_critical',
                    'severity': 'critical',
                    'message': f"Wassertemperatur {temp:.1f}°C — kritisch kalt! "
                               f"Wurzelschock, Nährstoffaufnahme blockiert.",
                    'value': temp,
                })
            elif temp <= thresholds['cold_warning']:
                alerts.append({
                    'type': 'temperature_cold_warning',
                    'severity': 'medium',
                    'message': f"Wassertemperatur {temp:.1f}°C — zu kalt. "
                               f"Nährstoffaufnahme verlangsamt sich.",
                    'value': temp,
                })
            elif temp >= thresholds['warm_critical']:
                alerts.append({
                    'type': 'temperature_high_critical',
                    'severity': 'critical',
                    'message': f"Wassertemperatur {temp:.1f}°C — kritisch! "
                               f"Gelöster Sauerstoff minimal, akute Wurzelfäule-Gefahr.",
                    'value': temp,
                })
            elif temp >= thresholds['warm_warning']:
                alerts.append({
                    'type': 'temperature_high_warning',
                    'severity': 'medium' if tank_type == 'reservoir' else 'high',
                    'message': f"Wassertemperatur {temp:.1f}°C — "
                               f"{'Algenrisiko' if tank_type == 'reservoir' else 'DO sinkt, Pythium-Risiko steigt'}.",
                    'value': temp,
                })

        # --- Gelöstsauerstoff (DO): Kritisch für Hydroponik ---
        if current_state.get('dissolved_oxygen_mgl') is not None:
            do = current_state['dissolved_oxygen_mgl']
            if tank_type in ('nutrient', 'recirculation'):
                if do < 4.0:
                    alerts.append({
                        'type': 'dissolved_oxygen_critical',
                        'severity': 'critical',
                        'message': f"Gelöstsauerstoff {do:.1f} mg/L — kritisch niedrig! "
                                   f"Anaerobe Bedingungen, akute Pythium-Gefahr. "
                                   f"Belüftung prüfen.",
                        'value': do,
                    })
                elif do < 6.0:
                    alerts.append({
                        'type': 'dissolved_oxygen_low',
                        'severity': 'high',
                        'message': f"Gelöstsauerstoff {do:.1f} mg/L — suboptimal "
                                   f"(Ziel: >6 mg/L, ideal >8 mg/L). "
                                   f"Belüftung erhöhen oder Temperatur senken.",
                        'value': do,
                    })

        # --- Kreuz-Alert: Hohe Temperatur + niedriger DO (Ursache statt Symptom) ---
        if (current_state.get('water_temp_celsius', 0) > 22
                and current_state.get('dissolved_oxygen_mgl', 99) < 6
                and tank_type in ('nutrient', 'recirculation')):
            alerts.append({
                'type': 'temp_do_compound',
                'severity': 'critical',
                'message': "Hohe Temperatur UND niedriger DO — Wassertemperatur senken "
                           "ist effektiver als Belüftung erhöhen. Ursache (Temperatur) "
                           "statt Symptom (DO) beheben. Optionen: Wasserkühler, "
                           "Eisflaschen, Nacht-Wasserwechsel.",
            })

        # --- ORP: Relevant für Rezirkulation mit Sterilisation ---
        if current_state.get('orp_mv') is not None:
            orp = current_state['orp_mv']
            if tank_type == 'recirculation':
                if orp < 250:
                    alerts.append({
                        'type': 'orp_reducing',
                        'severity': 'high',
                        'message': f"ORP {orp} mV — reduzierende Bedingungen. "
                                   f"Anaerobe Pathogene möglich. Desinfektion prüfen.",
                        'value': orp,
                    })
                if tank.get('has_uv_sterilizer') or tank.get('has_ozone_generator'):
                    if orp < 650:
                        alerts.append({
                            'type': 'orp_sterilization_insufficient',
                            'severity': 'medium',
                            'message': f"ORP {orp} mV — Sterilisation möglicherweise "
                                       f"nicht effektiv (Ziel: >700 mV). "
                                       f"UV-Lampe/Ozon-Generator prüfen.",
                            'value': orp,
                        })

        # --- Füllstand ---
        if current_state.get('fill_level_percent') is not None:
            fill = current_state['fill_level_percent']
            if fill < 20:
                alerts.append({
                    'type': 'low_fill_level',
                    'severity': 'high',
                    'message': f"Füllstand {fill:.0f}% — Nachfüllen erforderlich",
                    'value': fill,
                })

        # --- Algenrisiko (Licht + Temperatur + Nährstoffe) ---
        # Licht ist der primäre Treiber — ohne Photosynthese keine Algen
        algae_risk_score = 0
        if not tank.get('is_light_proof', tank.get('has_lid', True)):
            algae_risk_score += 2  # Nicht lichtdicht
        elif not tank.get('has_lid', True):
            algae_risk_score += 1  # Deckel, aber möglicherweise transluzent
        water_temp = current_state.get('water_temp_celsius', 0)
        if water_temp > 22:
            algae_risk_score += 1
        if water_temp > 28:
            algae_risk_score += 1
        if tank_type in ('nutrient', 'recirculation'):
            algae_risk_score += 1  # Nährstoffe immer vorhanden
        if algae_risk_score >= 3:
            alerts.append({
                'type': 'algae_risk',
                'severity': 'medium',
                'message': "Erhöhtes Algenrisiko — Kombination aus Lichteinfall, "
                           "Temperatur und Nährstoffen. Lichtdichten Deckel anbringen "
                           "und/oder Temperatur senken.",
            })

        # --- Biofilm-Risiko bei Rezirkulation (multifaktoriell) ---
        if tank_type == 'recirculation':
            biofilm_risk = 0
            if current_state.get('water_temp_celsius', 0) > 22:
                biofilm_risk += 1
            if not tank.get('has_uv_sterilizer') and not tank.get('has_ozone_generator'):
                biofilm_risk += 1
            if has_organics if 'has_organics' in dir() else False:
                biofilm_risk += 2  # Organische Additive erhöhen Biofilm-Risiko stark
            if 'age_hours' in dir() and age_hours > 120:
                biofilm_risk += 1
            if biofilm_risk >= 3:
                alerts.append({
                    'type': 'biofilm_risk',
                    'severity': 'high',
                    'message': "Erhöhtes Biofilm-Risiko in Rezirkulationssystem. "
                               "Enzymatischen Reiniger einsetzen oder "
                               "Wasserwechsel-Intervall verkürzen.",
                })

        # --- Lösungsalter (temperaturkorrigiert, Q10-Regel) ---
        # Chelat-Degradation beschleunigt sich exponentiell mit Temperatur:
        # Q10 = 2 → Degradation verdoppelt sich pro 10°C über Referenz (20°C)
        if (tank_type in ('nutrient', 'recirculation')
                and last_fill_event
                and last_fill_event.get('fill_type') == 'full_change'):
            from datetime import datetime
            filled_at = last_fill_event.get('filled_at')
            if isinstance(filled_at, str):
                filled_at = datetime.fromisoformat(filled_at)
            if filled_at is not None:
                age_hours = (datetime.now() - filled_at).total_seconds() / 3600
                has_organics = any(
                    f.get('is_organic', False)  # Explizites Flag, konsistent mit REQ-004
                    for f in (last_fill_event.get('fertilizers_used') or [])
                )

                # Q10-Korrektur: Temperatur-gewichtetes Alter (Referenz 20°C)
                avg_temp = current_state.get('water_temp_celsius', 20)
                temp_factor = 2 ** ((avg_temp - 20) / 10)  # Q10-Regel
                effective_age_hours = age_hours * temp_factor

                base_warning_hours = 120 if has_organics else 240  # 5 bzw. 10 Tage bei 20°C
                if effective_age_hours > base_warning_hours:
                    actual_days = age_hours / 24
                    effective_days = effective_age_hours / 24
                    temp_note = (f" (temperaturkorrigiert: {effective_days:.0f} Tage Äquivalent bei {avg_temp:.0f}°C)"
                                 if abs(temp_factor - 1.0) > 0.1 else "")
                    alerts.append({
                        'type': 'solution_age',
                        'severity': 'medium',
                        'message': f"Nährstofflösung ist {actual_days:.0f} Tage alt{temp_note}. "
                                   f"Eisenchelate und {'organische Additive degradieren' if has_organics else 'Mikronährstoffe können degradiert sein'}. "
                                   f"Wasserwechsel empfohlen.",
                        'value': round(age_hours),
                    })

        return alerts

    def resolve_water_defaults(
        self,
        fill_event: 'TankFillEvent',
        tank: dict,
        nutrient_plan: Optional[dict] = None,
        site_water_source: Optional[dict] = None,
    ) -> dict:
        """
        Füllt fehlende Wasserquellen-Felder auf dem TankFillEvent über die
        4-stufige Kaskade auf:
          1. Explizit im TankFillEvent (höchste Prio)
          2. NutrientPlan-Default (water_mix_ratio_ro_percent)
          3. Site-WaterSource-Profil (TapWaterProfile + RoWaterProfile)
          4. Manuelle Eingabe (Fallback — keine Defaults)

        Gibt ein dict mit aufgelösten Feldern und `water_defaults_source` zurück:
        - 'explicit': Werte direkt vom Nutzer eingegeben
        - 'nutrient_plan': Mischverhältnis aus NutrientPlan, Parameter aus Site
        - 'site_profile': Parameter direkt aus Site-Profil (ohne Mischverhältnis)
        - 'manual': Keine Defaults verfügbar, manuelle Eingabe nötig

        Nutzt WaterMixCalculator (REQ-004) für Mischverhältnis-Berechnung.
        """
        ...

    def record_fill_event(
        self,
        tank: dict,
        fill_event: 'TankFillEvent',
        current_state: Optional[dict] = None,
    ) -> dict:
        """
        Erfasst eine Tankbefüllung und erzeugt automatisch einen TankState-Record.
        current_state: Aktueller Tankzustand für Temperatur-Delta-Prüfung bei Top-Up.

        Returns: {fill_event: dict, tank_state: dict, warnings: list}
        """
        warnings = []

        # Plausibilitätsprüfung: Volumen vs. Tank-Kapazität
        if fill_event.fill_type == FillType.FULL_CHANGE:
            ratio = fill_event.volume_liters / tank['volume_liters']
            if ratio < 0.5:
                warnings.append(
                    f"Vollwechsel mit nur {fill_event.volume_liters}L "
                    f"bei {tank['volume_liters']}L Tank — wirklich Vollwechsel?"
                )
        elif fill_event.fill_type == FillType.TOP_UP:
            if fill_event.volume_liters > tank['volume_liters'] * 0.5:
                warnings.append(
                    f"Auffüllung von {fill_event.volume_liters}L ist >50% "
                    f"des Tank-Volumens — Vollwechsel stattdessen?"
                )

        # EC-Abweichungs-Check
        if fill_event.target_ec_ms is not None and fill_event.measured_ec_ms is not None:
            deviation = abs(fill_event.target_ec_ms - fill_event.measured_ec_ms)
            if deviation > 0.3:
                warnings.append(
                    f"EC-Abweichung: Ziel {fill_event.target_ec_ms} mS, "
                    f"gemessen {fill_event.measured_ec_ms} mS "
                    f"(Δ {deviation:.2f} mS)"
                )

        # pH-Abweichungs-Check
        if fill_event.target_ph is not None and fill_event.measured_ph is not None:
            ph_deviation = abs(fill_event.target_ph - fill_event.measured_ph)
            if ph_deviation > 0.5:
                warnings.append(
                    f"pH-Abweichung: Ziel {fill_event.target_ph}, "
                    f"gemessen {fill_event.measured_ph} "
                    f"(Δ {ph_deviation:.1f})"
                )

        # Temperatur-Delta bei Nachfüllung (Wurzelschock-Prävention)
        if (fill_event.water_temperature_celsius is not None
                and current_state is not None
                and current_state.get('water_temp_celsius') is not None):
            temp_diff = abs(fill_event.water_temperature_celsius - current_state['water_temp_celsius'])
            if temp_diff > 5:
                warnings.append(
                    f"Temperaturdifferenz {temp_diff:.1f}°C zwischen Nachfüllwasser "
                    f"({fill_event.water_temperature_celsius}°C) und Tanklösung "
                    f"({current_state['water_temp_celsius']}°C). Wurzelschock möglich."
                )

        # Chlor/Chloramin-Warnung bei biologischen Additiven (REQ-004 Inkompatibilität)
        total_chlorine = (fill_event.chlorine_ppm or 0) + (fill_event.chloramine_ppm or 0)
        if total_chlorine > 0.5:
            has_biologicals = any(
                'myko' in (f.product_name or '').lower()
                or 'tricho' in (f.product_name or '').lower()
                or 'bacillus' in (f.product_name or '').lower()
                or 'kompost' in (f.product_name or '').lower()
                for f in fill_event.fertilizers_used
            )
            if has_biologicals:
                if fill_event.chloramine_ppm and fill_event.chloramine_ppm > 0.5:
                    warnings.append(
                        f"Chloramin {fill_event.chloramine_ppm:.1f} ppm im Wasser — "
                        f"biologische Additive werden geschädigt. "
                        f"Ascorbinsäure (1g/400L bei 1 ppm) oder Aktivkohle-Filter "
                        f"zwingend erforderlich. Abstehen ist NICHT ausreichend!"
                    )
                elif fill_event.chlorine_ppm and fill_event.chlorine_ppm > 0.5:
                    warnings.append(
                        f"Freies Chlor {fill_event.chlorine_ppm:.1f} ppm im Wasser — "
                        f"biologische Additive werden geschädigt. "
                        f"24h Abstehen lassen ODER Ascorbinsäure (1g/400L bei 1 ppm)."
                    )
                else:
                    warnings.append(
                        f"Gesamtchlor {total_chlorine:.1f} ppm im Wasser — "
                        f"biologische Additive werden geschädigt. Wasser entchloren."
                    )

        # Automatisch TankState-Record erzeugen (wenn Messwerte vorhanden)
        tank_state = None
        if fill_event.measured_ec_ms is not None or fill_event.measured_ph is not None:
            tank_state = {
                'recorded_at': fill_event.filled_at,
                'ph': fill_event.measured_ph,
                'ec_ms': fill_event.measured_ec_ms,
                'fill_level_liters': fill_event.volume_liters if fill_event.fill_type == FillType.FULL_CHANGE else None,
                'source': 'manual',
            }

        return {
            'fill_event': fill_event.model_dump(),
            'tank_state': tank_state,
            'warnings': warnings,
        }

    def validate_tank_safe_fertilizers(
        self,
        fertilizers: list[dict],
    ) -> tuple[bool, list[str]]:
        """
        Prüft ob alle Dünger tank-sicher sind.
        Returns: (all_safe, warnings)
        """
        warnings = []
        for fert in fertilizers:
            if not fert.get('tank_safe', True):
                warnings.append(
                    f"'{fert['product_name']}' ist nicht tank-sicher "
                    f"(organisch/Schwebstoffe) — manuelles Gießen per "
                    f"Gießkanne empfohlen (WateringEvent mit "
                    f"application_method='drench')"
                )
        return len(warnings) == 0, warnings

    def record_watering_event(
        self,
        watering: 'WateringEvent',
        location_irrigation_system: str,
    ) -> dict:
        """
        Erfasst einen Gießvorgang auf Slot-Ebene.
        Erzeugt automatisch FeedingEvents (REQ-004) pro betroffener Pflanze.

        Returns: {watering_event: dict, feeding_events: list, warnings: list}
        """
        warnings = []

        # Bei fertigation auf manuellem System warnen
        if (watering.application_method == ApplicationMethod.FERTIGATION
                and location_irrigation_system == 'manual'):
            warnings.append(
                "Fertigation auf Location mit manuellem Bewässerungssystem — "
                "kein Tank/Tropfer vorhanden. Meintest du 'drench' (Gießkanne)?"
            )

        # Bei Drench auf automatischem System: is_supplemental vorschlagen
        if (watering.application_method in (ApplicationMethod.DRENCH, ApplicationMethod.FOLIAR,
                                             ApplicationMethod.TOP_DRESS)
                and location_irrigation_system != 'manual'
                and not watering.is_supplemental):
            warnings.append(
                "Manuelles Gießen auf Location mit automatischem System — "
                "is_supplemental=true empfohlen für korrekte Dokumentation."
            )

        # Volumen-Plausibilität pro Slot (substrat-relativ wenn verfügbar)
        volume_per_slot = watering.volume_liters / len(watering.slot_keys)

        if watering.application_method == ApplicationMethod.FOLIAR:
            # Blattdüngung: typisch 0.05–0.2L pro Pflanze, >0.5L ist fast sicher ein Fehler
            if volume_per_slot > 0.5:
                warnings.append(
                    f"Foliar: {volume_per_slot:.2f}L pro Slot ist sehr hoch — "
                    f"typisch sind 0.05–0.2L pro Pflanze bei Blattdüngung."
                )
        elif volume_per_slot > 20:
            # Absoluter Fallback wenn kein Slot-Volumen bekannt
            warnings.append(
                f"Hohe Gießmenge ({volume_per_slot:.1f}L pro Slot) — "
                f"Substratüberschwemmung möglich."
            )

        return {
            'watering_event': watering.model_dump(),
            'warnings': warnings,
        }

    def validate_volume_per_slot(
        self,
        volume_per_slot: float,
        slot_substrate_volume_liters: Optional[float],
        application_method: str,
    ) -> Optional[str]:
        """
        Substrat-relative Volumen-Plausibilität (wenn Slot-Daten aus REQ-002 verfügbar).
        Ziel: ~30% Drain bei Drain-to-Waste, ~10% bei Rezirkulation.

        Returns: Warnung als String oder None.
        """
        if application_method == 'foliar':
            return None  # Foliar wird separat geprüft (siehe oben)

        if slot_substrate_volume_liters is not None and slot_substrate_volume_liters > 0:
            ratio = volume_per_slot / slot_substrate_volume_liters
            if ratio > 0.5:
                return (
                    f"Gießmenge ({volume_per_slot:.1f}L) ist {ratio:.0%} des "
                    f"Substratvolumens ({slot_substrate_volume_liters:.0f}L) — "
                    f"Überwässerung wahrscheinlich. Ziel: 20–30% für Drain-to-Waste."
                )
        return None

    def calculate_next_maintenance(
        self,
        schedule: dict,
        last_maintenance: Optional[dict],
    ) -> dict:
        """
        Berechnet nächsten Wartungstermin und Fälligkeitsstatus.
        """
        interval = timedelta(days=schedule['interval_days'])

        if last_maintenance is None:
            # Noch nie gewartet — sofort fällig
            return {
                'maintenance_type': schedule['maintenance_type'],
                'next_due': datetime.now(),
                'is_overdue': True,
                'days_overdue': 0,
                'status': 'overdue',
            }

        last_date = last_maintenance['performed_at']
        if isinstance(last_date, str):
            last_date = datetime.fromisoformat(last_date)

        next_due = last_date + interval
        now = datetime.now()
        reminder_start = next_due - timedelta(days=schedule['reminder_days_before'])

        if now > next_due:
            status = 'overdue'
            days_overdue = (now - next_due).days
        elif now >= reminder_start:
            status = 'due_soon'
            days_overdue = 0
        else:
            status = 'ok'
            days_overdue = 0

        return {
            'maintenance_type': schedule['maintenance_type'],
            'next_due': next_due,
            'is_overdue': status == 'overdue',
            'days_overdue': days_overdue,
            'status': status,
        }
```

**3. Standard-Wartungsintervalle je Tank-Typ:**
```python
DEFAULT_MAINTENANCE_SCHEDULES: dict[str, list[dict]] = {
    "nutrient": [
        {"type": "water_change", "interval_days": 7, "priority": "high"},
        {"type": "cleaning", "interval_days": 30, "priority": "medium"},
        {"type": "sanitization", "interval_days": 90, "priority": "high"},
        {"type": "calibration", "interval_days": 14, "priority": "medium"},
        {"type": "pump_inspection", "interval_days": 30, "priority": "low"},
    ],
    "irrigation": [
        {"type": "water_change", "interval_days": 14, "priority": "medium"},
        {"type": "cleaning", "interval_days": 60, "priority": "medium"},
        {"type": "sanitization", "interval_days": 90, "priority": "medium"},
        {"type": "calibration", "interval_days": 21, "priority": "low"},  # Seltener — intermittierende Nutzung
        {"type": "filter_change", "interval_days": 90, "priority": "medium"},
    ],
    "reservoir": [
        {"type": "cleaning", "interval_days": 90, "priority": "low"},
        {"type": "sanitization", "interval_days": 180, "priority": "low"},
        {"type": "calibration", "interval_days": 28, "priority": "low"},  # Seltene Nutzung, kein Nährstoffkontakt
        {"type": "filter_change", "interval_days": 60, "priority": "medium"},
    ],
    "recirculation": [
        {"type": "water_change", "interval_days": 7, "priority": "critical"},
        {"type": "cleaning", "interval_days": 14, "priority": "high"},
        {"type": "sanitization", "interval_days": 14, "priority": "critical"},  # War 60d — zu lang für Rezirkulation (systemweites Pathogen-Risiko)
        {"type": "calibration", "interval_days": 7, "priority": "high"},  # Inline-Sonden mit Dauerkontakt driften schneller
        {"type": "pump_inspection", "interval_days": 14, "priority": "medium"},
        {"type": "filter_change", "interval_days": 30, "priority": "high"},
    ],
}
```

**4. Task-Integration (REQ-006 Anbindung):**
```python
class MaintenanceTaskGenerator:
    """Erzeugt Aufgaben in REQ-006 basierend auf Wartungsplänen."""

    def generate_tasks_for_due_maintenance(
        self,
        tank_key: str,
        tank_name: str,
        due_maintenances: list[dict],
    ) -> list[dict]:
        """
        Wandelt fällige Wartungen in Task-Definitionen um (REQ-006 kompatibel).
        """
        tasks = []
        for m in due_maintenances:
            if m['status'] in ('overdue', 'due_soon'):
                task = {
                    'task_type': 'maintenance',
                    'trigger_type': 'schedule',
                    'title': f"Tank '{tank_name}': {m['maintenance_type'].replace('_', ' ').title()}",
                    'description': self._get_description(m),
                    'priority': 'critical' if m['status'] == 'overdue' else 'medium',
                    'due_date': m['next_due'],
                    'entity_type': 'tank',
                    'entity_key': tank_key,
                    'tags': ['tank', 'maintenance', m['maintenance_type']],
                }
                tasks.append(task)
        return tasks

    def _get_description(self, maintenance: dict) -> str:
        descriptions = {
            'water_change': "Nährstofflösung komplett wechseln. Alt-Lösung entsorgen, Tank spülen, frisch anmischen.",
            'cleaning': "Tank-Innenwände und Leitungen von Algen/Biofilm reinigen.",
            'sanitization': "Sterile Reinigung mit H2O2 (3%) oder Enzym-Reiniger. 30 Min einwirken lassen, gründlich spülen.",
            'calibration': "EC- und pH-Sonden mit Referenzlösungen kalibrieren (pH 4.0, 7.0; EC 1.413 mS).",
            'filter_change': "Inline-Filter und Vorfilter prüfen und bei Bedarf wechseln.",
            'pump_inspection': "Umwälz-/Druckpumpe auf Geräusche, Durchfluss und Dichtigkeit prüfen.",
        }
        base = descriptions.get(maintenance['maintenance_type'], "Wartung durchführen.")
        if maintenance['status'] == 'overdue':
            base = f"ÜBERFÄLLIG ({maintenance['days_overdue']} Tage)! " + base
        return base
```

### Datenvalidierung:
```python
from pydantic import BaseModel, Field, model_validator
from typing import Optional

class TankAssignmentValidator(BaseModel):
    """Validiert die Zuordnung Tank → Location"""

    tank_key: str
    location_key: str
    tank_type: TankType
    location_irrigation_system: Optional[str]

    @model_validator(mode='after')
    def validate_type_compatibility(self):
        """
        Recirculation-Tanks nur bei geschlossenen Systemen (hydro, nft, ebb_flow).
        Stock-Solution-Tanks dürfen nicht direkt einer Location zugeordnet werden.
        """
        closed_systems = {'hydro', 'nft', 'ebb_flow'}
        if self.tank_type == TankType.RECIRCULATION:
            if self.location_irrigation_system not in closed_systems:
                raise ValueError(
                    f"Rezirkulationstank nur bei geschlossenen Systemen "
                    f"({', '.join(closed_systems)}), nicht bei "
                    f"'{self.location_irrigation_system}'"
                )
        if self.tank_type == TankType.STOCK_SOLUTION:
            raise ValueError(
                "Stammlösungs-Tanks dürfen nicht direkt einer Location zugeordnet werden — "
                "sie müssen über feeds_from-Kaskade in einen Mischtank dosiert werden."
            )
        return self

class FillLevelValidator(BaseModel):
    """Plausibilitätsprüfung für Füllstandsmeldungen"""

    tank_volume_liters: float
    fill_level_liters: Optional[float] = None
    fill_level_percent: Optional[float] = None

    @model_validator(mode='after')
    def validate_and_normalize(self):
        if self.fill_level_liters is not None:
            if self.fill_level_liters > self.tank_volume_liters * 1.05:
                raise ValueError(
                    f"Füllstand ({self.fill_level_liters}L) übersteigt "
                    f"Tankvolumen ({self.tank_volume_liters}L) um >5%"
                )
            # Prozent automatisch berechnen wenn nicht gegeben
            if self.fill_level_percent is None:
                self.fill_level_percent = round(
                    (self.fill_level_liters / self.tank_volume_liters) * 100, 1
                )
        return self
```

### REST-API-Endpunkte:
```
# Tank-CRUD
POST   /api/v1/locations/{location_key}/tanks          — Tank erstellen und Location zuordnen
GET    /api/v1/locations/{location_key}/tanks           — Alle Tanks einer Location
GET    /api/v1/tanks                                     — Alle Tanks (mit Filter: type, has_alerts)
GET    /api/v1/tanks/{tank_key}                          — Tank-Details inkl. aktuellem Zustand
PUT    /api/v1/tanks/{tank_key}                          — Tank-Stammdaten aktualisieren
DELETE /api/v1/tanks/{tank_key}                          — Tank entfernen (nur wenn nicht aktiv versorgt)

# Zustandsmessungen
POST   /api/v1/tanks/{tank_key}/states                  — Neue Messung erfassen
GET    /api/v1/tanks/{tank_key}/states                  — Messverlauf (Pagination + Zeitraum-Filter)
GET    /api/v1/tanks/{tank_key}/states/latest            — Aktuellste Messung
GET    /api/v1/tanks/{tank_key}/alerts                   — Aktuelle Alerts basierend auf letztem State

# Befüllungshistorie
POST   /api/v1/tanks/{tank_key}/fills                    — Befüllung dokumentieren (erzeugt TankFillEvent + optional TankState)
GET    /api/v1/tanks/{tank_key}/fills                    — Befüllungshistorie (Pagination + Zeitraum-Filter)
GET    /api/v1/tanks/{tank_key}/fills/latest              — Letzte Befüllung
GET    /api/v1/tanks/{tank_key}/fills/stats               — Befüllungsstatistik (Aggregation über Zeitraum)

# Gießvorgänge (Slot-/Pflanzenebene)
POST   /api/v1/watering-events                           — Gießvorgang dokumentieren (Slot-Auswahl im Body)
GET    /api/v1/slots/{slot_key}/watering-events           — Gießhistorie eines Slots (Pagination + Zeitraum-Filter)
GET    /api/v1/locations/{location_key}/watering-events   — Gießhistorie aller Slots einer Location
GET    /api/v1/locations/{location_key}/watering-stats    — Statistik: Fertigation vs. manuelle Ergänzung

# Gießplan-Bestätigungsflow (REQ-006 Task → WateringEvent → FeedingEvents)
POST   /api/v1/watering-events/confirm                   — Vollständige Bestätigung mit Details (Volumen, Methode, EC/pH-Messungen)
POST   /api/v1/watering-events/quick-confirm             — Ein-Tap-Bestätigung mit Plan-Defaults (Kiosk/Mobile-optimiert)

# Wartung
POST   /api/v1/tanks/{tank_key}/maintenance              — Wartung dokumentieren
GET    /api/v1/tanks/{tank_key}/maintenance               — Wartungshistorie
GET    /api/v1/tanks/{tank_key}/maintenance/due           — Fällige Wartungen

# Wartungspläne
POST   /api/v1/tanks/{tank_key}/schedules                — Wartungsplan anlegen
GET    /api/v1/tanks/{tank_key}/schedules                — Alle Pläne eines Tanks
PUT    /api/v1/tanks/{tank_key}/schedules/{schedule_key} — Plan anpassen
DELETE /api/v1/tanks/{tank_key}/schedules/{schedule_key} — Plan deaktivieren

# Übergreifend
GET    /api/v1/maintenance/due                            — Alle fälligen Wartungen (tankübergreifend)
GET    /api/v1/locations/{location_key}/tanks/validation  — Prüfe ob Location Tank braucht

# Sensor-Integration Bulk-Endpoints (CF-004, CF-005)
GET    /api/v1/tanks/states/latest                        — Bulk: Alle Tanks mit jeweils neuestem TankState in einem Call (verhindert N+1-Problem bei Polling)
GET    /api/v1/tanks/alerts                               — Bulk: Aggregierte Tank-Alerts aller Tanks

# Sensor-Integration Live-Query (nur bei HA-Direktanbindung)
GET    /api/v1/tanks/{tank_key}/states/live                — Live-Abfrage: Holt aktuelle Sensorwerte direkt von Home Assistant (nur für Sensoren mit ha_entity_id)

# Sensor-Integration Webhook (CF-010)
POST   /api/v1/webhooks/sensor-event                      — Webhook für Sensor→KP Push (HA, ESPHome, MQTT-Bridge etc.)
```

**Bulk-Endpoint `GET /tanks/states/latest`:**
<!-- Quelle: HA-REVIEW-CORE CF-004 -->

Response-Format:
```json
[
  {
    "tank_key": "tank_zelt1",
    "tank_name": "Haupttank Grow Zelt 1",
    "tank_type": "nutrient",
    "latest_state": {
      "recorded_at": "2026-02-26T10:00:00Z",
      "ph": 5.9,
      "ec_ms": 1.75,
      "water_temp_celsius": 21.5,
      "fill_level_percent": 85,
      "dissolved_oxygen_mgl": 7.2,
      "orp_mv": 720,
      "source": "home_assistant"
    }
  }
]
```

**Webhook `POST /webhooks/sensor-event`:**
<!-- Quelle: HA-REVIEW-CORE CF-010, erweitert für alle REQ-005 Datenkanäle -->

Der Webhook ist **source-agnostisch** — er akzeptiert Sensor-Daten aus beliebigen Quellen (Home Assistant, ESPHome, MQTT-Bridge, Modbus-Gateway etc.). Die Zuordnung zum Tank erfolgt über den REQ-005 `:Sensor` und dessen `monitors_tank`-Edge.

Request-Format:
```json
{
  "event_type": "sensor_reading",
  "sensor_id": "sensor_tank1_ec",
  "value": 1.82,
  "unit": "mS/cm",
  "source": "ha_auto",
  "timestamp": "2026-02-26T10:05:00Z"
}
```

Alternativ mit `entity_id` (für HA-Automationen, die den Sensor-Key nicht kennen):
```json
{
  "event_type": "sensor_reading",
  "entity_id": "sensor.tank1_ec",
  "value": 1.82,
  "source": "ha_auto",
  "timestamp": "2026-02-26T10:05:00Z"
}
```

Oder mit `mqtt_topic` (für MQTT-Bridge/ESPHome-Weiterleitungen):
```json
{
  "event_type": "sensor_reading",
  "mqtt_topic": "esphome/tank1/ec",
  "value": 1.82,
  "source": "mqtt_auto",
  "timestamp": "2026-02-26T10:05:00Z"
}
```

**Sensor-Auflösung (Priorität):**
1. `sensor_id` → direkter Lookup in `sensors`-Collection
2. `entity_id` → Lookup über `Sensor.ha_entity_id`
3. `mqtt_topic` → Lookup über `Sensor.mqtt_topic`

**Verarbeitung (Dual-Write):**
1. Sensor auflösen (siehe oben), dann über `monitors_tank`-Edge den zugeordneten Tank ermitteln
2. **TimescaleDB:** Sensorwert als REQ-005 `Observation` in `sensor_readings`-Hypertable schreiben (mit `sensor_id`, `value`, `source`, `timestamp`). Unterliegt dem 3-stufigen Downsampling (NFR-011 R-14: 90d raw → 2y stündlich → 5y täglich).
3. **ArangoDB:** Anhand `Sensor.parameter` das richtige TankState-Feld bestimmen (ec → `ec_ms`, ph → `ph`, water_temp → `water_temp_celsius`, fill_level → `fill_level_percent`, dissolved_oxygen → `dissolved_oxygen_mgl`, orp → `orp_mv`). `TankState` mit `source` aus Request erstellen (oder in bestehenden aktuellen State mergen, wenn mehrere Sensoren innerhalb eines kurzen Zeitfensters melden).
4. Unterstützte `event_type`-Werte: `sensor_reading`, `watering_completed` (erzeugt WateringEvent), `maintenance_completed` (erzeugt MaintenanceLog)

> **Dual-Write-Begründung:** TimescaleDB liefert die hochfrequente Langzeit-Historie mit automatischem Downsampling (Trend-Analyse, Charts). ArangoDB `TankState` bleibt der operative Snapshot für Alerts, Dashboard und API-Abfragen. Manuelle TankState-Eingaben (`source='manual'`) gehen nur nach ArangoDB — kein TimescaleDB-Eintrag nötig.

| HTTP-Status | Fehlerfall |
|-------------|-----------|
| `200` | Sensor-Reading erfolgreich verarbeitet |
| `404` | Sensor nicht gefunden (weder sensor_id, entity_id noch mqtt_topic matchen) |
| `404` | Sensor hat keinen `monitors_tank`-Edge (ist keinem Tank zugeordnet) |
| `422` | Unbekannter `event_type` oder ungültiger `value`-Typ |

**Live-Query `GET /tanks/{tank_key}/states/live`:**

Holt aktuelle Sensorwerte **direkt von der Home Assistant REST API** (`GET /api/states/{entity_id}`) für alle `monitors_tank`-Sensoren des Tanks, die eine `ha_entity_id` haben. Damit sieht der Nutzer exakt dieselben Werte wie in seinem HA-Dashboard — ohne Verzögerung durch Polling-Intervalle oder Push-Latenz.

**Voraussetzungen:**
- HA-Integration aktiviert (`ha_token_set == true`, siehe REQ-005 §4a)
- Mindestens ein Sensor am Tank hat eine `ha_entity_id`
- Nutzer hat `ha_url` und `ha_token` in den Kontoeinstellungen hinterlegt (REQ-023)

**Funktionsweise:**
1. Alle `monitors_tank`-Sensoren des Tanks laden
2. Sensoren nach Datenkanal filtern:
   - **`ha_entity_id` gesetzt:** Live-Abfrage via `HomeAssistantConnector.get_sensor_state(entity_id)` — Echtzeit-Wert
   - **`mqtt_topic` oder `modbus_address` (ohne `ha_entity_id`):** Letzten bekannten Wert aus ArangoDB `TankState` verwenden — mit Zeitstempel und Kennzeichnung als nicht-live
3. Zusammengesetztes Ergebnis zurückgeben

Response-Format:
```json
{
  "tank_key": "tank_zelt1",
  "queried_at": "2026-02-26T10:05:02Z",
  "ha_connected": true,
  "values": [
    {
      "parameter": "ec",
      "value": 1.82,
      "unit": "mS/cm",
      "source": "ha_live",
      "ha_entity_id": "sensor.tank1_ec",
      "timestamp": "2026-02-26T10:05:01Z",
      "freshness": "live"
    },
    {
      "parameter": "ph",
      "value": 5.9,
      "unit": "pH",
      "source": "ha_live",
      "ha_entity_id": "sensor.tank1_ph",
      "timestamp": "2026-02-26T10:05:01Z",
      "freshness": "live"
    },
    {
      "parameter": "water_temp",
      "value": 21.3,
      "unit": "°C",
      "source": "mqtt_auto",
      "mqtt_topic": "esphome/tank1/temp",
      "timestamp": "2026-02-26T10:03:45Z",
      "freshness": "recent"
    }
  ],
  "warnings": ["Parameter 'water_temp' ist nicht live-fähig (MQTT-Push, letzter Wert vor 77s)"]
}
```

**`freshness`-Stufen:**

| Stufe | Bedingung | Bedeutung |
|-------|-----------|-----------|
| `live` | Wert soeben von HA abgefragt | Echtzeit — identisch mit HA-Dashboard |
| `recent` | Letzter Push/Webhook < 5 Minuten alt | Aktuell, aber nicht garantiert live |
| `stale` | Letzter bekannter Wert 5–60 Minuten alt | Veraltet — Nutzer sollte manuell prüfen |
| `offline` | Kein Wert seit > 60 Minuten oder Sensor offline | Sensor ausgefallen oder nicht erreichbar |

**Fehlerbehandlung:**

| HTTP-Status | Fehlerfall |
|-------------|-----------|
| `200` | Werte erfolgreich abgefragt (auch wenn einzelne Sensoren nicht erreichbar — `warnings` enthält Details) |
| `404` | Tank nicht gefunden |
| `409` | HA-Integration nicht aktiviert (`ha_token_set == false`) |
| `502` | HA nicht erreichbar (alle HA-Sensoren, Timeout nach 10s) |

**Wichtig:** Dieser Endpoint ist **kein Ersatz** für das reguläre State-Tracking. Er erzeugt **keinen** TankState in ArangoDB und **keine** Observation in TimescaleDB. Er ist ein reiner Read-Through für die UI. Soll der Live-Wert persistiert werden, muss der Nutzer explizit "Messung übernehmen" klicken (→ `POST /tanks/{key}/states`).

### Datenherkunft-Kennzeichnung (UI)

Alle Sensor- und Messwerte in der UI tragen eine **Herkunftskennzeichnung**, damit der Nutzer erkennt, woher ein Wert stammt und wie aktuell er ist.

**Source-Badges (MUI Chip, klein, neben dem Messwert):**

| Source | Badge | Farbe | Tooltip |
|--------|-------|-------|---------|
| `manual` | `Manuell` | `default` (grau) | "Manuell eingegeben am {timestamp}" |
| `ha_auto` | `HA` | `info` (blau) | "Home Assistant — {ha_entity_id}, {timestamp}" |
| `ha_live` | `HA Live` | `success` (grün) | "Live von Home Assistant abgefragt, {timestamp}" |
| `mqtt_auto` | `MQTT` | `secondary` (lila) | "MQTT-Push — {mqtt_topic}, {timestamp}" |
| `modbus_auto` | `Modbus` | `secondary` (lila) | "Modbus-Sensor, {timestamp}" |

**Freshness-Indikator (zusätzlich zum Source-Badge):**

| Freshness | Darstellung | Beispiel |
|-----------|-------------|---------|
| `live` | Grüner Punkt (pulsierend) | `● 1.82 mS/cm` |
| `recent` | Grüner Punkt (statisch) + relative Zeitangabe | `● 1.82 mS/cm · vor 2 Min` |
| `stale` | Gelber Punkt + relative Zeitangabe | `● 1.82 mS/cm · vor 23 Min` |
| `offline` | Roter Punkt + "Offline" | `● — · Offline seit 2h` |

**Platzierung:** Auf allen Seiten, die TankState-Werte anzeigen:
- **TankDetailPage:** State-Karten im Überblick-Tab — jeder Wert mit Source-Badge + Freshness
- **TankDetailPage Live-Tab:** Separater Tab "Live" (nur sichtbar wenn HA aktiv oder Sensoren vorhanden) — zeigt alle Sensorwerte mit Auto-Refresh (konfigurierbar: 10s/30s/60s/aus)
- **Dashboard Tank-Widget:** Kompakt — nur Freshness-Punkt, Tooltip zeigt Source

**i18n-Keys:**
```
tanks.source.manual: "Manuell" / "Manual"
tanks.source.ha_auto: "HA" / "HA"
tanks.source.ha_live: "HA Live" / "HA Live"
tanks.source.mqtt_auto: "MQTT" / "MQTT"
tanks.source.modbus_auto: "Modbus" / "Modbus"
tanks.freshness.live: "Live" / "Live"
tanks.freshness.recent: "vor {minutes} Min" / "{minutes} min ago"
tanks.freshness.stale: "vor {minutes} Min (veraltet)" / "{minutes} min ago (stale)"
tanks.freshness.offline: "Offline seit {duration}" / "Offline for {duration}"
tanks.live.title: "Live-Sensorwerte" / "Live Sensor Values"
tanks.live.ha_only: "Live-Abfrage nur mit Home Assistant möglich" / "Live query requires Home Assistant"
tanks.live.adopt_value: "Messung übernehmen" / "Adopt reading"
tanks.live.auto_refresh: "Auto-Refresh" / "Auto-refresh"
tanks.live.push_delay_hint: "MQTT/Webhook-Werte können verzögert sein" / "MQTT/Webhook values may be delayed"
```

### Seed-Daten:
```json
// tanks collection
{ "_key": "tank_zelt1", "name": "Haupttank Grow Zelt 1", "tank_type": "nutrient", "volume_liters": 50, "material": "plastic", "has_lid": true, "has_air_pump": true, "has_circulation_pump": true, "has_heater": false, "installed_on": "2025-06-01" }
{ "_key": "tank_regenwasser", "name": "Regenwassertonne Garten", "tank_type": "reservoir", "volume_liters": 300, "material": "plastic", "has_lid": true, "has_air_pump": false, "has_circulation_pump": false, "has_heater": false, "installed_on": "2024-03-15" }
{ "_key": "tank_recirc_nft", "name": "NFT-Rücklauf Zelt 2", "tank_type": "recirculation", "volume_liters": 20, "material": "plastic", "has_lid": true, "has_air_pump": true, "has_circulation_pump": true, "has_heater": false, "has_uv_sterilizer": true, "has_ozone_generator": false, "installed_on": "2025-09-10" }

// has_tank edge collection
{ "_from": "locations/growzelt1", "_to": "tanks/tank_zelt1" }
{ "_from": "locations/garten", "_to": "tanks/tank_regenwasser" }
{ "_from": "locations/growzelt2", "_to": "tanks/tank_recirc_nft" }

// supplies edge collection
{ "_from": "tanks/tank_zelt1", "_to": "locations/growzelt1" }
{ "_from": "tanks/tank_regenwasser", "_to": "locations/garten" }
{ "_from": "tanks/tank_recirc_nft", "_to": "locations/growzelt2" }

// feeds_from edge collection (Kaskade: Regenwasser → Mischtank)
{ "_from": "tanks/tank_zelt1", "_to": "tanks/tank_regenwasser" }

// tank_fill_events collection
{ "_key": "fill_zelt1_001", "filled_at": "2026-02-19T10:00:00Z", "fill_type": "full_change", "volume_liters": 48, "mixing_result_key": null, "nutrient_plan_key": "plan_tomato_coco", "target_ec_ms": 1.8, "target_ph": 5.8, "measured_ec_ms": 1.75, "measured_ph": 5.9, "water_source": "osmose", "source_tank_key": "tank_regenwasser", "base_water_ec_ms": 0.05, "fertilizers_used": [{"product_name": "CalMag", "ml_per_liter": 1.0, "product_key": "fert_calmag"}, {"product_name": "Flora Micro", "ml_per_liter": 1.5, "product_key": "fert_micro"}, {"product_name": "Flora Bloom", "ml_per_liter": 2.0, "product_key": "fert_bloom"}], "performed_by": "admin", "notes": "Wöchentlicher Vollwechsel" }
{ "_key": "fill_zelt1_002", "filled_at": "2026-02-22T08:30:00Z", "fill_type": "top_up", "volume_liters": 12, "mixing_result_key": null, "nutrient_plan_key": "plan_tomato_coco", "target_ec_ms": 1.8, "target_ph": null, "measured_ec_ms": 1.7, "measured_ph": 6.0, "water_source": "osmose", "source_tank_key": null, "base_water_ec_ms": 0.05, "fertilizers_used": [{"product_name": "CalMag", "ml_per_liter": 0.5, "product_key": "fert_calmag"}, {"product_name": "Flora Micro", "ml_per_liter": 1.5, "product_key": "fert_micro"}, {"product_name": "Flora Bloom", "ml_per_liter": 2.0, "product_key": "fert_bloom"}], "performed_by": "admin", "notes": "Verdunstung ausgeglichen — CalMag auch bei Top-Up essenziell bei Coco/Osmose (CEC bindet Ca/Mg)" }
{ "_key": "fill_zelt1_003", "filled_at": "2026-02-24T14:00:00Z", "fill_type": "adjustment", "volume_liters": 2, "mixing_result_key": null, "nutrient_plan_key": null, "target_ec_ms": null, "target_ph": 5.8, "measured_ec_ms": 1.85, "measured_ph": 5.7, "water_source": null, "source_tank_key": null, "base_water_ec_ms": null, "fertilizers_used": [], "performed_by": "admin", "notes": "pH-Down Korrektur (pH war auf 6.5 gedriftet)" }

// has_fill_event edge collection
{ "_from": "tanks/tank_zelt1", "_to": "tank_fill_events/fill_zelt1_001" }
{ "_from": "tanks/tank_zelt1", "_to": "tank_fill_events/fill_zelt1_002" }
{ "_from": "tanks/tank_zelt1", "_to": "tank_fill_events/fill_zelt1_003" }

// watering_events collection (Slot-/Pflanzenebene)
{ "_key": "water_evt_001", "watered_at": "2026-02-19T11:00:00Z", "application_method": "fertigation", "is_supplemental": false, "volume_liters": 2.5, "slot_keys": ["GROWZELT1_A1", "GROWZELT1_A2", "GROWZELT1_A3"], "tank_fill_event_key": "fill_zelt1_001", "nutrient_plan_key": "plan_tomato_coco", "fertilizers_used": [], "target_ec_ms": 1.8, "measured_ec_ms": null, "runoff_ec_ms": 1.6, "runoff_ph": 6.1, "water_source": "tank", "performed_by": "admin", "notes": "Reguläre Tropfer-Bewässerung nach Vollwechsel" }
{ "_key": "water_evt_002", "watered_at": "2026-02-20T09:00:00Z", "application_method": "drench", "is_supplemental": true, "volume_liters": 1.5, "slot_keys": ["GROWZELT1_A1", "GROWZELT1_A2"], "tank_fill_event_key": null, "nutrient_plan_key": null, "fertilizers_used": [{"product_name": "Komposttee (selbst gebraut)", "ml_per_liter": 0, "product_key": null}, {"product_name": "Mykorrhiza-Suspension", "ml_per_liter": 2.0, "product_key": "fert_myko"}], "target_ec_ms": null, "measured_ec_ms": null, "water_source": "rainwater", "performed_by": "admin", "notes": "Organische Ergänzungsdüngung per Gießkanne — Komposttee + Mykorrhiza, nicht über Tropfer" }
{ "_key": "water_evt_003", "watered_at": "2026-02-22T16:00:00Z", "application_method": "foliar", "is_supplemental": true, "volume_liters": 0.3, "slot_keys": ["GROWZELT1_A1", "GROWZELT1_A2", "GROWZELT1_A3"], "tank_fill_event_key": null, "nutrient_plan_key": null, "fertilizers_used": [{"product_name": "CalMag Foliar Spray", "ml_per_liter": 0.5, "product_key": "fert_calmag_foliar"}], "target_ec_ms": null, "measured_ec_ms": null, "water_source": "osmose", "performed_by": "admin", "notes": "Blattdüngung mit Kalzium gegen Blütenend-Fäule" }

// watered_slot edge collection
{ "_from": "watering_events/water_evt_001", "_to": "slots/GROWZELT1_A1" }
{ "_from": "watering_events/water_evt_001", "_to": "slots/GROWZELT1_A2" }
{ "_from": "watering_events/water_evt_001", "_to": "slots/GROWZELT1_A3" }
{ "_from": "watering_events/water_evt_002", "_to": "slots/GROWZELT1_A1" }
{ "_from": "watering_events/water_evt_002", "_to": "slots/GROWZELT1_A2" }
{ "_from": "watering_events/water_evt_003", "_to": "slots/GROWZELT1_A1" }
{ "_from": "watering_events/water_evt_003", "_to": "slots/GROWZELT1_A2" }
{ "_from": "watering_events/water_evt_003", "_to": "slots/GROWZELT1_A3" }

// watering_from edge collection (WateringEvent → TankFillEvent)
{ "_from": "watering_events/water_evt_001", "_to": "tank_fill_events/fill_zelt1_001" }

// maintenance_schedules (automatisch bei Tank-Erstellung generiert)
{ "_key": "sched_zelt1_wc", "maintenance_type": "water_change", "interval_days": 7, "reminder_days_before": 1, "is_active": true, "priority": "high", "auto_create_task": true }
{ "_key": "sched_zelt1_clean", "maintenance_type": "cleaning", "interval_days": 30, "reminder_days_before": 3, "is_active": true, "priority": "medium", "auto_create_task": true }
{ "_key": "sched_zelt1_cal", "maintenance_type": "calibration", "interval_days": 14, "reminder_days_before": 1, "is_active": true, "priority": "medium", "auto_create_task": true }

// has_schedule edges
{ "_from": "tanks/tank_zelt1", "_to": "maintenance_schedules/sched_zelt1_wc" }
{ "_from": "tanks/tank_zelt1", "_to": "maintenance_schedules/sched_zelt1_clean" }
{ "_from": "tanks/tank_zelt1", "_to": "maintenance_schedules/sched_zelt1_cal" }
```

### Gießplan-Bestätigungsflow

Der Bestätigungsflow verbindet REQ-006 (Task) mit REQ-014 (WateringEvent) und REQ-004 (FeedingEvent). Ein Gießplan-Task (erzeugt von `generate_watering_tasks`) wird bestätigt und erzeugt dabei die zugehörigen Events.

**`POST /api/v1/watering-events/confirm` — Vollständige Bestätigung:**

Für erfahrene Nutzer, die Details anpassen möchten (Volumen, EC/pH-Messungen, Dünger-Override).

```json
// Request
{
    "task_key": "feeding:watering:tomaten_hochbeet_a_2025:2026-02-27",
    "application_method": "drench",
    "volume_liters": 10.0,
    "use_plan_dosages": true,
    "fertilizers_override": null,
    "measured_ec_ms": 1.75,
    "measured_ph": 5.9,
    "runoff_ec_ms": 2.1,
    "runoff_ph": 6.2,
    "water_source": "osmose",
    "notes": "Leichte Welke an TOM-03 beobachtet"
}

// Response (201 Created)
{
    "watering_event_key": "watering_evt_20260227_001",
    "task_key": "feeding:watering:tomaten_hochbeet_a_2025:2026-02-27",
    "task_status": "completed",
    "watering_event": {
        "watered_at": "2026-02-27T08:15:00Z",
        "application_method": "drench",
        "volume_liters": 10.0,
        "slot_keys": ["HOCHBEETA_1", "HOCHBEETA_2", "..."],
        "measured_ec_ms": 1.75,
        "measured_ph": 5.9,
        "nutrient_plan_key": "plan_tomato_coco",
        "task_key": "feeding:watering:tomaten_hochbeet_a_2025:2026-02-27"
    },
    "feeding_events_created": 18,
    "phase_summary": [
        {"phase": "vegetative", "plant_count": 15, "target_ec_ms": 1.4},
        {"phase": "flowering", "plant_count": 3, "target_ec_ms": 1.8}
    ]
}
```

**Ablauf (confirm):**
1. Task validieren: existiert, status='pending' oder 'in_progress', hat planting_run_key
2. PlantingRun laden + NutrientPlan auflösen
3. Slots aller aktiven Pflanzen im Run ermitteln
4. WateringEvent erstellen (mit task_key als Rückreferenz)
5. `watered_slot`-Edges für alle betroffenen Slots erzeugen
6. Wenn `use_plan_dosages=true`:
   - Pflanzen nach Phase gruppieren (via WateringScheduleEngine.resolve_dosages_for_run)
   - Für jede Pflanze: FeedingEvent (REQ-004) mit phasen-spezifischen Dosierungen erstellen
   - FED_BY-Edge (PlantInstance → FeedingEvent) + TRIGGERED_BY-Edge (FeedingEvent → WateringEvent)
7. Wenn `fertilizers_override` gesetzt: Override-Dosierungen statt Plan-Dosierungen verwenden
8. Task als 'completed' markieren + watering_event_key setzen
9. CareConfirmation (REQ-022) erzeugen für adaptive Learning (sofern CareProfile existiert)

**`POST /api/v1/watering-events/quick-confirm` — Ein-Tap-Bestätigung:**

Für Einsteiger, Kiosk-Modus und Mobile. Nutzt alle Defaults aus dem NutrientPlan.

```json
// Request (minimal)
{
    "task_key": "feeding:watering:tomaten_hochbeet_a_2025:2026-02-27",
    "notes": null
}

// Response (201 Created)
{
    "watering_event_key": "watering_evt_20260227_002",
    "task_key": "feeding:watering:tomaten_hochbeet_a_2025:2026-02-27",
    "task_status": "completed",
    "defaults_used": {
        "application_method": "drench",
        "volume_liters": 2.0,
        "from_plan": "Tomato Heavy Coco"
    },
    "feeding_events_created": 18
}
```

**Ablauf (quick-confirm):**
1. Task validieren (wie confirm)
2. PlantingRun + NutrientPlan laden
3. Defaults aus WateringSchedule (application_method) und NutrientPlanPhaseEntry (volume_per_feeding_liters) übernehmen
4. WateringEvent erstellen mit Defaults
5. FeedingEvents erstellen (wie confirm, mit Plan-Dosierungen)
6. Task als 'completed' markieren
7. CareConfirmation (REQ-022) erzeugen

**Fehlerbehandlung:**

| HTTP-Status | Fehlerfall |
|-------------|-----------|
| `400` | task_key fehlt oder ungültiges Format |
| `404` | Task nicht gefunden oder kein PlantingRun zugeordnet |
| `409` | Task bereits completed (Duplikat-Schutz) |
| `422` | PlantingRun hat keinen NutrientPlan; Run ist nicht aktiv |

## 4. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt wurde nachträglich ergänzt, um die Auth-Anforderungen
> gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung) zu dokumentieren.

**Standardregel:** Alle Endpunkte dieses REQ erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft, sofern nicht anders angegeben.

| Ressource/Endpoint-Gruppe | Lesen | Schreiben | Löschen |
|---------------------------|-------|-----------|---------|
| Tanks | Mitglied | Mitglied | Admin |
| Tank-States | Mitglied | Mitglied | — |
| Tank-Fills | Mitglied | Mitglied | — |
| Watering-Events | Mitglied | Mitglied | Admin |

## 5. Abhängigkeiten

**Erforderliche Module:**
- REQ-002 (Standort): Location für Tank-Zuordnung, `irrigation_system` für Pflicht-Validierung; **HOCH** — `Site.water_source` (TapWaterProfile, RoWaterProfile) als Default-Quelle in der Wasserquellen-Kaskade für TankFillEvent-Felder
- REQ-004 (Düngung): **HOCH** — MixingResult als Input für Tank-Befüllung; NutrientPlan + WateringScheduleEngine für Bestätigungsflow (Dosierungs-Auflösung pro Phase); FeedingEvent-Erzeugung bei Gießplan-Bestätigung
- REQ-005 (Sensorik): **HOCH** — Sensor-Daten für automatische Zustandserfassung (pH, EC, Füllstand, Temperatur, DO, ORP). `monitors_tank`-Edge verknüpft REQ-005 `:Sensor` (mit `ha_entity_id`, `mqtt_topic` oder `modbus_address`) mit Tank. Unterstützt alle 4 Datenkanäle gleichwertig: Home Assistant (`ha_auto`), MQTT direkt/ESPHome (`mqtt_auto`), Modbus (`modbus_auto`), manuell (`manual`). Webhook `POST /webhooks/sensor-event` als Push-Kanal. **Hinweis:** Bei `UserPreference.smart_home_enabled == false` (REQ-005 §4b) werden Sensor-Binding-Sektion, Live-Query-Button und Source-Badges ausgeblendet — Tank-Zustände dann nur manuell erfassbar.
- REQ-006 (Aufgabenplanung): **HOCH** — Task-Completion bei Gießplan-Bestätigung; `planting_run_key` und `watering_event_key` auf Task
- REQ-013 (Pflanzdurchlauf): **HOCH** — PlantingRun als Gruppierungs-Container für Bestätigungsflow; Pflanzen-Phasen-Gruppierung; Slot-Ermittlung

**Wird benötigt von:**
- REQ-004 (Düngung): **HOCH** — Tank als Zielgefäß für MixingResult; EC-Budget basiert auf Tank-Volumen
- REQ-005 (Sensorik): **MITTEL** — Tank-Sensoren als zusätzliche Sensor-Locations (Füllstand, Wassertemperatur)
- REQ-006 (Aufgabenplanung): **HOCH** — Wartungs-Tasks werden automatisch aus MaintenanceSchedule generiert
- REQ-009 (Dashboard): **MITTEL** — Tank-Status-Widget, Alert-Anzeige, fällige Wartungen
- REQ-013 (Pflanzdurchlauf): **MITTEL** — PlantingRun referenziert Tank als Versorgungsquelle; Gießkalender-Endpoint nutzt WateringEvent-Historie
- REQ-022 (Pflegeerinnerungen): **NIEDRIG** — CareConfirmation-Interop bei Gießplan-Bestätigung (Adaptive Learning)
- REQ-018 (Aktorik): **MITTEL** — Stock-Solution-Tanks als Quelle für automatisierte Dosierpumpen

**Celery-Tasks:**
- `check_maintenance_due` — Täglich: Prüft alle Tanks auf fällige Wartungen, erzeugt Tasks (REQ-006)
- `check_tank_alerts` — Stündlich: Prüft Tank-Zustände gegen Grenzwerte, erzeugt Alerts

## 6. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **Tank-CRUD:** Vollständiges Erstellen, Lesen, Aktualisieren und Löschen von Tanks
- [ ] **Location-Zuordnung:** Tank wird über `has_tank`-Edge einer Location zugeordnet
- [ ] **Pflicht-Validierung:** Bei `irrigation_system != 'manual'` wird ein zugeordneter Tank erzwungen
- [ ] **Tank-Typen:** Alle 4 Typen (nutrient, irrigation, reservoir, recirculation) unterstützt
- [ ] **Typ-Kompatibilität:** Recirculation-Tank nur bei geschlossenen Systemen erlaubt
- [ ] **Zustandserfassung:** Manuelle und automatische (REQ-005) Messungen für pH, EC, Temperatur, DO, ORP, Füllstand
- [ ] **Zustandshistorie:** Zeitserie von TankState-Records mit Pagination und Zeitraum-Filter
- [ ] **Alert-System (differenziert):** Tank-Typ-abhängige Grenzwert-Prüfung:
  - pH-Grenzen nach Tank-Typ (nutrient: 5.5–6.5, recirculation: 5.5–6.3, irrigation: 5.8–6.8)
  - EC relativ zum Ziel-EC des letzten Fill-Events (Warnung >20%, Alarm >30%)
  - Temperatur differenziert (Wärme UND Kälte, nach Tank-Typ)
  - DO-Alerts für Hydroponik (<4 mg/L kritisch, <6 mg/L suboptimal)
  - ORP-Alerts für Rezirkulation (<250 mV Pathogen-Risiko, <650 mV Sterilisation unzureichend)
  - Lösungsalter-Warnung (5d mit Organik / 10d mineralisch)
  - pH-Drift relativ zum letzten Wasserwechsel
- [ ] **Befüllungshistorie:** Jede Tankbefüllung wird als immutables TankFillEvent dokumentiert
- [ ] **Befüllungstypen:** Vollwechsel, Auffüllen und Korrektur werden unterschieden
- [ ] **Rezept-Verknüpfung:** TankFillEvent kann optional auf MixingResult und NutrientPlan (REQ-004) referenzieren
- [ ] **Dünger-Snapshot:** Verwendete Dünger + Dosierungen werden als unveränderliche Kopie im Event gespeichert
- [ ] **Soll/Ist-Vergleich:** Ziel-EC/pH und gemessene Werte nach Befüllung werden erfasst
- [ ] **Wasserquellen-Qualität:** Chlor/Chloramin (ppm) und Alkalinität (ppm) optional erfassbar auf TankFillEvent
- [ ] **Chlor-Warnung:** Bei Chlor >0.5 ppm + biologischen Additiven (Mykorrhiza, Trichoderma, Bacillus) wird Entchlorung empfohlen
- [ ] **Desinfektions-Infrastruktur:** TankDefinition unterstützt `has_uv_sterilizer` und `has_ozone_generator`
- [ ] **Volumen-Plausibilität:** Foliar-spezifische Grenzwerte (>0.5L/Slot = Warnung), substrat-relative Prüfung wenn Slot-Volumen verfügbar
- [ ] **Automatischer TankState:** Bei Befüllung mit Messwerten wird automatisch ein TankState-Record erzeugt
- [ ] **Befüllungsstatistik:** Aggregierte Auswertung über Zeiträume (Anzahl, Volumen, EC-Abweichung)
- [ ] **WateringEvent:** Gießvorgänge auf Slot-/Pflanzenebene werden als immutable Events dokumentiert
- [ ] **Applikationsmethoden:** Fertigation, Drench, Foliar und Top Dress werden unterschieden
- [ ] **Ergänzende Handdüngung:** Manuelles Gießen per Gießkanne kann als `is_supplemental=true` neben automatischer Bewässerung dokumentiert werden
- [ ] **Tank-Safety-Warnung:** Bei nicht-tanksicheren Düngern (`tank_safe=false` aus REQ-004) im TankFillEvent wird Warnung ausgegeben und Drench empfohlen
- [ ] **Slot-Gießhistorie:** Vollständige Gießhistorie pro Slot abrufbar (alle Applikationsmethoden)
- [ ] **Statistik:** Vergleich Fertigation vs. manuelle Ergänzungsdüngung pro Location/Zeitraum
- [ ] **Wartungshistorie:** Alle Wartungsaktionen dokumentiert mit Typ, Datum, Produkten
- [ ] **Wartungspläne:** Wiederkehrende Schedules mit konfigurierbarem Intervall und Erinnerung
- [ ] **Standard-Schedules:** Bei Tank-Erstellung werden Default-Wartungspläne automatisch angelegt (je nach Tank-Typ)
- [ ] **Task-Generierung:** Fällige Wartungen erzeugen automatisch Tasks in REQ-006
- [ ] **Tank-Kaskade:** `feeds_from`-Edge für Tankketten (Reservoir → Mischtank)
- [ ] **Lösch-Schutz:** Tank kann nicht gelöscht werden, wenn er aktive Location versorgt
- [ ] **Füllstand-Plausibilität:** Füllstand kann Tank-Volumen nicht signifikant übersteigen
- [ ] **Celery-Beat:** `check_maintenance_due` (täglich) und `check_tank_alerts` (stündlich) registriert
- [ ] **Salting-Out-Effekt:** DO-Sättigungsbeschreibung berücksichtigt EC-Einfluss auf Gasloeslichkeit
- [ ] **Organik-Erkennung:** Lösungsalter-Check basiert auf `is_organic`-Flag (FertilizerSnapshot), nicht auf fehlendem `product_key`
- [ ] **Chlor/Chloramin-Differenzierung:** Separate Felder `chlorine_ppm` und `chloramine_ppm` mit differenzierten Entchlorungsempfehlungen
- [ ] **EC-Drift-Trend:** Rezirkulation erkennt steigende/fallende EC-Trends über letzte 3+ Messungen mit diagnostischer Empfehlung
- [ ] **Compound-Alert Temperatur×DO:** Kreuz-Validierung priorisiert Ursachenbehebung (Temperatur senken) über Symptombekämpfung (Belüftung)
- [ ] **Biofilm-Risiko:** Multifaktorieller Alert (Temperatur, Organik, UV/Ozon, Lösungsalter) für Rezirkulation
- [ ] **Stock-Solution Tank-Typ:** `stock_solution` in TankType mit angepassten Grenzwerten (EC bis 250 mS) und Direktzuordnungs-Sperre
- [ ] **Runoff-Interpretation:** Substratabhängige Interpretation von Drain-EC über Slot→Substrat-Kette dokumentiert
- [ ] **Nachfüllwasser-Temperatur:** `water_temperature_celsius` auf TankFillEvent mit Wurzelschock-Warnung bei Delta >5°C
- [ ] **Q10-Lösungsalter:** Temperaturkorrigiertes Lösungsalter (Degradation verdoppelt sich pro 10°C über 20°C-Referenz)
- [ ] **Substratspezifische pH-Bereiche:** `PH_RANGES_BY_SUBSTRATE` für Irrigation-Tanks (Coco: 5.8–6.2, Erde: 6.0–6.8, Living Soil: 6.2–6.8)
- [ ] **Lichtdichtheit:** `is_light_proof` auf TankDefinition als primärer Faktor für Algenrisiko-Score
- [ ] **FertilizerSnapshot Feststoffe:** `g_per_liter` für Top-Dress/Trockendünger neben `ml_per_liter`
- [ ] **Seed-Daten CalMag:** Top-Up bei Coco/Osmose enthält CalMag (CEC-Sättigung)
- [ ] **Differenzierte Kalibrierungsintervalle:** Kalibrierungsintervall nach Tank-Typ und Sondenplatzierung (Rezirkulation inline: 7d, Nährstoff: 14d, Irrigation: 21d, Reservoir: 28d)
- [ ] **Gießplan-Confirm:** POST /watering-events/confirm erzeugt WateringEvent + FeedingEvents + Task-Completion in einer Transaktion
- [ ] **Gießplan-Quick-Confirm:** POST /watering-events/quick-confirm nutzt Plan-Defaults (Volumen, Methode, Dosierungen)
- [ ] **Phasen-Dosierung:** Bei `use_plan_dosages=true` werden Dosierungen automatisch pro Phase aus NutrientPlan aufgelöst
- [ ] **Fertilizer-Override:** Bei Angabe von `fertilizers_override` werden Override-Dosierungen statt Plan-Dosierungen verwendet
- [ ] **Task-Rückreferenz:** WateringEvent.task_key verlinkt zurück auf den bestätigten Gießplan-Task
- [ ] **Duplikat-Schutz:** Bereits bestätigte Tasks (status='completed') werden mit 409 Conflict abgelehnt
- [ ] **CareConfirmation-Interop:** Bei Gießplan-Bestätigung wird automatisch CareConfirmation (REQ-022) erzeugt
- [ ] **TankFillEvent water_mix_ratio_ro_percent:** Optionales Feld (0–100) auf TankFillEvent speicher-/lesbar
- [ ] **TankFillEvent water_source 'mixed':** Neuer Enum-Wert `'mixed'` für Osmose/Leitungswasser-Mischungen
- [ ] **resolve_water_defaults Kaskade:** Fehlende Wasserquellen-Felder werden über die 4-stufige Kaskade (explizit → NutrientPlan → Site → manuell) aufgelöst
- [ ] **water_defaults_source:** API-Response enthält `water_defaults_source`-Feld mit der Quelle der aufgelösten Defaults
- [ ] **Kaskade-Transparenz:** Nutzer sieht im UI, ob `base_water_ec_ms` manuell eingegeben oder aus Site/Plan berechnet wurde
- [ ] **WaterMixCalculator-Integration:** Bei bekanntem Mischverhältnis wird `base_water_ec_ms` automatisch via WaterMixCalculator (REQ-004) berechnet
- [ ] **Sensor-Binding via monitors_tank Edge:** REQ-005 `:Sensor` wird über `monitors_tank`-Edge mit Tank verknüpft. Sensor trägt `ha_entity_id`, `mqtt_topic` oder `modbus_address` — alle Datenkanäle gleichwertig (CF-006)
- [ ] **Sensor-Parameter-Mapping:** `Sensor.parameter` bestimmt das TankState-Feld: ec→`ec_ms`, ph→`ph`, water_temp→`water_temp_celsius`, fill_level→`fill_level_percent`, dissolved_oxygen→`dissolved_oxygen_mgl`, orp→`orp_mv`
- [ ] **Bulk-States-Endpoint:** `GET /tanks/states/latest` liefert alle Tanks mit jeweils neuestem TankState in einem API-Call (CF-004)
- [ ] **Bulk-Alerts-Endpoint:** `GET /tanks/alerts` liefert aggregierte Tank-Alerts aller Tanks in einem API-Call
- [ ] **Webhook Source-Agnostisch:** `POST /webhooks/sensor-event` akzeptiert Sensor-Daten aus beliebigen Quellen (HA, ESPHome, MQTT-Bridge, Modbus-Gateway) und routet über `sensor_id`, `entity_id` oder `mqtt_topic` zum Tank (CF-010)
- [ ] **Webhook Dual-Write:** Webhook schreibt Sensorwert parallel als REQ-005 `Observation` in TimescaleDB (mit Downsampling) und als `TankState` in ArangoDB
- [ ] **Manuelle Eingabe nur ArangoDB:** Manuelle TankState-Eingaben (`source='manual'`) gehen nur nach ArangoDB, kein TimescaleDB-Eintrag
- [ ] **DO/ORP-Export:** `dissolved_oxygen_mgl` und `orp_mv` als HA-Entities in HA-CUSTOM-INTEGRATION.md exportiert (CF-005)
- [ ] **Live-Query Endpoint:** `GET /tanks/{key}/states/live` fragt Sensorwerte direkt von HA ab (nur Sensoren mit `ha_entity_id`). Kein TankState/Observation erzeugt — reiner Read-Through.
- [ ] **Live-Query Fallback:** Sensoren ohne `ha_entity_id` (MQTT/Modbus) liefern letzten bekannten Wert aus ArangoDB mit Zeitstempel und `freshness`-Angabe
- [ ] **Live-Query Voraussetzung:** Endpoint gibt `409` wenn HA-Integration nicht aktiviert (`ha_token_set == false`)
- [ ] **Messung übernehmen:** UI bietet "Messung übernehmen"-Button für Live-Werte → erstellt TankState + Observation via `POST /tanks/{key}/states`
- [ ] **Source-Badge:** Alle Messwerte in der UI zeigen Source-Badge (MUI Chip): `Manuell`, `HA`, `HA Live`, `MQTT`, `Modbus`
- [ ] **Freshness-Indikator:** Messwerte zeigen farbcodierten Freshness-Punkt: `live` (grün pulsierend), `recent` (grün statisch), `stale` (gelb), `offline` (rot)
- [ ] **Live-Tab:** TankDetailPage zeigt "Live"-Tab nur wenn HA aktiv oder Sensoren vorhanden. Auto-Refresh konfigurierbar (10s/30s/60s/aus).
- [ ] **Push-Delay-Hinweis:** UI zeigt Hinweis bei MQTT/Webhook-Sensoren: "MQTT/Webhook-Werte können verzögert sein"

### Testszenarien:

**Szenario 1: Tank-Pflicht bei automatischer Bewässerung**
```
GIVEN: Location "Grow Zelt 1" mit irrigation_system="drip", kein Tank zugeordnet
WHEN: System validiert Location-Konfiguration
THEN:
  - Warnung: "Automatische Bewässerung konfiguriert, aber kein Tank zugeordnet"
  - Validierung schlägt fehl bei Versuch, Bewässerung zu starten
  - Nach Zuordnung eines Tanks: Validierung OK
```

**Szenario 2: Wasserwechsel-Fälligkeit und Task-Generierung**
```
GIVEN: Tank "Haupttank Zelt 1" (nutrient), Wasserwechsel-Intervall 7 Tage,
       letzter Wechsel vor 8 Tagen
WHEN: Celery-Task `check_maintenance_due` läuft
THEN:
  - Wartung "water_change" ist 1 Tag überfällig
  - Neuer Task wird in REQ-006 generiert:
    Titel: "Tank 'Haupttank Zelt 1': Water Change"
    Priorität: critical (überfällig)
  - Dashboard zeigt Alert
```

**Szenario 3: Tank-Alerts bei kritischen Werten**
```
GIVEN: Nährstofftank mit Zustand: pH=7.0, EC=2.8, Wassertemp=27°C, DO=3.5, Füllstand=15%
       Letzter Vollwechsel mit target_ec_ms=1.8, measured_ph=5.8
WHEN: System prüft Grenzwerte
THEN:
  - 6 Alerts erzeugt:
    1. "pH 7.0 außerhalb Zielbereich (5.5–6.5) für Tank-Typ 'nutrient'" — severity: critical (>0.5 über Grenze)
    2. "pH-Drift 1.2 seit letzter Befüllung (war 5.8, jetzt 7.0)" — severity: medium
    3. "EC 2.80 mS — 56% vom Ziel (1.80 mS) abgewichen (gestiegen). Salzakkumulation?" — severity: high
    4. "Wassertemperatur 27.0°C — kritisch! DO sinkt, Pythium-Risiko steigt." — severity: critical
    5. "Gelöstsauerstoff 3.5 mg/L — kritisch niedrig! Anaerobe Bedingungen." — severity: critical
    6. "Füllstand 15% — Nachfüllen erforderlich" — severity: high
```

**Szenario 4: Recirculation-Tank nur bei geschlossenem System**
```
GIVEN: Location "Beet A" mit irrigation_system="drip" (offenes System)
WHEN: Nutzer versucht einen Recirculation-Tank zuzuordnen
THEN:
  - System lehnt ab: "Rezirkulationstank nur bei geschlossenen Systemen (hydro, nft, ebb_flow)"
  - Bei Location mit irrigation_system="nft": Zuordnung erfolgreich
```

**Szenario 5: Tank-Kaskade (Reservoir → Mischtank)**
```
GIVEN: "Regenwassertonne" (reservoir, 300L) → feeds_from → "Haupttank Zelt 1" (nutrient, 50L)
WHEN: Nutzer füllt Haupttank auf und mischt Nährstofflösung
THEN:
  - System zeigt Quell-Tank (Regenwassertonne) als Wasserquelle
  - Basis-EC wird von Regenwasser-Tank übernommen (nicht Leitungswasser-Default)
  - REQ-004 MixingResult referenziert beide Tanks
```

**Szenario 6: Standard-Wartungspläne bei Tank-Erstellung**
```
GIVEN: Nutzer erstellt neuen Tank vom Typ "recirculation"
WHEN: Tank wird gespeichert
THEN:
  - 6 Wartungspläne automatisch angelegt:
    water_change (7d, critical), cleaning (14d, high),
    sanitization (14d, critical), calibration (14d, high),
    pump_inspection (14d, medium), filter_change (30d, high)
  - Alle Pläne mit auto_create_task=true
  - Nutzer kann Intervalle individuell anpassen
```

**Szenario 7: Tank-Löschung mit aktiver Versorgung**
```
GIVEN: Tank "Haupttank Zelt 1" versorgt Location "Grow Zelt 1" (3 aktive Pflanzen)
WHEN: Nutzer versucht Tank zu löschen
THEN:
  - System blockiert: "Tank kann nicht gelöscht werden — versorgt aktiv 'Grow Zelt 1'"
  - Nutzer muss zuerst Zuordnung auflösen oder Pflanzen umsetzen
```

**Szenario 8: Tankbefüllung als Vollwechsel mit Rezept dokumentieren**
```
GIVEN: Tank "Haupttank Zelt 1" (nutrient, 50L),
       NutrientPlan "Tomato Heavy Coco" mit Phase vegetative (Ziel-EC 1.8, pH 5.8),
       Dünger: CalMag 1.0 ml/L, Flora Micro 1.5 ml/L, Flora Bloom 2.0 ml/L
WHEN: POST /api/v1/tanks/tank_zelt1/fills
      Body: { fill_type: "full_change", volume_liters: 48,
              nutrient_plan_key: "plan_tomato_coco",
              target_ec_ms: 1.8, target_ph: 5.8,
              measured_ec_ms: 1.75, measured_ph: 5.9,
              water_source: "osmose", base_water_ec_ms: 0.05,
              fertilizers_used: [{product_name: "CalMag", ml_per_liter: 1.0}, ...] }
THEN:
  - TankFillEvent immutabel gespeichert mit allen Feldern
  - has_fill_event-Edge von Tank zum Event erstellt
  - Automatisch TankState-Record erzeugt (ec_ms: 1.75, ph: 5.9, source: 'manual')
  - Dünger-Snapshot ist unabhängig vom Quell-Fertilizer-Dokument
  - Response enthält warnings: [] (EC-Abweichung 0.05 < 0.3 Toleranz)
```

**Szenario 9: Auffüllung mit Volumen-Warnung**
```
GIVEN: Tank "Haupttank Zelt 1" (nutrient, 50L), letzte Befüllung vor 3 Tagen
WHEN: POST /api/v1/tanks/tank_zelt1/fills
      Body: { fill_type: "top_up", volume_liters: 30, target_ec_ms: 1.8 }
THEN:
  - TankFillEvent wird gespeichert
  - Warnung: "Auffüllung von 30L ist >50% des Tank-Volumens — Vollwechsel stattdessen?"
```

**Szenario 10: pH-Korrektur ohne Rezept**
```
GIVEN: Tank "Haupttank Zelt 1", pH ist auf 6.5 gedriftet
WHEN: POST /api/v1/tanks/tank_zelt1/fills
      Body: { fill_type: "adjustment", volume_liters: 0.5,
              target_ph: 5.8, measured_ph: 5.7,
              notes: "pH-Down Korrektur" }
THEN:
  - TankFillEvent gespeichert (kein mixing_result_key, kein nutrient_plan_key)
  - TankState-Record mit ph: 5.7 erzeugt
  - Keine Warnung (pH-Abweichung 0.1 < 0.5 Toleranz)
```

**Szenario 11: Befüllungshistorie abrufen**
```
GIVEN: Tank "Haupttank Zelt 1" mit 3 historischen Befüllungen im Februar
WHEN: GET /api/v1/tanks/tank_zelt1/fills?start=2026-02-01&end=2026-02-28
THEN:
  - 3 Events chronologisch absteigend sortiert
  - Jedes Event enthält: fill_type, volume_liters, target/measured EC/pH, Dünger-Snapshot
  - Verknüpfte NutrientPlan-Namen werden aufgelöst
```

**Szenario 12: Befüllungsstatistik für Verbrauchsanalyse**
```
GIVEN: Tank "Haupttank Zelt 1" mit 4 Vollwechseln, 8 Auffüllungen, 2 Korrekturen im Januar
WHEN: GET /api/v1/tanks/tank_zelt1/fills/stats?start=2026-01-01&end=2026-01-31
THEN:
  - total_fills: 14
  - full_changes: 4, top_ups: 8, adjustments: 2
  - total_volume_liters: 288 (4×48 + 8×12 + 2×0.5)
  - avg_ec_deviation: 0.12
```

**Szenario 13: Ergänzende organische Düngung per Gießkanne neben Drip-System**
```
GIVEN: Location "Grow Zelt 1" mit irrigation_system="drip", Tank zugeordnet,
       Slots A1, A2 mit Tomaten in Coco,
       Dünger "Komposttee" (is_organic=true, tank_safe=false, recommended_application="drench"),
       Dünger "Mykorrhiza-Suspension" (is_organic=true, tank_safe=false)
WHEN: POST /api/v1/watering-events
      Body: { application_method: "drench", is_supplemental: true,
              volume_liters: 1.5, slot_keys: ["GROWZELT1_A1", "GROWZELT1_A2"],
              fertilizers_used: [{product_name: "Komposttee"}, {product_name: "Mykorrhiza-Suspension", ml_per_liter: 2.0}],
              water_source: "rainwater", notes: "Organische Ergänzung per Gießkanne" }
THEN:
  - WateringEvent immutabel gespeichert mit is_supplemental=true
  - watered_slot-Edges zu beiden Slots erstellt
  - FeedingEvents (REQ-004) pro betroffener Pflanze erzeugt mit application_method="drench"
  - Dünger-Snapshot unveränderlich im Event gespeichert
  - Keine Tank-Interaktion (kein TankFillEvent, kein TankState)
```

**Szenario 14: Tank-Safety-Warnung bei nicht-tanksicherem Dünger**
```
GIVEN: Tank "Haupttank Zelt 1" (nutrient),
       Dünger "Fischemulsion" (is_organic=true, tank_safe=false)
WHEN: Nutzer versucht TankFillEvent zu erstellen mit Fischemulsion in fertilizers_used
THEN:
  - Warnung: "'Fischemulsion' ist nicht tank-sicher (organisch/Schwebstoffe) —
    manuelles Gießen per Gießkanne empfohlen (WateringEvent mit application_method='drench')"
  - TankFillEvent wird NICHT blockiert (Warnung, kein Fehler — Nutzer entscheidet)
```

**Szenario 15: Blattdüngung als Ergänzung**
```
GIVEN: Location "Grow Zelt 1" mit irrigation_system="drip",
       Pflanzen zeigen Kalzium-Mangel (Blütenend-Fäule)
WHEN: POST /api/v1/watering-events
      Body: { application_method: "foliar", is_supplemental: true,
              volume_liters: 0.3, slot_keys: ["GROWZELT1_A1", "GROWZELT1_A2", "GROWZELT1_A3"],
              fertilizers_used: [{product_name: "CalMag Foliar Spray", ml_per_liter: 0.5}],
              water_source: "osmose" }
THEN:
  - WateringEvent mit application_method="foliar" gespeichert
  - Niedrige Gießmenge (0.1L pro Slot) — keine Volumen-Warnung
  - Slot-Gießhistorie zeigt Foliar-Event separat von Fertigation-Events
```

**Szenario 16: Gießhistorie eines Slots zeigt alle Applikationsmethoden**
```
GIVEN: Slot "GROWZELT1_A1" mit 3 Gießvorgängen im Februar:
       - 19.02. fertigation (aus Tank, 0.83L)
       - 20.02. drench (Komposttee per Gießkanne, 0.75L, supplemental)
       - 22.02. foliar (CalMag Spray, 0.1L, supplemental)
WHEN: GET /api/v1/slots/GROWZELT1_A1/watering-events?start=2026-02-01&end=2026-02-28
THEN:
  - 3 Events chronologisch absteigend sortiert
  - Jedes Event enthält: application_method, is_supplemental, volume, Dünger-Snapshot
  - Fertigation-Event verlinkt auf TankFillEvent, Drench/Foliar nicht
  - Nutzer sieht vollständiges Bild: mineralische Basis-Ernährung + organische Ergänzung
```

**Szenario 17: Statistik zeigt hybride Versorgung**
```
GIVEN: Location "Grow Zelt 1" im Februar: 12 Fertigations, 4 Drenches (supplemental),
       2 Foliars (supplemental), 1 Top Dress
WHEN: GET /api/v1/locations/growzelt1/watering-stats?start=2026-02-01&end=2026-02-28
THEN:
  - total_waterings: 19
  - fertigation_count: 12, drench_count: 4, foliar_count: 2, top_dress_count: 1
  - supplemental_count: 7
  - total_volume: ~35L
```

**Szenario 18: Manuelle Zustandserfassung**
```
GIVEN: Tank "Haupttank Zelt 1", letzte Messung vor 3 Tagen
WHEN: Nutzer erfasst neue Werte: pH=6.2, EC=1.8, Temp=21°C, Füllstand=35L
THEN:
  - Neuer TankState-Record mit source='manual' erstellt
  - fill_level_percent automatisch berechnet (35/50 = 70%)
  - Keine Alerts (alle Werte im Zielbereich)
  - Messung in Zustandsverlauf sichtbar
```

**Szenario 19: Gießplan-Bestätigung (vollständig)**
```
GIVEN: Gießplan-Task für Run "Tomaten Hochbeet A" (18 Pflanzen: 15 vegetative, 3 flowering),
       NutrientPlan "Tomato Heavy Coco" zugewiesen
WHEN: POST /api/v1/watering-events/confirm
      Body: { task_key: "feeding:watering:tomaten_hochbeet_a_2025:2026-02-27",
              application_method: "drench", volume_liters: 10.0,
              use_plan_dosages: true, measured_ec_ms: 1.75, measured_ph: 5.9,
              water_source: "osmose" }
THEN:
  - 1 WateringEvent erstellt (task_key gesetzt, slot_keys = alle Run-Slots)
  - 18 FeedingEvents erstellt (15× vegetative Dosierung, 3× flowering Dosierung)
  - 18 FED_BY-Edges + 18 TRIGGERED_BY-Edges
  - Task status → 'completed', watering_event_key gesetzt
  - CareConfirmation erzeugt (reminder_type: 'watering', action: 'confirmed')
```

**Szenario 20: Gießplan-Quick-Confirm (Ein-Tap)**
```
GIVEN: Gießplan-Task für Run "Orchideen Fensterbank" (5 Pflanzen, alle vegetative),
       NutrientPlan "Orchid Soak Weekly" (volume: 0.5L, method: drench)
WHEN: POST /api/v1/watering-events/quick-confirm
      Body: { task_key: "feeding:watering:orchideen_fenster:2026-02-27" }
THEN:
  - WateringEvent mit Defaults: application_method=drench, volume=0.5L
  - 5 FeedingEvents mit vegetative-Dosierungen
  - Task completed
  - Response: defaults_used zeigt verwendeten Plan und Werte
```

**Szenario 21: Bestätigung eines bereits erledigten Tasks**
```
GIVEN: Gießplan-Task mit status='completed' (bereits bestätigt)
WHEN: POST /api/v1/watering-events/confirm mit gleichem task_key
THEN:
  - HTTP 409 Conflict
  - Message: "Task bereits abgeschlossen — WateringEvent existiert bereits"
```

**Szenario 22: Live-Abfrage mit gemischten Sensoren (HA + MQTT)**
```
GIVEN: Tank "Haupttank Zelt 1" hat 3 monitors_tank-Sensoren:
       - EC-Sensor: ha_entity_id="sensor.tank1_ec" (HA-Direktanbindung)
       - pH-Sensor: ha_entity_id="sensor.tank1_ph" (HA-Direktanbindung)
       - Temp-Sensor: mqtt_topic="esphome/tank1/temp" (ESPHome via MQTT, kein HA)
       HA-Integration aktiviert (ha_token_set=true)
WHEN: GET /api/v1/tanks/tank_zelt1/states/live
THEN:
  - EC: value=1.82, source="ha_live", freshness="live" (direkt von HA abgefragt)
  - pH: value=5.9, source="ha_live", freshness="live" (direkt von HA abgefragt)
  - Temp: value=21.3, source="mqtt_auto", freshness="recent", timestamp=vor 45s
  - warnings: ["Parameter 'water_temp' ist nicht live-fähig (MQTT-Push)"]
  - UI zeigt: EC/pH mit grün pulsierendem Punkt + "HA Live"-Badge,
              Temp mit grün statischem Punkt + "MQTT"-Badge + "vor 45s"
```

**Szenario 23: Live-Abfrage ohne HA-Integration**
```
GIVEN: Tank "Regenwassertonne" hat 1 Sensor: mqtt_topic="esphome/garten/level"
       HA-Integration NICHT aktiviert (ha_token_set=false)
WHEN: GET /api/v1/tanks/tank_regenwasser/states/live
THEN:
  - HTTP 409 Conflict
  - Message: "HA-Integration nicht aktiviert — Live-Abfrage nicht möglich"
  - UI zeigt stattdessen letzte bekannte Werte mit Freshness-Indikator
```

**Szenario 24: Nutzer übernimmt Live-Wert als Messung**
```
GIVEN: Live-Tab zeigt EC=1.85 (ha_live) für "Haupttank Zelt 1"
WHEN: Nutzer klickt "Messung übernehmen"
THEN:
  - POST /api/v1/tanks/tank_zelt1/states mit {ec_ms: 1.85, source: "ha_auto"}
  - TankState in ArangoDB erzeugt
  - Observation in TimescaleDB erzeugt (Dual-Write)
  - Live-Tab zeigt Bestätigung: "Messung übernommen"
```

---

**Hinweise für RAG-Integration:**
- Keywords: Tank, Reservoir, Bewässerung, Nährstofflösung, Wasserwechsel, Reinigung, Desinfektion, Kalibrierung, Wartungsplan, Wartungshistorie, Befüllungshistorie, Tankbefüllung, Vollwechsel, Auffüllung, Korrektur, Dünger-Snapshot, Rezept-Verknüpfung, Füllstand, Algenrisiko, Rezirkulation, Tankkaskade, Gießkanne, Gießvorgang, manuelle Bewässerung, ergänzende Handdüngung, Blattdüngung, Komposttee, organischer Dünger, Applikationsmethode, Fertigation, Drench, Foliar, Top Dress, Gelöstsauerstoff, Sauerstoff, Pythium, Wurzelfäule, ORP, Sterilisation, UV-C, Ozon, Chlor, Chloramin, Alkalinität, Karbonathärte, Lösungsalter, Chelat-Degradation, pH-Drift, EC-Abweichung, Wurzelschock, Kälte, Salting-Out-Effekt, Q10-Regel, Biofilm, EC-Drift, EC-Trend, Stammlösung, Stock Solution, A/B-Tank, Compound-Alert, Lichtdichtheit, Substrat-pH, CalMag-Pufferung, Nachfüllwasser-Temperatur, Temperaturschock, Drain-to-Waste, Runoff-Interpretation
- Technische Begriffe: MaintenanceSchedule, TankState, TankFillEvent, WateringEvent, ApplicationMethod, FillType, FertilizerSnapshot, TankType, MaintenanceType, feeds_from, has_tank, has_fill_event, watered_slot, watering_from, supplies, mixed_into, monitors_tank, auto_create_task, tank_safe, is_organic, is_supplemental, Celery-Beat, dissolved_oxygen_mgl, orp_mv, chlorine_ppm, chloramine_ppm, alkalinity_ppm, has_uv_sterilizer, has_ozone_generator, is_light_proof, solution_age, ph_drift, ec_deviation, ec_trend_rising, ec_trend_falling, temp_do_compound, biofilm_risk, algae_risk, stock_solution, water_temperature_celsius, g_per_liter, PH_RANGES_BY_SUBSTRATE, Q10, ha_entity_id, mqtt_topic, modbus_address, ha_live, freshness, source_badge, dual_write, sensor_event, live_query
- Verknüpfung: Zentral für REQ-002 (Standort — irrigation_system), REQ-004 (Düngung — MixingResult, NutrientPlan, FeedingEvent, ApplicationMethod, Fertilizer.tank_safe, WateringScheduleEngine), REQ-005 (Sensorik — monitors_tank Edge, Observation, HomeAssistantConnector, MQTT, Modbus, Live-Query), REQ-006 (Aufgabenplanung — Gießplan-Tasks, Task-Completion), REQ-013 (Pflanzdurchlauf — Run-basierter Bestätigungsflow), REQ-022 (Pflegeerinnerungen — CareConfirmation-Interop)
