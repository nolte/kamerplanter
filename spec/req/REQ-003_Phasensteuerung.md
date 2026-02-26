# Spezifikation: REQ-003 - Phasensteuerung

```yaml
ID: REQ-003
Titel: Phänologische Phasensteuerung & Ressourcen-Profile
Kategorie: Wachstumslogik
Fokus: Beides
Technologie: Python, ArangoDB
Status: Entwurf
Version: 2.1
```

## 1. Business Case

**User Story:** "Als Gärtner möchte ich, dass das System die aktuelle Wachstumsphase automatisch erkennt und Ressourcen (Licht, Wasser, Nährstoffe) dynamisch anpasst, um optimale Wachstumsbedingungen zu gewährleisten."

**Beschreibung:**
Das System implementiert eine State-Machine für phänologische Phasenübergänge mit:
- **Automatische Transitions:** Zeitbasiert (nach N Tagen) oder ereignisgesteuert (manuelle Blüte-Einleitung)
- **Phasenspezifische Ressourcen-Profile:** Für Licht (PPFD, Spektrum, Photoperiode), Wasser (Frequenz, Volumen), Nährstoffe (NPK-Ratio, EC-Zielwerte)
- **Rückwärts-Kompatibilität:** Support für Spezies ohne definierte Phasen (Standardprofil)
- **Stress-Phasen:** Temporäre Zustände wie Hardening-Off, Drought-Stress für Terpen-Induktion

Typische Phasen-Sequenzen:
- **Annuelle:** Keimung → Sämling → Vegetativ → Blüte → Fruchtreife → Seneszenz
- **Perenniale:** [Keimung → ...] → Dormanz → Neuaustrieb → [Wiederholt Vegetativ/Blüte]
- **Bienniale:** Jahr 1: Keimung → Vegetativ → Dormanz | Jahr 2: Neuaustrieb → Blüte → Samenreife

**Dauerkulturen-Modus (Perennial):**
Mehrjährige Pflanzen (Obstbäume, Beerensträucher, Stauden) durchlaufen jährlich wiederkehrende
Zyklen statt eines einmaligen linearen Durchlaufs. Das System unterstützt:
- **Saisonale Zyklen:** Jedes Jahr bildet eine eigene Saison mit eigenem Phasen-Durchlauf
  (Dormanz → Austrieb → Vegetativ → Blüte → Fruchtentwicklung → Reife → Seneszenz → Dormanz)
- **Reifegrad-Tracking:** Juvenile Phase (kein Ertrag), Produktive Phase, Ertragsrückgang
- **Saison-Vergleich:** Ertrag und Performance über Jahre hinweg vergleichbar
- **Vernalisierung:** Kältestunden-Akkumulation pro Saison (nutzt VernalizationTracker aus REQ-001)

## 2. ArangoDB-Modellierung

### Dokumentsammlungen (Collections):
- **`growth_phases`** - Wachstumsphase
  - Properties:
    - `name: str` (z.B. "vegetative", "flowering", "ripening")
    - `display_name: str` (z.B. "Vegetative Wachstumsphase")
    - `typical_duration_days: int`
    - `sequence_order: int`
    - `is_terminal: bool` (Letzte Phase vor Ernte/Tod)
    - `allows_harvest: bool`
    - `stress_tolerance: Literal['low', 'medium', 'high']`
    - `is_recurring: bool` — Phase wiederholt sich jährlich (true für Dauerkulturen-Phasen)

- **`requirement_profiles`** - Ressourcen-Anforderungen
  - Properties:
    - `light_ppfd_target: int` (μmol/m²/s)
    - `photoperiod_hours: float`
    - `light_spectrum: dict` (z.B. {"red": 0.6, "blue": 0.3, "far_red": 0.1})
    - `temperature_day_c: float`
    - `temperature_night_c: float`
    - `humidity_day_percent: int`
    - `humidity_night_percent: int`
    - `vpd_target_kpa: float`
    - `co2_ppm: Optional[int]`
    - `irrigation_frequency_days: float`
    - `irrigation_volume_ml_per_plant: int`

- **`nutrient_profiles`** - NPK und Mikronährstoffe
  - Properties:
    - `npk_ratio: tuple[int, int, int]` (z.B. (3, 1, 2) für Vegi)
    - `target_ec_ms: float`
    - `target_ph: float`
    - `calcium_ppm: Optional[int]`
    - `magnesium_ppm: Optional[int]`
    - `micro_nutrients: dict[str, int]`

- **`phase_transition_rules`** - Übergangslogik
  - Properties:
    - `trigger_type: Literal['time_based', 'manual', 'event_based', 'conditional']`
    - `auto_transition_after_days: Optional[int]`
    - `required_conditions: Optional[dict]` (z.B. {"min_height_cm": 30})
    - `notification_before_days: int` (Warnung vor Auto-Transition)
    - `is_cycle_restart: bool` — Transition startet einen neuen saisonalen Zyklus
      (erlaubt Rückwärts-Transition bei Dauerkulturen, z.B. Seneszenz → Dormanz)

