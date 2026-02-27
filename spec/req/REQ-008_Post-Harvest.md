# Spezifikation: REQ-008 - Post-Harvest

```yaml
ID: REQ-008
Titel: Post-Harvest: Veredelung, Fermentierung & Lagerreife
Kategorie: Post-Harvest
Fokus: Beides
Technologie: Python, Umweltsensorik, TimescaleDB (Zeitreihen)
Status: Entwurf
Version: 2.2 (U/P-Findings integriert)
```

## 1. Business Case

**User Story:** "Als Gärtner möchte ich Trocknungs-, Fermentierungs- und Lagerungsprozesse überwachen und steuern, um Qualität, Aroma, Haltbarkeit und Lagerfähigkeit meiner Ernte zu maximieren."

**Beschreibung:**
Das System implementiert spezies-spezifische Post-Harvest-Protokolle für die Phase zwischen Ernte und Endverbrauch mit präziser Umgebungskontrolle:

**Post-Harvest-Prozesse:**

**1. Trocknung (Drying):**
- **Cannabis/Hopfen/Kräuter:**
  - **Slow-Dry-Methode:** 7-14 Tage bei 15-21°C, 45-55% RLF
  - **Ziel:** 75-80% Gewichtsverlust (von Nass zu Trocken, ca. 10-12% Restfeuchte)
  - **Snap-Test:** Zweige brechen aber splittern nicht
  - **Qualitätskriterien:** Langsame Trocknung = besseres Aroma
  
- **Chili/Paprika:**
  - **Lufttrocknung:** 2-4 Wochen bei Raumtemperatur
  - **Dörrgerät:** 50-60°C für 6-12h (schneller aber weniger Aroma)
  
- **Speisepilze** (Champignon, Shiitake, Austernpilz):
  - **Dehydrator:** 45-55°C bis cracker-dry (Speisepilze vertragen höhere Temperaturen)
  - **Kritisch:** Über 60°C = Aromaverlust und Texturschäden

- **Heilpilze / empfindliche Pilze** (z.B. Psilocybe, Löwenmähne):
  - **Dehydrator:** 35-40°C bis cracker-dry
  - **Kritisch:** Über 40°C = Wirkstoff-/Terpen-Verlust (Psilocybin, Hericenone)
  
- **Zwiebeln/Knoblauch (P-004: Phasentrennung Härtung vs. Lagerung):**
  - **Phase 1 — Schalenhärtung (Curing):** 2-3 Wochen bei 25-30°C, niedrige RLF
    - UV-Exposition GEWÜNSCHT: Fördert Schalenhärtung und antimikrobielle Wirkung
    - Gut belüfteter, sonniger (aber nicht heißer) Standort
  - **Phase 2 — Langzeitlagerung:** Dunkel, 10-15°C, 60-70% RLF
    - KEIN UV: Licht fördert Keimung und Ergrünung (Chlorophyll-Synthese)
    - Übergang zu Phase 2 wenn Hals vollständig trocken und papierartig

**2. Curing (Fermentierung/Veredelung):**
- **Cannabis:**
  - **Jar-Curing:** 3-8 Wochen in verschlossenen Gläsern
  - **Burping-Schedule:** 
    - Woche 1-2: 2x täglich 15min lüften
    - Woche 3-4: 1x täglich 10min
    - Woche 5+: Wöchentlich 5min
  - **Ziel-RH im Jar:** 58-62% (Boveda-Packs)
  - **Prozesse:** Chlorophyll-Abbau, Terpen-Entwicklung
  
- **Sauerkraut:**
  - **Phase 1 (Leuconostoc, Tag 1-3):** 18-22°C, schnelle CO₂-Bildung, täglich Gasen ablassen
  - **Phase 2 (Lactobacillus, Tag 4-21):** 15-18°C für langsamere, aromatischere Fermentation
  - **Salzlake:** 2-2.5% Salzgehalt, Gemüse muss vollständig unter Lake sein
  - **Fertig:** pH < 4.0, milchsauer, keine Gasbildung mehr

- **Kimchi:**
  - **Phase 1 (Raumtemperatur, 1-3 Tage):** 18-22°C für Initialfermentation
  - **Phase 2 (Kaltfermentation):** 2-5°C im Kühlschrank für 2-4 Wochen
  - **Salzgehalt:** 3-5% (höher als Sauerkraut durch Gochugaru/Fischsauce)
  - **Hinweis:** Kimchi erfordert anaerobe Bedingung, anderes Temperaturprofil als Sauerkraut
  
- **Tabak** (Anbau in Deutschland genehmigungspflichtig gemäß TabStG):
  - **Air-Curing (Lufttrocknung):** 4-8 Wochen bei 15-30°C, 65-70% RH — Burley, Orientalischer
  - **Flue-Curing (Heißlufttrocknung):** 5-7 Tage, Temp-Rampe 35→70°C — Virginia. Nur hier gilt 55°C als kritische Schwelle für enzymatische Prozesse
  - **Fire-Curing (Rauchtrocknung):** 3-10 Tage, 30-50°C über offenem Feuer — Latakia, Dark-Fired
  - **Nachfermentation in Ballen:** 6-12 Monate bei kontrollierter Temperatur (max. 55°C nur bei Flue-Cured)

**3. Aging/Reifung:**
- **Kürbis/Squash:**
  - **Nachreife:** 2-3 Monate bei 10-15°C
  - **Verbessert:** Geschmack, Textur, Lagerfähigkeit
  
- **Tomaten (grün geerntet):**
  - **Ethylen-Management:**
    - **Professionell:** Kontrollierte Ethylen-Begasung (0.1-1 ppm) bei 18-21°C, 85-90% RH
    - **Hobby:** Mit reifen Äpfeln/Bananen in geschlossener Papiertüte lagern (unkontrolliert, aber effektiv)
    - **ACHTUNG:** Ethylen-empfindliche Produkte (Salat, Gurke, Brokkoli, Kräuter) NICHT zusammen mit Ethylen-Produzenten (Tomate, Apfel, Banane) lagern — beschleunigt Vergilbung, Bitterkeit und Verderb
  - **Nachreife:** 1-3 Wochen bei 18-21°C
  
- **Wein/Käse (optional):**
  - **Langzeitreifung:** Monate bis Jahre
  - **Klima-kontrolliert:** Spezifische Temp/RLF

**4. Storage (Langzeitlagerung):**
- **Temperatur-Zonen:**
  - **Kühl (0-5°C):** Wurzelgemüse, Äpfel, Kohl
  - **Keller (10-15°C):** Kürbis, Zwiebeln, Kartoffeln
  - **Raumtemperatur (18-22°C):** Getrocknete Kräuter, Samen
  
- **Luftfeuchte-Kontrolle:**
  - **Hoch (80-95%):** Wurzelgemüse in Sand
  - **Mittel (60-70%):** Kürbis, Zwiebeln
  - **Niedrig (40-50%):** Getrocknete Produkte

**Kritische Parameter:**

**Temperatur:**
- **Zu hoch:** Schimmel, Degradation, Insekten
- **Zu niedrig:** Gefrierungsschäden, Geschmacksverlust

**Luftfeuchte:**
- **Zu hoch (>65%):** Schimmelgefahr (Botrytis, Aspergillus)
- **Zu niedrig (<40%):** Übertrocknung, Terpen-Verlust, Brüchigkeit

**Luftaustausch:**
- **Zu wenig:** CO2-Akkumulation, Schimmel
- **Zu viel:** Zu schnelle Trocknung, Aroma-Verlust

**Qualitäts-Monitoring:**
- **Gewichtsverlauf:** Tägliche/wöchentliche Messungen
- **Visuelle Inspektion:** Schimmel, Verfärbungen, Schädlinge
- **Geruchstest:** Aroma-Entwicklung, Schimmel-Erkennung
- **Haptik:** Trockenheit, Festigkeit

## 2. ArangoDB-Modellierung

### Nodes:
- **`:StorageProtocol`** - Lagerungsvorschrift
  - Properties:
    - `protocol_id: str`
    - `protocol_type: Literal['drying', 'curing', 'aging', 'hardening', 'storage']`
    - `protocol_name: str`
    - `description: str`
    - `typical_duration_days: int`
    - `critical_for_quality: bool`

- **`:CuringPhase`** - Teil-Phase des Protokolls
  - Properties:
    - `phase_id: str`
    - `phase_name: str` (z.B. "early_cure", "burping", "final_cure")
    - `sequence_order: int`
    - `duration_days: int`
    - `action_required: str` (z.B. "Burp jars daily")
    - `action_frequency: str` (z.B. "twice_daily", "weekly")
    - `success_indicators: list[str]`

- **`:StorageCondition`** - Sollwerte für Umgebung
  - Properties:
    - `condition_id: str`
    - `temp_target_c: float`
    - `temp_tolerance_c: float` (±Abweichung)
    - `rh_target_percent: int`
    - `rh_tolerance_percent: int`
    - `air_exchange_per_hour: Optional[float]`
    - `light_exposure: Literal['none', 'minimal', 'indirect', 'direct']`
    - `critical_max_rh: int` (Schimmel-Schwelle)
    - `critical_min_rh: int` (Übertrocknung-Schwelle)
    - `target_water_activity: Optional[float]` (Wasseraktivität a_w — biologisch korrekter Endpunkt-Indikator: Schimmelpilze ab a_w > 0.65, Cannabis-Ziel: 0.55-0.65, Kräuter: < 0.50, Getrocknete Pilze: < 0.30)
    - `co2_max_ppm: Optional[int]` (Maximal tolerierbare CO2-Konzentration im Trocknungsraum. Default: 1500 ppm. Über 2000 ppm → unzureichende Belüftung, beschleunigte anaerobe Prozesse, Schimmelrisiko. U-005)
    - `max_uv_exposure: Optional[Literal['none', 'minimal', 'controlled', 'direct']]` (UV-Exposition-Toleranz. Cannabis/Hopfen: 'none' — UV degradiert THC/Terpene. Zwiebel-Härtung: 'controlled'. Langzeitlagerung: 'none'. U-008)

- **`:StorageLocation`** - Physischer Lagerort
  - Properties:
    - `location_id: str`
    - `location_name: str` (z.B. "Drying Room", "Curing Closet", "Root Cellar")
    - `location_type: Literal['room', 'closet', 'cellar', 'fridge', 'jar', 'container']`
    - `capacity_kg: Optional[float]`
    - `current_utilization_percent: float`
    - `has_active_climate_control: bool`
    - `sensor_ids: list[str]`

