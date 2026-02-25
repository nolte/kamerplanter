# Spezifikation: REQ-006 - Aufgabenplanung

```yaml
ID: REQ-006
Titel: Modulare Aufgabenplanung & Benutzerdefinierte Workflows
Kategorie: Prozessmanagement
Fokus: Beides
Technologie: Python, GraphDB (Neo4j), Celery (Task Scheduling)
Status: Entwurf
Version: 2.0 (Maximal Erweitert)
```

## 1. Business Case

**User Story:** "Als Gärtner möchte ich bewährte Best-Practice-Workflows nutzen oder eigene Pflegestrategien als Templates speichern, um konsistente Ergebnisse zu erzielen, keine kritischen Eingriffe zu vergessen und meine Arbeitsabläufe zu optimieren."

**Beschreibung:**
Das System implementiert ein flexibles, templat-basiertes Task-Management-System mit intelligenter Planung und Dependency-Resolution:

**Workflow-Typen:**

**System-Templates (Built-in Best Practices):**
- **Cannabis SOG (Sea of Green):** Keine Topping, hohe Pflanzendichte, kurze Vegi
- **Cannabis SCROG (Screen of Green):** LST, Netz-Training, Lollipopping
- **Cannabis Mainlining:** Symmetrisches Topping, 8 Haupttriebe
- **Tomaten Multi-Stem:** Ausgeizen, Stützen, Fruchtausdünnung
- **Kartoffel-Häufeln:** Mehrmaliges Anhäufeln für höhere Erträge
- **Beerensträucher-Schnitt:** Jahreszeitlicher Rückschnitt

**User-Blueprints (Eigene Strategien):**
- Speicherbar, editierbar, teilbar mit Community
- Versionierung von Template-Änderungen
- Import/Export als JSON

**Task-Trigger-Typen:**
1. **Phase-Entry:** Automatisch beim Phasenwechsel (z.B. Blüte-Start)
2. **Days-After-Phase:** X Tage nach Phasen-Eintritt
3. **Days-After-Planting:** X Tage nach Pflanzung
4. **Absolute-Date:** Festes Kalenderdatum
5. **Conditional:** Basierend auf Zustand (z.B. Höhe > 30cm)
6. **Manual:** Nutzer initiiert

**Task-Kategorien:**
- **Training:** Topping, FIM, LST (Low-Stress), HST (High-Stress), Supercropping
- **Pruning:** Defoliation, Lollipopping, Sucker-Removal, Thinning
- **Transplanting:** Up-Potting, Umsetzen in Beet
- **Feeding:** Spezialdünger-Gaben, Foliar-Feeding
- **IPM:** Präventives Spraying, Nützlings-Ausbringung
- **Harvest:** Partial-Harvest, Final-Harvest, Flushing-Start
- **Maintenance:** Substrat-Check, Reinigung, Equipment-Wartung

**Intelligente Features:**
- **HST-Validation:** Verhindert High-Stress-Training in kritischen Phasen
- **Dependency-Chains:** Tasks werden automatisch verschoben wenn Vorgänger verspätet
- **Resource-Conflicts:** Warnung bei gleichzeitigen Tasks an verschiedenen Pflanzen
- **Completion-Verification:** Foto-Upload-Pflicht bei kritischen Eingriffen
- **Learning-Mode:** System lernt durchschnittliche Completion-Times

**Hormon-Verständnis (Plant Stress Physiology):**
- **Auxin-Dominanz:** Topping erhöht laterales Wachstum
- **Stress-Recovery:** Mindestens 3-7 Tage zwischen HST-Events
- **Photoperiod-Sensitivity:** Keine HST während Blüte-Transition
- **Hermaphroditism-Risk:** Cannabis reagiert auf Stress mit Zwitter-Bildung

## 2. GraphDB-Modellierung

### Nodes:
- **`:WorkflowTemplate`** - Wiederverwendbarer Workflow
  - Properties:
    - `template_id: str`
    - `name: str`
    - `description: str`
    - `created_by: str` (User-ID oder "system")
    - `created_at: datetime`
    - `version: str` (Semantic Versioning)
    - `is_public: bool`
    - `species_compatible: list[str]` (Binomiale Namen)
    - `growth_system: Literal['soil', 'hydro', 'coco', 'any']`
    - `difficulty_level: Literal['beginner', 'intermediate', 'advanced']`
    - `estimated_total_hours: float`
    - `category: Literal['training', 'maintenance', 'harvest', 'custom']`
    - `tags: list[str]`
    - `usage_count: int` (Wie oft verwendet)
    - `average_rating: Optional[float]`

- **`:TaskTemplate`** - Template für einzelne Aufgabe
  - Properties:
    - `task_template_id: str`
    - `name: str`
    - `instruction: str` (Detaillierte Anleitung)
    - `category: str`
    - `trigger_type: Literal['phase_entry', 'days_after_phase', 'days_after_planting', 'absolute_date', 'manual', 'conditional']`
    - `trigger_phase: Optional[str]` (z.B. "vegetative")
    - `days_offset: Optional[int]` (Für zeitbasierte Trigger)
    - `conditional_expression: Optional[str]` (z.B. "plant.height_cm > 30")
    - `requires_photo: bool`
    - `requires_confirmation: bool`
    - `stress_level: Literal['none', 'low', 'medium', 'high']`
    - `estimated_duration_minutes: int`
    - `tools_required: list[str]`
    - `materials_required: list[str]`
    - `skill_level: Literal['beginner', 'intermediate', 'advanced']`
    - `video_tutorial_url: Optional[str]`
    - `safety_notes: Optional[str]`

- **`:Task`** - Konkrete Aufgaben-Instanz
  - Properties:
    - `task_id: str`
    - `name: str`
    - `instruction: str`
    - `category: str`
    - `due_date: date`
    - `scheduled_time: Optional[time]`
    - `status: Literal['pending', 'in_progress', 'completed', 'skipped', 'failed']`
    - `priority: Literal['low', 'medium', 'high', 'critical']`
    - `created_at: datetime`
    - `started_at: Optional[datetime]`
    - `completed_at: Optional[datetime]`
    - `estimated_duration_minutes: int`
    - `actual_duration_minutes: Optional[int]`
    - `requires_photo: bool`
    - `photo_refs: list[str]` (S3 URLs oder Base64)
    - `completion_notes: Optional[str]`
    - `difficulty_rating: Optional[int]` (1-5, nachträglich)
    - `quality_rating: Optional[int]` (1-5, Ergebnis-Qualität)