- **`phase_histories`** - Historie für Analysen
  - Properties:
    - `entered_at: datetime`
    - `exited_at: Optional[datetime]`
    - `actual_duration_days: Optional[int]`
    - `transition_reason: str`
    - `performance_score: Optional[float]` (0-100, basierend auf Yield/Health)

- **`seasonal_cycles`** - Saisonaler Zyklus (nur Dauerkulturen)
  - Properties:
    - `plant_instance_key: str` — Referenz auf die Pflanze
    - `season_year: int` — Kalenderjahr (z.B. 2025)
    - `season_number: int` — Laufende Saison-Nummer (1-basiert, 1 = erste Saison der Pflanze)
    - `started_at: datetime` — Beginn (typisch: Austrieb nach Dormanz)
    - `ended_at: Optional[datetime]` — Ende (typisch: Eintritt in Dormanz)
    - `maturity_stage: Literal['juvenile', 'productive', 'declining']`
    - `chill_hours_accumulated: int` — Kältestunden der vorangegangenen Dormanz
    - `yield_kg: Optional[float]` — Gesamtertrag der Saison
    - `fruit_count: Optional[int]` — Anzahl Früchte (wenn zählbar)
    - `performance_notes: Optional[str]`

### Edge Collections:
```
consists_of:        lifecycle_configs  -> growth_phases         (Attribute: sequence)
next_phase:         growth_phases      -> growth_phases
governed_by:        growth_phases      -> phase_transition_rules
requires_profile:   growth_phases      -> requirement_profiles
uses_nutrients:     requirement_profiles -> nutrient_profiles
current_phase:      plant_instances    -> growth_phases
phase_history:      plant_instances    -> phase_histories
was_phase:          phase_histories    -> growth_phases
has_season:         plant_instances    -> seasonal_cycles
season_history:     seasonal_cycles    -> phase_histories    (Zuordnung Phase-History zu Saison)
```

### AQL-Beispiellogik:

**Nächste Phase mit Ressourcen-Profil laden:**
```aql
LET plant = DOCUMENT('plant_instances', @plant_id)

FOR current_phase IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['current_phase'] }
    FOR next IN 1..1 OUTBOUND current_phase GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['next_phase'] }
        FOR req IN 1..1 OUTBOUND next GRAPH 'kamerplanter_graph'
            OPTIONS { edgeCollections: ['requires_profile'] }
            FOR nutr IN 1..1 OUTBOUND req GRAPH 'kamerplanter_graph'
                OPTIONS { edgeCollections: ['uses_nutrients'] }
                LET rules = (
                    FOR rule IN 1..1 OUTBOUND next GRAPH 'kamerplanter_graph'
                        OPTIONS { edgeCollections: ['governed_by'] }
                        RETURN rule
                )
                RETURN { next, req, nutr, rule: FIRST(rules) }
```

**Auto-Transition Kandidaten finden (zeitbasiert):**
```aql
FOR plant IN plant_instances
    FOR phase IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['current_phase'] }
        FOR rule IN 1..1 OUTBOUND phase GRAPH 'kamerplanter_graph'
            OPTIONS { edgeCollections: ['governed_by'] }
            FILTER rule.trigger_type == 'time_based'
            FOR history IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
                OPTIONS { edgeCollections: ['phase_history'] }
                FILTER history.exited_at == null
                FOR hist_phase IN 1..1 OUTBOUND history GRAPH 'kamerplanter_graph'
                    OPTIONS { edgeCollections: ['was_phase'] }
                    FILTER hist_phase._id == phase._id
                    LET actual_duration = DATE_DIFF(history.entered_at, DATE_NOW(), 'days')
                    FILTER actual_duration >= rule.auto_transition_after_days
                    RETURN {
                        plant_id: plant._key,
                        current_phase: phase.name,
                        planned_duration: rule.auto_transition_after_days,
                        actual_duration: actual_duration
                    }
```

**VPD-Optimierung für aktuelle Phase:**
```aql
LET plant = DOCUMENT('plant_instances', @plant_id)
LET one_hour_ago = DATE_SUBTRACT(DATE_NOW(), 1, 'hours')

FOR phase IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['current_phase'] }
    FOR req IN 1..1 OUTBOUND phase GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['requires_profile'] }
        FOR slot IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
            OPTIONS { edgeCollections: ['placed_in'] }
            FOR location IN 1..1 INBOUND slot GRAPH 'kamerplanter_graph'
                OPTIONS { edgeCollections: ['has_slot'] }
                FOR sensor IN 1..1 OUTBOUND location GRAPH 'kamerplanter_graph'
                    OPTIONS { edgeCollections: ['has_sensor'] }
                    FOR obs IN 1..1 OUTBOUND sensor GRAPH 'kamerplanter_graph'
                        OPTIONS { edgeCollections: ['recorded'] }
                        FILTER obs.timestamp > one_hour_ago
                        LET temp = obs.temperature_c
                        LET rh = obs.humidity_percent
                        LET current_vpd = (610.7 * POW(10, (7.5 * temp / (237.3 + temp))) * (1 - rh / 100)) / 1000
                        RETURN {
                            target_vpd: req.vpd_target_kpa,
                            current_vpd_kpa: current_vpd,
                            vpd_deviation: ABS(req.vpd_target_kpa - current_vpd)
                        }
```