- **`:StorageObservation`** - Zustandsmessung
  - Properties:
    - `observation_id: str`
    - `timestamp: datetime`
    - `weight_g: Optional[float]`
    - `temperature_c: Optional[float]`
    - `rh_percent: Optional[float]`
    - `visual_condition: Literal['excellent', 'good', 'acceptable', 'concerning', 'critical']`
    - `aroma_quality: Literal['excellent', 'good', 'acceptable', 'off', 'moldy']`
    - `water_activity: Optional[float]` (a_w-Messung — präziser als RH für Schimmelrisiko-Bewertung)
    - `co2_ppm: Optional[int]` (CO2-Konzentration im Trocknungsraum. Über 1500 ppm → Belüftung erhöhen. U-005)
    - `defects_observed: list[str]` (z.B. ["mold_spot", "over_dry"])
    - `photo_refs: list[str]`
    - `observer: str`
    - `notes: Optional[str]`

- **`:BurpingEvent`** - Jar-Lüftung (Cannabis-Curing)
  - Properties:
    - `event_id: str`
    - `burped_at: datetime`
    - `duration_minutes: int`
    - `jar_rh_before: Optional[int]`
    - `jar_rh_after: Optional[int]`
    - `condensation_observed: bool`
    - `aroma_notes: Optional[str]`

- **`:TrimProtocol`** - Trim/Maniküre-Dokumentation (U-007)
  - Properties:
    - `trim_id: str`
    - `trim_type: Literal['wet_trim', 'dry_trim', 'machine_trim']` (Wet: direkt nach Ernte, Dry: nach Trocknung, Machine: automatisiert)
    - `trim_quality: Literal['hand_premium', 'hand_standard', 'machine']` (Qualitätsstufe des Trimms)
    - `pre_trim_weight_g: float` (Gewicht vor Trim)
    - `post_trim_weight_g: float` (Gewicht nach Trim)
    - `trim_waste_g: float` (Verschnitt — Sugar Leaves, kleine Blätter)
    - `trim_usable_g: Optional[float]` (Verwertbarer Verschnitt — für Extrakte, Edibles)
    - `trimmer: str` (User-ID)
    - `trimmed_at: datetime`
    - `duration_minutes: Optional[int]`
    - `notes: Optional[str]`

- **`:MoldAlert`** - Schimmel-Warnung
  - Properties:
    - `alert_id: str`
    - `triggered_at: datetime`
    - `severity: Literal['warning', 'critical']`
    - `trigger_reason: str` (z.B. "RH >65% for 6h")
    - `affected_location: str`
    - `action_taken: Optional[str]`
    - `resolved_at: Optional[datetime]`

- **`:DryingProgress`** - Trocknungs-Tracking
  - Properties:
    - `progress_id: str`
    - `start_weight_g: float`
    - `current_weight_g: float`
    - `target_weight_g: float`
    - `weight_loss_percent: float`
    - `dryness_progress_percent: float`
    - `snap_test_passed: Optional[bool]` (Unabhängiger boolean-Input vom Benutzer — nicht berechnet. Snap-Test Ergebnis: True = bricht sauber, False = biegt sich noch / splittert. P-002)
    - `estimated_days_remaining: int`
    - `water_activity: Optional[float]` (a_w-Wert — objektiver Trocknungsendpunkt, ergänzt gewichtsbasierte Berechnung)
    - `co2_ppm_current: Optional[int]` (Aktuelle CO2-Konzentration im Trocknungsraum. U-005)

### Edge Collections:
```aql
// Edge Collection: requires_post_harvest
// species -> storage_protocols

// Edge Collection: has_phase
// storage_protocols -> curing_phases  (edge attribute: sequence)

// Edge Collection: requires_conditions
// curing_phases -> storage_conditions

// Edge Collection: undergoing
// batches -> curing_phases

// Edge Collection: stored_in
// batches -> storage_locations

// Edge Collection: monitored_by
// storage_locations -> storage_observations

// Edge Collection: has_drying_progress
// batches -> drying_progress

// Edge Collection: burping_event
// batches -> burping_events

// Edge Collection: triggered_alert
// storage_locations -> mold_alerts

// Edge Collection: triggered
// storage_observations -> mold_alerts  (RH-basierte Alerts)

// Edge Collection: trimmed_as
// batches -> trim_protocols  (U-007: Trim/Maniküre-Dokumentation)
```

### AQL-Beispiellogik:

**Burping-Schedule basierend auf Cure-Dauer:**
```aql
// Hole Batch mit aktiver Curing-Phase
FOR batch IN batches
  FILTER batch.batch_id == @batch_id
  FOR phase IN 1..1 OUTBOUND batch GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['undergoing'] }
    FILTER phase.phase_name == 'jar_curing'

    // Berechne Tage in Curing
    LET days_in_cure = DATE_DIFF(batch.curing_started, DATE_NOW(), "day")

    // Bestimme Burping-Frequenz
    LET burping_schedule = (
      days_in_cure <= 7 ? {
        frequency: 'twice_daily',
        duration_min: 15,
        times: ['09:00', '21:00'],
        reason: 'Early cure - high moisture'
      } :
      days_in_cure <= 14 ? {
        frequency: 'daily',
        duration_min: 10,
        times: ['12:00'],
        reason: 'Mid cure - moisture stabilizing'
      } :
      days_in_cure <= 21 ? {
        frequency: 'every_2_days',
        duration_min: 10,
        times: ['12:00'],
        reason: 'Late cure - low moisture'
      } : {
        frequency: 'weekly',
        duration_min: 5,
        times: ['12:00'],
        reason: 'Final cure - maintenance only'
      }
    )

    // Hole letzte Burping-Events (letzte 7 Tage)
    LET recent_burps = (
      FOR burp IN 1..1 OUTBOUND batch GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['burping_event'] }
        FILTER burp.burped_at > DATE_SUBTRACT(DATE_NOW(), 7, "day")
        SORT burp.burped_at DESC
        RETURN burp
    )

    // Berechne nächstes Burping
    LET next_burping = (
      LENGTH(recent_burps) == 0
        ? DATE_ISO8601(DATE_NOW())  // Sofort wenn noch nie geburpt
        : DATE_ADD(recent_burps[0].burped_at,
            burping_schedule.frequency == 'twice_daily' ? 12 :
            burping_schedule.frequency == 'daily' ? 24 :
            burping_schedule.frequency == 'every_2_days' ? 48 :
            168,  // weekly
            "hour"
          )
    )

    RETURN {
      batch_id: batch.batch_id,
      days_in_cure: days_in_cure,
      burping_schedule: burping_schedule,
      last_burped: LENGTH(recent_burps) == 0 ? null : recent_burps[0].burped_at,
      next_burping: next_burping,
      overdue: next_burping < DATE_ISO8601(DATE_NOW()),
      notes: [
        'Prüfe auf Schimmel (weiß/grau = schlecht)',
        'Boveda 62% Pack ab Woche 2 empfohlen',
        'Ziel-RH im Jar: 58-62%'
      ]
    }
```

**Schimmel-Prävention mit RH-Monitoring:**
```aql
// Aggregiere letzte 6h Messungen pro StorageLocation
FOR location IN storage_locations
  LET observations = (
    FOR obs IN 1..1 OUTBOUND location GRAPH 'kamerplanter_graph'
      OPTIONS { edgeCollections: ['monitored_by'] }
      FILTER obs.timestamp > DATE_SUBTRACT(DATE_NOW(), 6, "hour")
      RETURN obs
  )
  FILTER LENGTH(observations) > 0

  LET avg_rh_6h = AVG(observations[*].rh_percent)
  LET max_rh_6h = MAX(observations[*].rh_percent)
  LET min_temp_6h = MIN(observations[*].temperature_c)
  LET max_temp_6h = MAX(observations[*].temperature_c)

  // Bestimme Schimmel-Risiko
  // Primär: a_w-Sensor (biologisch präziser — Schimmelpilze wachsen ab a_w > 0.65,
  // unabhängig von Raumluftfeuchte). Fallback: RH-basiert wenn kein a_w-Sensor.
  LET has_aw_sensor = LENGTH(observations[* FILTER CURRENT.water_activity != null]) > 0
  LET avg_aw_6h = has_aw_sensor
    ? AVG(observations[* FILTER CURRENT.water_activity != null].water_activity)
    : null

  LET risk_level = (
    // a_w-basierte Bewertung (bevorzugt, wenn Sensor vorhanden)
    has_aw_sensor AND avg_aw_6h > 0.65 ? 'CRITICAL' :
    has_aw_sensor AND avg_aw_6h > 0.60 ? 'WARNING' :
    // RH-basierte Bewertung (Fallback ohne a_w-Sensor)
    !has_aw_sensor AND avg_rh_6h > 65 ? 'CRITICAL' :
    !has_aw_sensor AND avg_rh_6h > 62 ? 'WARNING' :
    !has_aw_sensor AND (avg_rh_6h > 55 AND max_temp_6h > 22) ? 'WARNING' :
    'OK'
  )

  FILTER risk_level IN ['WARNING', 'CRITICAL']

  // Prüfe ob Alert bereits existiert
  LET existing_alerts = (
    FOR alert IN 1..1 OUTBOUND location GRAPH 'kamerplanter_graph'
      OPTIONS { edgeCollections: ['triggered_alert'] }
      FILTER alert.resolved_at == null
      RETURN alert
  )

  // Erstelle neuen Alert wenn nötig
  FILTER LENGTH(existing_alerts) == 0 AND risk_level == 'CRITICAL'

  LET trigger = has_aw_sensor
    ? CONCAT('a_w ', ROUND(avg_aw_6h, 3), ' > 0.65 über 6h')
    : CONCAT('RH ', ROUND(avg_rh_6h, 1), '% > 65% über 6h (kein a_w-Sensor)')

  LET new_alert = FIRST(
    INSERT {
      alert_id: UUID(),
      triggered_at: DATE_ISO8601(DATE_NOW()),
      severity: risk_level,
      trigger_reason: trigger,
      affected_location: location.location_id,
      action_required: (
        risk_level == 'CRITICAL'
          ? 'SOFORT: Dehumidifier einschalten, Luftaustausch erhöhen, visuell auf Schimmel prüfen'
          : 'Überwachen: RH senken auf <60%, a_w-Ziel < 0.60'
      )
    } INTO mold_alerts
    RETURN NEW
  )

  // Erstelle Edge location -> alert
  INSERT { _from: location._id, _to: new_alert._id }
    INTO triggered_alert

  RETURN {
    location: location.location_name,
    risk_level: risk_level,
    avg_rh_6h: ROUND(avg_rh_6h, 1),
    max_rh_6h: ROUND(max_rh_6h, 1),
    temp_range: [ROUND(min_temp_6h, 1), ROUND(max_temp_6h, 1)],
    alert_created: true,
    recommendations: [
      'Öffne alle Belüftungen',
      'Stelle Dehumidifier auf',
      'Prüfe alle Batches visuell',
      'Reduziere Raum-Feuchtigkeit auf <55%'
    ]
  }
```