- **`:TaskDependency`** - Abhängigkeits-Regel
  - Properties:
    - `dependency_type: Literal['blocks', 'requires', 'recommended_after']`
    - `min_delay_days: int` (Minimum zwischen Tasks)
    - `max_delay_days: Optional[int]`
    - `strict: bool` (Muss erfüllt sein vs. Warnung)

- **`:TaskSchedule`** - Zeitliche Planung
  - Properties:
    - `schedule_id: str`
    - `recurrence_pattern: Optional[str]` (Cron-Expression)
    - `next_occurrence: Optional[datetime]`
    - `auto_generate: bool`

- **`:WorkflowExecution`** - Laufende Workflow-Instanz
  - Properties:
    - `execution_id: str`
    - `started_at: datetime`
    - `completed_at: Optional[datetime]`
    - `completion_percentage: float`
    - `on_schedule: bool`
    - `days_ahead_behind: int`

- **`:TaskComment`** - Kommentare/Notizen
  - Properties:
    - `comment_id: str`
    - `comment_text: str`
    - `created_by: str`
    - `created_at: datetime`

### Edges:
```cypher
(:WorkflowTemplate)-[:CONTAINS {sequence: int}]->(:TaskTemplate)
(:TaskTemplate)-[:REQUIRES_PHASE]->(:GrowthPhase)
(:TaskTemplate)-[:DEPENDS_ON]->(:TaskDependency)->(:TaskTemplate)
(:TaskTemplate)-[:INCOMPATIBLE_WITH]->(:TaskTemplate)  // Nicht zusammen ausführbar
(:PlantInstance)-[:FOLLOWS]->(:WorkflowTemplate)
(:PlantInstance)-[:EXECUTING]->(:WorkflowExecution)
(:WorkflowExecution)-[:GENERATED]->(:Task)
(:Task)-[:INSTANCE_OF]->(:TaskTemplate)
(:PlantInstance)-[:HAS_TASK]->(:Task)
(:Task)-[:BLOCKS]->(:Task)  // Konkrete Dependency-Chain
(:Task)-[:COMPLETED_BY {timestamp: datetime}]->(:User)
(:Task)-[:HAS_COMMENT]->(:TaskComment)-[:WRITTEN_BY]->(:User)
(:WorkflowTemplate)-[:RATED_BY {rating: int, timestamp: datetime}]->(:User)
```

### Cypher-Beispiellogik:

**Task-Queue mit Priorisierung:**
```cypher
MATCH (plant:PlantInstance)-[:HAS_TASK]->(task:Task)
WHERE task.status = 'pending'

// Berechne Dringlichkeit
WITH plant, task,
     CASE
       WHEN task.due_date < date() THEN 'OVERDUE'
       WHEN task.due_date = date() THEN 'TODAY'
       WHEN task.due_date <= date() + duration('P3D') THEN 'THIS_WEEK'
       ELSE 'FUTURE'
     END AS urgency,
     date() - task.due_date AS days_overdue

// Prüfe ob Task blockiert ist
OPTIONAL MATCH (task)<-[:BLOCKS]-(blocker:Task)
WHERE blocker.status != 'completed'

WITH plant, task, urgency, days_overdue,
     COLLECT(blocker) AS blocking_tasks

WHERE SIZE(blocking_tasks) = 0  // Nur nicht-blockierte Tasks

// Score für Sortierung
WITH plant, task, urgency, days_overdue,
     CASE task.priority
       WHEN 'critical' THEN 100
       WHEN 'high' THEN 75
       WHEN 'medium' THEN 50
       WHEN 'low' THEN 25
     END AS priority_score,
     CASE urgency
       WHEN 'OVERDUE' THEN 1000
       WHEN 'TODAY' THEN 500
       WHEN 'THIS_WEEK' THEN 100
       ELSE 10
     END AS urgency_score

WITH plant, task, urgency, days_overdue,
     priority_score + urgency_score + (days_overdue * 10) AS total_score

RETURN task.task_id,
       task.name,
       plant.instance_id AS plant,
       task.due_date,
       urgency,
       days_overdue,
       task.priority,
       total_score,
       task.estimated_duration_minutes

ORDER BY total_score DESC, task.due_date ASC
LIMIT 20
```