**Saison-Vergleich für Dauerkultur:**
```aql
// Vergleicht Ertrag und Phasen-Dauern über mehrere Saisons einer Pflanze
FOR season IN seasonal_cycles
    FILTER season.plant_instance_key == @plant_key
    SORT season.season_number ASC
    LET phase_durations = (
        FOR history IN phase_histories
            FOR edge IN season_history
                FILTER edge._from == season._id AND edge._to == history._id
                RETURN {
                    phase: history.phase_name,
                    duration_days: history.actual_duration_days
                }
    )
    RETURN {
        season: season.season_number,
        year: season.season_year,
        maturity: season.maturity_stage,
        yield_kg: season.yield_kg,
        chill_hours: season.chill_hours_accumulated,
        phases: phase_durations
    }
```

## 3. Technische Umsetzung (Python)

### Logik-Anforderungen:

**1. State-Machine für Phasenübergänge:**
```python
from datetime import datetime, timedelta
from typing import Literal, Optional
from pydantic import BaseModel, Field
from enum import Enum

class TransitionTrigger(str, Enum):
    TIME_BASED = "time_based"
    MANUAL = "manual"
    EVENT_BASED = "event_based"
    CONDITIONAL = "conditional"

class PhaseTransitionEngine(BaseModel):
    """Steuert Übergänge zwischen Wachstumsphasen"""
    
    plant_id: str
    current_phase: str
    phase_entered_at: datetime
    auto_transition_days: Optional[int] = None
    transition_trigger: TransitionTrigger
    
    def check_transition_due(self) -> tuple[bool, str, Optional[str]]:
        """
        Returns: (should_transition, reason, next_phase_name)
        """
        days_in_phase = (datetime.now() - self.phase_entered_at).days
        
        if self.transition_trigger == TransitionTrigger.TIME_BASED:
            if self.auto_transition_days is None:
                return False, "Keine Auto-Transition konfiguriert", None
            
            if days_in_phase >= self.auto_transition_days:
                return True, f"Geplante Dauer erreicht ({self.auto_transition_days} Tage)", "next_phase"
            
            # Warnung 3 Tage vorher
            days_remaining = self.auto_transition_days - days_in_phase
            if days_remaining <= 3 and days_remaining > 0:
                return False, f"WARNUNG: Automatische Transition in {days_remaining} Tagen", None
        
        if self.transition_trigger == TransitionTrigger.MANUAL:
            return False, "Manuelle Steuerung aktiv", None
        
        return False, "Transition-Bedingungen nicht erfüllt", None
    
    def execute_transition(
        self,
        next_phase_name: str,
        arango_db,
        override_reason: Optional[str] = None
    ) -> dict:
        """
        Führt Phasenübergang durch und aktualisiert Graph
        """
        transition_timestamp = datetime.now()
        actual_duration = (transition_timestamp - self.phase_entered_at).days

        # 1. Schließe aktuelle Phase-History
        arango_db.aql.execute("""
            FOR plant IN plant_instances
                FILTER plant._key == @plant_id
                FOR history IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
                    OPTIONS { edgeCollections: ['phase_history'] }
                    FILTER history.exited_at == null
                    UPDATE history WITH {
                        exited_at: @exit_time,
                        actual_duration_days: @duration,
                        transition_reason: @reason
                    } IN phase_histories
        """,
        bind_vars={
            'plant_id': self.plant_id,
            'exit_time': transition_timestamp.isoformat(),
            'duration': actual_duration,
            'reason': override_reason or "Automatische Transition"
        })

        # 2. Aktualisiere CURRENT_PHASE (alte Edge entfernen, neue anlegen)
        arango_db.aql.execute("""
            FOR plant IN plant_instances
                FILTER plant._key == @plant_id
                FOR phase, edge IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
                    OPTIONS { edgeCollections: ['current_phase'] }
                    REMOVE edge IN current_phase
        """, bind_vars={'plant_id': self.plant_id})

        arango_db.aql.execute("""
            LET plant = DOCUMENT(CONCAT('plant_instances/', @plant_id))
            FOR next IN growth_phases
                FILTER next.name == @next_phase
                INSERT { _from: plant._id, _to: next._id } INTO current_phase
        """, bind_vars={'plant_id': self.plant_id, 'next_phase': next_phase_name})

        # 3. Erstelle neue Phase-History
        arango_db.aql.execute("""
            LET plant = DOCUMENT(CONCAT('plant_instances/', @plant_id))
            FOR phase IN growth_phases
                FILTER phase.name == @phase_name
                LET history = FIRST(
                    INSERT {
                        entered_at: @enter_time,
                        exited_at: null,
                        transition_reason: 'New phase started'
                    } INTO phase_histories
                    RETURN NEW
                )
                INSERT { _from: plant._id, _to: history._id } INTO phase_history
                INSERT { _from: history._id, _to: phase._id } INTO was_phase
        """,
        bind_vars={
            'plant_id': self.plant_id,
            'phase_name': next_phase_name,
            'enter_time': transition_timestamp.isoformat()
        })

        # 4. Hole neue Ressourcen-Profile
        cursor = arango_db.aql.execute("""
            FOR phase IN growth_phases
                FILTER phase.name == @phase_name
                FOR req IN 1..1 OUTBOUND phase GRAPH 'kamerplanter_graph'
                    OPTIONS { edgeCollections: ['requires_profile'] }
                    FOR nutr IN 1..1 OUTBOUND req GRAPH 'kamerplanter_graph'
                        OPTIONS { edgeCollections: ['uses_nutrients'] }
                        RETURN { req, nutr }
        """, bind_vars={'phase_name': next_phase_name})
        new_profile = next(cursor, None)

        return {
            'transition_completed': True,
            'previous_phase': self.current_phase,
            'new_phase': next_phase_name,
            'actual_duration_days': actual_duration,
            'new_requirements': new_profile['req'] if new_profile else None,
            'new_nutrients': new_profile['nutr'] if new_profile else None
        }
```