**Trocknungs-Fortschritt mit Gewichts-Tracking:**
```aql
FOR batch IN batches
  FILTER batch.batch_id == @batch_id

  // Hole DryingProgress
  FOR progress IN 1..1 OUTBOUND batch GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['has_drying_progress'] }

    // Hole aktuelle und historische Gewichte
    LET weight_history = (
      FOR location IN 1..1 OUTBOUND batch GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['stored_in'] }
        FOR obs IN 1..1 OUTBOUND location GRAPH 'kamerplanter_graph'
          OPTIONS { edgeCollections: ['monitored_by'] }
          FILTER obs.weight_g != null
            AND obs.timestamp > DATE_SUBTRACT(DATE_NOW(), 14, "day")
          SORT obs.timestamp DESC
          RETURN { timestamp: obs.timestamp, weight: obs.weight_g }
    )

    // Berechne Fortschritt
    LET current_weight = weight_history[0].weight
    LET start_weight = progress.start_weight_g
    LET target_weight = progress.target_weight_g

    LET dryness_percent = ((start_weight - current_weight) / (start_weight - target_weight) * 100)
    LET weight_loss_percent = ((start_weight - current_weight) / start_weight * 100)

    // Snap-Test Readiness (bei 70-80% Fortschritt)
    LET snap_test_ready = dryness_percent >= 70

    // Schätze verbleibende Tage (basierend auf Verlaufskurve)
    LET estimated_days_remaining = (
      dryness_percent >= 95 ? 0 :
      dryness_percent >= 80 ? 2 :
      dryness_percent >= 60 ? 4 :
      dryness_percent >= 40 ? 7 :
      10
    )

    // Update Progress
    UPDATE progress WITH {
      current_weight_g: current_weight,
      weight_loss_percent: weight_loss_percent,
      dryness_progress_percent: dryness_percent,
      snap_test_ready: snap_test_ready,
      estimated_days_remaining: estimated_days_remaining
    } IN drying_progress

    RETURN {
      batch_id: batch.batch_id,
      start_weight_g: start_weight,
      current_weight_g: ROUND(current_weight, 1),
      target_weight_g: target_weight,
      weight_loss_percent: ROUND(weight_loss_percent, 1),
      dryness_progress_percent: ROUND(dryness_percent, 1),
      snap_test_ready: snap_test_ready,
      estimated_days_remaining: estimated_days_remaining,
      ready_for_curing: dryness_percent >= 95,
      status: (
        dryness_percent >= 95 ? 'READY - Start Jar Curing' :
        dryness_percent >= 70 ? 'APPROACHING - Test Snap daily' :
        dryness_percent >= 40 ? 'DRYING - On track' :
        'EARLY - Just started'
      ),
      weight_history: (
        FOR w IN weight_history
          RETURN { date: DATE_FORMAT(w.timestamp, "%yyyy-%mm-%dd"), weight_g: w.weight }
      )
    }
```

**Storage-Inventar mit Haltbarkeits-Prognose:**
```aql
FOR location IN storage_locations
  // Hole alle Batches, die in dieser Location gelagert sind
  LET batch_data = (
    FOR batch IN 1..1 INBOUND location GRAPH 'kamerplanter_graph'
      OPTIONS { edgeCollections: ['stored_in'] }

      // Hole Storage-Protokoll über Traversierung: batch -> plant_instance -> species -> protocol
      LET species = FIRST(
        FOR v IN 2..2 OUTBOUND batch GRAPH 'kamerplanter_graph'
          OPTIONS { edgeCollections: ['derived_from', 'belongs_to_species'] }
          FILTER IS_SAME_COLLECTION('species', v)
          RETURN v
      )

      LET protocol = FIRST(
        FOR p IN 1..1 OUTBOUND species GRAPH 'kamerplanter_graph'
          OPTIONS { edgeCollections: ['requires_post_harvest'] }
          FILTER p.protocol_type == 'storage'
          RETURN p
      )

      // Berechne Lagerzeit
      LET days_in_storage = DATE_DIFF(batch.stored_at, DATE_NOW(), "day")

      // Hole aktuelle Conditions (letzte 24h)
      LET current_condition = FIRST(
        FOR obs IN 1..1 OUTBOUND location GRAPH 'kamerplanter_graph'
          OPTIONS { edgeCollections: ['monitored_by'] }
          FILTER obs.timestamp > DATE_SUBTRACT(DATE_NOW(), 24, "hour")
          SORT obs.timestamp DESC
          LIMIT 1
          RETURN obs
      )

      // Haltbarkeits-Schätzung — parametrisch statt hardcodiert (P-001):
      // base_shelf_life kommt aus dem StorageProtocol der jeweiligen Spezies.
      // condition_factor wird aus aktuellen IST-Bedingungen vs. SOLL berechnet.
      LET storage_protocol = FIRST(
        FOR p IN 1..1 OUTBOUND species GRAPH 'kamerplanter_graph'
          OPTIONS { edgeCollections: ['requires_post_harvest'] }
          FILTER p.protocol_type == 'storage'
          RETURN p
      )
      LET base_shelf_life = storage_protocol != null
        ? storage_protocol.typical_duration_days
        : 90  // Fallback für Arten ohne explizites Protokoll

      // Condition-Factor: Abweichung von Soll-Bedingungen reduziert Haltbarkeit
      LET condition = FIRST(
        FOR cond IN 1..1 OUTBOUND storage_protocol GRAPH 'kamerplanter_graph'
          OPTIONS { edgeCollections: ['requires_conditions'] }
          RETURN cond
      )
      LET temp_deviation = current_condition != null AND condition != null
        ? ABS(current_condition.temperature_c - condition.temp_target_c)
        : 0
      LET rh_deviation = current_condition != null AND condition != null
        ? ABS(current_condition.rh_percent - condition.rh_target_percent)
        : 0
      // Einfacher Condition-Factor: 1.0 bei idealen Bedingungen, <1.0 bei Abweichung
      LET condition_factor = MAX(0.3,
        1.0 - (temp_deviation * 0.03) - (rh_deviation * 0.01)
      )
      LET shelf_life_days = ROUND(base_shelf_life * condition_factor)

      LET days_remaining = shelf_life_days - days_in_storage
      LET shelf_life_used_percent = (days_in_storage / shelf_life_days * 100)

      RETURN {
        batch_id: batch.batch_id,
        species: species.common_names[0],
        weight_g: batch.actual_dry_weight_g,
        days_in_storage: days_in_storage,
        days_remaining: days_remaining,
        shelf_life_percent: ROUND(shelf_life_used_percent, 1),
        condition: current_condition.visual_condition,
        quality_grade: batch.quality_grade
      }
  )

  FILTER LENGTH(batch_data) > 0

  LET total_batches = LENGTH(batch_data)
  LET total_weight_g = SUM(batch_data[*].weight_g)
  LET avg_days_remaining = AVG(batch_data[*].days_remaining)

  SORT location.location_name

  RETURN {
    location: location.location_name,
    capacity_kg: location.capacity_kg,
    current_stock_kg: ROUND(total_weight_g / 1000, 2),
    utilization_percent: ROUND((total_weight_g / 1000) / location.capacity_kg * 100, 1),
    total_batches: total_batches,
    average_days_remaining: ROUND(avg_days_remaining, 0),
    batches: batch_data,
    alerts: (
      FOR b IN batch_data
        FILTER b.days_remaining < 30
        RETURN CONCAT(b.batch_id, ' läuft in ', TO_STRING(b.days_remaining), ' Tagen ab')
    )
  }
```

## 3. Technische Umsetzung (Python)

### Logik-Anforderungen:

**1. Drying Protocol Manager:**
```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, List, Dict
from datetime import datetime, date, timedelta

class DryingProtocol(BaseModel):
    """Trocknungs-Management mit Fortschritts-Tracking"""
    
    batch_id: str
    species_type: Literal['flower', 'herb', 'root', 'fruit', 'mushroom']
    initial_weight_g: float = Field(gt=0)
    current_weight_g: float = Field(gt=0)
    target_moisture_percent: float = Field(default=10, ge=5, le=15)
    drying_method: Literal['hang_dry', 'rack_dry', 'dehydrator', 'air_cure']
    
    @field_validator('current_weight_g')
    @classmethod
    def validate_weight_reduction(cls, v, info):
        initial = info.data.get('initial_weight_g', 0)
        if v > initial:
            raise ValueError("Current weight kann nicht größer als initial weight sein")
        return v
    
    def calculate_dryness_progress(self) -> Dict:
        """
        Berechnet Trocknungs-Fortschritt
        
        Returns:
            Detaillierter Progress-Report
        """
        weight_loss_pct = ((self.initial_weight_g - self.current_weight_g) / 
                          self.initial_weight_g * 100)
        
        # Ziel: 75-80% Gewichtsverlust für ~10% Restfeuchte
        target_loss = 100 - self.target_moisture_percent
        progress = min(100, (weight_loss_pct / target_loss) * 100)
        
        # Snap-Test-Bereitschaft: Berechnet als Hinweis, wann der Test sinnvoll ist.
        # WICHTIG (P-002): snap_test_ready ist eine Schätzung basierend auf Gewichtsverlust.
        # Der tatsächliche Snap-Test ist ein unabhängiger boolean Input
        # (DryingProgress.snap_test_passed), der vom Benutzer nach manuellem Test
        # gesetzt wird. Beide Werte zusammen ergeben das Gesamtbild:
        # - snap_test_ready (berechnet) = "Jetzt testen empfohlen"
        # - snap_test_passed (Input) = "Benutzer hat getestet: bricht sauber"
        snap_test_ready = progress >= 70

        # Übertrocknung-Warnung
        over_dried = weight_loss_pct > 85
        
        return {
            'weight_loss_percent': round(weight_loss_pct, 1),
            'dryness_progress_percent': round(progress, 1),
            'ready_for_curing': progress >= 95,
            'snap_test_ready': snap_test_ready,
            'over_dried': over_dried,
            'current_weight_g': self.current_weight_g,
            'estimated_final_weight_g': round(self.initial_weight_g * (self.target_moisture_percent / 100), 1),
            'estimated_days_remaining': self._estimate_remaining_days(progress),
            'next_action': self._get_next_action(progress, over_dried)
        }
    
    def _estimate_remaining_days(self, current_progress: float) -> int:
        """Schätzt verbleibende Trocknungs-Tage"""
        
        # Basis-Schätzung nach Methode
        base_days = {
            'hang_dry': 10,    # Langsam, beste Qualität
            'rack_dry': 8,
            'dehydrator': 1,   # Schnell, weniger Aroma
            'air_cure': 14     # Sehr langsam
        }
        
        total_days = base_days.get(self.drying_method, 10)
        
        if current_progress >= 95:
            return 0
        elif current_progress >= 70:
            return 2
        elif current_progress >= 50:
            return int(total_days * 0.3)
        else:
            return int(total_days * 0.7)
    
    def _get_next_action(self, progress: float, over_dried: bool) -> str:
        """Empfiehlt nächste Schritte"""
        
        if over_dried:
            return "WARNUNG: Übertrocknet - Sofort in Jars mit Boveda-Pack (62%)"
        elif progress >= 95:
            return "Bereit für Jar-Curing - Jetzt in luftdichte Gläser umfüllen"
        elif progress >= 70:
            return "Snap-Test täglich durchführen - Zweige sollten brechen aber nicht splittern"
        elif progress >= 40:
            return "Trocknung läuft normal - Temperatur/RLF überwachen"
        else:
            return "Frühe Phase - Sicherstellen dass Luftzirkulation gut ist"
    
    def perform_snap_test(self, snaps_cleanly: bool, splinters: bool) -> Dict:
        """
        Interpretiert Snap-Test-Ergebnis
        
        Args:
            snaps_cleanly: Zweig bricht sauber durch
            splinters: Zweig splittert
        
        Returns:
            Test-Interpretation
        """
        if snaps_cleanly and not splinters:
            return {
                'result': 'OPTIMAL',
                'recommendation': 'Perfekt getrocknet - Bereit für Curing',
                'moisture_estimate': '10-12%',
                'action': 'In Jars umfüllen und mit Curing beginnen'
            }
        elif snaps_cleanly and splinters:
            return {
                'result': 'OVERDRIED',
                'recommendation': 'Zu trocken - Rehydrierung nötig',
                'moisture_estimate': '<8%',
                'action': 'Boveda 62% Pack für 24h in Jar, dann neu testen'
            }
        else:  # Biegt sich nur
            return {
                'result': 'UNDERDRIED',
                'recommendation': 'Noch zu feucht - Weiter trocknen',
                'moisture_estimate': '>15%',
                'action': 'Noch 2-3 Tage hängen lassen, dann neu testen'
            }

class SpeciesSpecificDrying:
    """Spezies-spezifische Trocknungs-Parameter"""
    
    DRYING_SPECS = {
        'Cannabis sativa': {
            'method': 'hang_dry',
            'temp_range': (15, 21),
            'rh_range': (45, 55),
            'duration_days': (7, 14),
            'target_moisture': 10,
            'critical_notes': [
                'Langsame Trocknung = besseres Aroma',
                'Nie über 25°C (Terpen-Verlust)',
                'Dunkelheit (UV degradiert THC)',
                'Luftzirkulation ohne direkten Wind'
            ]
        },
        'Capsicum annuum': {  # Chili
            'method': 'air_cure',
            'temp_range': (20, 30),
            'rh_range': (30, 50),
            'duration_days': (14, 28),
            'target_moisture': 8,
            'critical_notes': [
                'String-Method: An Faden aufhängen',
                'Gute Luftzirkulation wichtig',
                'Dehydrator OK aber weniger Aroma'
            ]
        },
        'Allium cepa': {  # Zwiebel
            'method': 'air_cure',
            'temp_range': (25, 30),
            'rh_range': (20, 40),
            'duration_days': (14, 21),
            'target_moisture': 5,
            'critical_notes': [
                'Schalenhärtung Phase',
                'UV-Exposition fördert Härtung',
                'Laub muss komplett trocken sein'
            ]
        },
        'Agaricus bisporus': {  # Speisepilze
            'method': 'dehydrator',
            'temp_range': (45, 55),
            'rh_range': (10, 20),
            'duration_days': (0.25, 0.5),  # 6-12h
            'target_moisture': 5,
            'critical_notes': [
                'Speisepilze vertragen 45-55°C (NICHT über 60°C = Aromaverlust)',
                'Cracker-dry = vollständig trocken (a_w < 0.30)',
                'In luftdichten Behältern mit Silica lagern',
                'Hinweis: Für empfindliche Pilzarten (Psilocybe, Löwenmähne) '
                'max 40°C verwenden (Wirkstoffverlust bei höheren Temperaturen)'
            ]
        }
    }
    
    @classmethod
    def get_specs(cls, scientific_name: str) -> Dict:
        """Holt spezies-spezifische Trocknungs-Specs"""
        return cls.DRYING_SPECS.get(
            scientific_name,
            {  # Default
                'method': 'air_cure',
                'temp_range': (18, 24),
                'rh_range': (40, 60),
                'duration_days': (7, 14),
                'target_moisture': 10,
                'critical_notes': ['Allgemeine Trocknung']
            }
        )
```

**2. Jar Curing Manager (Cannabis-spezifisch):**
```python
from datetime import datetime, timedelta

class JarCuringManager(BaseModel):
    """Verwaltet Cannabis Jar-Curing mit Burping"""
    
    batch_id: str
    jar_count: int = Field(ge=1, le=100)
    grams_per_jar: float = Field(gt=0, le=500)
    curing_started_at: datetime
    target_rh_percent: int = Field(default=62, ge=55, le=65)
    
    def get_burping_schedule(self) -> Dict:
        """Generiert dynamischen Burping-Schedule"""
        
        days_in_cure = (datetime.now() - self.curing_started_at).days
        
        if days_in_cure <= 7:
            schedule = {
                'frequency': 'twice_daily',
                'duration_minutes': 15,
                'times': ['09:00', '21:00'],
                'reason': 'Woche 1 - Hohe Restfeuchte',
                'rh_target': '58-62%',
                'condensation_check': True
            }
        elif days_in_cure <= 14:
            schedule = {
                'frequency': 'daily',
                'duration_minutes': 10,
                'times': ['12:00'],
                'reason': 'Woche 2 - Feuchte stabilisiert sich',
                'rh_target': '58-62%',
                'condensation_check': True
            }
        elif days_in_cure <= 21:
            schedule = {
                'frequency': 'every_2_days',
                'duration_minutes': 10,
                'times': ['12:00'],
                'reason': 'Woche 3 - Fast fertig',
                'rh_target': '58-62%',
                'condensation_check': False
            }
        else:
            schedule = {
                'frequency': 'weekly',
                'duration_minutes': 5,
                'times': ['12:00'],
                'reason': 'Final Cure - Nur Wartung',
                'rh_target': '58-62%',
                'condensation_check': False
            }
        
        return {
            'days_in_cure': days_in_cure,
            'current_schedule': schedule,
            'next_burping': self._calculate_next_burping(days_in_cure),
            'total_cure_time': self._get_cure_duration_recommendation(),
            'quality_indicators': self._get_quality_indicators(days_in_cure),
            'notes': [
                'Boveda 62% Packs ab Woche 2 empfohlen',
                'Schimmel-Check bei jedem Burping (weiß/grau = schlecht)',
                'Aroma entwickelt sich über 3-8 Wochen',
                'Chlorophyll-Abbau = weniger "grüner" Geschmack'
            ]
        }
    
    def _calculate_next_burping(self, days_in_cure: int) -> datetime:
        """Berechnet nächsten Burping-Zeitpunkt"""
        
        hours_interval = {
            range(0, 8): 12,      # Twice daily
            range(8, 15): 24,     # Daily
            range(15, 22): 48,    # Every 2 days
            range(22, 365): 168   # Weekly
        }
        
        for day_range, hours in hours_interval.items():
            if days_in_cure in day_range:
                return datetime.now() + timedelta(hours=hours)
        
        return datetime.now() + timedelta(hours=168)
    
    def _get_cure_duration_recommendation(self) -> Dict:
        """Empfiehlt Cure-Dauer basierend auf Qualitätsziel"""
        
        return {
            'minimum': {
                'weeks': 2,
                'quality': 'Acceptable - Grundlegende Chlorophyll-Reduktion'
            },
            'good': {
                'weeks': 4,
                'quality': 'Good - Deutlich verbesserter Geschmack'
            },
            'optimal': {
                'weeks': 6,
                'quality': 'Optimal - Vollständig entwickeltes Terpen-Profil'
            },
            'premium': {
                'weeks': 8,
                'quality': 'Premium - Peak Aroma, maximale Smoothness'
            }
        }
    
    def _get_quality_indicators(self, days_in_cure: int) -> List[str]:
        """Gibt erwartete Qualitäts-Veränderungen an"""
        
        indicators = []
        
        if days_in_cure >= 3:
            indicators.append("✓ Erste Aroma-Veränderungen erkennbar")
        if days_in_cure >= 7:
            indicators.append("✓ Chlorophyll-Abbau begonnen (weniger grün)")
        if days_in_cure >= 14:
            indicators.append("✓ Harshness reduziert, smootherer Rauch")
        if days_in_cure >= 21:
            indicators.append("✓ Terpen-Profil voll entwickelt")
        if days_in_cure >= 42:
            indicators.append("✓ Peak-Qualität erreicht")
        
        return indicators
    
    def assess_jar_rh(self, measured_rh: int) -> Dict:
        """Bewertet Jar-Luftfeuchte und gibt Empfehlungen"""
        
        if measured_rh > 65:
            return {
                'status': 'TOO_HIGH',
                'risk': 'SCHIMMEL-GEFAHR',
                'action': 'SOFORT burpen und länger offen lassen (30min+)',
                'severity': 'critical',
                'explanation': 'RH >65% = hohe Schimmel-Wahrscheinlichkeit'
            }
        elif measured_rh > 62:
            return {
                'status': 'SLIGHTLY_HIGH',
                'risk': 'Erhöhtes Schimmel-Risiko',
                'action': 'Häufiger burpen (täglich statt alle 2 Tage)',
                'severity': 'warning'
            }
        elif 58 <= measured_rh <= 62:
            return {
                'status': 'OPTIMAL',
                'risk': 'Kein Risiko',
                'action': 'Weiter wie bisher',
                'severity': 'ok',
                'explanation': 'Perfekter Cure-Bereich'
            }
        elif 55 <= measured_rh < 58:
            return {
                'status': 'SLIGHTLY_LOW',
                'risk': 'Leichte Übertrocknung',
                'action': 'Boveda 62% Pack hinzufügen',
                'severity': 'info'
            }
        else:  # <55
            return {
                'status': 'TOO_LOW',
                'risk': 'Terpen-Verlust, zu trocken',
                'action': 'Boveda 62% Pack DRINGEND + seltener burpen',
                'severity': 'warning',
                'explanation': 'Material wird brüchig, Aroma-Verlust'
            }
```