**Workflow-Instantiation mit Dependency-Resolution:**
```cypher
// 1. Lade Workflow-Template
MATCH (wf:WorkflowTemplate {template_id: $template_id})
      -[contains:CONTAINS]->(tt:TaskTemplate)

// 2. Sammle Dependencies
OPTIONAL MATCH (tt)-[:DEPENDS_ON]->(dep:TaskDependency)->(dep_tt:TaskTemplate)

WITH wf, tt, contains.sequence AS sequence,
     COLLECT({
       dep_template: dep_tt.task_template_id,
       min_delay: dep.min_delay_days,
       strict: dep.strict
     }) AS dependencies

ORDER BY sequence

// 3. Erstelle Workflow-Execution
CREATE (exec:WorkflowExecution {
  execution_id: randomUUID(),
  started_at: datetime(),
  completion_percentage: 0,
  on_schedule: true,
  days_ahead_behind: 0
})

// 4. Verknüpfe mit Plant
WITH wf, exec, COLLECT({template: tt, seq: sequence, deps: dependencies}) AS tasks_data
MATCH (plant:PlantInstance {instance_id: $plant_id})
CREATE (plant)-[:EXECUTING]->(exec)
CREATE (plant)-[:FOLLOWS]->(wf)

// 5. Erstelle Task-Instanzen
UNWIND tasks_data AS task_data

WITH exec, plant, task_data,
     task_data.template AS tt

// Berechne Due-Date basierend auf Trigger
WITH exec, plant, task_data, tt,
     CASE tt.trigger_type
       WHEN 'phase_entry' THEN date()
       WHEN 'days_after_planting' THEN date(plant.planted_on) + duration({days: tt.days_offset})
       WHEN 'days_after_phase' THEN date() + duration({days: tt.days_offset})
       ELSE date() + duration({days: 7})
     END AS calculated_due_date

CREATE (task:Task {
  task_id: randomUUID(),
  name: tt.name,
  instruction: tt.instruction,
  category: tt.category,
  due_date: calculated_due_date,
  status: 'pending',
  priority: CASE tt.stress_level
    WHEN 'high' THEN 'high'
    WHEN 'medium' THEN 'medium'
    ELSE 'low'
  END,
  created_at: datetime(),
  estimated_duration_minutes: tt.estimated_duration_minutes,
  requires_photo: tt.requires_photo
})

CREATE (exec)-[:GENERATED]->(task)
CREATE (task)-[:INSTANCE_OF]->(tt)
CREATE (plant)-[:HAS_TASK]->(task)

// 6. Erstelle Dependency-Ketten
WITH exec, task_data
UNWIND task_data.deps AS dep_info

MATCH (exec)-[:GENERATED]->(task:Task)-[:INSTANCE_OF]->(:TaskTemplate {task_template_id: task_data.template.task_template_id})
MATCH (exec)-[:GENERATED]->(dep_task:Task)-[:INSTANCE_OF]->(:TaskTemplate {task_template_id: dep_info.dep_template})

CREATE (dep_task)-[:BLOCKS {min_delay_days: dep_info.min_delay, strict: dep_info.strict}]->(task)

RETURN exec.execution_id AS execution_id,
       COUNT(DISTINCT task) AS tasks_created
```

**HST-Validation (High-Stress Training):**
```cypher
MATCH (plant:PlantInstance {instance_id: $plant_id})
      -[:CURRENT_PHASE]->(phase:GrowthPhase)

// Prüfe ob Task HST ist
WITH plant, phase,
     $task_name AS task_name,
     $task_category AS task_category

// HST-Tasks die in Blüte verboten sind
WITH plant, phase, task_name, task_category,
     ['topping', 'fim', 'supercropping', 'transplant', 'heavy_defoliation'] AS forbidden_in_flower

// Prüfe ob Phase flowering/ripening ist
WITH plant, phase, task_name, task_category, forbidden_in_flower,
     phase.name IN ['flowering', 'early_flowering', 'late_flowering', 'ripening'] AS is_flower_phase

// Prüfe ob Task in Forbidden-Liste
WITH plant, phase, task_name, task_category, is_flower_phase,
     ANY(forbidden IN forbidden_in_flower WHERE toLower(task_name) CONTAINS forbidden) AS is_forbidden_hst

// Prüfe letzte HST-Tasks (Recovery-Zeit)
OPTIONAL MATCH (plant)-[:HAS_TASK]->(recent_hst:Task)
WHERE recent_hst.category = 'training'
  AND recent_hst.status = 'completed'
  AND recent_hst.completed_at > datetime() - duration('P7D')

WITH plant, phase, task_name, is_flower_phase, is_forbidden_hst,
     COUNT(recent_hst) AS recent_hst_count,
     MIN(duration.between(recent_hst.completed_at, datetime()).inDays) AS days_since_last_hst

RETURN {
  can_perform: NOT (is_flower_phase AND is_forbidden_hst),
  phase: phase.name,
  is_flower_phase: is_flower_phase,
  is_hst_task: is_forbidden_hst,
  reason: CASE
    WHEN is_flower_phase AND is_forbidden_hst 
      THEN 'KRITISCH: ' + task_name + ' in Blüte-Phase führt zu Hermaphroditismus und Stress'
    WHEN recent_hst_count > 0 AND days_since_last_hst < 3
      THEN 'WARNUNG: Nur ' + toString(days_since_last_hst) + ' Tage seit letztem HST - empfohlen: 7 Tage Recovery'
    ELSE 'OK'
  END,
  recovery_status: CASE
    WHEN days_since_last_hst IS NULL THEN 'no_recent_hst'
    WHEN days_since_last_hst < 3 THEN 'insufficient_recovery'
    WHEN days_since_last_hst < 7 THEN 'partial_recovery'
    ELSE 'full_recovery'
  END
} AS validation
```

**Dynamic Rescheduling bei Verzögerung:**
```cypher
MATCH (completed_task:Task {task_id: $completed_task_id})
WHERE completed_task.status = 'completed'

// Berechne Verzögerung
WITH completed_task,
     duration.between(date(completed_task.due_date), date(completed_task.completed_at)).days AS delay_days

WHERE delay_days > 0

// Finde alle abhängigen Tasks
MATCH (completed_task)-[:BLOCKS*]->(dependent:Task)
WHERE dependent.status = 'pending'

// Verschiebe Due-Date
SET dependent.due_date = dependent.due_date + duration({days: delay_days})

// Update Workflow-Execution Status
WITH completed_task, delay_days, COLLECT(dependent) AS dependents
MATCH (plant:PlantInstance)-[:HAS_TASK]->(completed_task)
MATCH (plant)-[:EXECUTING]->(exec:WorkflowExecution)

SET exec.on_schedule = false,
    exec.days_ahead_behind = exec.days_ahead_behind - delay_days

RETURN {
  delayed_by_days: delay_days,
  rescheduled_tasks: SIZE(dependents),
  new_execution_status: exec.on_schedule,
  total_delay: exec.days_ahead_behind
} AS result
```