**2. VPD-Calculator:**
```python
import math
from typing import Literal

class VPDCalculator:
    """Berechnet Vapor Pressure Deficit für Transpirationssteuerung"""
    
    @staticmethod
    def calculate_vpd(
        temperature_c: float,
        relative_humidity_percent: float,
        leaf_temperature_offset_c: float = -2.0
    ) -> float:
        """
        Berechnet VPD in kPa
        Args:
            temperature_c: Lufttemperatur
            relative_humidity_percent: Relative Luftfeuchte
            leaf_temperature_offset_c: Blatt ist typischerweise 2°C kühler
        Returns:
            VPD in kPa
        """
        # Sättigungsdampfdruck bei Lufttemperatur (in Pa)
        svp_air = 610.7 * (10 ** ((7.5 * temperature_c) / (237.3 + temperature_c)))
        
        # Tatsächlicher Dampfdruck
        avp = svp_air * (relative_humidity_percent / 100)
        
        # Sättigungsdampfdruck bei Blatttemperatur
        leaf_temp = temperature_c + leaf_temperature_offset_c
        svp_leaf = 610.7 * (10 ** ((7.5 * leaf_temp) / (237.3 + leaf_temp)))
        
        # VPD = Differenz in kPa
        vpd_kpa = (svp_leaf - avp) / 1000
        
        return round(vpd_kpa, 2)
    
    @staticmethod
    def get_vpd_recommendation(
        phase: str,
        current_vpd_kpa: float
    ) -> tuple[str, str]:
        """
        Gibt Empfehlungen basierend auf Phase und aktuellem VPD
        Returns: (status, recommendation)
        """
        # Ziel-VPD nach Phase
        target_ranges = {
            'seedling': (0.4, 0.8),
            'vegetative': (0.8, 1.2),
            'flowering': (1.0, 1.5),
            'late_flowering': (1.2, 1.6)
        }
        
        target_min, target_max = target_ranges.get(phase, (0.8, 1.2))
        
        if current_vpd_kpa < target_min:
            return "ZU NIEDRIG", f"Erhöhe Temperatur oder senke Luftfeuchte. Ziel: {target_min}-{target_max} kPa"
        elif current_vpd_kpa > target_max:
            return "ZU HOCH", f"Senke Temperatur oder erhöhe Luftfeuchte. Ziel: {target_min}-{target_max} kPa"
        else:
            return "OPTIMAL", f"VPD im Zielbereich ({target_min}-{target_max} kPa)"
```

**3. Ressourcen-Profil-Generator:**
```python
from pydantic import BaseModel, Field

class ResourceProfileGenerator(BaseModel):
    """Generiert automatische Ressourcen-Profile wenn nicht manuell definiert"""
    
    phase_name: str
    species_type: Literal['leafy', 'fruiting', 'flowering', 'root']
    
    def generate_light_profile(self) -> dict:
        """Generiert Lichtprofil basierend auf Phase und Typ"""
        
        base_profiles = {
            'seedling': {'ppfd': 200, 'photoperiod': 18, 'spectrum': {'blue': 0.6, 'red': 0.4}},
            'vegetative': {'ppfd': 400, 'photoperiod': 18, 'spectrum': {'blue': 0.4, 'red': 0.5, 'far_red': 0.1}},
            'flowering': {'ppfd': 600, 'photoperiod': 12, 'spectrum': {'blue': 0.2, 'red': 0.6, 'far_red': 0.2}},
            'ripening': {'ppfd': 400, 'photoperiod': 12, 'spectrum': {'blue': 0.1, 'red': 0.7, 'far_red': 0.2}}
        }
        
        profile = base_profiles.get(self.phase_name, base_profiles['vegetative'])
        
        # Anpassung nach Pflanzentyp
        if self.species_type == 'leafy':
            profile['ppfd'] = int(profile['ppfd'] * 0.8)  # Salate brauchen weniger Licht
        elif self.species_type == 'fruiting':
            profile['ppfd'] = int(profile['ppfd'] * 1.2)  # Tomaten, Paprika brauchen mehr
        
        return profile
    
    def generate_nutrient_profile(self) -> dict:
        """Generiert NPK-Verhältnis nach Phase"""
        
        phase_nutrients = {
            'seedling': {'npk': (1, 1, 1), 'ec': 0.8, 'ph': 6.0},
            'vegetative': {'npk': (3, 1, 2), 'ec': 1.4, 'ph': 5.8},
            'flowering': {'npk': (1, 3, 3), 'ec': 1.8, 'ph': 6.0},
            'ripening': {'npk': (0, 2, 4), 'ec': 1.2, 'ph': 6.2},
            'flushing': {'npk': (0, 0, 0), 'ec': 0.0, 'ph': 6.5}
        }
        
        return phase_nutrients.get(self.phase_name, phase_nutrients['vegetative'])
```