**3. Mold Prevention Monitor:**
```python
from typing import List

class MoldPreventionMonitor:
    """Schimmel-Früherkennung und Prävention"""
    
    # Kritische Schwellenwerte
    CRITICAL_RH = 65
    WARNING_RH = 62
    SAFE_RH = 55
    
    # Temperatur-RH Kombinations-Risiko
    HIGH_RISK_COMBOS = [
        {'temp_min': 20, 'temp_max': 25, 'rh_min': 60},
        {'temp_min': 15, 'temp_max': 20, 'rh_min': 65},
    ]
    
    @staticmethod
    def calculate_dew_point(temp_c: float, rh_percent: float) -> float:
        """
        Taupunkt-Berechnung nach Magnus-Formel.
        Kondensation auf Pflanzenoberflächen ist der primäre Schimmel-Auslöser.
        """
        import math
        a, b = 17.27, 237.7
        gamma = (a * temp_c) / (b + temp_c) + math.log(rh_percent / 100.0)
        return (b * gamma) / (a - gamma)

    @classmethod
    def assess_mold_risk(
        cls,
        temp_c: float,
        rh_percent: float,
        air_exchange_per_hour: float,
        duration_hours: float = 1.0,
        surface_temp_c: Optional[float] = None
    ) -> Dict:
        """
        Bewertet Schimmel-Risiko basierend auf Umgebungsbedingungen.
        Berücksichtigt Taupunkt-Nähe als primären Kondensations-Indikator.

        Args:
            surface_temp_c: Oberflächentemperatur des Lagerguts (wenn verfügbar).
                           Kondensation tritt auf wenn surface_temp <= dew_point.

        Returns:
            Risiko-Assessment mit Empfehlungen
        """

        risk_factors = []
        risk_score = 0
        dew_point = cls.calculate_dew_point(temp_c, rh_percent)

        # 1. RH-basiertes Risiko
        if rh_percent > cls.CRITICAL_RH:
            risk_factors.append(f"RH {rh_percent}% über kritischem Schwellenwert ({cls.CRITICAL_RH}%)")
            risk_score += 50
        elif rh_percent > cls.WARNING_RH:
            risk_factors.append(f"RH {rh_percent}% im Warn-Bereich")
            risk_score += 25

        # 2. Taupunkt-Nähe (Kondensationsrisiko)
        dew_margin = temp_c - dew_point
        check_temp = surface_temp_c if surface_temp_c is not None else temp_c
        surface_margin = check_temp - dew_point
        if surface_margin <= 0:
            risk_factors.append(
                f"KONDENSATION: Oberfläche ({check_temp:.1f}°C) ≤ Taupunkt ({dew_point:.1f}°C)"
            )
            risk_score += 60
        elif surface_margin <= 2:
            risk_factors.append(
                f"Taupunkt-Nähe: nur {surface_margin:.1f}°C Abstand — Kondensationsrisiko"
            )
            risk_score += 35

        # 3. Temp-RH Kombination
        for combo in cls.HIGH_RISK_COMBOS:
            if (combo['temp_min'] <= temp_c <= combo['temp_max'] and
                rh_percent >= combo['rh_min']):
                risk_factors.append(
                    f"Kritische Temp-RH Kombination: {temp_c}°C + {rh_percent}%"
                )
                risk_score += 30

        # 4. Luftaustausch
        if air_exchange_per_hour < 1:
            risk_factors.append("Unzureichender Luftaustausch (<1x/h)")
            risk_score += 20

        # 5. Dauer der Exposition
        if duration_hours > 6 and rh_percent > cls.WARNING_RH:
            risk_factors.append(f"Erhöhte RH über {duration_hours}h")
            risk_score += 15
        
        # Bestimme Risiko-Level
        if risk_score >= 70:
            level = 'CRITICAL'
            color = 'red'
            actions = [
                'SOFORTIGE MASSNAHMEN erforderlich!',
                '1. Dehumidifier einschalten',
                '2. Luftaustausch maximieren',
                '3. Alle Batches visuell auf Schimmel prüfen',
                '4. Temperatur senken wenn möglich',
                '5. Betroffene Bereiche isolieren'
            ]
        elif risk_score >= 40:
            level = 'WARNING'
            color = 'yellow'
            actions = [
                '1. RH auf <60% senken',
                '2. Luftzirkulation erhöhen',
                '3. Täglich visuell kontrollieren',
                '4. Erwäge Dehumidifier'
            ]
        elif risk_score >= 20:
            level = 'ATTENTION'
            color = 'orange'
            actions = [
                '1. RH überwachen',
                '2. Bereitmachen für Intervention'
            ]
        else:
            level = 'OK'
            color = 'green'
            actions = ['Bedingungen stabil - Weiter überwachen']
        
        return {
            'risk_level': level,
            'risk_score': risk_score,
            'color': color,
            'risk_factors': risk_factors,
            'actions': actions,
            'current_conditions': {
                'temperature_c': temp_c,
                'rh_percent': rh_percent,
                'dew_point_c': round(dew_point, 1),
                'dew_margin_c': round(dew_margin, 1),
                'air_exchange_h': air_exchange_per_hour,
                'duration_hours': duration_hours
            },
            'safe_targets': {
                'temp_c': '<20°C ideal',
                'rh_percent': f'<{cls.SAFE_RH}%',
                'air_exchange': '>2x/h'
            }
        }
    
    @staticmethod
    def identify_mold_type(visual_description: str, color: str, texture: str) -> Dict:
        """
        Hilft bei Identifikation von Schimmeltypen
        
        (DISCLAIMER: Nur informativ, kein Ersatz für Experten)
        """
        
        mold_types = {
            'botrytis': {
                'names': ['Botrytis', 'Grauschimmel', 'Bud Rot'],
                'appearance': 'Grau/braun, flauschig',
                'danger': 'CRITICAL',
                'action': 'Gesamte Blüte entfernen + 5cm Umkreis',
                'prevention': 'RH <50% in Blüte, gute Luftzirkulation'
            },
            'powdery_mildew': {
                'names': ['Echter Mehltau', 'Powdery Mildew'],
                'appearance': 'Weiß, pudrig, auf Blattoberfläche',
                'danger': 'HIGH',
                'action': 'Betroffene Blätter entfernen, Fungizid erwägen',
                'prevention': 'RH <60%, Luftbewegung'
            },
            'aspergillus_niger': {
                'names': ['Aspergillus niger', 'Schwarzschimmel'],
                'appearance': 'Schwarz, körnig/pulverig',
                'danger': 'CRITICAL',
                'action': 'KOMPLETTE Entsorgung - gesundheitsgefährlich!',
                'mycotoxin': 'Ochratoxin A (möglich, aber selten bei A. niger)',
                'prevention': 'RH <55%, Temperatur <25°C'
            },
            'aspergillus_flavus': {
                'names': ['Aspergillus flavus', 'Aflatoxin-Produzent'],
                'appearance': 'Grün-gelb, körnig/pudrig',
                'danger': 'CRITICAL',
                'action': 'SOFORTIGE ENTSORGUNG - Aflatoxin ist kanzerogen! '
                          'Nicht berühren ohne Handschuhe. Lagerort desinfizieren.',
                'mycotoxin': 'Aflatoxin B1 (kanzerogen, IARC Klasse 1)',
                'prevention': 'Strikte RH-Kontrolle <55%, Temperatur <25°C'
            },
            'aspergillus_fumigatus': {
                'names': ['Aspergillus fumigatus', 'Invasiver Schimmelpilz'],
                'appearance': 'Blaugrau bis grüngrau, samtig, oft in Substrat/Kompost',
                'danger': 'CRITICAL',
                'action': 'SOFORTIGE ENTSORGUNG - Invasive Aspergillose bei Immungeschwächten! '
                          'Atemschutzmaske (FFP2+) und Handschuhe tragen. '
                          'Sporen sind thermotolerant (bis 50°C überlebensfähig).',
                'mycotoxin': 'Gliotoxin (immunsuppressiv)',
                'health_risk': 'Häufigster Auslöser invasiver Aspergillosen beim Menschen. '
                               'Besonders gefährlich bei Cannabis-Konsum durch Inhalation.',
                'prevention': 'Strikte RH-Kontrolle <55%, HEPA-Filterung im Trocknungsraum, '
                              'Temperatur <25°C (thermotolerant, aber Wachstum verlangsamt)'
            },
            'penicillium': {
                'names': ['Penicillium', 'Blauschimmel'],
                'appearance': 'Blau/grün, flauschig',
                'danger': 'HIGH',
                'action': 'Batch isolieren, betroffene Teile entfernen',
                'prevention': 'Keine Beschädigungen, saubere Handhabung'
            }
        }
        
        # Einfache Keyword-Matching (in Produktion: ML-basiert)
        color_lower = color.lower()
        
        if 'grau' in color_lower or 'gray' in color_lower:
            # Differenziere: Blaugrau → A. fumigatus, Grau → Botrytis
            if 'blau' in color_lower or 'blue' in color_lower:
                identified = mold_types['aspergillus_fumigatus']
            else:
                identified = mold_types['botrytis']
        elif 'weiß' in color_lower or 'white' in color_lower:
            identified = mold_types['powdery_mildew']
        elif 'schwarz' in color_lower or 'black' in color_lower:
            identified = mold_types['aspergillus_niger']
        elif 'gelb' in color_lower or 'yellow' in color_lower:
            identified = mold_types['aspergillus_flavus']
        elif 'blau' in color_lower or 'grün' in color_lower:
            identified = mold_types['penicillium']
        else:
            identified = {
                'names': ['Unbekannt'],
                'appearance': visual_description,
                'danger': 'UNKNOWN',
                'action': 'Im Zweifelsfall: Komplette Entsorgung',
                'prevention': 'Strikte Hygiene'
            }
        
        return {
            'identified_as': identified['names'][0],
            'alternative_names': identified['names'],
            'danger_level': identified['danger'],
            'immediate_action': identified['action'],
            'prevention': identified['prevention'],
            'health_warning': 'WARNUNG: Einige Schimmelpilze sind gesundheitsgefährlich. Bei Unsicherheit entsorgen!'
        }
```

**4. Trim Protocol Manager (U-007):**
```python
class TrimProtocol(BaseModel):
    """
    Dokumentiert den Trim/Maniküre-Prozess zwischen Ernte und Trocknung/Curing.

    Trim-Methoden:
    - Wet Trim: Direkt nach Ernte, bevor Blätter antrocknen. Schnellere Trocknung,
      bessere Optik, aber höherer Terpen-Verlust.
    - Dry Trim: Nach 3-7 Tagen Trocknung. Langsamere Trocknung = besseres Aroma,
      aber arbeitsintensiver.
    - Machine Trim: Automatisiert, schnell, aber ungleichmäßig. Für große Mengen.
    """

    batch_id: str
    trim_type: Literal['wet_trim', 'dry_trim', 'machine_trim']
    trim_quality: Literal['hand_premium', 'hand_standard', 'machine']
    pre_trim_weight_g: float = Field(gt=0)
    post_trim_weight_g: float = Field(gt=0)
    trim_waste_g: float = Field(ge=0)
    trim_usable_g: float = Field(
        default=0, ge=0,
        description="Verwertbarer Verschnitt (Sugar Leaves → Extraktion, Butter, Edibles)"
    )
    trimmer: str
    trimmed_at: datetime
    duration_minutes: Optional[int] = Field(None, ge=1)

    @field_validator('post_trim_weight_g')
    @classmethod
    def validate_post_trim(cls, v, info):
        pre = info.data.get('pre_trim_weight_g', 0)
        if v > pre:
            raise ValueError("post_trim_weight darf nicht größer als pre_trim_weight sein")
        return v

    def calculate_trim_stats(self) -> Dict:
        """Berechnet Trim-Statistiken"""
        waste_percent = (self.trim_waste_g / self.pre_trim_weight_g) * 100
        usable_percent = (self.trim_usable_g / self.trim_waste_g) * 100 if self.trim_waste_g > 0 else 0

        return {
            'waste_percent': round(waste_percent, 1),
            'usable_waste_percent': round(usable_percent, 1),
            'trim_efficiency': round((self.post_trim_weight_g / self.pre_trim_weight_g) * 100, 1),
            'recommendation': self._get_trim_recommendation(waste_percent),
        }

    def _get_trim_recommendation(self, waste_pct: float) -> str:
        if waste_pct > 40:
            return 'Hoher Verschnitt — prüfe ob weniger aggressiv getrimmt werden kann.'
        elif waste_pct > 25:
            return 'Normaler Verschnitt für Cannabis (20-35% je nach Sorte).'
        else:
            return 'Niedriger Verschnitt — gut optimiert oder loose buds.'
```