**Workflow-Progress-Tracking:**
```cypher
MATCH (plant:PlantInstance {instance_id: $plant_id})
      -[:EXECUTING]->(exec:WorkflowExecution)
      -[:GENERATED]->(task:Task)

WITH exec,
     COUNT(task) AS total_tasks,
     COUNT(CASE WHEN task.status = 'completed' THEN 1 END) AS completed_tasks,
     COUNT(CASE WHEN task.status = 'pending' AND task.due_date < date() THEN 1 END) AS overdue_tasks,
     AVG(CASE WHEN task.status = 'completed' THEN task.actual_duration_minutes ELSE null END) AS avg_duration

WITH exec, total_tasks, completed_tasks, overdue_tasks, avg_duration,
     (toFloat(completed_tasks) / total_tasks * 100) AS completion_percentage

SET exec.completion_percentage = completion_percentage

RETURN {
  execution_id: exec.execution_id,
  total_tasks: total_tasks,
  completed: completed_tasks,
  pending: total_tasks - completed_tasks,
  overdue: overdue_tasks,
  completion_percent: round(completion_percentage, 1),
  avg_task_duration_min: round(avg_duration, 0),
  on_schedule: exec.on_schedule,
  days_offset: exec.days_ahead_behind
} AS progress
```

## 3. Technische Umsetzung (Python)

### Logik-Anforderungen:

**1. Task Template System:**
```python
from pydantic import BaseModel, Field, validator
from typing import Literal, Optional, List
from datetime import date, datetime, timedelta

class TaskTemplate(BaseModel):
    """Template für wiederverwendbare Aufgaben"""
    
    task_template_id: str
    name: str = Field(min_length=3, max_length=200)
    instruction: str = Field(min_length=10, max_length=2000)
    category: Literal['training', 'pruning', 'transplant', 'feeding', 'ipm', 'harvest', 'maintenance']
    trigger_type: Literal['phase_entry', 'days_after_phase', 'days_after_planting', 'absolute_date', 'manual', 'conditional']
    trigger_phase: Optional[str] = None
    days_offset: Optional[int] = Field(None, ge=0, le=365)
    conditional_expression: Optional[str] = None
    requires_photo: bool = False
    requires_confirmation: bool = False
    stress_level: Literal['none', 'low', 'medium', 'high']
    estimated_duration_minutes: int = Field(ge=1, le=480)
    tools_required: List[str] = Field(default_factory=list)
    materials_required: List[str] = Field(default_factory=list)
    skill_level: Literal['beginner', 'intermediate', 'advanced'] = 'beginner'
    video_tutorial_url: Optional[str] = None
    safety_notes: Optional[str] = None
    
    @validator('days_offset')
    def validate_days_offset_for_trigger(cls, v, values):
        trigger = values.get('trigger_type')
        if trigger in ['days_after_phase', 'days_after_planting']:
            if v is None:
                raise ValueError(f"days_offset erforderlich für {trigger}")
        return v
    
    @validator('trigger_phase')
    def validate_phase_for_trigger(cls, v, values):
        trigger = values.get('trigger_type')
        if trigger in ['phase_entry', 'days_after_phase']:
            if not v:
                raise ValueError(f"trigger_phase erforderlich für {trigger}")
        return v
    
    def calculate_due_date(
        self,
        plant_instance: dict,
        current_phase: Optional[str] = None
    ) -> date:
        """
        Berechnet Due-Date basierend auf Trigger-Typ
        
        Args:
            plant_instance: Dict mit planted_on, current_phase, etc.
            current_phase: Aktuelle Wachstumsphase
        
        Returns:
            Berechnetes Fälligkeitsdatum
        """
        today = date.today()
        
        if self.trigger_type == 'manual':
            return today
        
        elif self.trigger_type == 'absolute_date':
            # Wird extern gesetzt
            return today
        
        elif self.trigger_type == 'days_after_planting':
            planted_on = plant_instance.get('planted_on')
            if not planted_on:
                return today
            return planted_on + timedelta(days=self.days_offset)
        
        elif self.trigger_type == 'phase_entry':
            # Wird ausgelöst wenn Phase eintritt
            return today
        
        elif self.trigger_type == 'days_after_phase':
            # Annahme: Phase-Entry-Datum ist bekannt
            phase_entered_at = plant_instance.get('current_phase_entered_at')
            if not phase_entered_at:
                return today
            return phase_entered_at + timedelta(days=self.days_offset)
        
        elif self.trigger_type == 'conditional':
            # Wird ausgelöst wenn Bedingung erfüllt
            return today
        
        return today

class WorkflowTemplate(BaseModel):
    """Kompletter Workflow aus mehreren Tasks"""
    
    template_id: str
    name: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=10, max_length=1000)
    created_by: str
    version: str = Field(regex=r'^\d+\.\d+\.\d+$', description="Semantic Versioning")
    is_public: bool = False
    species_compatible: List[str] = Field(min_items=1, description="Binomiale Namen")
    growth_system: Literal['soil', 'hydro', 'coco', 'any'] = 'any'
    difficulty_level: Literal['beginner', 'intermediate', 'advanced']
    estimated_total_hours: float = Field(ge=0, le=1000)
    category: Literal['training', 'maintenance', 'harvest', 'custom']
    tags: List[str] = Field(default_factory=list)
    
    @validator('version')
    def validate_semver(cls, v):
        parts = v.split('.')
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError("Version muss Semantic Versioning folgen (X.Y.Z)")
        return v
    
    @validator('species_compatible')
    def validate_scientific_names(cls, v):
        for name in v:
            parts = name.split()
            if len(parts) < 2:
                raise ValueError(f"'{name}' ist kein gültiger binomialer Name")
        return v
```

