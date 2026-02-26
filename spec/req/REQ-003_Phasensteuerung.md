# Spezifikation: REQ-003 - Phasensteuerung

```yaml
ID: REQ-003
Titel: Phänologische Phasensteuerung & Ressourcen-Profile
Kategorie: Wachstumslogik
Fokus: Beides
Technologie: Python, GraphDB (Neo4j - Zustandsübergänge)
Status: Entwurf
Version: 2.0
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

## 2. GraphDB-Modellierung

### Nodes:
- **`:GrowthPhase`** - Wachstumsphase
  - Properties:
    - `name: str` (z.B. "vegetative", "flowering", "ripening")
    - `display_name: str` (z.B. "Vegetative Wachstumsphase")
    - `typical_duration_days: int`
    - `sequence_order: int`
    - `is_terminal: bool` (Letzte Phase vor Ernte/Tod)
    - `allows_harvest: bool`
    - `stress_tolerance: Literal['low', 'medium', 'high']`

- **`:RequirementProfile`** - Ressourcen-Anforderungen
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

- **`:NutrientProfile`** - NPK und Mikronährstoffe
  - Properties:
    - `npk_ratio: tuple[int, int, int]` (z.B. (3, 1, 2) für Vegi)
    - `target_ec_ms: float`
    - `target_ph: float`
    - `calcium_ppm: Optional[int]`
    - `magnesium_ppm: Optional[int]`
    - `micro_nutrients: dict[str, int]`

- **`:PhaseTransitionRule`** - Übergangslogik
  - Properties:
    - `trigger_type: Literal['time_based', 'manual', 'event_based', 'conditional']`
    - `auto_transition_after_days: Optional[int]`
    - `required_conditions: Optional[dict]` (z.B. {"min_height_cm": 30})
    - `notification_before_days: int` (Warnung vor Auto-Transition)

- **`:PhaseHistory`** - Historie für Analysen
  - Properties:
    - `entered_at: datetime`
    - `exited_at: Optional[datetime]`
    - `actual_duration_days: Optional[int]`
    - `transition_reason: str`
    - `performance_score: Optional[float]` (0-100, basierend auf Yield/Health)

### Edges:
```cypher
(:LifecycleConfig)-[:CONSISTS_OF {sequence: int}]->(:GrowthPhase)
(:GrowthPhase)-[:NEXT_PHASE]->(:GrowthPhase)
(:GrowthPhase)-[:GOVERNED_BY]->(:PhaseTransitionRule)
(:GrowthPhase)-[:REQUIRES_PROFILE]->(:RequirementProfile)
(:RequirementProfile)-[:USES_NUTRIENTS]->(:NutrientProfile)
(:PlantInstance)-[:CURRENT_PHASE]->(:GrowthPhase)
(:PlantInstance)-[:PHASE_HISTORY]->(:PhaseHistory)-[:WAS_PHASE]->(:GrowthPhase)
```

### Cypher-Beispiellogik:

**Nächste Phase mit Ressourcen-Profil laden:**
```cypher
MATCH (plant:PlantInstance {id: $plant_id})-[:CURRENT_PHASE]->(current:GrowthPhase)
      -[:NEXT_PHASE]->(next:GrowthPhase)-[:REQUIRES_PROFILE]->(req:RequirementProfile)
      -[:USES_NUTRIENTS]->(nutr:NutrientProfile)
OPTIONAL MATCH (next)-[:GOVERNED_BY]->(rule:PhaseTransitionRule)
RETURN next, req, nutr, rule
```

**Auto-Transition Kandidaten finden (zeitbasiert):**
```cypher
MATCH (plant:PlantInstance)-[:CURRENT_PHASE]->(phase:GrowthPhase)
      -[:GOVERNED_BY]->(rule:PhaseTransitionRule {trigger_type: 'time_based'})
MATCH (plant)-[:PHASE_HISTORY]->(history:PhaseHistory {exited_at: null})
      -[:WAS_PHASE]->(phase)
WHERE duration.between(history.entered_at, datetime()).days >= rule.auto_transition_after_days
RETURN plant.id, phase.name AS current_phase, 
       rule.auto_transition_after_days AS planned_duration,
       duration.between(history.entered_at, datetime()).days AS actual_duration
```

**VPD-Optimierung für aktuelle Phase:**
```cypher
MATCH (plant:PlantInstance)-[:CURRENT_PHASE]->(phase:GrowthPhase)
      -[:REQUIRES_PROFILE]->(req:RequirementProfile)
MATCH (plant)-[:PLACED_IN]->(:Slot)<-[:HAS_SLOT]-(:Location)
      -[:HAS_SENSOR]->(sensor:Sensor)-[:RECORDED]->(obs:Observation)
WHERE obs.timestamp > datetime() - duration('PT1H')
WITH req, obs, 
     obs.temperature_c AS temp,
     obs.humidity_percent AS rh
