# Spezifikation: REQ-006 - Aufgabenplanung

```yaml
ID: REQ-006
Titel: Modulare Aufgabenplanung & Benutzerdefinierte Workflows
Kategorie: Prozessmanagement
Fokus: Beides
Technologie: Python, ArangoDB, Celery (Task Scheduling)
Status: Entwurf
Version: 2.1 (Agrarbiologie-Review)
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

**Zimmerpflanzen-Templates (Built-in):**
- **Tropische Grünpflanze (Standard):** Gießen nach Substratfeuchte, monatlich düngen März-Oktober, Blattreinigung quartalsweise
- **Orchidee (Phalaenopsis):** Tauchbad wöchentlich, Orchideendünger alle 2 Wochen, Temperatur-Drop 5°C für 4 Wochen zur Blüte-Induktion
- **Kaktus/Sukkulente:** Minimalbewässerung, Winterruhe Oktober-Februar (kalt, trocken, kein Dünger), Umtopfen alle 2-3 Jahre
- **Calathea/Marante:** Erhöhte Luftfeuchte (>60% rH), kalkfreies Wasser, regelmäßige Schädlingskontrolle (Spinnmilben)

**Hydroponik-Wartungs-Templates (Built-in):**
- **Nährlösung-Wechsel:** Komplettwechsel alle 7-14 Tage mit EC/pH-Messung, Reservoir-Reinigung, Frisch-Ansatz (REQ-014)
- **Sonden-Kalibrierung:** Wöchentliche pH/EC-Kalibrierung mit Referenzlösungen
- **Wurzelinspektion:** Regelmäßige Kontrolle auf Pythium, Verfärbungen, Algenwachstum
- **System-Reinigung:** Leitungen, Pumpen, Tropfer spülen (H₂O₂ oder enzymatisch)

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
- **Ausgeizen:** Geiztrieb-Entfernung (Stabtomaten, Aubergine) — eigene Kategorie, nicht HST
- **Transplanting:** Up-Potting, Umsetzen in Beet
- **Feeding:** Spezialdünger-Gaben, Foliar-Feeding
- **IPM:** Präventives Spraying, Nützlings-Ausbringung
- **Harvest:** Partial-Harvest, Final-Harvest, Flushing-Start
- **Observation:** Wachstumsmessung, Blattkontrolle, pH/EC-Ablesung, Foto-Fortschrittsdokumentation, Symptom-Check
- **Maintenance:** Substrat-Check, Reinigung, Equipment-Wartung

**Intelligente Features:**
- **HST-Validation:** Verhindert High-Stress-Training in kritischen Phasen
- **Dependency-Chains:** Tasks werden automatisch verschoben wenn Vorgänger verspätet
- **Resource-Conflicts:** Warnung bei gleichzeitigen Tasks an verschiedenen Pflanzen
- **Completion-Verification:** Foto-Upload-Pflicht bei kritischen Eingriffen
- **Learning-Mode:** System lernt durchschnittliche Completion-Times

**Hormon-Verständnis (Plant Stress Physiology):**
- **Auxin-Dominanz:** Topping erhöht laterales Wachstum
- **Stress-Recovery:** Artspezifische Recovery-Zeiten (Cannabis 7d, Tomaten 2-3d, Paprika 5d)
- **Kumulativer Stress:** Stress-Hormone (Jasmonsäure, Ethylen) akkumulieren — mehrere HST-Events im 14-Tage-Fenster haben additive Effekte
- **Photoperiod-Sensitivity:** Kein Topping/FIM/Mainlining während Blüte; Supercropping im Stretch (Early Flowering) noch erlaubt
- **Hermaphroditism-Risk:** Cannabis reagiert auf Stress mit Zwitter-Bildung
- **Karenzzeit (PHI):** Wartezeit zwischen Pflanzenschutz (REQ-010) und Ernte — Lebensmittelsicherheits-Validierung
- **Tageszeit-Empfehlung:** Transplanting abends/Lights-Off (reduzierte Transpiration minimiert Welkestress; volle Dunkelperiode für Wurzel-Substrat-Kontakt), Training morgens (turgorreicher Stängel), Foliar bei Lights-Off (langsamere Verdunstung erhöht Kontaktzeit, kein Phototoxizitäts-Risiko bei Öl-Produkten)

## 2. ArangoDB-Graph-Modellierung

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
    - `trigger_type: Literal['phase_entry', 'days_after_phase', 'days_after_planting', 'absolute_date', 'manual', 'conditional', 'gdd_threshold']`
    - `trigger_phase: Optional[str]` (z.B. "vegetative")
    - `days_offset: Optional[int]` (Für zeitbasierte Trigger)
    - `gdd_threshold: Optional[float]` (Gradtagsumme ab Pflanzung/Phasenstart — biologisch genauer als Kalendertage, REQ-003)
    - `gdd_base_temperature_c: Optional[float]` (Basistemperatur für GDD, artspezifisch — z.B. 10°C für Mais, 5°C für Weizen)
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
    - `optimal_time_of_day: Optional[Literal['morning', 'afternoon', 'evening', 'lights_off']]` (Tageszeit-Empfehlung)

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
    - `skill_level: Literal['beginner', 'intermediate', 'advanced'] = 'beginner'` (von TaskTemplate propagiert oder direkt gesetzt)
    - `stress_level: Literal['none', 'low', 'medium', 'high'] = 'none'` (von TaskTemplate propagiert oder direkt gesetzt)
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
```
Edge Collections im Graph 'kamerplanter_graph':