**2. HST Validator (High-Stress Training):**
```python
class HST_Validator:
    """Verhindert High-Stress Training in kritischen Phasen"""
    
    # HST-Tasks die in Blüte/Fruchtbildung verboten sind
    FORBIDDEN_IN_FLOWER = [
        'topping',
        'fim',
        'supercropping',
        'transplant',
        'heavy_defoliation',
        'mainlining'
    ]
    
    # Phasen in denen HST kritisch ist
    CRITICAL_PHASES = [
        'flowering',
        'early_flowering',
        'late_flowering',
        'ripening',
        'fruiting'
    ]
    
    # Mindest-Recovery-Zeit zwischen HST-Events
    MIN_RECOVERY_DAYS = {
        'topping': 7,
        'supercropping': 5,
        'transplant': 10,
        'heavy_defoliation': 7,
        'fim': 7
    }
    
    @classmethod
    def can_perform_hst(
        cls,
        task_name: str,
        current_phase: str,
        recent_hst_tasks: List[dict]
    ) -> tuple[bool, str, dict]:
        """
        Validiert ob HST durchgeführt werden kann
        
        Args:
            task_name: Name des geplanten Tasks
            current_phase: Aktuelle Wachstumsphase
            recent_hst_tasks: Liste von {task_name, completed_at}
        
        Returns:
            (can_perform, reason, additional_info)
        """
        task_lower = task_name.lower()
        
        # 1. Prüfe ob Task HST ist
        is_hst = any(hst in task_lower for hst in cls.FORBIDDEN_IN_FLOWER)
        
        if not is_hst:
            return True, "Kein HST-Task", {}
        
        # 2. Prüfe kritische Phase
        if current_phase in cls.CRITICAL_PHASES:
            return False, (
                f"KRITISCH: {task_name} in {current_phase}-Phase führt zu:\n"
                f"- Hermaphroditismus (Zwitter-Bildung bei Cannabis)\n"
                f"- Reduktion der Blüten-/Fruchtbildung\n"
                f"- Verzögerte Reife\n"
                f"- Erhöhtes Krankheitsrisiko"
            ), {'severity': 'critical', 'phase': current_phase}
        
        # 3. Prüfe Recovery-Zeit
        if recent_hst_tasks:
            # Finde letzten HST-Task
            latest_hst = max(recent_hst_tasks, key=lambda x: x['completed_at'])
            days_since = (datetime.now() - latest_hst['completed_at']).days
            
            # Bestimme benötigte Recovery-Zeit
            required_recovery = cls.MIN_RECOVERY_DAYS.get(
                latest_hst['task_name'].lower().split()[0],
                7
            )
            
            if days_since < required_recovery:
                return False, (
                    f"WARNUNG: Nur {days_since} Tage seit letztem HST ({latest_hst['task_name']}).\n"
                    f"Empfohlene Recovery-Zeit: {required_recovery} Tage.\n"
                    f"Zu kurze Recovery kann führen zu:\n"
                    f"- Reduziertes Wachstum\n"
                    f"- Erhöhte Krankheitsanfälligkeit\n"
                    f"- Stress-Symptome (Blattverfärbung, Wachstumsstillstand)"
                ), {
                    'severity': 'warning',
                    'days_since_last_hst': days_since,
                    'required_recovery': required_recovery,
                    'can_override': True
                }
        
        return True, "HST kann sicher durchgeführt werden", {
            'severity': 'ok',
            'recommendation': 'Nach HST 7 Tage kein weiteres Training'
        }
    
    @staticmethod
    def get_hst_best_practices(task_name: str) -> dict:
        """Gibt Best-Practices für spezifische HST-Techniken"""
        
        practices = {
            'topping': {
                'best_timing': 'Vegetative Phase, min. 4-6 Nodien',
                'tools': ['Scharfe, sterilisierte Schere'],
                'steps': [
                    '1. Identifiziere Haupttrieb',
                    '2. Schneide oberhalb 3.-4. Nodium',
                    '3. Sauberer 45° Schnitt',
                    '4. Keine Bewässerung für 24h'
                ],
                'recovery': '7-10 Tage',
                'expected_outcome': '2 Haupttriebe, buschigeres Wachstum',
                'risks': ['Stress', 'Verlangsamtes Wachstum', 'Infektion an Schnittstelle']
            },
            'supercropping': {
                'best_timing': 'Späte Vegetative Phase, 2-3 Wochen vor Blüte',
                'tools': ['Nur Hände'],
                'steps': [
                    '1. Wähle Zweig der dominiert',
                    '2. Drücke sanft bis innere Struktur bricht',
                    '3. Biege vorsichtig 90°',
                    '4. Fixiere mit Pflanzenbinder wenn nötig'
                ],
                'recovery': '5-7 Tage (Kallus-Bildung)',
                'expected_outcome': 'Stärkerer Zweig, mehr Seitentriebe',
                'risks': ['Kompletter Bruch', 'Infektion', 'Wachstumsstillstand']
            },
            'lollipopping': {
                'best_timing': 'Frühe Blüte (Woche 1-2)',
                'tools': ['Schere'],
                'steps': [
                    '1. Entferne untere 1/3 der Zweige',
                    '2. Fokussiere auf schwach beleuchtete Bereiche',
                    '3. Arbeite über mehrere Tage verteilt'
                ],
                'recovery': '3-5 Tage',
                'expected_outcome': 'Energie-Fokus auf Top-Colas, bessere Luftzirkulation',
                'risks': ['Zu viel Laub entfernt = Stress', 'Reduzierte Photosynthese']
            }
        }
        
        task_key = task_name.lower().split()[0]
        return practices.get(task_key, {
            'best_timing': 'Konsultiere Fachliteratur',
            'tools': [],
            'steps': [],
            'recovery': 'Unbekannt',
            'expected_outcome': '',
            'risks': ['Unbekannte Technik']
        })
```