**5. Shelf Life Estimator (P-001, P-004, P-005):**
```python
class ShelfLifeEstimator:
    """
    Haltbarkeitsprognose basierend auf Art und Lagerbedingungen.
    Ersetzt hardcodierte Artenliterale durch parametrische Berechnung:
    base_shelf_life * condition_factor.
    """

    # Basis-Haltbarkeit (Tage) unter IDEALEN Bedingungen, artspezifisch
    BASE_SHELF_LIFE: dict[str, dict] = {
        'Cannabis sativa':    {'days': 365, 'basis': 'dried', 'notes': 'In luftdichten Jars mit Boveda'},
        'Allium cepa':        {'days': 180, 'basis': 'cured', 'notes': 'Schalenhärtung abgeschlossen'},
        'Solanum tuberosum':  {
            'days': 270, 'basis': 'cured',
            'notes': 'Sortenabhängig: Festkochende kürzer (180-210d), Mehligkochende länger (240-300d). '
                     'Ohne Keimhemmung (CIPC) signifikant kürzer.',
            'variety_modifiers': {
                'waxy':    0.7,    # Festkochend: ~189d
                'floury':  1.1,    # Mehligkochend: ~297d
                'default': 1.0,
            },
            'sprouting_inhibition': {
                'none':   0.5,     # Ohne Keimhemmung: ~135d
                'cold':   0.8,     # Nur Kühllagerung 3-4°C: ~216d
                'cipc':   1.0,     # Chemisch (CIPC): volle 270d
                'ethylene': 0.9,   # Ethylen-Begasung: ~243d
            },
        },
        'Cucurbita maxima':   {'days': 180, 'basis': 'cured', 'notes': 'Nach Nachreife-Phase'},
        'Capsicum annuum':    {'days': 365, 'basis': 'dried', 'notes': 'Komplett getrocknet'},
        'Humulus lupulus':     {'days': 365, 'basis': 'dried', 'notes': 'Vakuumversiegelt, tiefgekühlt optimal'},
        'Ocimum basilicum':   {'days': 180, 'basis': 'dried', 'notes': 'Luftdicht, dunkel'},
        # Pilze
        'Agaricus bisporus':  {'days': 365, 'basis': 'dried', 'notes': 'Cracker-dry, luftdicht'},
        'Lentinula edodes':   {'days': 730, 'basis': 'dried', 'notes': 'Shiitake trocknet exzellent'},
    }

    # Condition-Faktoren: Wie stark weichen IST-Bedingungen von SOLL ab?
    @classmethod
    def calculate_condition_factor(
        cls,
        temp_deviation_c: float,
        rh_deviation_percent: float,
        light_exposure: Literal['none', 'minimal', 'indirect', 'direct'] = 'none',
        packaging: Literal['vacuum', 'airtight', 'sealed', 'open'] = 'airtight',
    ) -> float:
        """
        Berechnet Konditions-Faktor (0.1 - 1.0) basierend auf Abweichung
        von idealen Lagerbedingungen.
        """
        factor = 1.0

        # Temperatur-Abweichung
        if temp_deviation_c > 10:
            factor *= 0.4
        elif temp_deviation_c > 5:
            factor *= 0.7
        elif temp_deviation_c > 2:
            factor *= 0.9

        # RH-Abweichung
        if rh_deviation_percent > 15:
            factor *= 0.5
        elif rh_deviation_percent > 10:
            factor *= 0.7
        elif rh_deviation_percent > 5:
            factor *= 0.85

        # Licht-Exposition (U-008: UV als Degradationsfaktor)
        light_factors = {'none': 1.0, 'minimal': 0.9, 'indirect': 0.7, 'direct': 0.4}
        factor *= light_factors.get(light_exposure, 1.0)

        # Verpackung
        pkg_factors = {'vacuum': 1.0, 'airtight': 0.95, 'sealed': 0.8, 'open': 0.5}
        factor *= pkg_factors.get(packaging, 0.8)

        return max(0.1, round(factor, 2))

    @classmethod
    def estimate_shelf_life(
        cls,
        species: str,
        condition_factor: float = 1.0,
        variety: Optional[str] = None,
        sprouting_inhibition: Optional[str] = None,
    ) -> Dict:
        """
        Schätzt Haltbarkeit: base_shelf_life * condition_factor * variety_modifier.
        Kein hardcodierter Artname in der Berechnung.
        """
        specs = cls.BASE_SHELF_LIFE.get(species, {'days': 90, 'basis': 'fresh', 'notes': 'Unbekannte Art'})
        base_days = specs['days']

        # Sortenspezifischer Modifier (P-005: Kartoffel/Zwiebel)
        variety_mod = 1.0
        if 'variety_modifiers' in specs and variety:
            variety_mod = specs['variety_modifiers'].get(variety, specs['variety_modifiers'].get('default', 1.0))

        # Keimhemmung (P-005: Kartoffel ohne CIPC)
        sprout_mod = 1.0
        if 'sprouting_inhibition' in specs and sprouting_inhibition:
            sprout_mod = specs['sprouting_inhibition'].get(
                sprouting_inhibition, 1.0
            )

        estimated_days = int(base_days * condition_factor * variety_mod * sprout_mod)

        return {
            'species': species,
            'base_shelf_life_days': base_days,
            'condition_factor': condition_factor,
            'variety_modifier': variety_mod,
            'sprouting_inhibition_modifier': sprout_mod,
            'estimated_shelf_life_days': estimated_days,
            'notes': specs.get('notes', ''),
        }
```

**6. Growing System Modifier (U-002):**
```python
class GrowingSystemModifier:
    """
    Differenzierung der Post-Harvest-Parameter nach Anbausystem.
    Hydro vs. Soil vs. Organisch beeinflusst:
    - Restfeuchtigkeit und Trocknungsdauer
    - Chlorophyll-Gehalt (und damit Curing-Dauer)
    - Nährstoff-Rückstände und Geschmacksprofil
    """

    SYSTEM_MODIFIERS: dict[str, dict] = {
        'hydro': {
            'drying_duration_modifier': 0.85,    # ~15% schnellere Trocknung (weniger Zellstruktur)
            'curing_duration_modifier': 0.9,      # Etwas kürzere Cure (weniger Chlorophyll)
            'chlorophyll_level': 'low',
            'residue_risk': 'medium',             # Kann Salzrückstände enthalten ohne Flushing
            'flush_recommended': True,
            'notes': 'Hydro-Material trocknet schneller — Übertrocknung vermeiden. '
                     'Flushing empfohlen für saubereren Geschmack.',
        },
        'coco': {
            'drying_duration_modifier': 0.9,
            'curing_duration_modifier': 0.95,
            'chlorophyll_level': 'medium',
            'residue_risk': 'medium',
            'flush_recommended': True,
            'notes': 'Ähnlich wie Hydro, aber Coco puffert mehr Nährstoffe.',
        },
        'soil': {
            'drying_duration_modifier': 1.0,     # Standard
            'curing_duration_modifier': 1.0,
            'chlorophyll_level': 'medium',
            'residue_risk': 'low',
            'flush_recommended': True,
            'notes': 'Standard-Trocknung. Längeres Flushing nötig (höhere CEC).',
        },
        'living_soil': {
            'drying_duration_modifier': 1.05,     # Etwas mehr Zellstruktur → längere Trocknung
            'curing_duration_modifier': 1.1,       # Mehr Chlorophyll → längere Cure für Geschmack
            'chlorophyll_level': 'high',
            'residue_risk': 'very_low',
            'flush_recommended': False,            # Kein Flushing — zerstört Mikrobiom
            'notes': 'Kein Flushing nötig. Organisch gebundene Nährstoffe. '
                     'Längere Cure empfohlen für optimalen Geschmack.',
        },
        'organic': {
            'drying_duration_modifier': 1.0,
            'curing_duration_modifier': 1.1,       # Mehr Chlorophyll
            'chlorophyll_level': 'high',
            'residue_risk': 'very_low',
            'flush_recommended': False,
            'notes': 'Organische Nährstoffe. Längere Cure für Chlorophyll-Abbau.',
        },
    }

    @classmethod
    def get_modifier(cls, growing_system: str) -> dict:
        """Gibt anbausystemspezifische Post-Harvest-Modifier zurück."""
        return cls.SYSTEM_MODIFIERS.get(growing_system, cls.SYSTEM_MODIFIERS['soil'])

    @classmethod
    def adjust_drying_duration(cls, base_days: int, growing_system: str) -> int:
        """Passt Trocknungsdauer an Anbausystem an."""
        mod = cls.get_modifier(growing_system)
        return max(1, round(base_days * mod['drying_duration_modifier']))
```

**7. CO2 Monitor (U-005):**
```python
class CO2Monitor:
    """
    CO2-Überwachung im Trocknungsraum.
    Pflanzen geben während der Trocknung CO2 ab (Zellatmung post-mortem).
    Bei unzureichender Belüftung steigt CO2 → anaerobe Prozesse → Schimmel/Fehlgerüche.
    """

    CO2_THRESHOLDS = {
        'optimal':  800,    # ppm — gute Belüftung
        'elevated': 1200,   # ppm — Belüftung erhöhen
        'warning':  1500,   # ppm — kritisch, sofort lüften
        'critical': 2000,   # ppm — Ernte-Qualität gefährdet
    }

    @classmethod
    def assess_co2(cls, co2_ppm: int, room_volume_m3: Optional[float] = None) -> Dict:
        """Bewertet CO2-Konzentration und gibt Empfehlungen."""
        if co2_ppm >= cls.CO2_THRESHOLDS['critical']:
            return {
                'level': 'CRITICAL',
                'co2_ppm': co2_ppm,
                'action': 'SOFORT lüften! CO2 > 2000 ppm fördert anaerobe Prozesse '
                          'und Schimmelbildung. Abluftventilator aktivieren.',
                'risk': 'Fehlgerüche (Ammoniak, Heu), beschleunigte Degradation',
            }
        elif co2_ppm >= cls.CO2_THRESHOLDS['warning']:
            return {
                'level': 'WARNING',
                'co2_ppm': co2_ppm,
                'action': 'Belüftung erhöhen. CO2 > 1500 ppm weist auf '
                          'unzureichenden Luftaustausch hin.',
            }
        elif co2_ppm >= cls.CO2_THRESHOLDS['elevated']:
            return {
                'level': 'ELEVATED',
                'co2_ppm': co2_ppm,
                'action': 'Monitoring fortsetzen. Leicht erhöht — ggf. Belüftung anpassen.',
            }
        return {
            'level': 'OK',
            'co2_ppm': co2_ppm,
            'action': 'Gute Belüftung. Weiter überwachen.',
        }
```