**4. Photoperioden-Manager:**
```python
from datetime import time

class PhotoperiodManager(BaseModel):
    """Verwaltet Licht-Zyklen und automatische Umstellung"""
    
    current_photoperiod_hours: float
    target_photoperiod_hours: float
    transition_days: int = Field(default=7, description="Schrittweise Umstellung")
    
    def calculate_transition_schedule(self) -> list[dict]:
        """
        Erstellt graduellen Übergang zwischen Photoperioden
        (Vermeidet Stress durch abrupte Änderung)
        """
        hour_diff = self.target_photoperiod_hours - self.current_photoperiod_hours
        daily_increment = hour_diff / self.transition_days
        
        schedule = []
        for day in range(self.transition_days + 1):
            hours = self.current_photoperiod_hours + (daily_increment * day)
            minutes = int((hours % 1) * 60)
            full_hours = int(hours)
            
            schedule.append({
                'day': day,
                'photoperiod_hours': round(hours, 2),
                'lights_on_duration': f"{full_hours:02d}:{minutes:02d}",
                'change_from_previous': round(daily_increment, 2) if day > 0 else 0
            })
        
        return schedule
    
    @staticmethod
    def calculate_light_times(
        photoperiod_hours: float,
        preferred_lights_on: time = time(6, 0)
    ) -> dict:
        """Berechnet Licht-EIN und AUS Zeiten.

        `preferred_lights_on` wird aus dem Location-Model übernommen
        (Feld `lights_on`), falls gesetzt. Bei natürlichem Licht und
        `use_dynamic_sunrise=True` wird die berechnete Sonnenaufgangszeit
        aus dem SunCalculator (REQ-002) verwendet.
        Default bleibt 06:00 für Abwärtskompatibilität.
        """

        hours_on = int(photoperiod_hours)
        minutes_on = int((photoperiod_hours % 1) * 60)

        lights_on_dt = datetime.combine(datetime.today(), preferred_lights_on)
        lights_off_dt = lights_on_dt + timedelta(hours=hours_on, minutes=minutes_on)

        return {
            'lights_on': lights_on_dt.time(),
            'lights_off': lights_off_dt.time(),
            'duration': f"{hours_on}h {minutes_on}min"
        }
```

**5. Dauerkulturen-Zyklus-Engine:**
```python
class MaturityStage(str, Enum):
    JUVENILE = "juvenile"         # Kein Ertrag (z.B. Apfelbaum < 3 Jahre)
    PRODUCTIVE = "productive"     # Voller Ertrag
    DECLINING = "declining"       # Ertragsrückgang (Alter)

class PerennialCycleEngine(BaseModel):
    """Verwaltet jährlich wiederkehrende Phasenzyklen für Dauerkulturen"""

    plant_id: str
    cycle_type: Literal['perennial']
    current_season_number: int = Field(ge=1)
    planted_year: int
    first_bearing_year: Optional[int] = None  # Ab wann Ertrag erwartet
    expected_productive_years: Optional[int] = None

    def get_maturity_stage(self, current_year: int) -> MaturityStage:
        """Bestimmt Reifegrad basierend auf Pflanzenalter"""
        plant_age = current_year - self.planted_year

        if self.first_bearing_year and plant_age < self.first_bearing_year:
            return MaturityStage.JUVENILE

        if self.expected_productive_years:
            productive_end = (self.first_bearing_year or 0) + self.expected_productive_years
            if plant_age > productive_end:
                return MaturityStage.DECLINING

        return MaturityStage.PRODUCTIVE

    def should_restart_cycle(
        self,
        current_phase: str,
        transition_rule: Optional[dict]
    ) -> tuple[bool, str]:
        """
        Prüft ob der saisonale Zyklus neu starten soll.
        Returns: (should_restart, reason)
        """
        if transition_rule and transition_rule.get('is_cycle_restart'):
            return True, f"Saisonaler Neustart: Saison {self.current_season_number + 1}"
        return False, "Kein Zyklus-Neustart"

    def start_new_season(
        self,
        arango_db,
        season_year: int,
        chill_hours: int = 0
    ) -> dict:
        """
        Startet eine neue Saison: erstellt SeasonalCycle-Dokument,
        setzt Pflanze auf erste wiederkehrende Phase (typisch: dormancy oder bud_break).
        """
        new_season_number = self.current_season_number + 1
        maturity = self.get_maturity_stage(season_year)

        # Neuen SeasonalCycle anlegen
        cursor = arango_db.aql.execute("""
            LET plant = DOCUMENT(CONCAT('plant_instances/', @plant_id))
            LET season = FIRST(
                INSERT {
                    plant_instance_key: @plant_id,
                    season_year: @year,
                    season_number: @season_num,
                    started_at: DATE_ISO8601(DATE_NOW()),
                    maturity_stage: @maturity,
                    chill_hours_accumulated: @chill_hours
                } INTO seasonal_cycles
                RETURN NEW
            )
            INSERT { _from: plant._id, _to: season._id } INTO has_season
            RETURN season
        """, bind_vars={
            'plant_id': self.plant_id,
            'year': season_year,
            'season_num': new_season_number,
            'maturity': maturity.value,
            'chill_hours': chill_hours
        })

        return {
            'season_number': new_season_number,
            'season_year': season_year,
            'maturity_stage': maturity.value,
            'chill_hours': chill_hours
        }

    def get_season_comparison(self, arango_db) -> list[dict]:
        """Vergleicht Ertrag und Performance über alle Saisons"""
        cursor = arango_db.aql.execute("""
            FOR season IN seasonal_cycles
                FILTER season.plant_instance_key == @plant_id
                SORT season.season_number ASC
                RETURN {
                    season: season.season_number,
                    year: season.season_year,
                    maturity: season.maturity_stage,
                    yield_kg: season.yield_kg,
                    chill_hours: season.chill_hours_accumulated
                }
        """, bind_vars={'plant_id': self.plant_id})
        return list(cursor)
```