**3. Workflow Executor:**
```python
from typing import Dict, List
from datetime import date, datetime

class WorkflowExecutor:
    """Generiert konkrete Tasks aus Templates"""
    
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
    
    def instantiate_workflow(
        self,
        plant_id: str,
        workflow_template_id: str,
        start_date: Optional[date] = None
    ) -> dict:
        """
        Erstellt Task-Instanzen aus Workflow-Template
        
        Returns:
            {
                execution_id: str,
                tasks_created: int,
                tasks: List[dict],
                dependencies_created: int
            }
        """
        if not start_date:
            start_date = date.today()
        
        with self.driver.session() as session:
            # Hole Plant-Info
            plant = session.run("""
                MATCH (p:PlantInstance {instance_id: $plant_id})
                OPTIONAL MATCH (p)-[:CURRENT_PHASE]->(phase:GrowthPhase)
                RETURN p.planted_on AS planted_on,
                       p.instance_id AS instance_id,
                       phase.name AS current_phase,
                       datetime() AS current_phase_entered_at
            """, plant_id=plant_id).single()
            
            if not plant:
                raise ValueError(f"Plant {plant_id} nicht gefunden")
            
            plant_data = {
                'planted_on': plant['planted_on'],
                'instance_id': plant['instance_id'],
                'current_phase': plant['current_phase'],
                'current_phase_entered_at': plant['current_phase_entered_at']
            }
            
            # Hole Workflow-Template mit Tasks
            result = session.run("""
                MATCH (wf:WorkflowTemplate {template_id: $wf_id})
                      -[contains:CONTAINS]->(tt:TaskTemplate)
                OPTIONAL MATCH (tt)-[:DEPENDS_ON]->(dep:TaskDependency)
                      ->(dep_tt:TaskTemplate)
                RETURN wf,
                       COLLECT({
                         template: tt,
                         sequence: contains.sequence,
                         dependencies: COLLECT({
                           dep_template_id: dep_tt.task_template_id,
                           min_delay_days: dep.min_delay_days,
                           strict: dep.strict
                         })
                       }) AS tasks_data
                ORDER BY contains.sequence
            """, wf_id=workflow_template_id).single()
            
            if not result:
                raise ValueError(f"Workflow-Template {workflow_template_id} nicht gefunden")
            
            workflow = result['wf']
            tasks_data = result['tasks_data']
            
            # Erstelle Workflow-Execution
            execution_id = self._create_execution(session, plant_id, workflow_template_id)
            
            # Erstelle Tasks
            created_tasks = []
            task_id_map = {}  # template_id -> task_id
            
            for task_data in tasks_data:
                template_dict = dict(task_data['template'])
                template = TaskTemplate(**template_dict)
                
                # Berechne Due-Date
                due_date = template.calculate_due_date(plant_data)
                
                # Erstelle Task
                task_id = self._create_task(
                    session=session,
                    plant_id=plant_id,
                    execution_id=execution_id,
                    template=template,
                    due_date=due_date
                )
                
                task_id_map[template.task_template_id] = task_id
                
                created_tasks.append({
                    'task_id': task_id,
                    'name': template.name,
                    'due_date': due_date,
                    'category': template.category
                })
            
            # Erstelle Dependency-Ketten
            dependencies_count = 0
            for task_data in tasks_data:
                template_id = task_data['template']['task_template_id']
                task_id = task_id_map.get(template_id)
                
                for dep in task_data['dependencies']:
                    if dep['dep_template_id']:
                        dep_task_id = task_id_map.get(dep['dep_template_id'])
                        
                        if dep_task_id and task_id:
                            self._create_dependency(
                                session,
                                dep_task_id,
                                task_id,
                                dep['min_delay_days']
                            )
                            dependencies_count += 1
            
            return {
                'execution_id': execution_id,
                'tasks_created': len(created_tasks),
                'tasks': created_tasks,
                'dependencies_created': dependencies_count
            }
    
    def _create_execution(self, session, plant_id: str, template_id: str) -> str:
        """Erstellt WorkflowExecution-Node"""
        result = session.run("""
            CREATE (exec:WorkflowExecution {
                execution_id: randomUUID(),
                started_at: datetime(),
                completion_percentage: 0,
                on_schedule: true,
                days_ahead_behind: 0
            })
            
            WITH exec
            MATCH (plant:PlantInstance {instance_id: $plant_id})
            MATCH (wf:WorkflowTemplate {template_id: $template_id})
            
            CREATE (plant)-[:EXECUTING]->(exec)
            CREATE (plant)-[:FOLLOWS]->(wf)
            
            RETURN exec.execution_id AS execution_id
        """, plant_id=plant_id, template_id=template_id).single()
        
        return result['execution_id']
    
    def _create_task(
        self,
        session,
        plant_id: str,
        execution_id: str,
        template: TaskTemplate,
        due_date: date
    ) -> str:
        """Erstellt Task-Node aus Template"""
        
        # Priority aus Stress-Level ableiten
        priority_map = {
            'none': 'low',
            'low': 'low',
            'medium': 'medium',
            'high': 'high'
        }
        
        result = session.run("""
            MATCH (exec:WorkflowExecution {execution_id: $exec_id})
            MATCH (plant:PlantInstance {instance_id: $plant_id})
            MATCH (tt:TaskTemplate {task_template_id: $template_id})
            
            CREATE (task:Task {
                task_id: randomUUID(),
                name: $name,
                instruction: $instruction,
                category: $category,
                due_date: date($due_date),
                status: 'pending',
                priority: $priority,
                created_at: datetime(),
                estimated_duration_minutes: $duration,
                requires_photo: $requires_photo,
                photo_refs: []
            })
            
            CREATE (exec)-[:GENERATED]->(task)
            CREATE (task)-[:INSTANCE_OF]->(tt)
            CREATE (plant)-[:HAS_TASK]->(task)
            
            RETURN task.task_id AS task_id
        """,
            exec_id=execution_id,
            plant_id=plant_id,
            template_id=template.task_template_id,
            name=template.name,
            instruction=template.instruction,
            category=template.category,
            due_date=due_date.isoformat(),
            priority=priority_map[template.stress_level],
            duration=template.estimated_duration_minutes,
            requires_photo=template.requires_photo
        ).single()
        
        return result['task_id']
    
    def _create_dependency(
        self,
        session,
        blocker_task_id: str,
        blocked_task_id: str,
        min_delay_days: int
    ):
        """Erstellt BLOCKS-Beziehung"""
        session.run("""
            MATCH (blocker:Task {task_id: $blocker_id})
            MATCH (blocked:Task {task_id: $blocked_id})
            
            CREATE (blocker)-[:BLOCKS {min_delay_days: $delay}]->(blocked)
        """, blocker_id=blocker_task_id, blocked_id=blocked_task_id, delay=min_delay_days)
```