contains:          WorkflowTemplates -> TaskTemplates        {sequence: int}
requires_phase:    TaskTemplates -> GrowthPhases
depends_on:        TaskTemplates -> TaskDependencies -> TaskTemplates
incompatible_with: TaskTemplates -> TaskTemplates             // Nicht zusammen ausführbar
follows:           PlantInstances -> WorkflowTemplates
executing:         PlantInstances -> WorkflowExecutions
generated:         WorkflowExecutions -> Tasks
instance_of:       Tasks -> TaskTemplates
has_task:          PlantInstances -> Tasks
blocks:            Tasks -> Tasks                             // Konkrete Dependency-Chain
completed_by:      Tasks -> Users                             {timestamp: datetime}
has_comment:       Tasks -> TaskComments
written_by:        TaskComments -> Users
rated_by:          WorkflowTemplates -> Users                 {rating: int, timestamp: datetime}
```

### AQL-Beispiellogik:

**Task-Queue mit Priorisierung:**
```aql
// Task-Queue: Alle pending Tasks mit Priorisierung
FOR plant IN PlantInstances
  FOR task IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['has_task'] }
    FILTER task.status == 'pending'

    // Berechne Dringlichkeit
    LET urgency = (
      task.due_date < DATE_NOW() ? 'OVERDUE' :
      task.due_date == DATE_ISO8601(DATE_NOW()) ? 'TODAY' :
      task.due_date <= DATE_ADD(DATE_NOW(), 3, 'day') ? 'THIS_WEEK' :
      'FUTURE'
    )
    LET days_overdue = DATE_DIFF(task.due_date, DATE_NOW(), 'day')

    // Prüfe ob Task blockiert ist
    LET blocking_tasks = (
      FOR blocker IN 1..1 INBOUND task GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['blocks'] }
        FILTER blocker.status != 'completed'
        RETURN blocker
    )
    FILTER LENGTH(blocking_tasks) == 0  // Nur nicht-blockierte Tasks

    // Score für Sortierung
    LET priority_score = (
      task.priority == 'critical' ? 100 :
      task.priority == 'high' ? 75 :
      task.priority == 'medium' ? 50 :
      25
    )
    LET urgency_score = (
      urgency == 'OVERDUE' ? 1000 :
      urgency == 'TODAY' ? 500 :
      urgency == 'THIS_WEEK' ? 100 :
      10
    )
    LET total_score = priority_score + urgency_score + (days_overdue * 10)

    SORT total_score DESC, task.due_date ASC
    LIMIT 20

    RETURN {
      task_id: task.task_id,
      name: task.name,
      plant: plant.instance_id,
      due_date: task.due_date,
      urgency: urgency,
      days_overdue: days_overdue,
      priority: task.priority,
      total_score: total_score,
      estimated_duration_minutes: task.estimated_duration_minutes
    }
```

**Workflow-Instantiation mit Dependency-Resolution:**
```aql
// 1. Lade Workflow-Template mit Tasks und Dependencies
LET wf = DOCUMENT('WorkflowTemplates', @template_id)

LET tasks_data = (
  FOR tt, contains_edge IN 1..1 OUTBOUND wf GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['contains'] }
    LET dependencies = (
      FOR dep, dep_edge IN 1..1 OUTBOUND tt GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['depends_on'] }
        FOR dep_tt IN 1..1 OUTBOUND dep GRAPH 'kamerplanter_graph'
          OPTIONS { edgeCollections: ['depends_on'] }
          RETURN {
            dep_template: dep_tt.task_template_id,
            min_delay: dep.min_delay_days,
            strict: dep.strict
          }
    )
    SORT contains_edge.sequence ASC
    RETURN { template: tt, seq: contains_edge.sequence, deps: dependencies }
)

// 2. Erstelle Workflow-Execution
LET exec = FIRST(
  INSERT {
    execution_id: UUID(),
    started_at: DATE_ISO8601(DATE_NOW()),
    completion_percentage: 0,
    on_schedule: true,
    days_ahead_behind: 0
  } INTO WorkflowExecutions
  RETURN NEW
)

// 3. Verknüpfe mit Plant
LET plant = FIRST(
  FOR p IN PlantInstances FILTER p.instance_id == @plant_id RETURN p
)
INSERT { _from: plant._id, _to: exec._id } INTO executing
INSERT { _from: plant._id, _to: wf._id } INTO follows

// 4. Erstelle Task-Instanzen
LET created_tasks = (
  FOR task_data IN tasks_data
    LET tt = task_data.template

    // Berechne Due-Date basierend auf Trigger
    LET calculated_due_date = (
      tt.trigger_type == 'phase_entry' ? DATE_ISO8601(DATE_NOW()) :
      tt.trigger_type == 'days_after_planting'
        ? DATE_ADD(plant.planted_on, tt.days_offset, 'day') :
      tt.trigger_type == 'days_after_phase'
        ? DATE_ADD(DATE_NOW(), tt.days_offset, 'day') :
      DATE_ADD(DATE_NOW(), 7, 'day')
    )

    LET new_task = FIRST(
      INSERT {
        task_id: UUID(),
        name: tt.name,
        instruction: tt.instruction,
        category: tt.category,
        due_date: calculated_due_date,
        status: 'pending',
        priority: (
          tt.stress_level == 'high' ? 'high' :
          tt.stress_level == 'medium' ? 'medium' :
          'low'
        ),
        created_at: DATE_ISO8601(DATE_NOW()),
        estimated_duration_minutes: tt.estimated_duration_minutes,
        requires_photo: tt.requires_photo
      } INTO Tasks
      RETURN NEW
    )

    // Verknüpfe Task mit Execution, Template und Plant
    INSERT { _from: exec._id, _to: new_task._id } INTO generated
    INSERT { _from: new_task._id, _to: tt._id } INTO instance_of
    INSERT { _from: plant._id, _to: new_task._id } INTO has_task

    RETURN { task: new_task, template_id: tt.task_template_id, deps: task_data.deps }
)

// 5. Erstelle Dependency-Ketten
FOR ct IN created_tasks
  FOR dep_info IN ct.deps
    LET dep_task = FIRST(
      FOR other IN created_tasks
        FILTER other.template_id == dep_info.dep_template
        RETURN other.task
    )
    FILTER dep_task != null
    INSERT {
      _from: dep_task._id,
      _to: ct.task._id,
      min_delay_days: dep_info.min_delay,
      strict: dep_info.strict
    } INTO blocks