**8. UV/Licht-Degradations-Manager (U-008):**
```python
class LightDegradationManager:
    """
    Licht (insbesondere UV) als Degradationsfaktor in Post-Harvest-Prozessen.

    - THC degradiert zu CBN unter UV-Licht (Halbwertszeit ~365 Tage im Dunkeln,
      ~90 Tage bei indirektem Licht, ~30 Tage bei direktem Sonnenlicht).
    - Terpene verdampfen schneller bei Wärme + Licht.
    - Chlorophyll baut bei Licht ab (erwünscht bei Curing, unerwünscht bei Lagerung).
    - Vitamine (C, A) in Gemüse degradieren unter Lichteinfluss.

    Zwiebel-Differenzierung (P-004):
    - Härtungsphase: UV-Exposition GEWÜNSCHT (fördert Schalenhärtung, 2-3 Wochen)
    - Langzeitlagerung: KEIN UV (fördert Keimung und Ergrünung)
    """

    SPECIES_LIGHT_SENSITIVITY: dict[str, dict] = {
        'cannabis': {
            'curing': 'none',        # Dunkel lagern — UV degradiert THC
            'storage': 'none',
            'packaging_recommendation': 'Opakes Glas (Violettglas/Miron) oder lichtdichte Behälter',
            'degradation_rate': 'THC → CBN: ~0.5%/Monat dunkel, ~3%/Monat bei indirektem Licht',
        },
        'onion': {
            'curing': 'controlled',   # UV GEWÜNSCHT für Schalenhärtung (P-004)
            'storage': 'none',        # Dunkel für Langzeitlagerung (P-004)
            'note': 'PHASENTRENNUNG: Härtung (2-3 Wochen UV) → Lagerung (dunkel). '
                    'UV in der Lagerphase fördert Keimung und Ergrünung.',
        },
        'potato': {
            'curing': 'none',         # KEIN Licht — Solanin-Bildung!
            'storage': 'none',
            'note': 'ABSOLUT DUNKEL: Licht (auch indirektes) induziert Solanin-Biosynthese. '
                    'Grüne Stellen = Solanin = giftig.',
        },
        'herb': {
            'curing': 'none',         # Dunkel trocknen — Farbe und Aroma erhalten
            'storage': 'none',
            'packaging_recommendation': 'Braunglas oder opake Dosen',
        },
    }

    @classmethod
    def get_light_protocol(cls, species_type: str, phase: Literal['curing', 'storage']) -> dict:
        """Gibt lichtspezifisches Protokoll für Art und Phase zurück."""
        specs = cls.SPECIES_LIGHT_SENSITIVITY.get(species_type, {
            'curing': 'minimal', 'storage': 'none',
        })
        return {
            'species': species_type,
            'phase': phase,
            'max_uv_exposure': specs.get(phase, 'none'),
            'recommendation': specs.get('packaging_recommendation', 'Lichtgeschützt lagern'),
            'note': specs.get('note', ''),
        }
```

**9. Storage Location Manager:**
```python
class StorageLocationManager(BaseModel):
    """Verwaltet Lagerorte und Inventar"""
    
    location_id: str
    location_name: str
    location_type: Literal['room', 'closet', 'cellar', 'fridge', 'jar', 'container']
    capacity_kg: float = Field(gt=0, le=1000)
    has_climate_control: bool = False
    
    def calculate_utilization(self, current_stock_kg: float) -> Dict:
        """Berechnet Lagerort-Auslastung"""
        
        utilization_pct = (current_stock_kg / self.capacity_kg) * 100
        
        if utilization_pct > 90:
            status = 'CRITICAL_FULL'
            recommendation = 'Sofort alternative Lagerung suchen'
        elif utilization_pct > 75:
            status = 'HIGH'
            recommendation = 'Platz wird knapp - Verbrauch erhöhen oder erweitern'
        elif utilization_pct > 50:
            status = 'MEDIUM'
            recommendation = 'Normale Auslastung'
        else:
            status = 'LOW'
            recommendation = 'Viel freie Kapazität'
        
        return {
            'capacity_kg': self.capacity_kg,
            'current_stock_kg': current_stock_kg,
            'available_kg': self.capacity_kg - current_stock_kg,
            'utilization_percent': round(utilization_pct, 1),
            'status': status,
            'recommendation': recommendation
        }
    
    def get_ideal_conditions(self, stored_species: List[str]) -> Dict:
        """Gibt ideale Lagerbedingungen basierend auf gespeicherten Spezies"""
        
        # Spezies-spezifische Anforderungen
        species_requirements = {
            'Cannabis sativa': {'temp': (15, 18), 'rh': (58, 62), 'light': 'none'},
            'Allium cepa': {'temp': (10, 15), 'rh': (60, 70), 'light': 'minimal'},
            'Solanum tuberosum': {'temp': (7, 10), 'rh': (85, 90), 'light': 'none'},
            'Cucurbita maxima': {'temp': (10, 15), 'rh': (60, 70), 'light': 'minimal'}
        }
        
        if not stored_species:
            return {'message': 'Keine Spezies im Lager'}
        
        # Finde Überschneidung der Anforderungen
        temp_ranges = [species_requirements.get(sp, {'temp': (15, 20)})['temp'] 
                      for sp in stored_species]
        rh_ranges = [species_requirements.get(sp, {'rh': (50, 60)})['rh'] 
                    for sp in stored_species]
        
        optimal_temp = (
            max(t[0] for t in temp_ranges),
            min(t[1] for t in temp_ranges)
        )
        
        optimal_rh = (
            max(r[0] for r in rh_ranges),
            min(r[1] for r in rh_ranges)
        )
        
        return {
            'location': self.location_name,
            'stored_species': stored_species,
            'optimal_temperature_c': optimal_temp,
            'optimal_rh_percent': optimal_rh,
            'light_exposure': 'Dunkel (alle Spezies)',
            'air_exchange': '2-4x/Tag öffnen für Frischluft',
            'notes': self._get_storage_notes(stored_species)
        }
    
    def _get_storage_notes(self, species: List[str]) -> List[str]:
        """Spezielle Lagerhinweise"""
        
        notes = []
        
        if 'Cannabis sativa' in species:
            notes.append("Cannabis: In luftdichten Jars mit Boveda-Packs")
        if 'Solanum tuberosum' in species:
            notes.append("Kartoffeln: KOMPLETT dunkel (sonst Solanin-Bildung)")
        if 'Allium cepa' in species:
            notes.append("Zwiebeln: Gute Luftzirkulation, nicht mit Kartoffeln lagern")
        
        return notes
```

### Datenvalidierung (Type Hinting):
```python
from typing import Literal, Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, date

ProtocolType = Literal['drying', 'curing', 'aging', 'hardening', 'storage']
DryingMethod = Literal['hang_dry', 'rack_dry', 'dehydrator', 'air_cure']
VisualCondition = Literal['excellent', 'good', 'acceptable', 'concerning', 'critical']
AromaQuality = Literal['excellent', 'good', 'acceptable', 'off', 'moldy']

class StorageObservation(BaseModel):
    """Zustandserfassung während Lagerung"""
    
    batch_id: str
    observed_at: datetime
    observer: str
    
    weight_g: Optional[float] = Field(None, gt=0)
    temperature_c: Optional[float] = Field(None, ge=-10, le=50)
    rh_percent: Optional[int] = Field(None, ge=0, le=100)
    
    water_activity: Optional[float] = Field(None, ge=0, le=1, description="a_w-Messwert")
    co2_ppm: Optional[int] = Field(None, ge=0, le=10000, description="CO2-Konzentration im Raum (U-005)")

    visual_condition: VisualCondition
    aroma_quality: AromaQuality

    defects_observed: List[str] = Field(default_factory=list)
    photo_refs: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=1000)
    
    @field_validator('defects_observed')
    @classmethod
    def validate_critical_defects(cls, v, info):
        critical_defects = ['mold', 'mold_spot', 'moldy']
        
        if any(defect in v for defect in critical_defects):
            if info.data.get('visual_condition') != 'critical':
                raise ValueError("Schimmel erfordert visual_condition='critical'")
        
        return v

class BurpingEvent(BaseModel):
    """Jar-Lüftungs-Ereignis"""
    
    batch_id: str
    burped_at: datetime
    duration_minutes: int = Field(ge=1, le=60)
    jar_rh_before: Optional[int] = Field(None, ge=0, le=100)
    jar_rh_after: Optional[int] = Field(None, ge=0, le=100)
    condensation_observed: bool = False
    aroma_notes: Optional[str] = None
    
    ambient_rh: Optional[int] = Field(None, ge=0, le=100)

    @field_validator('jar_rh_after')
    @classmethod
    def validate_rh_change(cls, v, info):
        """
        RH kann nach Burping steigen ODER fallen — Richtung hängt vom
        VPD-Gradienten zwischen Jar und Umgebung ab. Burping tauscht
        Luft aus, die Feuchtigkeitsrichtung ist nicht vorhersagbar
        ohne Kenntnis der Umgebungs-RH.
        """
        rh_before = info.data.get('jar_rh_before')
        ambient = info.data.get('ambient_rh')
        if rh_before and v:
            if v > rh_before:
                if ambient is not None and ambient < rh_before:
                    import warnings
                    warnings.warn(
                        f"RH-Anstieg ({rh_before}% → {v}%) bei niedriger Umgebungs-RH "
                        f"({ambient}%) — ungewöhnlich. Mögliche Ursache: Messfehler, "
                        f"Nachverdunstung aus feuchtem Material, oder Sensor-Drift.",
                        stacklevel=2,
                    )
                # Wenn ambient unbekannt: kein Fehler, da Richtung nicht vorhersagbar
        return v
```

## 4. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt wurde nachträglich ergänzt, um die Auth-Anforderungen
> gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung) zu dokumentieren.

**Standardregel:** Alle Endpunkte dieses REQ erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft. Alle Post-Harvest-Daten sind Tenant-scoped.

| Ressource/Endpoint-Gruppe | Lesen | Schreiben | Löschen |
|---------------------------|-------|-----------|---------|
| Trocknungsprozesse (Tenant-scoped) | Mitglied | Mitglied | Admin |
| Aushärtung/Curing (Tenant-scoped) | Mitglied | Mitglied | Admin |
| Qualitätsprüfungen (Tenant-scoped) | Mitglied | Mitglied | Admin |
| Lagerbestände (Tenant-scoped) | Mitglied | Mitglied | Admin |