**4. Dynamic Rescheduler:**
```python
class DynamicRescheduler:
    """Verschiebt nachgelagerte Tasks bei Verzögerungen"""
    
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
    
    def reschedule_dependent_tasks(
        self,
        completed_task_id: str
    ) -> dict:
        """
        Passt Due-Dates abhängiger Tasks an wenn Vorgänger verspätet
        
        Returns:
            {
                delay_days: int,
                rescheduled_count: int,
                affected_tasks: List[dict]
            }
        """
        with self.driver.session() as session:
            # Berechne Verzögerung
            result = session.run("""
                MATCH (task:Task {task_id: $task_id})
                WHERE task.status = 'completed'
                
                WITH task,
                     duration.between(
                         date(task.due_date),
                         date(task.completed_at)
                     ).days AS delay_days
                
                RETURN delay_days
            """, task_id=completed_task_id).single()
            
            if not result:
                return {'delay_days': 0, 'rescheduled_count': 0, 'affected_tasks': []}
            
            delay_days = result['delay_days']
            
            if delay_days <= 0:
                return {'delay_days': 0, 'rescheduled_count': 0, 'affected_tasks': []}
            
            # Verschiebe abhängige Tasks
            affected = session.run("""
                MATCH (completed:Task {task_id: $task_id})
                      -[:BLOCKS*]->(dependent:Task)
                WHERE dependent.status = 'pending'
                
                WITH dependent, $delay AS delay_days
                
                SET dependent.due_date = dependent.due_date + duration({days: delay_days})
                
                RETURN dependent.task_id AS task_id,
                       dependent.name AS name,
                       dependent.due_date AS new_due_date
            """, task_id=completed_task_id, delay=delay_days).data()
            
            # Update Workflow-Execution Status
            session.run("""
                MATCH (task:Task {task_id: $task_id})
                      <-[:GENERATED]-(exec:WorkflowExecution)
                
                SET exec.on_schedule = false,
                    exec.days_ahead_behind = exec.days_ahead_behind - $delay
            """, task_id=completed_task_id, delay=delay_days)
            
            return {
                'delay_days': delay_days,
                'rescheduled_count': len(affected),
                'affected_tasks': affected
            }
    
    def check_task_readiness(self, task_id: str) -> dict:
        """
        Prüft ob Task bereit ist (alle Blocker completed)
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (task:Task {task_id: $task_id})
                
                OPTIONAL MATCH (task)<-[:BLOCKS]-(blocker:Task)
                
                WITH task,
                     COLLECT(blocker) AS blockers,
                     COLLECT(CASE 
                       WHEN blocker.status = 'completed' THEN 1 
                       ELSE 0 
                     END) AS blocker_statuses
                
                WITH task, blockers,
                     SIZE([s IN blocker_statuses WHERE s = 0]) AS incomplete_blockers
                
                RETURN task.task_id AS task_id,
                       task.name AS name,
                       task.status AS status,
                       SIZE(blockers) AS total_blockers,
                       incomplete_blockers,
                       incomplete_blockers = 0 AS is_ready,
                       [b IN blockers WHERE b.status != 'completed' | b.name] AS blocking_tasks
            """, task_id=task_id).single()
            
            return dict(result) if result else {}
```

### Datenvalidierung (Type Hinting):
```python
from typing import Literal, Optional, List
from pydantic import BaseModel, Field, validator
from datetime import date, time, datetime

TaskCategory = Literal['training', 'pruning', 'transplant', 'feeding', 'ipm', 'harvest', 'maintenance']
TriggerType = Literal['phase_entry', 'days_after_phase', 'days_after_planting', 'absolute_date', 'manual', 'conditional']
TaskStatus = Literal['pending', 'in_progress', 'completed', 'skipped', 'failed']
TaskPriority = Literal['low', 'medium', 'high', 'critical']
StressLevel = Literal['none', 'low', 'medium', 'high']
SkillLevel = Literal['beginner', 'intermediate', 'advanced']

class TaskInstance(BaseModel):
    """Konkrete Task-Instanz"""
    
    task_id: str
    name: str = Field(min_length=3, max_length=200)
    instruction: str = Field(min_length=10)
    category: TaskCategory
    due_date: date
    scheduled_time: Optional[time] = None
    status: TaskStatus = 'pending'
    priority: TaskPriority = 'medium'
    estimated_duration_minutes: int = Field(ge=1, le=480)
    requires_photo: bool = False
    photo_refs: List[str] = Field(default_factory=list)
    completion_notes: Optional[str] = Field(None, max_length=1000)
    
    @validator('photo_refs')
    def validate_photos_when_required(cls, v, values):
        if values.get('requires_photo') and values.get('status') == 'completed':
            if not v:
                raise ValueError("Foto-Upload erforderlich für diesen Task")
        return v

class TaskCompletion(BaseModel):
    """Task-Abschluss-Daten"""
    
    task_id: str
    completed_at: datetime
    actual_duration_minutes: int = Field(ge=1)
    photo_refs: List[str] = Field(default_factory=list)
    completion_notes: Optional[str] = None
    difficulty_rating: Optional[int] = Field(None, ge=1, le=5)
    quality_rating: Optional[int] = Field(None, ge=1, le=5)
    
    def calculate_performance_score(self, estimated_duration: int) -> float:
        """
        Berechnet Performance-Score
        - Zeit-Effizienz
        - Qualität
        
        Returns: Score 0-100
        """
        # Zeit-Effizienz (50% des Scores)
        time_ratio = estimated_duration / self.actual_duration_minutes
        time_score = min(50, time_ratio * 50)
        
        # Qualität (50% des Scores)
        quality_score = (self.quality_rating or 3) / 5 * 50 if self.quality_rating else 30
        
        return round(time_score + quality_score, 1)
```

## 4. Abhängigkeiten

**Erforderliche Module:**
- REQ-001 (Stammdaten): Species für Template-Kompatibilität
- REQ-003 (Phasen): GrowthPhase für Phase-Trigger
- REQ-002 (Standort): Location für Multi-Plant-Workflows

**Wird benötigt von:**
- REQ-007 (Ernte): Harvest-Tasks als Teil von Workflows
- REQ-010 (IPM): IPM-Tasks (Spraying, Inspection)
- REQ-009 (Dashboard): Task-Queue-Widget

**Python-Bibliotheken:**
- `celery` - Zeitgesteuerte Task-Erinnerungen
- `croniter` - Cron-Expression-Parsing für Recurring Tasks
- `jsonschema` - Validierung von Workflow-JSON-Importen