RETURN {
  execution_id: exec.execution_id,
  tasks_created: LENGTH(created_tasks)
}
```

**HST-Validation (High-Stress Training):**
```aql
// HST-Validation: Prüfe ob High-Stress Training erlaubt ist
FOR plant IN PlantInstances
  FILTER plant.instance_id == @plant_id

  // Hole aktuelle Phase
  LET phase = FIRST(
    FOR p IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
      OPTIONS { edgeCollections: ['current_phase'] }
      RETURN p
  )

  LET task_name = @task_name
  LET task_category = @task_category

  // HST-Tasks: differenziert nach Phase (Early Flower erlaubt Supercropping/Transplant)
  LET forbidden_all_flower = ['topping', 'fim', 'mainlining', 'heavy_defoliation']
  LET forbidden_mid_flower = ['supercropping', 'transplant']

  // Prüfe Phase
  LET is_early_flower = phase.name IN ['early_flowering']
  LET is_mid_late_flower = phase.name IN ['flowering', 'late_flowering', 'ripening', 'fruiting']

  // Prüfe welche Verbotsliste greift
  LET is_all_flower_forbidden = LENGTH(
    FOR forbidden IN forbidden_all_flower
      FILTER CONTAINS(LOWER(task_name), forbidden)
      RETURN 1
  ) > 0
  LET is_mid_flower_forbidden = LENGTH(
    FOR forbidden IN forbidden_mid_flower
      FILTER CONTAINS(LOWER(task_name), forbidden)
      RETURN 1
  ) > 0
  LET is_forbidden_hst = (
    (is_mid_late_flower AND (is_all_flower_forbidden OR is_mid_flower_forbidden))
    OR (is_early_flower AND is_all_flower_forbidden)
  )

  // Prüfe letzte HST-Tasks (Recovery-Zeit)
  LET recent_hst_tasks = (
    FOR recent_hst IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
      OPTIONS { edgeCollections: ['has_task'] }
      FILTER recent_hst.category == 'training'
        AND recent_hst.status == 'completed'
        AND recent_hst.completed_at > DATE_SUBTRACT(DATE_NOW(), 7, 'day')
      RETURN recent_hst
  )
  LET recent_hst_count = LENGTH(recent_hst_tasks)
  LET days_since_last_hst = (
    recent_hst_count > 0
      ? MIN(FOR h IN recent_hst_tasks RETURN DATE_DIFF(h.completed_at, DATE_NOW(), 'day'))
      : null
  )

  RETURN {
    can_perform: NOT is_forbidden_hst,
    phase: phase.name,
    is_early_flower: is_early_flower,
    is_mid_late_flower: is_mid_late_flower,
    is_hst_task: is_all_flower_forbidden OR is_mid_flower_forbidden,
    reason: (
      is_forbidden_hst
        ? CONCAT('KRITISCH: ', task_name, ' in ', phase.name, '-Phase führt zu Hermaphroditismus und Stress')
        : (is_early_flower AND is_mid_flower_forbidden
            ? CONCAT('ERLAUBT: ', task_name, ' im Stretch (Early Flowering) noch möglich')
            : (recent_hst_count > 0 AND days_since_last_hst < 3
                ? CONCAT('WARNUNG: Nur ', TO_STRING(days_since_last_hst), ' Tage seit letztem HST')
                : 'OK'))
    ),
    recovery_status: (
      days_since_last_hst == null ? 'no_recent_hst' :
      days_since_last_hst < 3 ? 'insufficient_recovery' :
      days_since_last_hst < 7 ? 'partial_recovery' :
      'full_recovery'
    )
  }
```

**Dynamic Rescheduling bei Verzögerung:**
```aql
// Dynamic Rescheduling: Verschiebe abhängige Tasks bei Verzögerung
LET completed_task = FIRST(
  FOR t IN Tasks
    FILTER t.task_id == @completed_task_id AND t.status == 'completed'
    RETURN t
)

// Berechne Verzögerung
LET delay_days = DATE_DIFF(completed_task.due_date, completed_task.completed_at, 'day')

// Finde alle abhängigen Tasks (transitive Traversierung)
LET dependents = (
  FILTER delay_days > 0
  FOR dependent IN 1..10 OUTBOUND completed_task GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['blocks'] }
    FILTER dependent.status == 'pending'

    // Verschiebe Due-Date
    UPDATE dependent WITH {
      due_date: DATE_ADD(dependent.due_date, delay_days, 'day')
    } IN Tasks
    RETURN NEW
)

// Update Workflow-Execution Status
LET plant = FIRST(
  FOR p IN 1..1 INBOUND completed_task GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['has_task'] }
    RETURN p
)
LET exec = FIRST(
  FOR e IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['executing'] }
    UPDATE e WITH {
      on_schedule: false,
      days_ahead_behind: e.days_ahead_behind - delay_days
    } IN WorkflowExecutions
    RETURN NEW
)

RETURN {
  delayed_by_days: delay_days,
  rescheduled_tasks: LENGTH(dependents),
  new_execution_status: exec.on_schedule,
  total_delay: exec.days_ahead_behind
}
```

**Workflow-Progress-Tracking:**
```aql
// Workflow-Progress-Tracking
FOR plant IN PlantInstances
  FILTER plant.instance_id == @plant_id

  FOR exec IN 1..1 OUTBOUND plant GRAPH 'kamerplanter_graph'
    OPTIONS { edgeCollections: ['executing'] }

    LET tasks = (
      FOR task IN 1..1 OUTBOUND exec GRAPH 'kamerplanter_graph'
        OPTIONS { edgeCollections: ['generated'] }
        RETURN task
    )

    LET total_tasks = LENGTH(tasks)
    LET completed_tasks = LENGTH(FOR t IN tasks FILTER t.status == 'completed' RETURN 1)
    LET overdue_tasks = LENGTH(
      FOR t IN tasks
        FILTER t.status == 'pending' AND t.due_date < DATE_ISO8601(DATE_NOW())
        RETURN 1
    )
    LET avg_duration = AVERAGE(
      FOR t IN tasks
        FILTER t.status == 'completed' AND t.actual_duration_minutes != null
        RETURN t.actual_duration_minutes
    )

    LET completion_percentage = (total_tasks > 0 ? (completed_tasks / total_tasks * 100) : 0)

    // Update Execution mit aktuellem Fortschritt
    UPDATE exec WITH { completion_percentage: completion_percentage } IN WorkflowExecutions

    RETURN {
      execution_id: exec.execution_id,
      total_tasks: total_tasks,
      completed: completed_tasks,
      pending: total_tasks - completed_tasks,
      overdue: overdue_tasks,
      completion_percent: ROUND(completion_percentage, 1),
      avg_task_duration_min: ROUND(avg_duration, 0),
      on_schedule: exec.on_schedule,
      days_offset: exec.days_ahead_behind
    }
```

## 3. Technische Umsetzung (Python)

### Logik-Anforderungen:

**1. Task Template System:**
```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional, List
from datetime import date, datetime, timedelta