## 5. Abhängigkeiten

**Erforderliche Module:**
- REQ-007 (Ernte): Batch-Übergabe
- REQ-005 (Sensorik): Temperatur/RLF/CO2-Monitoring
- REQ-001 (Stammdaten): Spezies-spezifische Protokolle
- REQ-003 (Phasen): **Post-Harvest-Phasenverknüpfung (U-006)** — Der Übergang von `harvest` zu Post-Harvest (Trocknung/Curing/Lagerung) wird als formaler Phasenübergang in der REQ-003 State-Machine modelliert. Options:
  - Option A: `post_harvest` als eigene Phase nach `harvest` in der State-Machine
  - Option B: Post-Harvest als Unterphasen-System (`drying` → `curing` → `storage`) das parallel zur REQ-003 Phase läuft, aber über `batch_status` getrackt wird
  - **Gewählte Option:** B — Post-Harvest hat eine eigene Zustandsmaschine pro Batch (da ein `plant_instance` mehrere Batches erzeugen kann, z.B. bei Partial Harvest). REQ-003 trackt den Plant-Lebenszyklus, REQ-008 den Batch-Lebenszyklus.
  - **Batch-Status-Machine:** `fresh` → `drying` → `curing` → `aging` (optional) → `stored` → `consumed`/`disposed`
- REQ-010 (IPM): **Karenz-Gate** — Batch darf nur in Post-Harvest übergehen, wenn letzte chemische Behandlung > Karenzzeit zurückliegt. Das System prüft den IPM-Treatment-Log vor Batch-Freigabe. Zusätzlich: `pesticide_residue_status` als optionales Feld auf Batch (z.B. 'clean', 'within_limits', 'residue_detected', 'untested').

**Wird benötigt von:**
- REQ-009 (Dashboard): Storage-Inventar-Widget
- Externes System: Vertriebs-/Verbrauchs-Tracking

**Hardware-Integrationen:**
- Hygrometer (digital, mit Logging)
- Thermometer
- Boveda-Packs (62% RH)
- Dehumidifier (optional)

**Python-Bibliotheken:**
- `timescaledb` oder `influxdb` - Zeitreihen für Gewichts-Tracking

## 6. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **5+ Post-Harvest-Protokolle:** Cannabis, Zwiebel, Tomate, Kräuter, Pilze
- [ ] **Gewichts-Tracking:** Täglich in ersten 7 Tagen, dann wöchentlich
- [ ] **Snap-Test-Assistent:** Interpretation von Test-Ergebnissen
- [ ] **Burping-Timer:** Push-Notifications für Jar-Curing
- [ ] **Schimmel-Alert:** Automatische Warnung bei RH >65% für >6h
- [ ] **Lager-Inventar:** Echtzeit-Bestand mit Haltbarkeits-Prognose
- [ ] **Boveda-Pack-Empfehlung:** Auto-Vorschlag bei RH <58%
- [ ] **Jar-ID-System:** QR-Codes für einzelne Gläser
- [ ] **Dryness-Progress-Tracking:** Fortschrittsbalken mit Schätzung
- [ ] **Spezies-spezifische Guides:** Step-by-Step für jede Art
- [ ] **Mold-Type-Identification:** Hilfe bei Schimmel-Erkennung
- [ ] **Storage-Condition-Optimizer:** Ideale Bedingungen für Multi-Species
- [ ] **Curing-Quality-Timeline:** Was passiert in Woche 1, 2, 3, etc.
- [ ] **Emergency-Protocols:** Schimmel-Fund, Übertrocknung, etc.
- [ ] **Photo-Comparison:** Before/After während Cure
- [ ] **Water-Activity-Tracking:** a_w-Messung in DryingProgress und StorageObservation
- [ ] **Taupunkt-Berechnung:** Dew-Point-basierte Kondensations-Warnung im Mold-Risk-Assessment
- [ ] **Karenz-Gate:** REQ-010-Prüfung vor Batch-Übergang in Post-Harvest
- [ ] **Phasen-Fermentation:** Separate Temperaturprofile für Leuconostoc/Lactobacillus-Phasen
- [ ] **Pilz-Differenzierung:** Speisepilze (45-55°C) vs. Heilpilze (35-40°C) Trocknungsprofile
- [ ] **Anbausystem-Modifier (U-002):** GrowingSystemModifier differenziert Trocknungs-/Curing-Dauer nach Hydro/Coco/Soil/Living Soil/Organisch
- [ ] **Aspergillus-Differenzierung (U-004):** A. niger (Ochratoxin), A. flavus (Aflatoxin, kanzerogen), A. fumigatus (Aspergillose, invasiv) — jeweils mit spezifischen Maßnahmen
- [ ] **CO2-Überwachung (U-005):** co2_ppm in StorageObservation und DryingProgress; CO2Monitor mit Schwellenwerten (800/1200/1500/2000 ppm)
- [ ] **Batch-Status-Machine (U-006):** fresh → drying → curing → aging → stored → consumed/disposed; Verknüpfung mit REQ-003 Plant-Phase
- [ ] **Trim-Protokoll (U-007):** TrimProtocol mit trim_type (wet/dry/machine), Gewichte vor/nach, verwertbarer Verschnitt
- [ ] **Licht/UV-Degradation (U-008):** LightDegradationManager mit artspezifischen Licht-Protokollen; Cannabis dunkel, Zwiebel-Härtung kontrolliert UV, Kartoffel absolut dunkel
- [ ] **Parametrische Haltbarkeitsprognose (P-001):** base_shelf_life * condition_factor statt hardcodierte Artenliterale
- [ ] **Snap-Test als Input (P-002):** snap_test_passed als unabhängiger boolean User-Input neben berechnetem snap_test_ready
- [ ] **Zwiebel-Phasentrennung (P-004):** Härtung (UV gewünscht) vs. Langzeitlagerung (dunkel) als separate Protokoll-Phasen
- [ ] **Kartoffel-Keimhemmung (P-005):** Sortenspezifische (festkochend/mehlig) und keimhemmungsabhängige (CIPC/Ethylen/Kühlung/keine) Haltbarkeits-Modifier
- [ ] **Pestizid-Rückstandsstatus:** pesticide_residue_status auf Batch-Ebene (REQ-010 Verknüpfung)

### Testszenarien:

**Szenario 1: Cannabis Slow-Dry mit Fortschritts-Tracking**
```
GIVEN: Batch mit 450g Nassgewicht
      Ziel: 10% Restfeuchte (112g Trockengewicht)
      Tag 0: 450g
      Tag 3: 320g (29% Verlust)
      Tag 7: 180g (60% Verlust)
WHEN: Fortschritt wird berechnet
THEN:
  - dryness_progress_percent = 73%
  - snap_test_ready = true
  - estimated_days_remaining = 2
  - next_action = "Snap-Test täglich durchführen"
```

**Szenario 2: Burping-Schedule (Jar-Curing)**
```
GIVEN: Batch in Jar-Curing seit 5 Tagen
WHEN: get_burping_schedule() aufgerufen
THEN:
  - frequency = 'twice_daily'
  - duration_minutes = 15
  - times = ['09:00', '21:00']
  - notes = "Boveda 62% Packs ab Woche 2 empfohlen"
```

**Szenario 3: Schimmel-Alert bei kritischer RH**
```
GIVEN: Drying Room mit:
      RH = 68% (letzte 6 Stunden durchschnittlich)
      Temp = 19°C
WHEN: Stündlicher Health-Check läuft
THEN:
  - MoldAlert erstellt
  - severity = 'CRITICAL'
  - trigger_reason = "RH 68% > 65% über 6h"
  - action_required = "SOFORT: Dehumidifier einschalten..."
  - Push-Notification an User
```

**Szenario 4: Jar-RH Assessment**
```
GIVEN: Jar-Hygrometer zeigt 72% RH
WHEN: assess_jar_rh(72) aufgerufen
THEN:
  - status = 'TOO_HIGH'
  - risk = 'SCHIMMEL-GEFAHR'
  - action = 'SOFORT burpen und länger offen lassen (30min+)'
  - severity = 'critical'
```

**Szenario 5: Snap-Test-Interpretation**
```
GIVEN: Zweig wird getestet
      snaps_cleanly = True
      splinters = True (splittert)
WHEN: perform_snap_test(True, True)
THEN:
  - result = 'OVERDRIED'
  - moisture_estimate = '<8%'
  - action = 'Boveda 62% Pack für 24h in Jar'
```

**Szenario 6: Multi-Species Storage Optimizer**
```
GIVEN: Root Cellar mit:
      - Kartoffeln (ideal: 7-10°C, 85-90% RH)
      - Zwiebeln (ideal: 10-15°C, 60-70% RH)
WHEN: get_ideal_conditions(['Solanum tuberosum', 'Allium cepa'])
THEN:
  - optimal_temperature_c = (10, 10)  # Überschneidung
  - optimal_rh_percent = (85, 70)     # Konflikt!
  - notes = "Zwiebeln und Kartoffeln NICHT zusammen lagern"
```

**Szenario 7: Haltbarkeits-Prognose**
```
GIVEN: Cannabis-Batch in Storage seit 120 Tagen
      Shelf-life: 365 Tage bei korrekter Lagerung
WHEN: Storage-Inventar-Query läuft
THEN:
  - days_remaining = 245
  - shelf_life_used_percent = 33%
  - alert = None (noch > 30 Tage)
```

---

**Hinweise für RAG-Integration:**
- Keywords: Trocknung, Curing, Burping, Fermentierung, Schimmel, Lagerung, Snap-Test, Wasseraktivität, Taupunkt, CO2-Überwachung, Trim, Maniküre, UV-Degradation, Keimhemmung, Anbausystem, Batch-Status
- Fachbegriffe: Chlorophyll-Abbau, Terpen-Entwicklung, Botrytis, Aspergillus niger, Aspergillus flavus, Aspergillus fumigatus, Aflatoxin, Gliotoxin, Boveda, Dehumidifier, Water Activity (a_w), Dew Point, Karenzzeit, Solanin, CIPC, Ochratoxin, Aspergillose, Wet-Trim, Dry-Trim, Phasentrennung (Härtung/Lagerung)
- Verknüpfung: Direkt nach REQ-007 (Ernte), vor Endverbrauch/Vertrieb, Karenz-Gate über REQ-010 (IPM), Batch-Status-Machine ergänzt REQ-003 Plant-Phase, CO2/RH-Monitoring über REQ-005
- Pflanzenwissenschaft: Nachreife, Ethylen-Management, Schalenhärtung (UV-Phase vs. Lagerung), Fermentation, Leuconostoc, Lactobacillus, Psilocybin, Hericenone, Solanin-Biosynthese, CBN-Degradation unter UV, Mykotoxine (Aflatoxin B1, Ochratoxin A, Gliotoxin)