RETURN req.vpd_target_kpa AS target_vpd,
       ((610.7 * 10^(7.5*temp/(237.3+temp))) * (1 - rh/100) / 1000) AS current_vpd_kpa,
       abs(req.vpd_target_kpa - ((610.7 * 10^(7.5*temp/(237.3+temp))) * (1 - rh/100) / 1000)) AS vpd_deviation
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
        neo4j_session,
        override_reason: Optional[str] = None
    ) -> dict:
        """
        Führt Phasenübergang durch und aktualisiert Graph
        """
        transition_timestamp = datetime.now()
        actual_duration = (transition_timestamp - self.phase_entered_at).days
        
        # 1. Schließe aktuelle Phase-History
        neo4j_session.run("""
            MATCH (p:PlantInstance {id: $plant_id})
                  -[:PHASE_HISTORY]->(history:PhaseHistory {exited_at: null})
            SET history.exited_at = $exit_time,
                history.actual_duration_days = $duration,
                history.transition_reason = $reason
        """, 
        plant_id=self.plant_id,
        exit_time=transition_timestamp,
        duration=actual_duration,
        reason=override_reason or "Automatische Transition"
        )
        
        # 2. Aktualisiere CURRENT_PHASE
        neo4j_session.run("""
            MATCH (p:PlantInstance {id: $plant_id})-[old:CURRENT_PHASE]->(:GrowthPhase)
            DELETE old
            WITH p
            MATCH (next:GrowthPhase {name: $next_phase})
            CREATE (p)-[:CURRENT_PHASE]->(next)
        """, plant_id=self.plant_id, next_phase=next_phase_name)
        
        # 3. Erstelle neue Phase-History
        neo4j_session.run("""
            MATCH (p:PlantInstance {id: $plant_id})
            MATCH (phase:GrowthPhase {name: $phase_name})
            CREATE (p)-[:PHASE_HISTORY]->(history:PhaseHistory {
                entered_at: $enter_time,
                exited_at: null,
                transition_reason: 'New phase started'
            })-[:WAS_PHASE]->(phase)
        """, 
        plant_id=self.plant_id,
        phase_name=next_phase_name,
        enter_time=transition_timestamp
        )
        
        # 4. Hole neue Ressourcen-Profile
        new_profile = neo4j_session.run("""
            MATCH (phase:GrowthPhase {name: $phase_name})
                  -[:REQUIRES_PROFILE]->(req:RequirementProfile)
                  -[:USES_NUTRIENTS]->(nutr:NutrientProfile)
            RETURN req, nutr
        """, phase_name=next_phase_name).single()
        
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

### Datenvalidierung:
```python
from typing import Literal, Optional, Tuple
from pydantic import BaseModel, Field, validator

class RequirementProfileDefinition(BaseModel):
    """Ressourcen-Anforderungen einer Phase"""
    
    light_ppfd_target: int = Field(ge=0, le=2000, description="μmol/m²/s")
    photoperiod_hours: float = Field(ge=0, le=24)
    temperature_day_c: float = Field(ge=10, le=40)
    temperature_night_c: float = Field(ge=5, le=35)
    humidity_day_percent: int = Field(ge=20, le=95)
    humidity_night_percent: int = Field(ge=30, le=95)
    vpd_target_kpa: float = Field(ge=0.2, le=2.5)
    
    @validator('temperature_night_c')
    def validate_temp_range(cls, v, values):
        day_temp = values.get('temperature_day_c')
        if day_temp and v > day_temp:
            raise ValueError("Nachttemperatur muss niedriger als Tagestemperatur sein")
        return v
    
    @validator('photoperiod_hours')
    def validate_photoperiod(cls, v):
        if v < 8 and v > 0:
            raise ValueError("Photoperiode unter 8h kritisch für Photosynthese")
        return v

class NutrientProfileDefinition(BaseModel):
    """Nährstoff-Profil für eine Phase"""
    
    npk_ratio: Tuple[int, int, int] = Field(description="Nitrogen-Phosphor-Kalium Verhältnis")
    target_ec_ms: float = Field(ge=0.0, le=4.0, description="Elektrische Leitfähigkeit in mS/cm")
    target_ph: float = Field(ge=4.0, le=8.0)
    
    @validator('npk_ratio')
    def validate_npk(cls, v):
        if all(x == 0 for x in v):
            return v  # Flushing-Phase erlaubt
        if any(x < 0 for x in v):
            raise ValueError("NPK-Werte können nicht negativ sein")
        return v

TransitionTriggerType = Literal['time_based', 'manual', 'event_based', 'conditional']
PhaseType = Literal['seedling', 'vegetative', 'flowering', 'ripening', 'dormancy', 'flushing']
```

## 4. Abhängigkeiten

**Erforderliche Module:**
- REQ-001 (Stammdaten): LifecycleConfig und GrowthPhase-Definitionen
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

---

**Hinweise für RAG-Integration:**
- Keywords: Phasensteuerung, State-Machine, VPD, Photoperiode, NPK-Profil, Ressourcen
- Fachbegriffe: Phänologie, Transpiration, Vapor Pressure Deficit, PPFD, Spektrum
- Verknüpfung: Zentral für REQ-004 (Düngung), REQ-005 (Sensorik), REQ-006 (Tasks)