class TaskTemplate(BaseModel):
    """Template für wiederverwendbare Aufgaben"""
    
    task_template_id: str
    name: str = Field(min_length=3, max_length=200)
    instruction: str = Field(min_length=10, max_length=2000)
    category: Literal['training', 'pruning', 'ausgeizen', 'transplant', 'feeding', 'ipm', 'harvest', 'observation', 'maintenance', 'care_reminder']
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
    optimal_time_of_day: Optional[Literal['morning', 'afternoon', 'evening', 'lights_off']] = Field(
        None,
        description="Empfohlene Tageszeit für optimale Ergebnisse. "
                    "morning: Stängel turgorreich, flexibel (ideal für LST/Supercropping). "
                    "afternoon/evening: Reduzierte Transpiration, Pflanze hat Nacht zur Erholung. "
                    "lights_off: Für Foliar-Feeding (langsamere Verdunstung = höhere Aufnahme, "
                    "kein Phototoxizitäts-Risiko bei Öl-Produkten wie Neem)."
    )

    @field_validator('days_offset')
    @classmethod
    def validate_days_offset_for_trigger(cls, v, info):
        trigger = info.data.get('trigger_type')
        if trigger in ['days_after_phase', 'days_after_planting']:
            if v is None:
                raise ValueError(f"days_offset erforderlich für {trigger}")
        return v
    
    @field_validator('trigger_phase')
    @classmethod
    def validate_phase_for_trigger(cls, v, info):
        trigger = info.data.get('trigger_type')
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
    
    @field_validator('version')
    @classmethod
    def validate_semver(cls, v):
        parts = v.split('.')
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError("Version muss Semantic Versioning folgen (X.Y.Z)")
        return v
    
    @field_validator('species_compatible')
    @classmethod
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
    # Differenziert nach Phase: early_flowering erlaubt Supercropping/Transplant
    # (Stretch-Phase = letztes vegetatives Internodienwachstum)
    FORBIDDEN_IN_ALL_FLOWER = [
        'topping',
        'fim',
        'mainlining',
        'heavy_defoliation',
    ]
    FORBIDDEN_FROM_MID_FLOWER = [
        'supercropping',    # Erlaubt in early_flowering (Canopy-Höhenkontrolle im Stretch)
        'transplant',       # Erlaubt in early_flowering bei rootbound-Pflanzen
    ]

    # Phasen-Einteilung für HST-Validierung
    EARLY_FLOWER_PHASES = ['early_flowering']  # Stretch — einige HST noch erlaubt
    CRITICAL_PHASES = [
        'flowering',        # Mitte Blüte — nur FORBIDDEN_IN_ALL_FLOWER
        'late_flowering',
        'ripening',
        'fruiting'
    ]

    # Mindest-Recovery-Zeit zwischen HST-Events — artspezifisch
    # Standard-Recovery (Cannabis). Andere Arten über species_recovery_factors skaliert.
    BASE_RECOVERY_DAYS = {
        'topping': 7,
        'supercropping': 5,
        'transplant': 10,
        'heavy_defoliation': 7,
        'fim': 7
    }

    # Skalierungsfaktoren für Recovery-Zeiten nach Pflanzentyp
    # Faktor < 1.0 = schnellere Erholung, > 1.0 = langsamere Erholung
    SPECIES_RECOVERY_FACTORS: dict[str, float] = {
        'cannabis':     1.0,    # Basis (Cannabis ist der Referenz-Organismus)
        'tomato':       0.4,    # Schneller Metabolismus, hohe Auxin-Produktion (2-3 Tage statt 7)
        'pepper':       0.7,    # Empfindlicher als Tomaten, aber schneller als Cannabis
        'cucumber':     0.5,    # Schnell wachsend
        'herb_annual':          0.4,    # Basilikum, Koriander — krautig-einjährig, schnelle Regeneration
        'herb_perennial_soft':  0.6,    # Minze, Oregano — krautig-mehrjährig
        'herb_perennial_woody': 0.9,    # Rosmarin, Lavendel — verholzend, langsame Kallusbildung
        'potato':       0.6,    # Langsamer als andere Solanaceae (Tomate, Paprika),
                                #   da Assimilat-Priorisierung auf Knollenbildung liegt
        'berry':        0.8,    # Holzige Stängel = langsamere Kallusbildung
        'default':      1.0,
    }

    # Temperatur-Modifikator für Recovery-Zeit:
    # Bei höheren Temperaturen läuft der Metabolismus schneller (Kallusbildung beschleunigt).
    # Bei Hitzestress (>32°C) wird Recovery durch Stress-Überlagerung wieder verlangsamt.
    TEMPERATURE_RECOVERY_MODIFIERS: dict[tuple, float] = {
        (15, 20): 1.5,   # Kühle Bedingungen: 50% längere Recovery
        (20, 25): 1.2,   # Unter Optimum
        (25, 28): 1.0,   # Optimal
        (28, 32): 1.1,   # Leichter Hitzestress
        (32, 40): 1.4,   # Hitzestress: 40% länger
    }

    @classmethod
    def can_perform_hst(
        cls,
        task_name: str,
        current_phase: str,
        recent_hst_tasks: List[dict],
        species_type: str = 'cannabis',
    ) -> tuple[bool, str, dict]:
        """
        Validiert ob HST durchgeführt werden kann.
        Berücksichtigt Phase, artspezifische Recovery und kumulativen Stress.

        Args:
            task_name: Name des geplanten Tasks
            current_phase: Aktuelle Wachstumsphase
            recent_hst_tasks: Liste von {task_name, completed_at}
            species_type: Pflanzentyp für Recovery-Skalierung

        Returns:
            (can_perform, reason, additional_info)
        """
        task_lower = task_name.lower()

        # 1. Prüfe ob Task in den Verbotslisten steht
        is_all_flower_forbidden = any(hst in task_lower for hst in cls.FORBIDDEN_IN_ALL_FLOWER)
        is_mid_flower_forbidden = any(hst in task_lower for hst in cls.FORBIDDEN_FROM_MID_FLOWER)
        is_hst = is_all_flower_forbidden or is_mid_flower_forbidden

        if not is_hst:
            return True, "Kein HST-Task", {}

        # 2. Prüfe Phase — differenziert nach Early vs. Mid/Late Flower
        if current_phase in cls.CRITICAL_PHASES and (is_all_flower_forbidden or is_mid_flower_forbidden):
            return False, (
                f"KRITISCH: {task_name} in {current_phase}-Phase führt zu:\n"
                f"- Hermaphroditismus (Zwitter-Bildung bei Cannabis)\n"
                f"- Reduktion der Blüten-/Fruchtbildung\n"
                f"- Verzögerte Reife\n"
                f"- Erhöhtes Krankheitsrisiko"
            ), {'severity': 'critical', 'phase': current_phase}

        if current_phase in cls.EARLY_FLOWER_PHASES and is_all_flower_forbidden:
            return False, (
                f"KRITISCH: {task_name} in Early-Flowering (Stretch) verboten.\n"
                f"Supercropping und Transplant sind im Stretch noch erlaubt — "
                f"aber Topping, FIM, Mainlining und Heavy Defoliation nicht."
            ), {'severity': 'critical', 'phase': current_phase}

        # 3. Artspezifische Recovery-Zeit prüfen
        recovery_factor = cls.SPECIES_RECOVERY_FACTORS.get(species_type, 1.0)

        if recent_hst_tasks:
            latest_hst = max(recent_hst_tasks, key=lambda x: x['completed_at'])
            days_since = (datetime.now() - latest_hst['completed_at']).days

            base_recovery = cls.BASE_RECOVERY_DAYS.get(
                latest_hst['task_name'].lower().split()[0], 7
            )
            required_recovery = max(1, int(base_recovery * recovery_factor))

            if days_since < required_recovery:
                return False, (
                    f"WARNUNG: Nur {days_since} Tage seit letztem HST ({latest_hst['task_name']}).\n"
                    f"Empfohlene Recovery-Zeit für {species_type}: {required_recovery} Tage "
                    f"(Basis {base_recovery}d × Faktor {recovery_factor}).\n"
                    f"Zu kurze Recovery kann führen zu:\n"
                    f"- Reduziertes Wachstum\n"
                    f"- Erhöhte Krankheitsanfälligkeit\n"
                    f"- Stress-Symptome (Blattverfärbung, Wachstumsstillstand)"
                ), {
                    'severity': 'warning',
                    'days_since_last_hst': days_since,
                    'required_recovery': required_recovery,
                    'species_type': species_type,
                    'can_override': True
                }

        # 4. Kumulativen Stress prüfen (rollendes Fenster)
        # Schwellwert und Fenster sind konfigurierbar — initiale Schätzwerte,
        # nicht literaturbasiert. Kalibrierung über Nutzerfeedback empfohlen.
        CUMULATIVE_STRESS_THRESHOLD = 0.7  # Konfigurierbar pro Nutzerprofil
        STRESS_WINDOW_DAYS = 14            # Konfigurierbar
        cumulative = cls.calculate_cumulative_stress(recent_hst_tasks, species_type)
        if cumulative['stress_score'] > CUMULATIVE_STRESS_THRESHOLD:
            return False, (
                f"WARNUNG: Kumulativer Stress-Score {cumulative['stress_score']:.1f}/1.0 "
                f"(max. empfohlen: 0.7).\n"
                f"{cumulative['event_count']} HST-Events in den letzten 14 Tagen.\n"
                f"Stress-Hormone (Jasmonsäure, Ethylen) akkumulieren — "
                f"weitere HST kann Auxin/Cytokinin-Balance dauerhaft stören."
            ), {
                'severity': 'warning',
                'cumulative_stress': cumulative,
                'can_override': True
            }

        return True, "HST kann sicher durchgeführt werden", {
            'severity': 'ok',
            'species_type': species_type,
            'recovery_factor': recovery_factor,
            'recommendation': f'Nach HST {int(7 * recovery_factor)} Tage kein weiteres Training'
        }

    @classmethod
    def calculate_cumulative_stress(
        cls,
        recent_hst_tasks: List[dict],
        species_type: str = 'cannabis',
        window_days: int = 14,
    ) -> dict:
        """
        Berechnet kumulativen Stress-Score über ein rollendes Zeitfenster.
        Jedes HST-Event trägt proportional zu seinem Stress-Level bei,
        gewichtet nach Aktualität (neuere Events zählen stärker).

        Returns:
            {stress_score: float (0-1+), event_count: int, events: list}
        """
        # Initiale Schätzwerte — konfigurierbar pro Nutzerprofil,
        # empirisch zu verfeinern über Ergebnisdaten und Nutzerfeedback.
        stress_weights = {
            'topping': 0.3,
            'fim': 0.25,
            'supercropping': 0.2,
            'transplant': 0.35,
            'heavy_defoliation': 0.3,
            'mainlining': 0.35,
            'lollipopping': 0.1,
            'light_defoliation': 0.05,
            'ausgeizen': 0.05,  # Niedriger Stress — Routine-Kulturmaßnahme
        }

        recovery_factor = cls.SPECIES_RECOVERY_FACTORS.get(species_type, 1.0)
        cutoff = datetime.now() - timedelta(days=window_days)

        score = 0.0
        counted_events = []
        for task in (recent_hst_tasks or []):
            completed = task.get('completed_at')
            if completed and completed > cutoff:
                task_key = task['task_name'].lower().split()[0]
                weight = stress_weights.get(task_key, 0.15)
                # Neuere Events zählen stärker (lineare Abnahme über Fenster)
                days_ago = (datetime.now() - completed).days
                recency = 1.0 - (days_ago / window_days)
                score += weight * recency * recovery_factor
                counted_events.append({
                    'task': task['task_name'],
                    'days_ago': days_ago,
                    'contribution': round(weight * recency * recovery_factor, 3),
                })

        return {
            'stress_score': round(score, 2),
            'event_count': len(counted_events),
            'window_days': window_days,
            'events': counted_events,
        }
    
    @staticmethod
    def get_hst_best_practices(task_name: str) -> dict:
        """Gibt Best-Practices für spezifische HST-Techniken"""
        
        # Artspezifische Best-Practices. Cannabis ist Referenz, andere Arten ergänzen.
        practices = {
            'topping': {
                'best_timing': 'Vegetative Phase, artabhängig (siehe species_notes)',
                'tools': ['Scharfe, sterilisierte Schere'],
                'steps': [
                    '1. Identifiziere Haupttrieb / Wachstumspunkt',
                    '2. Schneide an artspezifischer Position (s.u.)',
                    '3. Sauberer 45° Schnitt',
                    '4. Bewässerung substratabhängig: Erde/Coco normal weiter, '
                    'Hydro-NFT/DWC NICHT stoppen (Wurzelaustrocknung!), ggf. EC -20%'
                ],
                'recovery': '7-10 Tage (Cannabis), 2-3 Tage (Tomaten/Kräuter)',
                'expected_outcome': 'Laterale Verzweigung durch Auxin-Umverteilung',
                'risks': ['Stress', 'Verlangsamtes Wachstum', 'Infektion an Schnittstelle'],
                'species_notes': {
                    'cannabis': 'Ab 4.-6. Nodium, oberhalb 3.-4. Node schneiden',
                    'tomato': 'Für Stabtomaten NICHT Topping, sondern Ausgeizen verwenden '
                              '(eigene Kategorie). Topping nur bei Busch-Tomaten (determinate).',
                    'pepper': 'Am "V" (erste Gabelung) toppen für buschigeres Wachstum. '
                              'Recovery 5+ Tage.',
                    'basil': 'Ab 3. Nodium pinchen — fördert Verzweigung, Recovery 1-2 Tage.',
                    'default': 'Fachliteratur konsultieren für artspezifisches Topping.',
                }
            },
            'supercropping': {
                'best_timing': 'Späte Vegi bis früher Stretch (Early Flowering Woche 1-3)',
                'tools': ['Nur Hände'],
                'steps': [
                    '1. Wähle Zweig der dominiert',
                    '2. Drücke sanft bis innere Struktur bricht',
                    '3. Biege vorsichtig 90°',
                    '4. Fixiere mit Pflanzenbinder wenn nötig'
                ],
                'recovery': '5-7 Tage (Kallus-Bildung)',
                'expected_outcome': 'Stärkerer Zweig, gleichmäßige Canopy-Höhe',
                'risks': ['Kompletter Bruch', 'Infektion', 'Wachstumsstillstand'],
                'note': 'Im Stretch (Early Flowering) erlaubt zur Höhenkontrolle — '
                        'ab Mitte Blüte verboten (Blütencluster-Schaden).'
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
            },
            'ausgeizen': {
                'best_timing': 'Vegetative Phase, wöchentlich ab 3. Rispe (Stabtomaten)',
                'tools': ['Hände (bei < 5 cm)', 'Schere (bei > 5 cm)'],
                'steps': [
                    '1. Identifiziere Geiztriebe in Blattachseln',
                    '2. Bei < 5 cm Länge: Handabbruch (sauberer, weniger Infektionsrisiko)',
                    '3. Bei > 5 cm: Sauberer Scherenschnitt',
                ],
                'recovery': '0-1 Tag (sehr niedriger Stress)',
                'stress_level': 'low',  # Kein HST — Routine-Kulturmaßnahme
                'expected_outcome': 'Assimilat-Fokus auf Fruchtstände statt vegetatives Wachstum',
                'risks': ['Versehentliches Entfernen des Haupttriebs'],
                'note': 'Hormonphysiologisch NICHT identisch mit Topping: Ausgeizen entfernt '
                        'Auxin-Senken (Seitenmeristeme), Topping entfernt die Auxin-Quelle (Apex). '
                        'Die Wuchsreaktion ist gegensätzlich.',
                'species_notes': {
                    'tomato_indeterminate': 'Standard-Pflegemaßnahme, kein HST',
                    'tomato_determinate': 'NICHT ausgeizen — Buschtomaten brauchen Seitentriebe für Ertrag',
                    'eggplant': 'Geiztriebe unterhalb erster Gabelung entfernen',
                }
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

**3. Karenzzeit-Validator (PHI — Pre-Harvest Interval):**
```python
class KarenzzeitValidator:
    """
    Validiert die Einhaltung von Wartezeiten zwischen IPM-Maßnahmen (REQ-010)
    und Ernte-Tasks. Kritisch für Lebensmittelsicherheit — besonders bei
    Cannabis (Inhalation verschärft Toxizitätsrisiko).
    """

    # Standard-Karenzzeiten in Tagen (konservativ, aus Produktzulassungen)
    DEFAULT_PHI_DAYS: dict[str, int] = {
        'neem_oil':             7,
        'pyrethrin':            1,
        'spinosad':             3,
        'bacillus_thuringiensis': 0,   # BT — biologisch, keine Wartezeit
        'potassium_bicarbonate': 0,
        'sulfur':               14,
        'copper_fungicide':     14,
        'systemic_fungicide':   21,
        'hydrogen_peroxide':    0,     # Zerfällt schnell
        'insecticidal_soap':    1,
        'diatomaceous_earth':   0,
        'beneficial_insects':   0,     # Nützlinge — keine Wartezeit
        'default':              14,    # Unbekanntes Produkt → konservativ
    }

    @classmethod
    def validate_harvest_safe(
        cls,
        plant_id: str,
        planned_harvest_date: date,
        recent_ipm_tasks: List[dict],
    ) -> tuple[bool, list[str]]:
        """
        Prüft ob Ernte sicher ist unter Einhaltung aller Karenzzeiten.

        Args:
            plant_id: Pflanze die geerntet werden soll
            planned_harvest_date: Geplantes Erntedatum
            recent_ipm_tasks: Liste von {task_name, completed_at, product_used, phi_days}

        Returns:
            (is_safe, warnings)
        """
        warnings = []
        is_safe = True

        for ipm_task in recent_ipm_tasks:
            completed = ipm_task.get('completed_at')
            if not completed:
                continue

            if isinstance(completed, str):
                completed = datetime.fromisoformat(completed).date()
            elif isinstance(completed, datetime):
                completed = completed.date()

            product = ipm_task.get('product_used', 'default')
            phi_days = ipm_task.get('phi_days') or cls.DEFAULT_PHI_DAYS.get(
                product.lower().replace(' ', '_').replace('-', '_'),
                cls.DEFAULT_PHI_DAYS['default']
            )

            safe_date = completed + timedelta(days=phi_days)
            if planned_harvest_date < safe_date:
                days_remaining = (safe_date - planned_harvest_date).days
                is_safe = False
                warnings.append(
                    f"KARENZZEIT NICHT EINGEHALTEN: '{ipm_task.get('task_name', product)}' "
                    f"am {completed.isoformat()} angewendet — Karenzzeit {phi_days} Tage. "
                    f"Früheste sichere Ernte: {safe_date.isoformat()} "
                    f"(noch {days_remaining} Tage warten)."
                )

        return is_safe, warnings
```

**4. Workflow Executor:**
```python
from typing import Dict, List
from datetime import date, datetime

class WorkflowExecutor:
    """Generiert konkrete Tasks aus Templates"""

    def __init__(self, arango_db):
        self.db = arango_db

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

        # Hole Plant-Info
        plant = self.db.aql.execute("""
            FOR p IN PlantInstances
              FILTER p.instance_id == @plant_id
              LET phase = FIRST(
                FOR ph IN 1..1 OUTBOUND p GRAPH 'kamerplanter_graph'
                  OPTIONS { edgeCollections: ['current_phase'] }
                  RETURN ph
              )
              RETURN {
                planted_on: p.planted_on,
                instance_id: p.instance_id,
                current_phase: phase.name,
                current_phase_entered_at: DATE_ISO8601(DATE_NOW())
              }
        """, bind_vars={'plant_id': plant_id}).next()

        if not plant:
            raise ValueError(f"Plant {plant_id} nicht gefunden")

        plant_data = {
            'planted_on': plant['planted_on'],
            'instance_id': plant['instance_id'],
            'current_phase': plant['current_phase'],
            'current_phase_entered_at': plant['current_phase_entered_at']
        }

        # Hole Workflow-Template mit Tasks
        result = self.db.aql.execute("""
            FOR wf IN WorkflowTemplates
              FILTER wf.template_id == @wf_id
              LET tasks_data = (
                FOR tt, contains_edge IN 1..1 OUTBOUND wf GRAPH 'kamerplanter_graph'
                  OPTIONS { edgeCollections: ['contains'] }
                  LET dependencies = (
                    FOR dep, dep_edge IN 1..1 OUTBOUND tt GRAPH 'kamerplanter_graph'
                      OPTIONS { edgeCollections: ['depends_on'] }
                      FOR dep_tt IN 1..1 OUTBOUND dep GRAPH 'kamerplanter_graph'
                        OPTIONS { edgeCollections: ['depends_on'] }
                        RETURN {
                          dep_template_id: dep_tt.task_template_id,
                          min_delay_days: dep.min_delay_days,
                          strict: dep.strict
                        }
                  )
                  SORT contains_edge.sequence ASC
                  RETURN {
                    template: tt,
                    sequence: contains_edge.sequence,
                    dependencies: dependencies
                  }
              )
              RETURN { wf: wf, tasks_data: tasks_data }
        """, bind_vars={'wf_id': workflow_template_id}).next()
            
            if not result:
                raise ValueError(f"Workflow-Template {workflow_template_id} nicht gefunden")
            
            workflow = result['wf']
            tasks_data = result['tasks_data']
            
            # Erstelle Workflow-Execution
            execution_id = self._create_execution(plant_id, workflow_template_id)
            
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
    
    def _create_execution(self, plant_id: str, template_id: str) -> str:
        """Erstellt WorkflowExecution-Dokument"""
        result = self.db.aql.execute("""
            LET exec = FIRST(
              INSERT {
                execution_id: UUID(),
                started_at: DATE_ISO8601(DATE_NOW()),
                completion_percentage: 0,
                on_schedule: true,
                days_ahead_behind: 0
              } INTO WorkflowExecutions
              RETURN NEW
            )

            LET plant = FIRST(
              FOR p IN PlantInstances FILTER p.instance_id == @plant_id RETURN p
            )
            LET wf = FIRST(
              FOR w IN WorkflowTemplates FILTER w.template_id == @template_id RETURN w
            )

            INSERT { _from: plant._id, _to: exec._id } INTO executing
            INSERT { _from: plant._id, _to: wf._id } INTO follows

            RETURN exec.execution_id
        """, bind_vars={'plant_id': plant_id, 'template_id': template_id}).next()

        return result
    
    def _create_task(
        self,
        plant_id: str,
        execution_id: str,
        template: TaskTemplate,
        due_date: date
    ) -> str:
        """Erstellt Task-Dokument aus Template"""

        # Priority aus Stress-Level ableiten
        priority_map = {
            'none': 'low',
            'low': 'low',
            'medium': 'medium',
            'high': 'high'
        }

        result = self.db.aql.execute("""
            LET exec = FIRST(
              FOR e IN WorkflowExecutions FILTER e.execution_id == @exec_id RETURN e
            )
            LET plant = FIRST(
              FOR p IN PlantInstances FILTER p.instance_id == @plant_id RETURN p
            )
            LET tt = FIRST(
              FOR t IN TaskTemplates FILTER t.task_template_id == @template_id RETURN t
            )

            LET new_task = FIRST(
              INSERT {
                task_id: UUID(),
                name: @name,
                instruction: @instruction,
                category: @category,
                due_date: @due_date,
                status: 'pending',
                priority: @priority,
                created_at: DATE_ISO8601(DATE_NOW()),
                estimated_duration_minutes: @duration,
                requires_photo: @requires_photo,
                photo_refs: []
              } INTO Tasks
              RETURN NEW
            )

            INSERT { _from: exec._id, _to: new_task._id } INTO generated
            INSERT { _from: new_task._id, _to: tt._id } INTO instance_of
            INSERT { _from: plant._id, _to: new_task._id } INTO has_task

            RETURN new_task.task_id
        """, bind_vars={
            'exec_id': execution_id,
            'plant_id': plant_id,
            'template_id': template.task_template_id,
            'name': template.name,
            'instruction': template.instruction,
            'category': template.category,
            'due_date': due_date.isoformat(),
            'priority': priority_map[template.stress_level],
            'duration': template.estimated_duration_minutes,
            'requires_photo': template.requires_photo
        }).next()

        return result
    
    def _create_dependency(
        self,
        blocker_task_id: str,
        blocked_task_id: str,
        min_delay_days: int
    ):
        """Erstellt blocks-Edge"""
        self.db.aql.execute("""
            LET blocker = FIRST(
              FOR t IN Tasks FILTER t.task_id == @blocker_id RETURN t
            )
            LET blocked = FIRST(
              FOR t IN Tasks FILTER t.task_id == @blocked_id RETURN t
            )
            INSERT {
              _from: blocker._id,
              _to: blocked._id,
              min_delay_days: @delay
            } INTO blocks
        """, bind_vars={
            'blocker_id': blocker_task_id,
            'blocked_id': blocked_task_id,
            'delay': min_delay_days
        })
```

**4. Dynamic Rescheduler:**
```python
class DynamicRescheduler:
    """Verschiebt nachgelagerte Tasks bei Verzögerungen"""

    def __init__(self, arango_db):
        self.db = arango_db

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
        # Berechne Verzögerung
        result = self.db.aql.execute("""
            FOR task IN Tasks
              FILTER task.task_id == @task_id AND task.status == 'completed'
              LET delay_days = DATE_DIFF(task.due_date, task.completed_at, 'day')
              RETURN delay_days
        """, bind_vars={'task_id': completed_task_id}).next()

        if result is None:
            return {'delay_days': 0, 'rescheduled_count': 0, 'affected_tasks': []}

        delay_days = result

        if delay_days <= 0:
            return {'delay_days': 0, 'rescheduled_count': 0, 'affected_tasks': []}

        # Verschiebe abhängige Tasks (transitive Traversierung)
        affected = list(self.db.aql.execute("""
            LET completed = FIRST(
              FOR t IN Tasks FILTER t.task_id == @task_id RETURN t
            )
            FOR dependent IN 1..10 OUTBOUND completed GRAPH 'kamerplanter_graph'
              OPTIONS { edgeCollections: ['blocks'] }
              FILTER dependent.status == 'pending'
              UPDATE dependent WITH {
                due_date: DATE_ADD(dependent.due_date, @delay, 'day')
              } IN Tasks
              RETURN {
                task_id: NEW.task_id,
                name: NEW.name,
                new_due_date: NEW.due_date
              }
        """, bind_vars={'task_id': completed_task_id, 'delay': delay_days}))

        # Update Workflow-Execution Status
        self.db.aql.execute("""
            LET task = FIRST(
              FOR t IN Tasks FILTER t.task_id == @task_id RETURN t
            )
            FOR exec IN 1..1 INBOUND task GRAPH 'kamerplanter_graph'
              OPTIONS { edgeCollections: ['generated'] }
              UPDATE exec WITH {
                on_schedule: false,
                days_ahead_behind: exec.days_ahead_behind - @delay
              } IN WorkflowExecutions
        """, bind_vars={'task_id': completed_task_id, 'delay': delay_days})

        return {
            'delay_days': delay_days,
            'rescheduled_count': len(affected),
            'affected_tasks': affected
        }

    def check_task_readiness(self, task_id: str) -> dict:
        """
        Prüft ob Task bereit ist (alle Blocker completed)
        """
        result = self.db.aql.execute("""
            FOR task IN Tasks
              FILTER task.task_id == @task_id

              LET blockers = (
                FOR blocker IN 1..1 INBOUND task GRAPH 'kamerplanter_graph'
                  OPTIONS { edgeCollections: ['blocks'] }
                  RETURN blocker
              )
              LET incomplete_blockers = LENGTH(
                FOR b IN blockers FILTER b.status != 'completed' RETURN 1
              )

              RETURN {
                task_id: task.task_id,
                name: task.name,
                status: task.status,
                total_blockers: LENGTH(blockers),
                incomplete_blockers: incomplete_blockers,
                is_ready: incomplete_blockers == 0,
                blocking_tasks: (
                  FOR b IN blockers FILTER b.status != 'completed' RETURN b.name
                )
              }
        """, bind_vars={'task_id': task_id}).next()

        return dict(result) if result else {}
```

### Datenvalidierung (Type Hinting):
```python
from typing import Literal, Optional, List
from pydantic import BaseModel, Field, field_validator
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
    
    @field_validator('photo_refs')
    @classmethod
    def validate_photos_when_required(cls, v, info):
        if info.data.get('requires_photo') and info.data.get('status') == 'completed':
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
- REQ-001 (Stammdaten): Species für Template-Kompatibilität + `species_type` für artspezifische Recovery-Zeiten
- REQ-003 (Phasen): GrowthPhase für Phase-Trigger (inkl. `early_flowering` Differenzierung), GDD-Daten für `gdd_threshold`-Trigger
- REQ-002 (Standort): Location für Multi-Plant-Workflows
- REQ-010 (IPM): IPM-Task-Historie für Karenzzeit-Validierung bei Harvest-Tasks
- REQ-018 (Umgebungssteuerung): **Task-Aktor-Integration** — Tasks wie "Licht umstellen auf 12/12" können optional mit Aktor-Aktionen verknüpft werden. Bei automatischer Aktor-Ausführung: Task auto-completed. Bei manueller Steuerung: Task als Reminder. Konflikterkennung: Task "Licht 18/6" + Phase-Profil "12/12" = Warnung.

**Wird benötigt von:**
- REQ-007 (Ernte): Harvest-Tasks als Teil von Workflows
- REQ-010 (IPM): IPM-Tasks (Spraying, Inspection)
- REQ-009 (Dashboard): Task-Queue-Widget
- REQ-014 (Tankmanagement): **HOCH** — Automatische Wartungs-Tasks aus MaintenanceSchedule (Wasserwechsel, Reinigung, Kalibrierung etc.)

**Python-Bibliotheken:**
- `celery` - Zeitgesteuerte Task-Erinnerungen
- `croniter` - Cron-Expression-Parsing für Recurring Tasks
- `jsonschema` - Validierung von Workflow-JSON-Importen

## 5. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **Template-Bibliothek:** 15+ System-Workflows (Cannabis, Tomaten, Kartoffeln, etc.)
- [ ] **User-Workflows:** Nutzer können eigene Templates erstellen/editieren
- [ ] **Foto-Upload-Enforcement:** Tasks mit requires_photo=true blockieren ohne Foto
- [ ] **HST-Validierung:** System verhindert Topping/FIM/Mainlining in Blüte; Supercropping/Transplant im Stretch (Early Flowering) erlaubt
- [ ] **Artspezifische Recovery:** Recovery-Zeiten nach species_type skaliert (Cannabis 1.0x, Tomaten 0.4x, Paprika 0.7x), Kräuter differenziert (annual/perennial_soft/perennial_woody)
- [ ] **Temperatur-Modifikator:** Recovery-Zeiten temperaturabhängig skaliert (optimal 25-28°C)
- [ ] **Kumulativer Stress:** Stress-Score über konfigurierbares Fenster (Default 14 Tage) mit konfigurierbarem Schwellwert (Default 0.7)
- [ ] **Ausgeizen-Kategorie:** Eigene Task-Kategorie für Geiztrieb-Entfernung (nicht unter Topping)
- [ ] **Observation-Kategorie:** Beobachtungs-Tasks (Wachstumsmessung, pH/EC, Foto-Dokumentation)
- [ ] **Zimmerpflanzen-Templates:** Orchidee, Kaktus/Sukkulente, tropische Grünpflanze, Calathea
- [ ] **Hydroponik-Wartung:** Nährlösung-Wechsel, Sonden-Kalibrierung, System-Reinigung als System-Templates
- [ ] **GDD-Trigger:** Task-Auslösung basierend auf akkumulierten Gradtagsummen (REQ-003)
- [ ] **Task-Aktor-Integration:** Tasks optional mit REQ-018 Aktor-Aktionen verknüpfbar
- [ ] **Karenzzeit-Validierung:** Harvest-Tasks werden gegen letzte IPM-Maßnahmen validiert (PHI-Einhaltung)
- [ ] **Tageszeit-Empfehlung:** TaskTemplates können `optimal_time_of_day` empfehlen
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

**Szenario 2a: HST-Validierung verhindert Topping in Early Flower**
```
GIVEN: Cannabis in Early-Flowering-Phase (Stretch)
WHEN: Nutzer versucht "Topping" Task zu erstellen
THEN:
  - HST_Validator.can_perform_hst() → False
  - Error-Message: "KRITISCH: Topping in Early-Flowering verboten.
    Supercropping und Transplant sind im Stretch noch möglich."
  - UI blockiert Task-Erstellung
  - Vorschlag: "Supercropping zur Höhenkontrolle im Stretch"
```

**Szenario 2b: Supercropping im Stretch erlaubt**
```
GIVEN: Cannabis in Early-Flowering-Phase (Stretch, Woche 2)
WHEN: Nutzer erstellt "Supercropping" Task
THEN:
  - HST_Validator.can_perform_hst() → True
  - Message: "ERLAUBT: Supercropping im Stretch (Early Flowering) noch möglich"
  - Task wird erstellt mit Hinweis: "Ab Mitte Blüte nicht mehr möglich"
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
- Keywords: Workflow, Task, HST, Training, Topping, LST, Dependency, Scheduling, Template, Ausgeizen, Observation, Zimmerpflanzen, Hydroponik-Wartung, GDD-Trigger
- Fachbegriffe: Auxin-Dominanz, Hermaphroditismus, Mainlining, Lollipopping, SOG, SCROG, Supercropping, Karenzzeit, PHI, Kumulativer Stress, Jasmonsäure, Ethylen, Stretch-Phase, Early Flowering, Geiztrieb, Assimilat-Verteilung, Phototoxizität, Transpiration
- Verknüpfung: Zentral für REQ-003 (Phasen-Trigger + GDD), REQ-007 (Harvest-Tasks), REQ-010 (IPM-Tasks + Karenzzeit), REQ-018 (Aktor-Verknüpfung), REQ-014 (Hydroponik-Wartung)
- Pflanzenwissenschaft: Stress-Physiologie, Hormon-Regulation, Recovery-Zeiten, artspezifische Metabolismus-Geschwindigkeit, Tageszeit-Einfluss auf Pflanzenphysiologie, Temperatur-Recovery-Modifikation