**Erweiterung des PhaseTransitionEngine für Dauerkulturen:**

Die bestehende Rückwärts-Transition-Sperre (`sequence_order`-Vergleich) wird für Dauerkulturen
erweitert: Wenn die `PhaseTransitionRule` das Flag `is_cycle_restart=true` hat, wird eine
Rückwärts-Transition erlaubt. Dies ist der einzige Fall, in dem `sequence_order` rückwärts
gehen darf — es handelt sich um den kontrollierten Saison-Neustart.

Pseudocode-Erweiterung:
```python
def validate_transition(self, plant_key: str, target_phase_key: str) -> list[str]:
    # ... bestehende Logik ...

    # Rückwärts-Check mit Dauerkulturen-Ausnahme
    if target_phase.sequence_order <= current_phase.sequence_order:
        transition_rule = self._find_transition_rule(current_phase.key, target_phase_key)
        if transition_rule and transition_rule.is_cycle_restart:
            warnings.append("Saisonaler Zyklus-Neustart")
        else:
            raise PhaseTransitionError("Rückwärts-Transition nicht erlaubt")
```

### Datenvalidierung:
```python
from typing import Literal, Optional, Tuple
from pydantic import BaseModel, Field, field_validator

class RequirementProfileDefinition(BaseModel):
    """Ressourcen-Anforderungen einer Phase"""
    
    light_ppfd_target: int = Field(ge=0, le=2000, description="μmol/m²/s")
    photoperiod_hours: float = Field(ge=0, le=24)
    temperature_day_c: float = Field(ge=10, le=40)
    temperature_night_c: float = Field(ge=5, le=35)
    humidity_day_percent: int = Field(ge=20, le=95)
    humidity_night_percent: int = Field(ge=30, le=95)
    vpd_target_kpa: float = Field(ge=0.2, le=2.5)
    
    @field_validator('temperature_night_c')
    @classmethod
    def validate_temp_range(cls, v, info):
        day_temp = info.data.get('temperature_day_c')
        if day_temp and v > day_temp:
            raise ValueError("Nachttemperatur muss niedriger als Tagestemperatur sein")
        return v
    
    @field_validator('photoperiod_hours')
    @classmethod
    def validate_photoperiod(cls, v):
        if v < 8 and v > 0:
            raise ValueError("Photoperiode unter 8h kritisch für Photosynthese")
        return v

class NutrientProfileDefinition(BaseModel):
    """Nährstoff-Profil für eine Phase"""
    
    npk_ratio: Tuple[int, int, int] = Field(description="Nitrogen-Phosphor-Kalium Verhältnis")
    target_ec_ms: float = Field(ge=0.0, le=4.0, description="Elektrische Leitfähigkeit in mS/cm")
    target_ph: float = Field(ge=4.0, le=8.0)
    
    @field_validator('npk_ratio')
    @classmethod
    def validate_npk(cls, v):
        if all(x == 0 for x in v):
            return v  # Flushing-Phase erlaubt
        if any(x < 0 for x in v):
            raise ValueError("NPK-Werte können nicht negativ sein")
        return v

TransitionTriggerType = Literal['time_based', 'manual', 'event_based', 'conditional']
PhaseType = Literal['seedling', 'vegetative', 'flowering', 'ripening', 'dormancy', 'flushing',
                    'bud_break', 'fruit_development', 'senescence']

class SeasonalCycleDefinition(BaseModel):
    """Saisonaler Zyklus einer Dauerkultur"""

    plant_instance_key: str
    season_year: int = Field(ge=2000, le=2100)
    season_number: int = Field(ge=1)
    maturity_stage: Literal['juvenile', 'productive', 'declining']
    chill_hours_accumulated: int = Field(ge=0, default=0)
    yield_kg: Optional[float] = Field(None, ge=0)
    fruit_count: Optional[int] = Field(None, ge=0)

MaturityStage = Literal['juvenile', 'productive', 'declining']
```