## 5. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **Template-Bibliothek:** 15+ System-Workflows (Cannabis, Tomaten, Kartoffeln, etc.)
- [ ] **User-Workflows:** Nutzer können eigene Templates erstellen/editieren
- [ ] **Foto-Upload-Enforcement:** Tasks mit requires_photo=true blockieren ohne Foto
- [ ] **HST-Validierung:** System verhindert Topping/Supercropping in Blüte
- [ ] **Dependency-Resolution:** Korrekte Berechnung von Abhängigkeitsketten
- [ ] **Auto-Rescheduling:** Verzögerte Tasks verschieben Nachfolger automatisch
- [ ] **Kalender-Ansicht:** Gantt-Chart für nächste 4 Wochen
- [ ] **Push-Notifications:** Erinnerungen für überfällige/heutige Tasks
- [ ] **Bulk-Actions:** Mehrere Tasks auf einmal als "completed" markieren
- [ ] **Task-Comments:** Nutzer können Notizen/Fragen zu Tasks hinterlassen
- [ ] **Progress-Tracking:** Workflow-Fortschritt in % für jede Pflanze
- [ ] **Template-Versioning:** Änderungen an Templates erstellen neue Version
- [ ] **Import/Export:** Workflows als JSON exportieren/importieren
- [ ] **Mobile-Optimierung:** Touch-freundliche Task-Abhak-Funktion
- [ ] **Recurring-Tasks:** Wartungs-Tasks mit Cron-Expression (z.B. wöchentliche Reinigung)
- [ ] **Conditional-Trigger:** Tasks basierend auf Bedingungen (z.B. "wenn Höhe > 50cm")
- [ ] **Time-Estimates:** System lernt durchschnittliche Completion-Times pro Task-Typ
- [ ] **Skill-Level-Filter:** Anfänger sehen nur Beginner-Templates
- [ ] **Video-Tutorials:** Links zu Anleitungsvideos in Templates

### Testszenarien:

**Szenario 1: Cannabis SOG Workflow-Instantiation**
```
GIVEN: Cannabis-Pflanze, gepflanzt am 01.01.2025
WHEN: SOG-Workflow wird angewendet
THEN:
  - Tasks generiert:
    1. Tag 14: Transplant zu finalen Töpfen
    2. Tag 18: Light Defoliation (untere Blätter)
    3. Tag 21: Switch zu 12/12 Licht (Blüte-Einleitung)
    4. Tag 35: Lollipopping (untere 1/3 entfernen)
    5. Tag 56: Flushing starten
    6. Tag 70: Ernte
  - Alle Tasks haben Status 'pending'
  - Dependencies: Task 2 blockt durch Task 1, etc.
```

**Szenario 2: HST-Validierung verhindert Topping**
```
GIVEN: Cannabis in Early-Flowering-Phase
WHEN: Nutzer versucht "Topping" Task zu erstellen
THEN:
  - HST_Validator.can_perform_hst() → False
  - Error-Message: "KRITISCH: Topping in flowering-Phase führt zu Hermaphroditismus"
  - UI blockiert Task-Erstellung
  - Vorschlag: "LST (Low-Stress) ist noch möglich"
```

**Szenario 3: Dynamic Rescheduling**
```
GIVEN: Workflow mit Tasks:
  - Task A: Topping (Due: 15.01, Completed: 20.01) → 5 Tage Verzögerung
  - Task B: Defoliation (Due: 22.01, abhängig von Task A mit min_delay=7)
WHEN: Task A als completed markiert mit 5 Tagen Verspätung
THEN:
  - Task B.due_date wird verschoben: 22.01 → 27.01
  - WorkflowExecution.on_schedule = false
  - WorkflowExecution.days_ahead_behind = -5
  - Notification: "Workflow 5 Tage hinter Zeitplan"
```

**Szenario 4: Dependency-Blockierung**
```
GIVEN: Task A (Transplant) blockiert Task B (Heavy Defoliation)
      Task A.status = 'pending'
WHEN: Nutzer versucht Task B zu starten
THEN:
  - check_task_readiness(Task B) → is_ready = false
  - blocking_tasks = ["Transplant"]
  - UI zeigt: "Wartend auf: Transplant"
  - Task B ist ausgegraut / nicht klickbar
```

**Szenario 5: Foto-Upload-Enforcement**
```
GIVEN: Task "Mainlining - 4. Topping" mit requires_photo=true
WHEN: Nutzer klickt "Complete" ohne Foto hochzuladen
THEN:
  - Validierung schlägt fehl
  - Error: "Foto-Dokumentation erforderlich für diesen Task"
  - Modal: Kamera-Upload oder Datei-Auswahl
  - Task bleibt 'in_progress' bis Foto vorhanden
```

**Szenario 6: Recovery-Zeit-Warnung**
```
GIVEN: Supercropping wurde vor 3 Tagen abgeschlossen
WHEN: Nutzer plant neues Topping (beides HST)
THEN:
  - HST_Validator warnt: "Nur 3 Tage seit letztem HST"
  - Empfohlen: 7 Tage Recovery
  - Severity: 'warning', can_override: true
  - UI: "Fortfahren auf eigenes Risiko" Button
```

**Szenario 7: Template-Import (Community-Workflow)**
```
GIVEN: User lädt "Advanced-SCROG.json" von Community
WHEN: Import-Funktion wird aufgerufen
THEN:
  - JSON-Schema-Validierung
  - Prüfung auf required fields (name, tasks, dependencies)
  - WorkflowTemplate-Node erstellt mit created_by='imported'
  - Tasks und Dependencies werden rekonstruiert
  - Success: "Workflow 'Advanced SCROG' importiert (Version 1.2.0)"
```

---

**Hinweise für RAG-Integration:**
- Keywords: Workflow, Task, HST, Training, Topping, LST, Dependency, Scheduling, Template
- Fachbegriffe: Auxin-Dominanz, Hermaphroditismus, Mainlining, Lollipopping, SOG, SCROG, Supercropping
- Verknüpfung: Zentral für REQ-003 (Phasen-Trigger), REQ-007 (Harvest-Tasks), REQ-010 (IPM-Tasks)
- Pflanzenwissenschaft: Stress-Physiologie, Hormon-Regulation, Recovery-Zeiten