**Standard-Phasen für Dauerkulturen (Perennial-Template):**

| Phase | `sequence_order` | `is_recurring` | `typical_duration_days` | `allows_harvest` | Beschreibung |
|---|---|---|---|---|---|
| `dormancy` | 0 | `true` | 90 (variabel) | `false` | Winterruhe, Kältestunden-Akkumulation |
| `bud_break` | 1 | `true` | 14 | `false` | Austrieb, Knospenöffnung |
| `vegetative` | 2 | `true` | 60 | `false` | Trieb- und Blattwachstum |
| `flowering` | 3 | `true` | 21 | `false` | Blüte, Bestäubung |
| `fruit_development` | 4 | `true` | 90 | `false` | Fruchtansatz und -wachstum |
| `ripening` | 5 | `true` | 30 | `true` | Fruchtreife, Ernte möglich |
| `senescence` | 6 | `true` | 30 | `false` | Blattfall, Einlagerung von Reservestoffen |

Transition `senescence → dormancy` hat `is_cycle_restart: true` und startet eine neue Saison.

Für immergrüne Dauerkulturen (z.B. Zitrus) entfällt `senescence`; `dormancy` kann optional sein.

## 4. Abhängigkeiten

**Erforderliche Module:**
- REQ-001 (Stammdaten): LifecycleConfig (`cycle_type`, `dormancy_required`, `vernalization_required`),
  DormancyTrigger (Dormanz-Auslösung), VernalizationTracker (Kältestunden-Tracking),
  GrowthPhase-Definitionen
- REQ-002 (Standort): Slot-Zuordnung für Ressourcen-Steuerung
- REQ-005 (Sensorik): Klimadaten für VPD-Berechnung und Feedback-Loop

**Wird benötigt von:**
- REQ-004 (Düngung): NPK-Profile aus aktueller Phase
- REQ-006 (Tasks): Phasenspezifische Aufgaben (z.B. Topping nur in Vegi)
- REQ-007 (Ernte): Harvest-Permission nur in finalen Phasen
- REQ-010 (IPM): Phasenspezifische Vulnerabilitäten

## 5. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **Phasen-State-Machine:** Graph-basierte Zustandsübergänge voll funktionsfähig
- [ ] **Auto-Transition:** Zeitbasierte Übergänge mit konfigurierbarer Vorwarnzeit
- [ ] **Manual-Override:** Manuelle Phasen-Einleitung (z.B. Blüte) jederzeit möglich
- [ ] **Ressourcen-Profile:** Jede Phase hat Light/Climate/Nutrient-Profile
- [ ] **VPD-Berechnung:** Echtzeit-VPD mit Zielbereich-Validierung
- [ ] **Photoperioden-Transition:** Gradueller Übergang (7 Tage) zwischen Licht-Zyklen
- [ ] **Phase-History:** Vollständiges Tracking aller Phasen mit Performance-Scores
- [ ] **NPK-Auto-Adjust:** Automatische Dünger-Anpassung bei Phasenwechsel
- [ ] **Stress-Phasen:** Support für temporäre Zustände (Hardening, Drought-Stress)
- [ ] **Rückwärts-Transition:** Verhinderung (Blüte → Vegi nicht erlaubt)
- [ ] **Multi-Phase-Harvests:** Support für kontinuierliche Ernte (z.B. Salat, Kräuter)
- [ ] **Dashboard-Integration:** Visuelle Phase-Indikatoren mit Fortschrittsbalken
- [ ] **Notification-System:** Push bei anstehenden Auto-Transitions
- [ ] **Profile-Versionierung:** Änderungen an Standard-Profilen historisiert
- [ ] **Species-Override:** Spezies-spezifische Profile überschreiben Defaults
- [ ] **Dauerkulturen-Zyklus:** Perenniale Pflanzen durchlaufen jährlich wiederkehrende Phasenzyklen
- [ ] **Zyklische Transition:** `is_cycle_restart`-Flag erlaubt kontrollierten Rückwärts-Übergang (Seneszenz → Dormanz)
- [ ] **Saisonales Tracking:** Jede Saison wird als `seasonal_cycles`-Dokument mit Jahr, Ertrag und Reifegrad erfasst
- [ ] **Reifegrad-Berechnung:** Automatische Bestimmung von juvenile/productive/declining basierend auf Pflanzenalter
- [ ] **Saison-Vergleich:** Ertrag und Phasen-Dauern sind über mehrere Jahre vergleichbar
- [ ] **Perennial-Phasen-Template:** Standard-Phasensequenz für Dauerkulturen (dormancy → bud_break → vegetative → flowering → fruit_development → ripening → senescence)
- [ ] **Kältestunden-Integration:** Chill-Hours pro Saison aus VernalizationTracker (REQ-001) übernommen

### Testszenarien:

**Szenario 1: Automatische Vegi → Blüte Transition**
```
GIVEN: Cannabis in Vegi-Phase seit 28 Tagen (geplant: 28 Tage)
WHEN: Täglicher Scheduler läuft
THEN:
  - System initiiert Übergang zu Blüte-Phase
  - Photoperiode wechselt graduell von 18h auf 12h (über 7 Tage)
  - NPK-Ratio ändert sich von 3-1-2 zu 1-3-3
  - EC-Zielwert steigt von 1.4 auf 1.8 mS
  - Alert: "Blütephase gestartet - Überwache VPD (Ziel: 1.0-1.5 kPa)"
```

**Szenario 2: VPD außerhalb Zielbereich**
```
GIVEN: Pflanze in Blüte, Ziel-VPD: 1.2 kPa, aktuell: Temp 28°C, RLF 70%
WHEN: System berechnet aktuellen VPD
THEN:
  - Errechneter VPD: 1.12 kPa (OPTIMAL)
  - Status: GRÜN
  - Keine Anpassungen erforderlich
  
WHEN: RLF steigt auf 85%
THEN:
  - Neuer VPD: 0.56 kPa (ZU NIEDRIG)
  - Status: ROT
  - Empfehlung: "Senke RLF auf 60-65% oder erhöhe Temp auf 30°C"
```

**Szenario 3: Manuelle Blüte-Einleitung bei Photoperiod-neutraler Pflanze**
```
GIVEN: Autoflower-Cannabis (day_neutral), aktuell Vegi
WHEN: Nutzer klickt "Blüte einleiten"
THEN:
  - Sofortige Transition (keine Photoperioden-Änderung)
  - NPK-Wechsel zu Blüte-Profil
  - Phase-History dokumentiert: "Manual override by user"
  - Nächste Auto-Transition geplant für: +56 Tage (typische Blütedauer)
```

**Szenario 4: Gradueller Photoperioden-Wechsel**
```
GIVEN: Transition von 18h → 12h über 7 Tage
WHEN: Transition startet
THEN:
  - Tag 0: 18:00h
  - Tag 1: 17:09h (-51 min)
  - Tag 2: 16:17h (-51 min)
  - Tag 3: 15:26h (-51 min)
  - Tag 4: 14:34h (-51 min)
  - Tag 5: 13:43h (-51 min)
  - Tag 6: 12:51h (-51 min)
  - Tag 7: 12:00h (Ziel erreicht)
```

**Szenario 5: Apfelbaum — Erster Saisonzyklus (Juvenil)**
```
GIVEN: Apfelbaum (Malus domestica, 'Boskoop'), gepflanzt 2024,
       first_bearing_year: 3, LifecycleConfig: cycle_type=perennial
WHEN: Pflanze durchläuft Saison 1 (2024)
THEN:
  - Maturity-Stage: "juvenile" (Alter < 3 Jahre)
  - Phasen: dormancy → bud_break → vegetative → senescence → dormancy
  - Phasen flowering/fruit_development/ripening werden übersprungen (juvenil)
  - SeasonalCycle-Dokument: { season_number: 1, season_year: 2024, maturity_stage: "juvenile", yield_kg: null }
```

**Szenario 6: Apfelbaum — Produktive Saison mit Ernte**
```
GIVEN: Apfelbaum, gepflanzt 2020, aktuell Saison 5 (2025), maturity_stage: "productive"
       Durchlief: dormancy (90 Tage, 800 Kältestunden) → bud_break → vegetative → flowering → fruit_development → ripening
WHEN: Nutzer erfasst Ernte: 45 kg, 320 Äpfel
THEN:
  - SeasonalCycle wird aktualisiert: { yield_kg: 45.0, fruit_count: 320 }
  - Saison-Vergleich zeigt: 2023: 38 kg, 2024: 42 kg, 2025: 45 kg (steigend)
  - Nach Ernte: Transition zu senescence → dormancy (is_cycle_restart=true)
  - Neue Saison 6 (2026) wird angelegt
```

**Szenario 7: Zyklische Transition — Seneszenz → Dormanz**
```
GIVEN: Perenniale Pflanze in Phase "senescence" (sequence_order: 6)
WHEN: Transition zu "dormancy" (sequence_order: 0) wird ausgelöst
THEN:
  - Normale Rückwärts-Sperre wird NICHT ausgelöst (is_cycle_restart=true)
  - Aktuelle Saison wird geschlossen (ended_at gesetzt)
  - Neue Saison wird erstellt (season_number + 1)
  - Phase-History wird korrekt der neuen Saison zugeordnet
```

---

**Hinweise für RAG-Integration:**
- Keywords: Phasensteuerung, State-Machine, VPD, Photoperiode, NPK-Profil, Ressourcen, Dauerkultur, Perennial, Saisonzyklus, Reifegrad, Kältestunden, Obstbaum, Juvenil
- Fachbegriffe: Phänologie, Transpiration, Vapor Pressure Deficit, PPFD, Spektrum, Vernalisierung, Seneszenz, Austrieb, Chill-Hours, Fruchtentwicklung
- Verknüpfung: Zentral für REQ-004 (Düngung), REQ-005 (Sensorik), REQ-006 (Tasks)
