# Spezifikation: REQ-006 - Aufgabenplanung

```yaml
ID: REQ-006
Titel: Modulare Aufgabenplanung & Benutzerdefinierte Workflows
Kategorie: Prozessmanagement
Fokus: Beides
Technologie: Python, ArangoDB, Celery (Task Scheduling)
Status: Entwurf
Version: 3.0 (Vollständige Einzelaufgaben-Pflege & Phasengebundene Workflows)
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
- **Umtopf-Workflow (generisch):** Substratcheck alle 12-18 Monate, Wurzelschnitt bei Bedarf, schrittweise Topfgrößen-Steigerung (max. +2 cm Durchmesser), Drainage-Kontrolle, 2 Wochen reduzierte Düngung nach Umtopfen
- **Überwinterungs-Workflow:** Saisonaler Trigger (Oktober): Dünger reduzieren/einstellen, Gießintervall verlängern, kühlen Standort beziehen (5-12°C für Kaktus, 15-18°C für Tropenpflanzen), Licht-Supplementierung bei <8h Tageslicht, Schädlingskontrolle intensivieren (Trockenstress fördert Spinnmilben)
- **Vermehrungs-Workflow (Stecklinge):** Mutterpflanze identifizieren, Stecklingsschnitt (morgens, turgorreich), Bewurzelungshormon optional, Mini-Gewächshaus / hohe Luftfeuchte, Wurzelkontrolle nach 2-4 Wochen, Abhärtung 1 Woche, Umtopfen
- **Saisonale Düngung:** Beginn März (Wachstumsbeginn): langsam auf Volldüngung hochfahren, Reduktion September, Einstellen November-Februar; Frequenz und Konzentration artspezifisch konfigurierbar

**Hydroponik-Wartungs-Templates (Built-in):**
- **Nährlösung-Wechsel:** Komplettwechsel alle 7-14 Tage mit EC/pH-Messung, Reservoir-Reinigung, Frisch-Ansatz (REQ-014)
- **Sonden-Kalibrierung:** Wöchentliche pH/EC-Kalibrierung mit Referenzlösungen
- **Wurzelinspektion:** Regelmäßige Kontrolle auf Pythium, Verfärbungen, Algenwachstum
- **System-Reinigung:** Leitungen, Pumpen, Tropfer spülen (H₂O₂ oder enzymatisch)

**Outdoor/Freiland-Templates (Built-in):**
- **Frostschutz-Workflow:** Wetter-Trigger bei Frostwarnung (<3°C Nachttemperatur): Empfindliche Pflanzen abdecken (Vlies, Folie), Topfpflanzen einräumen, Bewässerung reduzieren (gefrorenes Substrat = Wurzelschaden), Frostschutz-Vlies-Bestand prüfen
- **Abhärtungs-Workflow:** Schrittweise Akklimatisierung von Indoor nach Outdoor: Tag 1-3 geschützter Schatten (2-3h), Tag 4-6 halbschattig (4-5h), Tag 7-10 volle Sonne (vormittags), Tag 11-14 ganztags; Rückfall-Task bei Kälteeinbruch
- **Obstbaum-Jahresschnitt:** Saisonaler Trigger (Februar/März für Kernobst, Juli/August für Steinobst): Totholz entfernen, Wasserschosse schneiden, Kronenform korrigieren, Wundverschluss bei Schnitten >3cm Durchmesser
- **Saisonende-Workflow (Herbst):** Abgestorbene Pflanzen entfernen, Beete mulchen, Kompost einarbeiten, Gründüngung aussäen, Bewässerungssystem winterfest machen, Werkzeuge reinigen und ölen

<!-- Quelle: Outdoor-Garden-Planner Review G-005 -->
**Erweiterte Outdoor/Freiland-Templates:**
- **Frühjahrs-Beetvorbereitung:** Saisonaler Trigger (März): Kompost ausbringen (3-4 L/m² für Starkzehrer-Beete), Boden lockern (nicht umgraben — Bodenlebewesen schonen!), Mulch entfernen, Bodentemperatur prüfen (>8°C für Direktsaat)
- **Voranzucht-Workflow (Indoor→Outdoor):** Start ab Februar: Aussaat nach Aussaatkalender (REQ-001 `sowing_indoor_weeks_before_last_frost`), Pikieren nach Keimblattstadium, Abhärtung 10-14 Tage vor Auspflanzen, Auspflanzen nach Eisheiligen (REQ-001 `frost_sensitivity` prüfen!)
- **Gründüngung-Workflow:** Trigger nach Ernte eines Beets: Gründüngung aussäen (Phacelia Aug-Sep, Senf bis Okt, Inkarnatklee Sep-Okt), einarbeiten vor Blüte oder Frost absterben lassen, Beet für Frühjahr vorbereiten
- **Überwinterungs-Checklist:** Saisonaler Trigger (Oktober): Generiert pro Pflanze basierend auf `OverwinteringProfile` (REQ-022) eine Aufgabenliste — Knollen ausgraben, Kübelpflanzen einräumen, Rosen anhäufeln, Vlies anbringen, Wasserleitungen entleeren
- **Frühlings-Auswinterungs-Checklist:** Saisonaler Trigger (März/April): Winterschutz entfernen, Rosen abhäufeln, Obstbäume schneiden, Kübelpflanzen schrittweise rausstellen, eingelagerte Knollen vorziehen
- **Sukzessions-Aussaat:** Recurring-Template: "Alle 3 Wochen Salat nachsäen" von April bis August, "Alle 4 Wochen Radieschen" von März bis September — konfigurierbare Abstände und Zeiträume pro Species (REQ-013 `clone_from_run_key`)
- **Staudenteilung-Workflow:** Saisonaler Trigger (Frühjahr oder Herbst, artspezifisch): Staude ausgraben, teilen (Messer/Spaten), Teilstücke neu einpflanzen, gut wässern, 2 Wochen schonen
- **Rosen-Jahrespflege:** Zusammengesetzter Workflow über das ganze Jahr: Frühjahrsschnitt (bei Forsythienblüte!), Sommerblüte ausputzen, Herbst-Anhäufeln, Winterschutz

**User-Blueprints (Eigene Strategien):**
- Speicherbar, editierbar, teilbar mit Community
- Versionierung von Template-Änderungen
- Import/Export als JSON

<!-- Quelle: Einzelaufgaben-Pflege Review v3.0 -->
### Vollständige Einzelaufgaben-Pflege (CRUD+)

Das System bietet dem Nutzer vollständige Kontrolle über einzelne Aufgaben — unabhängig davon, ob diese manuell erstellt, aus Templates generiert oder durch Celery-Tasks erzeugt wurden. Jede Aufgabe kann individuell angepasst, erweitert und verwaltet werden.

**Erweiterte Einzelaufgaben-Features:**

**Tags & freie Kategorisierung:**
- Jede Task-Instanz kann beliebig viele benutzerdefinierte Tags tragen (`tags: list[str]`)
- Tags sind frei eingebbar (kein vordefiniertes Vokabular) und ermöglichen Filterung/Suche über die Task-Queue
- Beispiele: `["dringend", "hochbeet-a", "mit-luna-besprechen", "nächste-woche"]`
- Tags werden bei Workflow-Instantiation nicht vom Template propagiert — sie sind rein nutzerindividuell

**Checkliste (Subtasks):**
- Jede Task-Instanz kann eine eingebettete Checkliste tragen (`checklist: list[ChecklistItem]`)
- ChecklistItem: `{ text: str, done: bool, order: int }`
- Die Checkliste ermöglicht Teilschritte innerhalb einer Aufgabe, ohne dafür separate Tasks zu erstellen
- Fortschrittsanzeige: "3/5 Schritte erledigt"
- Nutzer können Checklist-Einträge frei hinzufügen, umbenennen, umsortieren und löschen
- TaskTemplates können eine Default-Checkliste definieren, die bei Instantiation auf die Task-Instanz kopiert wird
- Beim Abschluss der Aufgabe müssen nicht alle Checklist-Einträge erledigt sein (optional konfigurierbar via `require_all_checklist_items: bool` am TaskTemplate)

**Bewertungen nach Abschluss:**
- `difficulty_rating: Optional[int]` (1-5) — Wie schwierig war die Aufgabe?
- `quality_rating: Optional[int]` (1-5) — Wie gut ist das Ergebnis?
- Bewertungen werden bei `complete_task()` optional mitgegeben
- Über die Zeit lernt das System durchschnittliche Schwierigkeitsgrade pro Task-Kategorie/Template (Learning-Mode)

**Zeitplanung mit Uhrzeit:**
- `scheduled_time: Optional[time]` — Geplante Uhrzeit zusätzlich zum `due_date`
- Wird von TaskTemplate `optimal_time_of_day` in eine konkrete Uhrzeit aufgelöst (morning=08:00, afternoon=14:00, evening=18:00, lights_off=22:00 — konfigurierbar)
- Nutzer können die Uhrzeit jederzeit überschreiben

**User-Zuweisung (Multi-Tenant):**
- `assigned_to_user_key: Optional[str]` — Welches Tenant-Mitglied soll die Aufgabe erledigen?
- Bei Gemeinschaftsgärten (REQ-024) kann ein Admin Tasks an Mitglieder zuweisen
- Filter: "Meine Aufgaben" vs. "Alle Aufgaben"
- Optional: Notification an zugewiesenen Nutzer

**Wiederkehrende Aufgaben (Recurring Tasks):**
- `recurrence_rule: Optional[str]` — Cron-Expression für automatische Wiedererzeugung (z.B. `"0 8 * * 1"` = jeden Montag 08:00)
- `recurrence_end_date: Optional[date]` — Optionales Ende der Wiederholung
- `parent_recurring_task_key: Optional[str]` — Referenz auf die "Eltern-Aufgabe" die die Wiederholung definiert
- Bei Completion einer wiederkehrenden Task wird automatisch die nächste Instanz erzeugt
- Nutzer können die Wiederholung jederzeit stoppen, ändern oder pausieren
- Celery-Beat prüft täglich offene Recurring-Rules und erzeugt fällige Instanzen

**Task-Klonen (Duplikate):**
- `POST /tasks/{key}/clone` — Erzeugt eine Kopie einer bestehenden Aufgabe
- Übernimmt: name, instruction, category, priority, tags, checklist, timer, estimated_duration
- Setzt zurück: status=pending, due_date=null, completed_at=null, photo_refs=[]
- Optional: `target_plant_key` für Zuweisung an andere Pflanze
- Optional: `due_date_offset_days` für automatische Datumsverschiebung

**Task-Wiedereröffnung (Reopen):**
- `POST /tasks/{key}/reopen` — Setzt eine abgeschlossene/übersprungene Aufgabe zurück auf `pending`
- Nur möglich für Status `completed`, `skipped`
- Setzt `completed_at`, `actual_duration_minutes`, `completion_notes` zurück
- Behält `photo_refs`, `tags`, `checklist` bei
- Audit-Trail: `reopened_at: datetime`, `reopened_from_status: str`

**Task-Neuzuweisung (Reassign):**
- `plant_key` ist über TaskUpdate änderbar — Aufgaben können einer anderen Pflanze zugewiesen werden
- `assigned_to_user_key` ist über TaskUpdate änderbar

**Batch-Operationen:**
- `POST /tasks/batch/status` — Mehrere Tasks gleichzeitig starten, abschließen oder überspringen
  - Body: `{ task_keys: list[str], action: Literal['start', 'complete', 'skip'], completion_notes?: str }`
- `POST /tasks/batch/delete` — Mehrere Tasks gleichzeitig löschen (nur pending/skipped)
  - Body: `{ task_keys: list[str] }`
- `POST /tasks/batch/assign` — Mehrere Tasks einem Nutzer zuweisen
  - Body: `{ task_keys: list[str], assigned_to_user_key: str }`
- Batch-Operationen sind atomar: entweder alle erfolgreich oder Rollback mit Fehlerliste

**Task-Kommentare:**
- Nutzer können Notizen, Fragen und Beobachtungen an Tasks hinterlassen
- Kommentare sind chronologisch geordnet und an den erstellenden User gebunden
- CRUD: `GET/POST /tasks/{key}/comments`, `PUT/DELETE /tasks/{key}/comments/{comment_key}`
- Kommentare werden bei Task-Löschung kaskadiert gelöscht

**Task-Änderungshistorie:**
- Jede Statusänderung und jedes Update wird als Audit-Entry protokolliert
- `GET /tasks/{key}/history` — Chronologische Liste aller Änderungen
- Entry: `{ changed_at: datetime, changed_by: str, field: str, old_value: any, new_value: any }`
- Ermöglicht Nachvollziehbarkeit: "Wer hat wann was geändert?"

### Phasengebundene Workflow-Gestaltung

Der Nutzer kann Workflows so gestalten, dass einzelne Tätigkeiten an bestimmte Wachstumsphasen gebunden sind und bei Phasenwechsel automatisch fällig werden. Jede Aufgabe innerhalb eines Workflows kann individuell konfiguriert werden.

**Phasen-Trigger im Workflow-Designer:**
- Jedes TaskTemplate innerhalb eines Workflows kann unabhängig einen eigenen `trigger_type` und `trigger_phase` haben
- Beispiel: Ein Workflow "Cannabis SCROG" enthält:
  - Task A: "Topping" → `trigger_phase: 'vegetative'`, `trigger_type: 'days_after_phase'`, `days_offset: 14`
  - Task B: "SCROG-Netz montieren" → `trigger_phase: 'vegetative'`, `trigger_type: 'days_after_phase'`, `days_offset: 21`
  - Task C: "Lollipopping" → `trigger_phase: 'flowering'`, `trigger_type: 'phase_entry'`
  - Task D: "SCROG-Füllgrad prüfen" → `trigger_phase: 'flowering'`, `trigger_type: 'days_after_phase'`, `days_offset: 7`
  - Task E: "Flushing starten" → `trigger_phase: 'flowering'`, `trigger_type: 'days_after_phase'`, `days_offset: 49`
  - Task F: "Ernte" → `trigger_phase: 'harvest'`, `trigger_type: 'phase_entry'`
- Bei Workflow-Instantiation werden nur die Tasks sofort erzeugt, deren Phase bereits aktiv ist
- Die übrigen Tasks werden als "dormant" gespeichert und bei Phase-Transition automatisch aktiviert (Status `dormant` → `pending`)

**Individuelle Task-Anpassung innerhalb von Workflows:**
- Nach Workflow-Instantiation kann der Nutzer jede einzelne Task-Instanz individuell anpassen:
  - Name, Instruktion, Priorität, Fälligkeitsdatum, Checkliste, Timer, Tags ändern
  - Phasen-Binding beibehalten oder überschreiben (`trigger_phase_override`)
  - Tasks innerhalb des Workflows löschen (ohne den Workflow zu brechen)
  - Zusätzliche Tasks dem laufenden Workflow hinzufügen (`POST /workflows/executions/{key}/tasks`)
- Änderungen an Instanzen wirken sich nicht auf das Template aus (One-Way: Template → Instanz)
- Template-Updates erzeugen keine Änderungen an bereits instanziierten Workflows

**Dormant-Status für phasengebundene Tasks:**
- Neuer TaskStatus: `dormant` — Task existiert, ist aber noch nicht fällig (Phase nicht erreicht)
- Dormant-Tasks erscheinen in der UI als "Geplant" in einer separaten Sektion
- Bei Phase-Transition (REQ-003) prüft das System automatisch, ob dormante Tasks für die neue Phase aktiviert werden müssen
- Celery-Task oder Phase-Transition-Hook: `activate_dormant_tasks_for_phase(plant_key, new_phase)`
- Aktivierung: Status `dormant` → `pending`, `due_date` wird basierend auf `trigger_type` berechnet

**Workflow-Instanz-Übersicht:**
- Pro laufendem Workflow sieht der Nutzer:
  - Alle Tasks gruppiert nach Phase (visuell als Timeline/Gantt)
  - Welche Phase aktiv ist (Highlight)
  - Welche Tasks dormant (zukünftige Phasen), pending, in_progress, completed sind
  - Fortschritt: "Phase 2/4, 7/12 Tasks erledigt"
- Der Nutzer kann die Reihenfolge und Phase-Zuordnung der Tasks per Drag&Drop ändern (nur bei User-Workflows, nicht bei System-Workflows)

**Task-Trigger-Typen:**
1. **Phase-Entry:** Automatisch beim Phasenwechsel (z.B. Blüte-Start)
2. **Days-After-Phase:** X Tage nach Phasen-Eintritt
3. **Days-After-Planting:** X Tage nach Pflanzung
4. **Absolute-Date:** Festes Kalenderdatum
5. **Conditional:** Basierend auf Zustand (z.B. Höhe > 30cm)
6. **Manual:** Nutzer initiiert
<!-- Quelle: Outdoor-Garden-Planner Review G-005 -->
7. **Seasonal-Month:** Fester Kalendermonat (z.B. "Jedes Jahr im Oktober" — für saisonale Gartenaufgaben)
8. **Phenological:** Basierend auf phänologischen Zeigerpflanzen (z.B. "Wenn Forsythie blüht" = Rosen schneiden; "Wenn Holunder blüht" = Bohnen säen; "Wenn Apfel blüht" = Kartoffeln legen). Der Nutzer dokumentiert das Eintreten des phänologischen Ereignisses, das System löst dann die verknüpften Tasks aus.

> **Future Feature (niedrige Priorität):** Mondkalender / Biorhythmus-Trigger.
> Einige Gärtner orientieren sich am Mondkalender (z.B. Maria Thun) für
> Aussaat, Pflanzung, Schnitt und Ernte. Eine optionale Integration könnte
> Trigger basierend auf Mondphasen (Neumond, Vollmond, auf-/absteigend) und
> Tierkreiszeichen-Tagen (Wurzel-/Blatt-/Blüte-/Fruchttage) bieten.
> Wissenschaftliche Evidenz ist begrenzt — daher als optionales Plugin konzipieren,
> nicht als Kern-Feature. Datenquelle: astronomische API oder statische Tabelle.

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
<!-- Quelle: Outdoor-Garden-Planner Review G-005 -->
- **Seasonal:** Saisonale Gartenaufgaben (Beetvorbereitung, Winterschutz, Gründüngung)
- **Phenological:** Durch phänologische Beobachtungen ausgelöste Tasks

**Intelligente Features:**
- **HST-Validation:** Verhindert High-Stress-Training in kritischen Phasen
- **Dependency-Chains:** Tasks werden automatisch verschoben wenn Vorgänger verspätet
- **Resource-Conflicts:** Warnung bei gleichzeitigen Tasks an verschiedenen Pflanzen
- **Completion-Verification:** Foto-Upload-Pflicht bei kritischen Eingriffen
- **Learning-Mode:** System lernt durchschnittliche Completion-Times

<!-- Quelle: Cannabis Indoor Grower Review W-006 -->
**Task-Timer & Countdown-Integration:**

Timer sind kein eigenständiges Modul, sondern eine optionale Eigenschaft einzelner Task-Schritte. Beim Starten einer Aufgabe (Status-Übergang `pending` → `in_progress`) kann ein zugehöriger Countdown-Timer mitlaufen, der den Nutzer bei zeitkritischen Arbeitsschritten unterstützt.

- **Vordefinierte Timer-Dauer:** Jedes `TaskTemplate` kann eine optionale `timer_duration_seconds: Optional[int]` tragen. Bei Workflow-Instantiation wird dieser Wert auf die Task-Instanz propagiert. Beispiele:
  - Nährlösung mischen — CalMag umrühren: 120 s (2 min)
  - Einwirkzeit Foliar-Spray vor Lights-Off: 1800 s (30 min)
  - Burping (Gläser öffnen nach Trocknung): 900 s (15 min)
  - Einwirkzeit IPM-Behandlung (z.B. Neemöl-Kontaktzeit): 600 s (10 min)
  - Wurzelbad beim Umtopfen: 300 s (5 min)
- **Timer-Label:** Optionaler `timer_label: Optional[str]` beschreibt den Zweck des Countdowns in der UI (z.B. "Umrühren", "Einwirkzeit", "Belüftung"). Wird am TaskTemplate definiert und auf die Instanz propagiert.
- **Manuelle Timer:** Nutzer können bei Tasks ohne vordefinierte Dauer ad-hoc einen Timer starten und die Dauer frei wählen. Der Wert wird auf der Task-Instanz als `timer_duration_seconds` gespeichert.
- **Benachrichtigung bei Ablauf:** Bei Timer-Ende wird eine akustische und/oder haptische Benachrichtigung (Ton, Vibration) ausgelöst. Die Benachrichtigungsart ist in den User-Preferences konfigurierbar (REQ-020/REQ-021). Auf mobilen Geräten wird eine Push-Notification erzeugt, falls die App im Hintergrund ist.
- **Timer-Zustand:** Der Timer läuft clientseitig (Frontend/Flutter). Pause/Resume wird unterstützt. Der Timer-Zustand wird nicht serverseitig persistiert — bei App-Neustart geht ein laufender Timer verloren. Die tatsächliche Aufgabendauer (`actual_duration_minutes`) wird unabhängig vom Timer erfasst.
- **Kein Blockieren:** Der Timer-Ablauf blockiert nicht den Task-Abschluss. Der Nutzer kann einen Task jederzeit abschließen, unabhängig vom Timer-Stand. Der Timer dient als Orientierungshilfe, nicht als Pflicht.

**Anwendungsfälle (Querbezüge):**
| Anwendungsfall | Timer-Dauer | Querbezug |
|----------------|-------------|-----------|
| CalMag umrühren vor Base-A-Zugabe | 2 min | REQ-004 (Mischsequenz-Validierung) |
| Einwirkzeit Foliar-Spray vor Lights-Off | 30 min | REQ-006 (Feeding-Tasks, `optimal_time_of_day: lights_off`) |
| Burping-Reminder (Gläser öffnen, belüften) | 15 min | REQ-008 (Post-Harvest Curing) |
| Einwirkzeit IPM-Behandlung | 10–30 min | REQ-010 (Treatment-Tasks) |
| Substrat-Einweichen vor Transplant | 5–15 min | REQ-019 (Substratvorbereitung) |

> **Implementierungshinweis:** Die Timer-Felder (`timer_duration_seconds`, `timer_label`) werden am `:TaskTemplate`-Node und am `:Task`-Node als optionale Properties ergänzt (siehe Abschnitt 2 und 3). Die Frontend-Komponente rendert einen visuellen Countdown (Kreisdiagramm oder Balken) mit Start/Pause/Reset-Buttons. Akustische Signale nutzen die Web Audio API (Desktop) bzw. lokale Notifications (Mobile/PWA, UI-NFR-012).

**Hormon-Verständnis (Plant Stress Physiology):**
- **Auxin-Dominanz:** Topping erhöht laterales Wachstum
- **Stress-Recovery:** Artspezifische Recovery-Zeiten (Cannabis 7d, Tomaten 2-3d, Paprika 5d)
- **Kumulativer Stress:** Stress-Hormone (Jasmonsäure, Ethylen) akkumulieren — mehrere HST-Events im 14-Tage-Fenster haben additive Effekte
- **Photoperiod-Sensitivity:** Kein Topping/FIM/Mainlining während Blüte; Supercropping im Stretch (Early Flowering) noch erlaubt
- **Hermaphroditism-Risk:** Cannabis reagiert auf Stress mit Zwitter-Bildung
- **Karenzzeit (PHI):** Wartezeit zwischen Pflanzenschutz (REQ-010) und Ernte — Lebensmittelsicherheits-Validierung
- **Tageszeit-Empfehlung:** Transplanting abends/Lights-Off (reduzierte Transpiration minimiert Welkestress; volle Dunkelperiode für Wurzel-Substrat-Kontakt), Training morgens (turgorreicher Stängel), Foliar bei Lights-Off (langsamere Verdunstung erhöht Kontaktzeit, kein Phototoxizitäts-Risiko bei Öl-Produkten)

<!-- Quelle: Cannabis Indoor Grower Review G-004 -->
**Training-Plan (Canopy Management):**

Training ist kein loser Haufen Einzeltasks, sondern ein zusammenhängender Plan mit messbaren Canopy-Zielen, Recovery-Tracking und Equipment-Verwaltung. Das System bildet Training-Strategien als dediziertes Subsystem ab, das auf dem bestehenden HST-Validator aufsetzt und ihn um Planungslogik, Canopy-Metriken und Autoflower-Schutz erweitert.

**Training-Strategien als Workflow-Templates:**
- **LST-Only:** Nur Low-Stress-Training (Biegen, Binden). Für Autoflower geeignet. Kein Recovery-Timer erforderlich.
- **Top+SCROG (Screen of Green):** Topping ab 4.-6. Node, dann SCROG-Netz für gleichmäßige Canopy. Equipment: SCROG-Netz mit konfigurierbarer Netz-Höhe.
- **Mainlining/Manifolding:** Symmetrisches Topping zu einem definierten Zeitplan — z.B. "Node 3 toppen, dann symmetrisch 8 Haupttriebe aufbauen". Mehrstufiger Workflow mit strikten Dependencies und Foto-Pflicht pro Schritt.
- **SOG (Sea of Green):** Keine HST-Events, hohe Pflanzendichte, kurze Vegetationsphase. Canopy-Gleichmäßigkeit durch Genetik-Selektion statt Training.
- **Defoliation-Schedule:** Geplante Entlaubung in Phasen (leicht in Vegi, strategisch in Early Flower, Lollipopping vor Mitte Blüte).

**Training-Event-Modell:**
Jedes Training-Event wird als `:TrainingEvent`-Dokument erfasst (ergänzt den bestehenden `:Task`-Node):
- `event_type: Literal['topping', 'fim', 'lst_bend', 'lst_tie', 'scrog_tuck', 'lollipop', 'defoliation', 'supercrop', 'mainline_cut']`
- `performed_at: datetime` — Zeitpunkt der Durchführung
- `affected_nodes: list[int]` — Betroffene Node-Positionen (z.B. `[3, 4]` bei Mainlining)
- `affected_branches: Optional[list[str]]` — Betroffene Triebe (z.B. `["main_left_1", "main_right_2"]`)
- `recovery_days: int` — Erwartete Erholungsdauer (aus HST_Validator.BASE_RECOVERY_DAYS)
- `recovery_end_date: date` — Berechnet: `performed_at + recovery_days`
- `notes: Optional[str]` — Freitext für Beobachtungen
- `photo_ref: Optional[str]` — Foto-Dokumentation (Pflicht bei HST-Events)

**Canopy-Metriken:**
Messbare Parameter zur Bewertung des Training-Fortschritts:
- `canopy_height_min_cm: float` — Niedrigster Trieb
- `canopy_height_max_cm: float` — Höchster Trieb
- `canopy_height_avg_cm: float` — Durchschnittshöhe (berechnet)
- `canopy_evenness_score: float` — Gleichmäßigkeits-Score: `1.0 - (max - min) / max`. Werte nahe 1.0 = perfekt eben, < 0.7 = ungleichmäßig, Intervention empfohlen (LST/Supercropping zur Höhenkorrektur)
- `scrog_fill_percentage: Optional[float]` — Prozentualer Anteil der belegten Netzfläche (0-100%). Ziel: 80-95% vor Blüte-Switch. Nur relevant wenn SCROG-Equipment zugewiesen.
- `branch_count: int` — Anzahl aktiver Triebe/Colas
- `measured_at: date` — Messzeitpunkt

Canopy-Metriken werden als `:CanopyMeasurement`-Dokumente gespeichert und über `has_canopy_measurement`-Edges mit der PlantInstance verknüpft. Zeitreihen ermöglichen Trend-Analyse (Wachstumskurve, Canopy-Entwicklung).

**SCROG-Equipment:**
- SCROG-Netz als Equipment-Typ auf dem `:Slot` (REQ-002)
- Properties: `net_height_cm: float` (Netz-Höhe über Topfrand), `net_grid_size_cm: float` (Maschenweite, typisch 5-10 cm), `net_area_cm2: float` (Gesamtfläche)
- `scrog_tuck`-Events tracken das Durchfädeln von Trieben durch das Netz
- Canopy-Observation-Task ("SCROG-Füllgrad messen") als Recurring-Task im Workflow

**Recovery-Timer:**
Nach jedem HST-Event wird automatisch eine Erholungsphase angezeigt:
- Recovery-Dauer aus `HST_Validator.BASE_RECOVERY_DAYS` (artspezifisch skaliert via `SPECIES_RECOVERY_FACTORS`)
- Status-Anzeige: "Tag 2/7 Erholung nach Topping" mit Fortschrittsbalken
- **Warnung bei Überlappung:** Wenn ein nächstes HST-Event geplant ist und die Recovery-Phase noch läuft, wird eine Warnung ausgegeben: "Erholungsphase endet am {recovery_end_date}, geplantes {next_event} am {next_date} liegt {n} Tage vor Ablauf"
- Der HST-Validator nutzt `recovery_end_date` aus dem TrainingEvent statt nur die generische 7-Tage-Prüfung aus der Task-Historie
- Recovery-Timer berücksichtigt den Temperatur-Modifikator (`TEMPERATURE_RECOVERY_MODIFIERS`) bei verfügbaren Umgebungsdaten (REQ-005)

**Autoflower-Guard:**
Automatische Warnung bei HST-Events für Autoflower-Cultivars:
- Cross-Reference zu REQ-001: `Cultivar.flowering_type == 'autoflower'` (vgl. G-009 Autoflower-Erkennung)
- **Verboten (mit Override):** Topping, FIM, Supercropping, Mainlining — "HST nicht empfohlen bei Autoflower-Sorten. Autoflower haben eine fixe Lebenszeit; Stress-Recovery reduziert die produktive Wachstumsphase überproportional."
- **Erlaubt:** LST (Biegen, Binden), leichte Defoliation, SCROG-Tucking — diese Low-Stress-Maßnahmen beeinträchtigen das Wachstum nicht signifikant
- Severity: `warning` mit `can_override: true` — erfahrene Grower können HST an robusten Autoflower-Genetiken bewusst durchführen
- Prüfung erfolgt im `HST_Validator.can_perform_hst()` als zusätzlicher Check vor der Phasen-Prüfung

**Integration mit bestehenden Modulen:**
- **PlantInstance (REQ-013):** TrainingEvents und CanopyMeasurements werden über Edges mit der PlantInstance verknüpft. Ein aktiver Training-Plan referenziert den zugewiesenen WorkflowTemplate.
- **HST-Validator:** Nutzt `recovery_end_date` aus TrainingEvents für präzisere Recovery-Prüfung. Autoflower-Guard als vorgelagerter Check.
- **Canopy-Height als Sensorwert (REQ-005):** `canopy_height_max_cm` kann als manueller oder semi-automatischer Messwert (Kamera + Bildverarbeitung) in die Sensor-Pipeline einfließen.
- **Task-System:** Training-Events erzeugen automatisch Observation-Follow-up-Tasks ("Recovery prüfen nach Topping", "Canopy-Höhe messen", "SCROG-Füllgrad dokumentieren").

<!-- Quelle: Outdoor-Garden-Planner Review G-005 -->
**12-Monats-Gartenkalender-Template (Freiland, Mitteleuropa):**

Das System bietet ein Jahreskalender-Template, das für jeden Monat die wichtigsten Gartenaufgaben als `seasonal_month`-Tasks generiert. Der Kalender ist als WorkflowTemplate gespeichert und wird bei Aktivierung für das aktuelle Jahr instanziiert.

| Monat | Generierte Tasks | Trigger |
|-------|-----------------|---------|
| Jan | Saatgut-Inventur, Gartenplan erstellen, Obstbaumschnitt (frostfrei) | `seasonal_month: 1` |
| Feb | Voranzucht starten (Paprika, Chili, Aubergine), Beerensträucher schneiden | `seasonal_month: 2` |
| Mär | Beetvorbereitung (Kompost), Rosen abhäufeln, Frühkartoffeln vorkeimen | `seasonal_month: 3` + `phenological: forsythia_bloom` |
| Apr | Direktsaat (Möhren, Radieschen, Erbsen), Staudenteilung, Kartoffeln legen | `seasonal_month: 4` + `phenological: apple_bloom` |
| Mai | Frostempfindliches auspflanzen (nach Eisheiligen!), Kübelpflanzen raus | `seasonal_month: 5` + `phenological: elderberry_bloom` |
| Jun | Erdbeerernte, Tomaten ausgeizen, Sukzessions-Aussaat Salat/Bohnen | `seasonal_month: 6` |
| Jul | Haupternte, Steinobstschnitt, Stecklinge schneiden, Bewässerung intensiv | `seasonal_month: 7` |
| Aug | Herbstgemüse säen (Feldsalat, Spinat), Gründüngung auf leere Beete | `seasonal_month: 8` |
| Sep | Äpfel/Birnen ernten, Herbstpflanzungen, Frühblüher-Zwiebeln stecken | `seasonal_month: 9` |
| Okt | Winterschutz-Checklist (REQ-022), Dahlien ausgraben, Kübelpflanzen rein | `seasonal_month: 10` |
| Nov | Rosen anhäufeln, Beete mulchen, Kompost umsetzen, Laub kompostieren | `seasonal_month: 11` |
| Dez | Gartenruhe, Jahresrückblick, Saatgutkataloge studieren, Planung nächstes Jahr | `seasonal_month: 12` |

**Regionale Anpassung:** Der Kalender verschiebt sich um ±2-4 Wochen basierend auf der `climate_zone` der Site (REQ-002). In USDA 6b (Mittelgebirge) beginnt die Voranzucht 2-3 Wochen später als in USDA 8a (Rheingraben).

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
    - `category: Literal['training', 'maintenance', 'harvest', 'seasonal', 'custom']`
    - `tags: list[str]`
    - `usage_count: int` (Wie oft verwendet)
    - `average_rating: Optional[float]`

- **`:TaskTemplate`** - Template für einzelne Aufgabe
  - Properties:
    - `task_template_id: str`
    - `name: str`
    - `instruction: str` (Detaillierte Anleitung)
    - `category: str`
    - `trigger_type: Literal['phase_entry', 'days_after_phase', 'days_after_planting', 'absolute_date', 'manual', 'conditional', 'gdd_threshold', 'seasonal_month', 'phenological']`
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
    - `timer_duration_seconds: Optional[int]` (Countdown-Dauer in Sekunden, z.B. 120 für "2 min umrühren") <!-- W-006 -->
    - `timer_label: Optional[str]` (Beschriftung des Timers in der UI, z.B. "Umrühren", "Einwirkzeit") <!-- W-006 -->
    <!-- Quelle: Outdoor-Garden-Planner Review G-005 -->
    - `trigger_month: Optional[int]` (Für seasonal_month-Trigger, z.B. 10 für Oktober)
    - `phenological_event: Optional[str]` (Phänologisches Ereignis, z.B. "forsythia_bloom", "elderberry_bloom", "apple_bloom")

- **`:Task`** - Konkrete Aufgaben-Instanz
  - Properties:
    - `task_id: str`
    - `name: str`
    - `instruction: str`
    - `category: str`
    - `due_date: date`
    - `scheduled_time: Optional[time]`
    - `status: Literal['pending', 'in_progress', 'completed', 'skipped', 'failed', 'dormant']`
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
    - `planting_run_key: Optional[str]` (Referenz auf PlantingRun — für Run-basierte Tasks wie Gießplan-Tasks. Ermöglicht Gruppierung nach Run und Duplikat-Prüfung)
    - `watering_event_key: Optional[str]` (Referenz auf WateringEvent — nach Bestätigung des Gießvorgangs gefüllt. Verknüpft Task mit dem erzeugten Event für Rückverfolgbarkeit)
    - `timer_duration_seconds: Optional[int]` (von TaskTemplate propagiert oder manuell gesetzt) <!-- W-006 -->
    - `timer_label: Optional[str]` (von TaskTemplate propagiert oder manuell gesetzt) <!-- W-006 -->
    <!-- Quelle: Einzelaufgaben-Pflege v3.0 -->
    - `tags: list[str]` (benutzerdefinierte Tags zur freien Kategorisierung, z.B. `["dringend", "hochbeet-a"]`)
    - `checklist: list[ChecklistItem]` (eingebettete Checkliste mit Teilschritten, `{ text: str, done: bool, order: int }`)
    - `assigned_to_user_key: Optional[str]` (zugewiesenes Tenant-Mitglied, REQ-024)
    - `recurrence_rule: Optional[str]` (Cron-Expression für wiederkehrende Erzeugung, z.B. `"0 8 * * 1"`)
    - `recurrence_end_date: Optional[date]` (optionales Ende der Wiederholung)
    - `parent_recurring_task_key: Optional[str]` (Referenz auf die Eltern-Recurring-Aufgabe)
    - `trigger_phase: Optional[str]` (Phasen-Binding bei Workflow-Tasks — für dormant-Aktivierung)
    - `trigger_phase_override: Optional[str]` (nutzerindividuelle Überschreibung des Phasen-Bindings)
    - `reopened_at: Optional[datetime]` (Zeitpunkt der Wiedereröffnung, Audit-Trail)
    - `reopened_from_status: Optional[str]` (Status vor Wiedereröffnung, z.B. 'completed')

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

- **`:TaskComment`** - Kommentare/Notizen zu Aufgaben
  - Properties:
    - `comment_id: str`
    - `comment_text: str` (max. 2000 Zeichen)
    - `created_by: str` (User-Key)
    - `created_at: datetime`
    - `updated_at: Optional[datetime]`

<!-- Quelle: Einzelaufgaben-Pflege v3.0 -->
- **`:TaskAuditEntry`** - Änderungshistorie für Aufgaben
  - Properties:
    - `audit_id: str`
    - `task_key: str`
    - `changed_at: datetime`
    - `changed_by: str` (User-Key)
    - `action: Literal['created', 'updated', 'status_changed', 'reopened', 'assigned', 'cloned', 'commented']`
    - `field: Optional[str]` (geändertes Feld, z.B. 'priority', 'status')
    - `old_value: Optional[str]` (vorheriger Wert als JSON-String)
    - `new_value: Optional[str]` (neuer Wert als JSON-String)

<!-- Quelle: Cannabis Indoor Grower Review G-004 -->
- **`:TrainingEvent`** - Einzelnes Training-Ereignis mit Recovery-Tracking
  - Properties:
    - `training_event_id: str`
    - `event_type: Literal['topping', 'fim', 'lst_bend', 'lst_tie', 'scrog_tuck', 'lollipop', 'defoliation', 'supercrop', 'mainline_cut']`
    - `performed_at: datetime`
    - `affected_nodes: list[int]` (Node-Positionen, z.B. `[3, 4]`)
    - `affected_branches: Optional[list[str]]` (Trieb-Bezeichnungen, z.B. `["main_left_1"]`)
    - `recovery_days: int` (aus HST_Validator.BASE_RECOVERY_DAYS × SPECIES_RECOVERY_FACTORS)
    - `recovery_end_date: date` (berechnet: performed_at + recovery_days)
    - `photo_ref: Optional[str]` (Pflicht bei HST-Events)
    - `notes: Optional[str]`

- **`:CanopyMeasurement`** - Zeitpunkt-bezogene Canopy-Messung
  - Properties:
    - `measurement_id: str`
    - `measured_at: date`
    - `canopy_height_min_cm: float`
    - `canopy_height_max_cm: float`
    - `canopy_height_avg_cm: float` (berechnet)
    - `canopy_evenness_score: float` (berechnet: `1.0 - (max - min) / max`)
    - `scrog_fill_percentage: Optional[float]` (0-100%, nur bei SCROG-Equipment)
    - `branch_count: int`
    - `notes: Optional[str]`

<!-- Quelle: Outdoor-Garden-Planner Review G-005 -->
- **`:PhenologicalEvent`** — Dokumentiertes phänologisches Ereignis
  - Properties:
    - `event_type: str` (z.B. "forsythia_bloom", "elderberry_bloom", "apple_bloom", "first_frost", "last_frost")
    - `observed_date: date` (Beobachtungsdatum)
    - `year: int`
    - `notes: Optional[str]`
    - `photo_ref: Optional[str]`
    - `created_at: datetime`

Vordefinierte phänologische Zeiger (Mitteleuropa):
| Phänologisches Ereignis | Zeigerpflanze | Garten-Aktion |
|------------------------|---------------|---------------|
| `hazel_bloom` | Haselblüte (Feb) | Vorfrühling — erste Aussaaten im Kalthaus |
| `forsythia_bloom` | Forsythienblüte (Mär/Apr) | Rosen schneiden, Stauden teilen |
| `apple_bloom` | Apfelblüte (Apr/Mai) | Kartoffeln legen, frostempfindliche Direktsaat |
| `elderberry_bloom` | Holunderblüte (Mai/Jun) | Bohnen säen, alles auspflanzen (Frost vorbei) |
| `linden_bloom` | Lindenblüte (Jun/Jul) | Hochsommer — Ernte beginnt |
| `first_frost` | Erster Frost (Okt/Nov) | Winterschutz! Knollen ausgraben! |

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
assigned_to:       Tasks -> Users                             {assigned_at: datetime, assigned_by: str}
has_comment:       Tasks -> TaskComments
written_by:        TaskComments -> Users
rated_by:          WorkflowTemplates -> Users                 {rating: int, timestamp: datetime}
has_audit:         Tasks -> TaskAuditEntries
cloned_from:       Tasks -> Tasks                             // Referenz auf Quell-Task bei Klonen
recurs_from:       Tasks -> Tasks                             // Referenz auf Eltern-Recurring-Task

// Training-Plan (Canopy Management) — G-004:
has_training_event:       Tasks -> TrainingEvents                // Task erzeugt TrainingEvent bei Completion
training_on:              TrainingEvents -> PlantInstances       // An welcher Pflanze trainiert wurde
has_canopy_measurement:   PlantInstances -> CanopyMeasurements   // Canopy-Messwert-Zeitreihe
triggered_by_training:    Tasks -> TrainingEvents                // Follow-up-Task referenziert auslösendes Event

// Phänologische Trigger — G-005:
triggered_by_phenology:   Tasks -> PhenologicalEvents            // Task wurde durch phänologisches Ereignis ausgelöst
observed_at_site:         PhenologicalEvents -> Sites            // An welchem Standort beobachtet
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
    category: Literal['training', 'pruning', 'ausgeizen', 'transplant', 'feeding', 'ipm', 'harvest', 'observation', 'maintenance', 'care_reminder', 'seasonal', 'phenological']
    trigger_type: Literal['phase_entry', 'days_after_phase', 'days_after_planting', 'absolute_date', 'manual', 'conditional', 'seasonal_month', 'phenological']
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
    timer_duration_seconds: Optional[int] = Field(
        None, ge=1, le=7200,
        description="Optionaler Countdown-Timer in Sekunden. Wird bei Workflow-Instantiation "
                    "auf die Task-Instanz propagiert. Max. 2 Stunden (7200s)."
    )  # W-006
    timer_label: Optional[str] = Field(
        None, max_length=100,
        description="Beschriftung des Timers in der UI, z.B. 'Umrühren', 'Einwirkzeit', 'Belüftung'."
    )  # W-006
    optimal_time_of_day: Optional[Literal['morning', 'afternoon', 'evening', 'lights_off']] = Field(
        None,
        description="Empfohlene Tageszeit für optimale Ergebnisse. "
                    "morning: Stängel turgorreich, flexibel (ideal für LST/Supercropping). "
                    "afternoon/evening: Reduzierte Transpiration, Pflanze hat Nacht zur Erholung. "
                    "lights_off: Für Foliar-Feeding — Gründe: (1) Stomata vieler Arten öffnen bei "
                    "Dunkelheit (CAM) oder schließen bei hohem VPD/Licht, (2) niedrigerer VPD verlängert "
                    "Benetzungsdauer und damit Aufnahmezeit, (3) langsamere Verdunstung = höhere Aufnahme, "
                    "(4) kein Phototoxizitäts-Risiko bei Öl-Produkten (Neem, Paraffinöl)."
    )
    # Saisonale/Phänologische Trigger (Quelle: Outdoor-Garden-Planner Review G-005)
    trigger_month: Optional[int] = Field(
        None, ge=1, le=12,
        description="Für seasonal_month-Trigger: Kalendermonat (1-12), z.B. 10 für Oktober."
    )
    phenological_event: Optional[str] = Field(
        None, max_length=100,
        description="Phänologisches Ereignis, z.B. 'forsythia_bloom', 'elderberry_bloom', 'apple_bloom'. "
                    "Task wird ausgelöst wenn der Nutzer das Eintreten dieses Ereignisses dokumentiert."
    )
    # v3.0: Default-Checkliste und Checklist-Pflicht
    default_checklist: List[dict] = Field(
        default_factory=list,
        description="Default-Checkliste die bei Workflow-Instantiation auf die Task-Instanz kopiert wird. "
                    "Format: [{ 'text': str, 'order': int }]. Der Nutzer kann sie nach Instantiation frei ändern."
    )
    require_all_checklist_items: bool = Field(
        False,
        description="Wenn true, müssen alle Checklist-Einträge erledigt sein bevor der Task abgeschlossen werden kann."
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

    # G-005: Validierung für saisonale/phänologische Trigger
    @field_validator('trigger_month')
    @classmethod
    def validate_trigger_month(cls, v, info):
        trigger = info.data.get('trigger_type')
        if trigger == 'seasonal_month' and v is None:
            raise ValueError("trigger_month erforderlich für seasonal_month-Trigger")
        return v

    @field_validator('phenological_event')
    @classmethod
    def validate_phenological_event(cls, v, info):
        trigger = info.data.get('trigger_type')
        if trigger == 'phenological' and not v:
            raise ValueError("phenological_event erforderlich für phenological-Trigger")
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

        # G-005: Saisonale/Phänologische Trigger
        elif self.trigger_type == 'seasonal_month':
            # Nächstes Auftreten des konfigurierten Monats
            if self.trigger_month:
                year = today.year if today.month <= self.trigger_month else today.year + 1
                return date(year, self.trigger_month, 1)
            return today

        elif self.trigger_type == 'phenological':
            # Wird ausgelöst wenn phänologisches Ereignis dokumentiert wird
            # Due-Date = Beobachtungsdatum des Ereignisses
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
    category: Literal['training', 'maintenance', 'harvest', 'seasonal', 'custom']
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
                    '4. Bewässerung substratabhängig anpassen:\n'
                    '   - Erde: Normal weitergießen, ggf. 24h Bewässerungspause nur bei '
                    'sehr feuchtem Substrat (>70% VWC) — Erde hält Feuchtigkeit lange.\n'
                    '   - Coco: NICHT austrocknen lassen (Coco hat geringe Pufferkapazität), '
                    'Frequenz beibehalten, EC um 10-20% reduzieren.\n'
                    '   - Hydro-NFT/DWC: NICHT stoppen (Wurzelaustrocknung!), EC um 20% reduzieren, '
                    'pH kontrollieren (Stress kann pH-Drift verursachen).\n'
                    '   - Perlite/Vermiculite: Frequenz beibehalten, leicht reduzierte Gabe.'
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

<!-- Quelle: Cannabis Indoor Grower Review G-004 -->
**2b. Training-Plan-Modelle & Autoflower-Guard:**
```python
from pydantic import BaseModel, Field, computed_field
from typing import Literal, Optional
from datetime import date, datetime, timedelta


# --- Training-Event-Typen ---
TrainingEventType = Literal[
    'topping', 'fim', 'lst_bend', 'lst_tie', 'scrog_tuck',
    'lollipop', 'defoliation', 'supercrop', 'mainline_cut'
]

# HST-Typen die den Recovery-Timer auslösen
HST_EVENT_TYPES: set[str] = {
    'topping', 'fim', 'supercrop', 'mainline_cut'
}

# HST-Typen die bei Autoflower verboten sind (mit Override)
AUTOFLOWER_FORBIDDEN_HST: set[str] = {
    'topping', 'fim', 'supercrop', 'mainline_cut'
}


class TrainingEvent(BaseModel):
    """Einzelnes Training-Ereignis mit Recovery-Tracking"""

    training_event_id: str
    event_type: TrainingEventType
    performed_at: datetime
    affected_nodes: list[int] = Field(
        default_factory=list,
        description="Betroffene Node-Positionen (z.B. [3, 4] bei Mainlining)"
    )
    affected_branches: Optional[list[str]] = Field(
        None,
        description="Betroffene Triebe (z.B. ['main_left_1', 'main_right_2'])"
    )
    recovery_days: int = Field(
        ge=0,
        description="Erwartete Erholungsdauer in Tagen (aus HST_Validator)"
    )
    photo_ref: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=500)

    @computed_field
    @property
    def recovery_end_date(self) -> date:
        """Berechnet Ende der Erholungsphase"""
        return (self.performed_at + timedelta(days=self.recovery_days)).date()

    @computed_field
    @property
    def is_hst(self) -> bool:
        """Ist dieses Event ein High-Stress-Training?"""
        return self.event_type in HST_EVENT_TYPES

    def recovery_status(self, current_date: date | None = None) -> dict:
        """
        Berechnet den aktuellen Recovery-Status.

        Returns:
            {
                days_elapsed: int,
                days_remaining: int,
                is_recovered: bool,
                progress_percent: float,
                label: str  # z.B. "Tag 2/7 Erholung nach Topping"
            }
        """
        today = current_date or date.today()
        days_elapsed = (today - self.performed_at.date()).days
        days_remaining = max(0, self.recovery_days - days_elapsed)
        is_recovered = days_remaining == 0

        progress = min(1.0, days_elapsed / self.recovery_days) if self.recovery_days > 0 else 1.0

        return {
            'days_elapsed': days_elapsed,
            'days_remaining': days_remaining,
            'is_recovered': is_recovered,
            'progress_percent': round(progress * 100, 1),
            'label': (
                f"Erholung abgeschlossen ({self.event_type})"
                if is_recovered
                else f"Tag {days_elapsed}/{self.recovery_days} Erholung nach {self.event_type}"
            ),
        }


class CanopyMeasurement(BaseModel):
    """Zeitpunkt-bezogene Canopy-Messung"""

    measurement_id: str
    measured_at: date
    canopy_height_min_cm: float = Field(ge=0)
    canopy_height_max_cm: float = Field(ge=0)
    branch_count: int = Field(ge=1)
    scrog_fill_percentage: Optional[float] = Field(
        None, ge=0, le=100,
        description="Belegter Anteil der SCROG-Netzfläche (%). Nur bei SCROG-Equipment."
    )
    notes: Optional[str] = Field(None, max_length=500)

    @computed_field
    @property
    def canopy_height_avg_cm(self) -> float:
        """Durchschnittliche Canopy-Höhe"""
        return round((self.canopy_height_min_cm + self.canopy_height_max_cm) / 2, 1)

    @computed_field
    @property
    def canopy_evenness_score(self) -> float:
        """
        Gleichmäßigkeits-Score: 1.0 - (max - min) / max
        Werte nahe 1.0 = perfekt eben
        < 0.7 = ungleichmäßig, Intervention empfohlen
        """
        if self.canopy_height_max_cm == 0:
            return 1.0
        return round(
            1.0 - (self.canopy_height_max_cm - self.canopy_height_min_cm)
            / self.canopy_height_max_cm,
            3
        )


# Quelle: Outdoor-Garden-Planner Review G-005
class PhenologicalEvent(BaseModel):
    """Dokumentiertes phänologisches Ereignis (Zeigerpflanze)"""

    event_type: str = Field(
        min_length=3, max_length=100,
        description="z.B. 'forsythia_bloom', 'elderberry_bloom', 'apple_bloom', 'first_frost', 'last_frost'"
    )
    observed_date: date
    year: int = Field(ge=2000, le=2100)
    notes: Optional[str] = Field(None, max_length=500)
    photo_ref: Optional[str] = None
    created_at: datetime

    # Vordefinierte phänologische Zeiger (Mitteleuropa)
    PHENOLOGICAL_INDICATORS: dict[str, dict] = {
        'hazel_bloom':      {'name': 'Haselblüte',      'typical_month': 2,  'action': 'Vorfrühling — erste Aussaaten im Kalthaus'},
        'forsythia_bloom':  {'name': 'Forsythienblüte',  'typical_month': 3,  'action': 'Rosen schneiden, Stauden teilen'},
        'apple_bloom':      {'name': 'Apfelblüte',       'typical_month': 4,  'action': 'Kartoffeln legen, frostempfindliche Direktsaat'},
        'elderberry_bloom': {'name': 'Holunderblüte',    'typical_month': 5,  'action': 'Bohnen säen, alles auspflanzen (Frost vorbei)'},
        'linden_bloom':     {'name': 'Lindenblüte',      'typical_month': 6,  'action': 'Hochsommer — Ernte beginnt'},
        'first_frost':      {'name': 'Erster Frost',     'typical_month': 10, 'action': 'Winterschutz! Knollen ausgraben!'},
    }


class AutoflowerGuard:
    """
    Prüft ob HST-Events für Autoflower-Cultivars erlaubt sind.
    Cross-Reference: REQ-001 Cultivar.flowering_type, G-009 Autoflower-Erkennung.

    Autoflower haben eine genetisch fixierte Lebenszeit. Stress-Recovery
    nach HST reduziert die produktive Wachstumsphase überproportional,
    da die Pflanze nicht einfach länger in Vegi bleiben kann.
    """

    @classmethod
    def check(
        cls,
        event_type: str,
        flowering_type: str,
    ) -> tuple[bool, str, dict]:
        """
        Prüft ob ein Training-Event für den gegebenen Cultivar-Typ erlaubt ist.

        Args:
            event_type: Typ des geplanten Training-Events
            flowering_type: 'autoflower', 'photoperiod', 'fast_version', etc.

        Returns:
            (can_perform, reason, additional_info)
        """
        if flowering_type != 'autoflower':
            return True, "Kein Autoflower — keine Einschränkung", {}

        if event_type in AUTOFLOWER_FORBIDDEN_HST:
            return False, (
                f"WARNUNG: {event_type} nicht empfohlen bei Autoflower-Sorten. "
                f"Autoflower haben eine fixe Lebenszeit; Stress-Recovery nach HST "
                f"reduziert die produktive Wachstumsphase überproportional. "
                f"Alternative: LST, leichte Defoliation oder SCROG-Tucking."
            ), {
                'severity': 'warning',
                'can_override': True,
                'suggested_alternatives': ['lst_bend', 'lst_tie', 'defoliation', 'scrog_tuck'],
            }

        # LST, Defoliation, SCROG-Tucking sind erlaubt
        return True, (
            f"{event_type} ist Low-Stress und für Autoflower geeignet."
        ), {'severity': 'ok'}


class RecoveryTimerChecker:
    """
    Prüft Recovery-Überlappungen bei geplanten Training-Events.
    Nutzt TrainingEvent.recovery_end_date statt generische Task-Historie.
    """

    @classmethod
    def check_overlap(
        cls,
        planned_event_date: date,
        planned_event_type: str,
        recent_training_events: list[TrainingEvent],
    ) -> tuple[bool, str, dict]:
        """
        Prüft ob ein geplantes Training-Event in eine laufende Recovery-Phase fällt.

        Returns:
            (can_perform, reason, additional_info)
        """
        for event in recent_training_events:
            if not event.is_hst:
                continue

            if planned_event_date < event.recovery_end_date:
                days_before = (event.recovery_end_date - planned_event_date).days
                status = event.recovery_status(planned_event_date)
                return False, (
                    f"WARNUNG: Erholungsphase nach {event.event_type} "
                    f"(am {event.performed_at.date().isoformat()}) endet am "
                    f"{event.recovery_end_date.isoformat()}. "
                    f"Geplantes {planned_event_type} liegt {days_before} Tage vor Ablauf. "
                    f"Aktueller Status: {status['label']}"
                ), {
                    'severity': 'warning',
                    'can_override': True,
                    'recovery_status': status,
                    'blocking_event': event.training_event_id,
                    'days_before_recovery_end': days_before,
                }

        return True, "Keine Recovery-Überlappung", {'severity': 'ok'}
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

TaskCategory = Literal['training', 'pruning', 'ausgeizen', 'transplant', 'feeding', 'ipm', 'harvest', 'observation', 'maintenance', 'care_reminder', 'seasonal', 'phenological']
TriggerType = Literal['phase_entry', 'days_after_phase', 'days_after_planting', 'absolute_date', 'manual', 'conditional', 'gdd_threshold', 'seasonal_month', 'phenological']
# v3.0: 'dormant' Status für phasengebundene Workflow-Tasks (Phase noch nicht erreicht)
TaskStatus = Literal['pending', 'in_progress', 'completed', 'skipped', 'failed', 'dormant']
TaskPriority = Literal['low', 'medium', 'high', 'critical']
StressLevel = Literal['none', 'low', 'medium', 'high']
SkillLevel = Literal['beginner', 'intermediate', 'advanced']


# v3.0: Eingebettete Checkliste für Teilschritte innerhalb einer Aufgabe
class ChecklistItem(BaseModel):
    """Einzelner Checklist-Eintrag innerhalb einer Task-Instanz"""
    text: str = Field(min_length=1, max_length=500)
    done: bool = False
    order: int = Field(ge=0, description="Sortierposition innerhalb der Checkliste")


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
    # v3.0: Bewertungen nach Abschluss
    difficulty_rating: Optional[int] = Field(None, ge=1, le=5, description="Wie schwierig war die Aufgabe? (1=trivial, 5=sehr schwierig)")
    quality_rating: Optional[int] = Field(None, ge=1, le=5, description="Wie gut ist das Ergebnis? (1=schlecht, 5=exzellent)")
    skill_level: SkillLevel = 'beginner'
    stress_level: StressLevel = 'none'
    planting_run_key: Optional[str] = Field(
        None,
        description="Referenz auf PlantingRun — für Run-basierte Tasks (Gießplan-Workflow)"
    )
    watering_event_key: Optional[str] = Field(
        None,
        description="Referenz auf WateringEvent — nach Gießplan-Bestätigung gefüllt"
    )
    timer_duration_seconds: Optional[int] = Field(
        None, ge=1, le=7200,
        description="Countdown-Timer in Sekunden — von TaskTemplate propagiert oder manuell gesetzt"
    )  # W-006
    timer_label: Optional[str] = Field(
        None, max_length=100,
        description="Beschriftung des Timers, z.B. 'Umrühren', 'Einwirkzeit'"
    )  # W-006
    # v3.0: Einzelaufgaben-Pflege — Tags, Checkliste, Zuweisung, Wiederholung
    tags: List[str] = Field(
        default_factory=list,
        description="Benutzerdefinierte Tags zur freien Kategorisierung (kein vordefiniertes Vokabular)"
    )
    checklist: List[ChecklistItem] = Field(
        default_factory=list,
        description="Eingebettete Checkliste mit Teilschritten innerhalb der Aufgabe"
    )
    assigned_to_user_key: Optional[str] = Field(
        None,
        description="Zugewiesenes Tenant-Mitglied (REQ-024). Bei Gemeinschaftsgärten: Admin kann Tasks zuweisen."
    )
    recurrence_rule: Optional[str] = Field(
        None, max_length=100,
        description="Cron-Expression für automatische Wiedererzeugung, z.B. '0 8 * * 1' (jeden Montag 08:00)"
    )
    recurrence_end_date: Optional[date] = Field(
        None,
        description="Optionales Ende der Wiederholung"
    )
    parent_recurring_task_key: Optional[str] = Field(
        None,
        description="Referenz auf die Eltern-Aufgabe die die Wiederholung definiert"
    )
    # v3.0: Phasengebundene Workflow-Tasks
    trigger_phase: Optional[str] = Field(
        None,
        description="Phasen-Binding bei Workflow-Tasks — Task wird dormant erzeugt und bei Phase-Transition aktiviert"
    )
    trigger_phase_override: Optional[str] = Field(
        None,
        description="Nutzerindividuelle Überschreibung des Phasen-Bindings"
    )
    # v3.0: Audit-Trail für Wiedereröffnung
    reopened_at: Optional[datetime] = None
    reopened_from_status: Optional[str] = None

    @field_validator('photo_refs')
    @classmethod
    def validate_photos_when_required(cls, v, info):
        if info.data.get('requires_photo') and info.data.get('status') == 'completed':
            if not v:
                raise ValueError("Foto-Upload erforderlich für diesen Task")
        return v

    @field_validator('recurrence_rule')
    @classmethod
    def validate_cron_expression(cls, v):
        if v is not None:
            # Basis-Validierung: 5 Felder (minute hour day month weekday)
            parts = v.strip().split()
            if len(parts) != 5:
                raise ValueError("Cron-Expression muss 5 Felder haben (minute hour day month weekday)")
        return v

    @property
    def checklist_progress(self) -> tuple[int, int]:
        """Gibt (done_count, total_count) der Checkliste zurück"""
        total = len(self.checklist)
        done = sum(1 for item in self.checklist if item.done)
        return (done, total)

    @property
    def effective_trigger_phase(self) -> Optional[str]:
        """Gibt die effektive Phase zurück (Override > Original)"""
        return self.trigger_phase_override or self.trigger_phase


class TaskCompletion(BaseModel):
    """Task-Abschluss-Daten"""

    task_id: str
    completed_at: datetime
    actual_duration_minutes: int = Field(ge=1)
    photo_refs: List[str] = Field(default_factory=list)
    completion_notes: Optional[str] = None
    # v3.0: Bewertungen nach Abschluss
    difficulty_rating: Optional[int] = Field(None, ge=1, le=5, description="Wie schwierig war die Aufgabe?")
    quality_rating: Optional[int] = Field(None, ge=1, le=5, description="Wie gut ist das Ergebnis?")

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


# v3.0: Task-Kommentar-Modell
class TaskComment(BaseModel):
    """Kommentar/Notiz an einer Aufgabe"""

    comment_id: str
    task_key: str
    comment_text: str = Field(min_length=1, max_length=2000)
    created_by: str  # User-Key
    created_at: datetime
    updated_at: Optional[datetime] = None


# v3.0: Task-Änderungshistorie
class TaskAuditEntry(BaseModel):
    """Audit-Eintrag für Aufgaben-Änderungen"""

    audit_id: str
    task_key: str
    changed_at: datetime
    changed_by: str  # User-Key
    action: Literal['created', 'updated', 'status_changed', 'reopened', 'assigned', 'cloned', 'commented']
    field: Optional[str] = None  # Geändertes Feld, z.B. 'priority'
    old_value: Optional[str] = None  # Vorheriger Wert als JSON-String
    new_value: Optional[str] = None  # Neuer Wert als JSON-String
```

### Celery-Beat: Gießplan-Task-Generierung

**Task: `generate_watering_tasks`**
- **Schedule:** Täglich 05:00 UTC
- **Beschreibung:** Scannt alle aktiven PlantingRuns mit zugewiesenem NutrientPlan + WateringSchedule und erzeugt Gießplan-Tasks für den aktuellen Tag.

```python
from celery import shared_task
from datetime import date, time

@shared_task(name='generate_watering_tasks')
def generate_watering_tasks():
    """
    Täglicher Celery-Beat Task: Erzeugt Gießplan-Tasks für alle aktiven Runs.

    Ablauf:
    1. Lade alle PlantingRuns mit status='active' und nutrient_plan_key != null
    2. Für jeden Run: Lade den NutrientPlan und prüfe ob watering_schedule vorhanden
    3. Prüfe ob heute ein Gießtag ist (via WateringScheduleEngine.is_watering_due):
       - mode='weekdays': heute.weekday() in weekday_schedule?
       - mode='interval': Tage seit letztem Gießen >= interval_days?
    4. Idempotenz-Check: Existiert bereits ein Task mit
       category='feeding' AND planting_run_key=run_key AND due_date=heute?
       → Skip (kein Duplikat)
    5. Erzeuge Task:
       - task_id: f"feeding:watering:{run_key}:{today.isoformat()}"
       - name: f"Gießen: {run.name}" (i18n-Key: tasks.watering.name)
       - instruction: Generiert aus NutrientPlan + Phasengruppen
       - category: 'feeding'
       - due_date: heute
       - scheduled_time: WateringSchedule.preferred_time (falls gesetzt)
       - priority: 'high'
       - skill_level: 'beginner'
       - stress_level: 'none'
       - requires_photo: false
       - requires_confirmation: false
       - planting_run_key: run._key
       - estimated_duration_minutes: 15 (Default für manuelles Gießen)
    6. Erzeuge has_task-Edges zu allen aktiven Pflanzen im Run

    Idempotenz: Kein Duplikat wenn Task für Run+Datum schon existiert.
    Tenant-Scope: Task erbt tenant_key vom PlantingRun.
    """
    today = date.today()
    # ... Implementation
```

**Celery-Beat-Konfiguration:**
```python
CELERY_BEAT_SCHEDULE = {
    # ... bestehende Tasks ...
    'generate-watering-tasks': {
        'task': 'generate_watering_tasks',
        'schedule': crontab(hour=5, minute=0),  # Täglich 05:00 UTC
    },
}
```

## 4. Authentifizierung & Autorisierung

> **Hinweis (SEC-H-001):** Dieser Abschnitt wurde nachträglich ergänzt, um die Auth-Anforderungen
> gemäß REQ-023 (Authentifizierung) und REQ-024 (Mandantenverwaltung) zu dokumentieren.

**Standardregel:** Alle Endpunkte dieses REQ erfordern Authentifizierung (JWT Bearer Token)
und Tenant-Mitgliedschaft, sofern nicht anders angegeben.

| Ressource/Endpoint-Gruppe | Lesen | Schreiben | Löschen |
|---------------------------|-------|-----------|---------|
| Tasks (Tenant-scoped) | Mitglied | Mitglied | Admin |
| Task-Statusübergänge | — | Mitglied | — |
| Task-Kommentare | Mitglied | Mitglied (eigene) | Mitglied (eigene) / Admin (alle) |
| Task-Historie | Mitglied | — (systemgeneriert) | — |
| Task-Klonen | — | Mitglied | — |
| Task-Wiedereröffnen | — | Mitglied | — |
| Task-Batch-Operationen | — | Mitglied (eigene) / Admin (alle) | Admin |
| Task-Zuweisung | — | Admin / Grower (nur eigene) | — |
| Recurring-Tasks | Mitglied | Mitglied | Mitglied (eigene) / Admin (alle) |
| WorkflowTemplates | Mitglied | Admin | Admin |
| Workflow-Instanziierung | — | Mitglied | — |
| Workflow-Task-Hinzufügen | — | Mitglied (eigene Execution) | — |

## 5. Abhängigkeiten

**Erforderliche Module:**
- REQ-001 (Stammdaten): Species für Template-Kompatibilität + `species_type` für artspezifische Recovery-Zeiten + `Cultivar.flowering_type` für Autoflower-Guard (G-004)
- REQ-003 (Phasen): GrowthPhase für Phase-Trigger (inkl. `early_flowering` Differenzierung), GDD-Daten für `gdd_threshold`-Trigger
- REQ-002 (Standort): Location für Multi-Plant-Workflows
- REQ-004 (Dünge-Logik): **HOCH** — NutrientPlan + WateringSchedule + WateringScheduleEngine für `generate_watering_tasks` Celery-Beat; Phasen-Dosierungsauflösung
- REQ-010 (IPM): IPM-Task-Historie für Karenzzeit-Validierung bei Harvest-Tasks
- REQ-013 (Pflanzdurchlauf): **HOCH** — PlantingRun als Gruppierungs-Container für Gießplan-Tasks; `nutrient_plan_key` auf Run/Entry für Plan-Auflösung; PlantInstance für TrainingEvent- und CanopyMeasurement-Verknüpfung (G-004)
- REQ-005 (Sensorik): `canopy_height_max_cm` als manueller/semi-automatischer Messwert in die Sensor-Pipeline (G-004)
- REQ-018 (Umgebungssteuerung): **Task-Aktor-Integration** — Tasks wie "Licht umstellen auf 12/12" können optional mit Aktor-Aktionen verknüpft werden. Bei automatischer Aktor-Ausführung: Task auto-completed. Bei manueller Steuerung: Task als Reminder. Konflikterkennung: Task "Licht 18/6" + Phase-Profil "12/12" = Warnung.

**Wird benötigt von:**
- REQ-007 (Ernte): Harvest-Tasks als Teil von Workflows
- REQ-010 (IPM): IPM-Tasks (Spraying, Inspection)
- REQ-009 (Dashboard): Task-Queue-Widget
- REQ-014 (Tankmanagement): **HOCH** — Automatische Wartungs-Tasks aus MaintenanceSchedule; Gießplan-Bestätigungsflow (`confirm`/`quick-confirm`) nutzt Task-Key für Completion + WateringEvent-Erzeugung

**Neue/verstärkte Abhängigkeiten (v3.0):**
- REQ-003 (Phasen): **HOCH** — Phase-Transition-Hook muss `activate_dormant_tasks_for_phase()` aufrufen, um dormante Workflow-Tasks bei Phasenwechsel zu aktivieren
- REQ-024 (Mandantenverwaltung): **HOCH** — `assigned_to_user_key` erfordert Membership-Prüfung (nur Tenant-Mitglieder zuweisbar)

**Python-Bibliotheken:**
- `celery` - Zeitgesteuerte Task-Erinnerungen + Recurring-Task-Erzeugung
- `croniter` - Cron-Expression-Parsing für Recurring Tasks
- `jsonschema` - Validierung von Workflow-JSON-Importen

## 6. Akzeptanzkriterien

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
- [ ] **Zimmerpflanzen-Templates:** Orchidee, Kaktus/Sukkulente, tropische Grünpflanze, Calathea, Umtopf-Workflow, Überwinterung, Vermehrung (Stecklinge), saisonale Düngung
- [ ] **Outdoor-Templates:** Frostschutz-Workflow, Abhärtung (Indoor→Outdoor), Obstbaum-Jahresschnitt, Saisonende-Workflow
- [ ] **Hydroponik-Wartung:** Nährlösung-Wechsel, Sonden-Kalibrierung, System-Reinigung als System-Templates
- [ ] **GDD-Trigger:** Task-Auslösung basierend auf akkumulierten Gradtagsummen (REQ-003)
- [ ] **Task-Aktor-Integration:** Tasks optional mit REQ-018 Aktor-Aktionen verknüpfbar
- [ ] **Karenzzeit-Validierung:** Harvest-Tasks werden gegen letzte IPM-Maßnahmen validiert (PHI-Einhaltung)
- [ ] **Tageszeit-Empfehlung:** TaskTemplates können `optimal_time_of_day` empfehlen
- [ ] **Genetik-Variable (SOG-Timing):** cultivar_timing_factor skaliert Template-Tage bei Workflow-Instantiation
- [ ] **Substratspezifische Bewässerungs-Hinweise:** Post-HST-Bewässerung differenziert nach Erde/Coco/Hydro/Perlite
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
- [ ] **Gießplan-Task-Generierung:** `generate_watering_tasks` Celery-Beat erzeugt tägliche Gieß-Tasks für aktive Runs mit NutrientPlan+WateringSchedule
- [ ] **Gießplan-Idempotenz:** Kein Duplikat wenn Task für Run+Datum bereits existiert
- [ ] **Gießplan-Weekday-Modus:** Tasks werden nur an konfigurierten Wochentagen erzeugt
- [ ] **Gießplan-Interval-Modus:** Tasks werden im konfigurierten Intervall ab letztem Gießen erzeugt
- [ ] **Gießplan-Task-Felder:** `planting_run_key` und `watering_event_key` auf Task korrekt gesetzt
- [ ] **Gießplan-Tenant-Scope:** Tasks erben `tenant_key` vom PlantingRun
- [ ] **Task-Timer (W-006):** TaskTemplates und Task-Instanzen unterstützen optionale `timer_duration_seconds` und `timer_label`
- [ ] **Timer-Propagation (W-006):** Timer-Werte werden bei Workflow-Instantiation vom Template auf die Task-Instanz übertragen
- [ ] **Timer-UI (W-006):** Visueller Countdown (Kreis/Balken) mit Start/Pause/Reset bei Tasks mit Timer-Dauer
- [ ] **Timer-Benachrichtigung (W-006):** Akustische/haptische Benachrichtigung bei Timer-Ablauf (konfigurierbar in User-Preferences)
- [ ] **Timer-Ad-hoc (W-006):** Nutzer können bei Tasks ohne vordefinierte Dauer manuell einen Timer starten
- [ ] **Timer nicht-blockierend (W-006):** Timer-Ablauf blockiert nicht den Task-Abschluss — Orientierungshilfe, keine Pflicht
- [ ] **Training-Event-Modell (G-004):** TrainingEvent-Dokumente mit event_type, affected_nodes, recovery_days, recovery_end_date korrekt erstellt bei Training-Task-Completion
- [ ] **Canopy-Metriken (G-004):** CanopyMeasurement mit canopy_height_min/max/avg, canopy_evenness_score, branch_count; Zeitreihen-Trend pro PlantInstance
- [ ] **SCROG-Füllgrad (G-004):** scrog_fill_percentage nur bei zugewiesenem SCROG-Equipment erfassbar; Zielwert 80-95% vor Blüte-Switch
- [ ] **Recovery-Timer (G-004):** Nach HST-Events automatische Erholungsphase mit Fortschrittsbalken ("Tag 2/7 Erholung nach Topping")
- [ ] **Recovery-Überlappungswarnung (G-004):** Warnung wenn nächstes HST-Event vor Ablauf der Recovery-Phase geplant wird (can_override: true)
- [ ] **Autoflower-Guard (G-004):** Warnung bei Topping/FIM/Supercropping/Mainlining für Autoflower-Cultivars; LST/Defoliation/SCROG-Tucking bleiben erlaubt
- [ ] **Training-Strategie-Templates (G-004):** System-Templates für LST-Only, Top+SCROG, Mainlining/Manifolding, SOG, Defoliation-Schedule
- [ ] **Training-Follow-up-Tasks (G-004):** Automatische Observation-Tasks nach HST-Events (Recovery prüfen, Canopy messen, SCROG-Füllgrad dokumentieren)
- [ ] **Canopy-Evenness-Score (G-004):** Score-Berechnung `1.0 - (max-min)/max`; Intervention-Empfehlung bei Score < 0.7
<!-- Quelle: Outdoor-Garden-Planner Review G-005 -->
- [ ] **Erweiterte Outdoor-Templates (G-005):** Frühjahrs-Beetvorbereitung, Voranzucht-Workflow, Gründüngung, Überwinterungs-Checklist, Frühlings-Auswinterungs-Checklist, Sukzessions-Aussaat, Staudenteilung, Rosen-Jahrespflege
- [ ] **Seasonal-Month-Trigger (G-005):** Tasks können an feste Kalendermonate gebunden werden (trigger_type='seasonal_month', trigger_month=1-12)
- [ ] **Phenological-Trigger (G-005):** Tasks werden durch phänologische Beobachtungen ausgelöst (trigger_type='phenological', phenological_event='forsythia_bloom' etc.)
- [ ] **PhenologicalEvent-Dokumentation (G-005):** Nutzer können phänologische Ereignisse mit Datum, Foto und Notizen dokumentieren; System löst verknüpfte Tasks aus
- [ ] **12-Monats-Gartenkalender (G-005):** Jahreskalender-Template für Freiland (Mitteleuropa) mit monatsspezifischen Tasks; instanziierbar pro Jahr
- [ ] **Regionale Kalender-Anpassung (G-005):** Gartenkalender verschiebt sich basierend auf climate_zone der Site (REQ-002) um ±2-4 Wochen
- [ ] **Seasonal/Phenological-Kategorien (G-005):** Neue Task-Kategorien 'seasonal' und 'phenological' für saisonale und phänologische Aufgaben
- [ ] **Phänologische Zeigerpflanzen (G-005):** 6 vordefinierte Zeiger für Mitteleuropa (Hasel, Forsythie, Apfel, Holunder, Linde, Erster Frost) mit verknüpften Gartenaktionen
<!-- Quelle: Einzelaufgaben-Pflege v3.0 -->
- [ ] **Tags (v3.0):** Tasks unterstützen benutzerdefinierte Tags (`tags: list[str]`); Filterung/Suche über Tags in Task-Queue
- [ ] **Checkliste (v3.0):** Tasks unterstützen eingebettete Checklisten (`checklist: list[ChecklistItem]`); Fortschrittsanzeige "x/y Schritte erledigt"; optional `require_all_checklist_items` am TaskTemplate
- [ ] **Bewertungen (v3.0):** `difficulty_rating` und `quality_rating` (1-5) bei Task-Completion optional erfassbar; Performance-Score-Berechnung
- [ ] **Zeitplanung (v3.0):** `scheduled_time` auf Task-Instanz; Auflösung aus TaskTemplate `optimal_time_of_day` in konkrete Uhrzeit
- [ ] **User-Zuweisung (v3.0):** `assigned_to_user_key` auf Task; Filter "Meine Aufgaben" vs. "Alle Aufgaben"; Membership-Validierung (nur Tenant-Mitglieder)
- [ ] **Wiederkehrende Aufgaben (v3.0):** `recurrence_rule` (Cron), `recurrence_end_date`; automatische Erzeugung nächster Instanz bei Completion; Celery-Beat tägliche Prüfung; Stoppen/Ändern/Pausieren der Wiederholung
- [ ] **Task-Klonen (v3.0):** `POST /tasks/{key}/clone` erzeugt Kopie mit Status=pending; optionale `target_plant_key` und `due_date_offset_days`
- [ ] **Task-Wiedereröffnung (v3.0):** `POST /tasks/{key}/reopen` setzt completed/skipped → pending; Audit-Trail (`reopened_at`, `reopened_from_status`)
- [ ] **Task-Neuzuweisung (v3.0):** `plant_key` und `assigned_to_user_key` über TaskUpdate änderbar
- [ ] **Batch-Operationen (v3.0):** `POST /tasks/batch/status`, `POST /tasks/batch/delete`, `POST /tasks/batch/assign`; atomare Ausführung mit Rollback
- [ ] **Task-Kommentare (v3.0):** CRUD für Kommentare an Tasks; chronologisch geordnet; kaskadierte Löschung bei Task-Entfernung
- [ ] **Task-Änderungshistorie (v3.0):** `GET /tasks/{key}/history` zeigt alle Änderungen; TaskAuditEntry mit action, field, old_value, new_value
- [ ] **Dormant-Status (v3.0):** Tasks mit `trigger_phase` für zukünftige Phasen werden als `dormant` erzeugt; automatische Aktivierung bei Phase-Transition
- [ ] **Phase-Transition-Hook (v3.0):** `activate_dormant_tasks_for_phase()` wird bei jedem Phasenwechsel (REQ-003) aufgerufen; dormant → pending mit berechneter due_date
- [ ] **Workflow-Task-Anpassung (v3.0):** Jede instanziierte Task kann individuell angepasst werden (Name, Instruktion, Phase-Binding, Checkliste, Timer, Tags) ohne das Template zu ändern
- [ ] **Workflow-Tasks hinzufügen (v3.0):** `POST /workflows/executions/{key}/tasks` ermöglicht zusätzliche Tasks zu einem laufenden Workflow
- [ ] **Workflow-Tasks löschen (v3.0):** Einzelne Tasks innerhalb einer Workflow-Execution können gelöscht werden ohne den Workflow zu brechen
- [ ] **Workflow-Phase-Timeline (v3.0):** UI zeigt Tasks gruppiert nach Phase als Timeline/Gantt mit Highlight der aktiven Phase
- [ ] **Enum-Synchronisation (v3.0):** Backend `TaskCategory` enthält alle 12 Werte (training, pruning, ausgeizen, transplant, feeding, ipm, harvest, observation, maintenance, care_reminder, seasonal, phenological); Frontend-Kategorien sind identisch mit Backend-Enum

### Testszenarien:

**Szenario 1: Cannabis SOG Workflow-Instantiation**
```
GIVEN: Cannabis-Pflanze, gepflanzt am 01.01.2025
       Cultivar "Northern Lights" mit cultivar_timing_factor = 1.0 (Referenz-Sorte)
WHEN: SOG-Workflow wird angewendet
THEN:
  - Tasks generiert (Basis-Timing, skaliert mit cultivar_timing_factor):
    1. Tag 14 (× factor): Transplant zu finalen Töpfen
    2. Tag 18 (× factor): Light Defoliation (untere Blätter)
    3. Tag 21 (× factor): Switch zu 12/12 Licht (Blüte-Einleitung)
    4. Tag 35 (× factor): Lollipopping (untere 1/3 entfernen)
    5. Tag 56 (× factor): Flushing starten
    6. Tag 70 (× factor): Ernte
  - Alle Tasks haben Status 'pending'
  - Dependencies: Task 2 blockt durch Task 1, etc.

  HINWEIS zu Genetik-Variablen:
  Die Basis-Tage im SOG-Template sind Richtwerte für eine durchschnittliche
  Indica-dominante Sorte (8-9 Wochen Blütezeit). Andere Genetiken erfordern
  Anpassung:
  - cultivar_timing_factor: 0.8 (schnelle Autoflower) bis 1.5 (Sativa-Haze)
  - Dieser Faktor wird optional am Cultivar (REQ-001) hinterlegt und bei
    Workflow-Instantiation auf alle days_offset-Werte multipliziert.
  - Ohne Cultivar-Faktor: Basis-Timing wird unverändert verwendet.
  - GDD-basierte Trigger (trigger_type='gdd_threshold') sind biologisch
    präziser als fixe Kalendertage und sollten bei verfügbaren Temperaturdaten
    bevorzugt werden.
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

**Szenario 8: Gießplan-Task-Generierung (Celery-Beat)**
```
GIVEN: PlantingRun "Tomaten Hochbeet A" (status: active, 20 Pflanzen),
       NutrientPlan "Tomato Heavy Coco" mit WateringSchedule (weekdays: [0, 2, 4], preferred_time: "08:00")
       Heute ist Montag (weekday=0)
WHEN: Celery-Task `generate_watering_tasks` läuft um 05:00 UTC
THEN:
  - WateringScheduleEngine.is_watering_due → True (Montag in weekday_schedule)
  - Idempotenz-Check: Kein existierender Task für Run+heute
  - Neuer Task erzeugt:
    task_id: "feeding:watering:tomaten_hochbeet_a_2025:2026-02-27"
    name: "Gießen: Tomaten Hochbeet A 2025"
    category: "feeding"
    due_date: 2026-02-27
    scheduled_time: 08:00
    priority: "high"
    planting_run_key: "tomaten_hochbeet_a_2025"
  - has_task-Edges zu allen 20 aktiven Pflanzen
```

**Szenario 9: Gießplan-Idempotenz**
```
GIVEN: Gießplan-Task für Run "Tomaten Hochbeet A" und Datum 2026-02-27 existiert bereits
WHEN: Celery-Task `generate_watering_tasks` läuft erneut (z.B. bei Restart)
THEN:
  - Idempotenz-Check erkennt existierenden Task
  - Kein Duplikat erzeugt
  - Log: "Skipping: Task for run 'tomaten_hochbeet_a_2025' on 2026-02-27 already exists"
```

**Szenario 10: Gießplan-Interval-Modus**
```
GIVEN: PlantingRun mit NutrientPlan, WateringSchedule (interval: 3 Tage),
       Letztes Gießen vor 2 Tagen
WHEN: Celery-Task `generate_watering_tasks` läuft
THEN:
  - WateringScheduleEngine.is_watering_due → False (2 < 3 Tage)
  - Kein Task erzeugt
NEXT DAY: Celery-Task läuft erneut (3 Tage seit letztem Gießen)
  - WateringScheduleEngine.is_watering_due → True
  - Task wird erzeugt
```

<!-- Quelle: Cannabis Indoor Grower Review W-006 -->
**Szenario 11: Task-Timer bei Nährlösung-Mischvorgang**
```
GIVEN: Workflow "Nährlösung-Wechsel" mit Task "CalMag einrühren"
       TaskTemplate hat timer_duration_seconds=120, timer_label="Umrühren"
WHEN: Workflow wird instanziiert und Task generiert
THEN:
  - Task-Instanz hat timer_duration_seconds=120, timer_label="Umrühren"
  - Beim Starten des Tasks (pending → in_progress): UI zeigt 2-min-Countdown
  - Nutzer kann Timer starten/pausieren/zurücksetzen
  - Bei Ablauf: akustisches Signal (Ton) + Vibration (mobil)
  - Task kann vor, während oder nach Timer-Ablauf als 'completed' markiert werden
  - actual_duration_minutes wird unabhängig vom Timer erfasst
```

**Szenario 12: Ad-hoc-Timer ohne Template-Vorgabe**
```
GIVEN: Manuell erstellter Task "Foliar-Spray auftragen" ohne timer_duration_seconds
WHEN: Nutzer startet den Task und wählt "Timer starten" → gibt 30 min ein
THEN:
  - timer_duration_seconds=1800 wird auf Task-Instanz gespeichert
  - Countdown läuft im Frontend (30:00 → 00:00)
  - Benachrichtigung bei Ablauf
  - Bei App-Neustart: Timer-Zustand ist verloren (kein Server-State)
```

<!-- Quelle: Cannabis Indoor Grower Review G-004 -->
**Szenario 13: Autoflower-Guard verhindert Topping**
```
GIVEN: Cannabis-Pflanze, Cultivar "Auto Northern Lights" mit flowering_type='autoflower'
       Pflanze in vegetativer Phase, 4 Nodes entwickelt
WHEN: Nutzer versucht "Topping" Task zu erstellen
THEN:
  - AutoflowerGuard.check('topping', 'autoflower') → False
  - Warnung: "HST nicht empfohlen bei Autoflower-Sorten. Autoflower haben
    eine fixe Lebenszeit; Stress-Recovery reduziert die produktive
    Wachstumsphase überproportional."
  - Severity: 'warning', can_override: true
  - Vorgeschlagene Alternativen: ['lst_bend', 'lst_tie', 'defoliation', 'scrog_tuck']
  - UI: "Trotzdem fortfahren" Button für erfahrene Grower
```

**Szenario 14: LST bei Autoflower erlaubt**
```
GIVEN: Cannabis-Pflanze, Cultivar "Auto Gorilla Glue" mit flowering_type='autoflower'
WHEN: Nutzer erstellt "LST Bend" Task
THEN:
  - AutoflowerGuard.check('lst_bend', 'autoflower') → True
  - Message: "lst_bend ist Low-Stress und für Autoflower geeignet."
  - Task wird ohne Warnung erstellt
```

**Szenario 15: Recovery-Timer nach Topping**
```
GIVEN: Cannabis-Pflanze (photoperiod), Topping durchgeführt am 01.03.2026
       TrainingEvent erstellt: event_type='topping', recovery_days=7,
       recovery_end_date=08.03.2026
WHEN: Nutzer öffnet Pflanzen-Detail am 03.03.2026
THEN:
  - Recovery-Timer angezeigt: "Tag 2/7 Erholung nach Topping"
  - Fortschrittsbalken: 28.6%
  - Geplantes nächstes Training erst ab 08.03.2026 möglich ohne Warnung
```

**Szenario 16: Recovery-Überlappungswarnung**
```
GIVEN: Topping am 01.03.2026, recovery_end_date=08.03.2026
       Nutzer plant Supercropping für 05.03.2026
WHEN: RecoveryTimerChecker.check_overlap() aufgerufen
THEN:
  - Warnung: "Erholungsphase nach topping (am 2026-03-01) endet am 2026-03-08.
    Geplantes supercrop liegt 3 Tage vor Ablauf.
    Aktueller Status: Tag 4/7 Erholung nach topping"
  - can_override: true
  - UI: Warnung mit "Trotzdem fortfahren" Option
```

**Szenario 17: Canopy-Evenness-Score und SCROG-Füllgrad**
```
GIVEN: Cannabis-Pflanze mit SCROG-Netz, 6 Haupttriebe,
       Canopy-Höhen: Min 28 cm, Max 35 cm
       Netz belegt: 65% der Fläche
WHEN: CanopyMeasurement erstellt
THEN:
  - canopy_height_avg_cm: 31.5
  - canopy_evenness_score: 0.8 (1.0 - 7/35)
  - scrog_fill_percentage: 65
  - Score 0.8 > 0.7: keine Intervention nötig
  - SCROG-Füllgrad 65 < 80: Hinweis "SCROG-Netz noch nicht bereit für Blüte-Switch,
    Ziel: 80-95% Füllgrad"
```

**Szenario 18: Mainlining-Workflow als Training-Plan**
```
GIVEN: Cannabis-Pflanze (photoperiod), 4 Nodes entwickelt
WHEN: Workflow "Mainlining/Manifolding" instanziiert
THEN:
  - Tasks generiert (mit strikten Dependencies):
    1. "Erstes Topping an Node 3" (requires_photo=true, stress_level='high')
    2. "Recovery prüfen" (7 Tage nach Task 1, category='observation')
    3. "Canopy-Höhe messen" (category='observation')
    4. "Zweites Topping — symmetrisch 4 Triebe" (abhängig von Task 2)
    5. "Recovery prüfen" (7 Tage nach Task 4)
    6. "Drittes Topping — 8 Haupttriebe" (abhängig von Task 5)
    7. "Canopy-Evenness messen" (abhängig von Task 6)
  - Jede Topping-Task erzeugt bei Completion ein TrainingEvent
  - TrainingEvent.affected_nodes = [3] bei Task 1
  - Jede Recovery-Prüfung referenziert das auslösende TrainingEvent
```

<!-- Quelle: Outdoor-Garden-Planner Review G-005 -->
**Szenario 19: Seasonal-Month-Trigger generiert Oktober-Tasks**
```
GIVEN: Nutzer hat 12-Monats-Gartenkalender-Template aktiviert
       Site "Gemüsegarten" mit climate_zone USDA 7b
       Heutiges Datum: 01.10.2026
WHEN: System prüft seasonal_month-Tasks für Oktober (trigger_month=10)
THEN:
  - Tasks generiert (Kategorie 'seasonal'):
    1. "Winterschutz-Checklist durchgehen" (priority: high)
    2. "Dahlien-Knollen ausgraben und einlagern"
    3. "Kübelpflanzen ins Winterquartier räumen"
  - Alle Tasks haben due_date im Oktober 2026
  - Tasks erhalten has_task-Edges zu betroffenen PlantInstances
  - Überwinterungs-Checklist referenziert OverwinteringProfile (REQ-022) pro Pflanze
```

**Szenario 20: Phänologischer Trigger — Forsythienblüte löst Rosenschnitt aus**
```
GIVEN: Nutzer hat Rosen-Jahrespflege-Workflow aktiviert
       TaskTemplate "Frühjahrsschnitt Rosen" mit:
         trigger_type='phenological', phenological_event='forsythia_bloom'
WHEN: Nutzer dokumentiert PhenologicalEvent:
        event_type='forsythia_bloom', observed_date=2026-03-15,
        photo_ref='img/forsythia_2026.jpg'
THEN:
  - System erkennt Ereignis und sucht verknüpfte TaskTemplates
  - Task "Frühjahrsschnitt Rosen" wird generiert:
    category: 'phenological'
    due_date: 2026-03-15 (= observed_date)
    priority: 'high'
    instruction: "Rosen auf 3-5 Augen zurückschneiden, Totholz entfernen..."
  - triggered_by_phenology-Edge: Task → PhenologicalEvent
  - Notification: "Forsythienblüte beobachtet — Rosenschnitt fällig!"
```

**Szenario 21: 12-Monats-Gartenkalender-Instanziierung**
```
GIVEN: Nutzer aktiviert "12-Monats-Gartenkalender (Mitteleuropa)" für Jahr 2026
       Site hat climate_zone USDA 8a (Rheingraben, mild)
WHEN: Workflow wird für das Jahr instanziiert
THEN:
  - 12 Monats-Gruppen mit je 2-4 Tasks erzeugt (ca. 30-40 Tasks gesamt)
  - März-Tasks haben Dual-Trigger: seasonal_month=3 UND phenological=forsythia_bloom
  - Regionale Anpassung: Voranzucht (Feb) startet 2 Wochen früher als Standard
  - Alle Tasks haben category='seasonal' oder 'phenological'
  - WorkflowExecution trackt Fortschritt über das gesamte Jahr
```

**Szenario 22: Sukzessions-Aussaat als Recurring-Template**
```
GIVEN: Nutzer konfiguriert "Sukzessions-Aussaat Salat"
       interval: 3 Wochen, Zeitraum: April bis August
WHEN: Recurring-Template instanziiert
THEN:
  - Tasks generiert: 01.04, 22.04, 13.05, 03.06, 24.06, 15.07, 05.08, 26.08
  - Jeder Task: category='seasonal', priority='medium'
  - Instruction: "Salat nachsäen — Sorten abwechseln für kontinuierliche Ernte"
  - Tasks nur für konfigurierte Species generiert
```

<!-- Quelle: Einzelaufgaben-Pflege v3.0 -->
**Szenario 23: Task-Klonen mit Pflanzenwechsel**
```
GIVEN: Task "Topping an Node 5" für Pflanze "Cannabis #1"
       Status: completed, mit Foto-Referenzen und Completion-Notes
WHEN: Nutzer klickt "Task klonen" mit target_plant_key="Cannabis #2"
THEN:
  - Neuer Task erzeugt:
    name: "Topping an Node 5" (identisch)
    instruction: identisch
    category: training
    plant_key: "Cannabis #2" (neue Pflanze)
    status: pending
    due_date: null
    photo_refs: [] (leer)
    completion_notes: null
    tags: [] (kopiert von Original, falls vorhanden)
    checklist: kopiert von Original (alle done=false)
  - cloned_from-Edge zum Original-Task
  - TaskAuditEntry: action='cloned', new_value='original_task_key'
```

**Szenario 24: Wiederkehrende Aufgabe (Recurring Task)**
```
GIVEN: Task "Orchidee tauchen" mit recurrence_rule="0 8 * * 6"
       (jeden Samstag 08:00), recurrence_end_date=null
WHEN: Nutzer markiert Task als completed
THEN:
  - Task.status = 'completed', completed_at = jetzt
  - System erzeugt automatisch nächste Instanz:
    name: "Orchidee tauchen"
    due_date: nächster Samstag
    scheduled_time: 08:00
    status: pending
    parent_recurring_task_key: key des abgeschlossenen Tasks
    recurrence_rule: "0 8 * * 6" (propagiert)
  - recurs_from-Edge zum Eltern-Task
```

**Szenario 25: Task-Kommentare im Team**
```
GIVEN: Task "Rosenschnitt" im Gemeinschaftsgarten "Gartenfreunde"
       Assigned to: user "Maria"
WHEN: User "Klaus" (Admin) fügt Kommentar hinzu:
      "Bitte die kranken Triebe besonders beachten — sah letzte Woche nach Sternrußtau aus"
THEN:
  - TaskComment erstellt: comment_text, created_by='klaus', created_at=jetzt
  - has_comment-Edge: Task → Comment
  - written_by-Edge: Comment → User 'klaus'
  - TaskAuditEntry: action='commented'
  - Maria sieht den Kommentar auf der Task-Detail-Seite
```

**Szenario 26: Task-Wiedereröffnung**
```
GIVEN: Task "pH-Wert prüfen" mit status='completed', completed_at=gestern
       Nutzer stellt fest, dass die Messung fehlerhaft war
WHEN: Nutzer klickt "Wiedereröffnen"
THEN:
  - status: completed → pending
  - completed_at: null
  - actual_duration_minutes: null
  - completion_notes: null (zurückgesetzt)
  - reopened_at: jetzt
  - reopened_from_status: 'completed'
  - photo_refs: beibehalten (Fotos nicht gelöscht)
  - tags: beibehalten
  - checklist: beibehalten (items bleiben done/undone)
  - TaskAuditEntry: action='reopened', old_value='completed', new_value='pending'
```

**Szenario 27: Batch-Status-Änderung**
```
GIVEN: 5 Tasks mit status='pending' in der Task-Queue
       Nutzer wählt 3 davon aus
WHEN: Nutzer klickt "Alle abschließen" (Batch-Complete)
THEN:
  - POST /tasks/batch/status mit task_keys=[key1, key2, key3], action='complete'
  - Alle 3 Tasks: status=completed, completed_at=jetzt
  - Je ein TaskAuditEntry pro Task: action='status_changed'
  - Response: { success: 3, failed: 0, errors: [] }

GIVEN: 1 der 3 Tasks hat requires_photo=true und keine photo_refs
THEN:
  - Response: { success: 2, failed: 1, errors: [{ key: key2, reason: "Foto erforderlich" }] }
  - Rollback: Nur die 2 erfolgreichen werden committed
```

**Szenario 28: Phasengebundener Workflow mit Dormant-Tasks**
```
GIVEN: Cannabis-Pflanze in Phase "vegetative"
       Workflow "SCROG-Workflow" wird instanziiert mit Tasks:
         Task A: trigger_phase='vegetative', days_offset=14 → "Topping"
         Task B: trigger_phase='vegetative', days_offset=21 → "SCROG-Netz montieren"
         Task C: trigger_phase='flowering', phase_entry → "Lollipopping"
         Task D: trigger_phase='flowering', days_offset=7 → "SCROG-Füllgrad prüfen"
         Task E: trigger_phase='harvest', phase_entry → "Ernte"
WHEN: Workflow instanziiert
THEN:
  - Task A: status='pending', due_date=heute+14d (vegetative Phase aktiv)
  - Task B: status='pending', due_date=heute+21d
  - Task C: status='dormant' (flowering Phase noch nicht erreicht)
  - Task D: status='dormant'
  - Task E: status='dormant'
  - UI zeigt: "Phase Vegetativ: 2 Tasks | Phase Blüte: 2 geplant | Ernte: 1 geplant"

WHEN: Pflanze wechselt zu Phase "flowering"
THEN:
  - activate_dormant_tasks_for_phase(plant_key, 'flowering') wird aufgerufen
  - Task C: status dormant → pending, due_date=Phasenwechsel-Datum
  - Task D: status dormant → pending, due_date=Phasenwechsel-Datum + 7d
  - Task E: bleibt dormant (harvest Phase noch nicht erreicht)
  - Notification: "2 neue Aufgaben für Blüte-Phase aktiviert"
```

**Szenario 29: Individuelle Anpassung instanziierter Workflow-Tasks**
```
GIVEN: Workflow "Tomaten Multi-Stem" instanziiert mit 6 Tasks
       Task "Ausgeizen" hat trigger_phase='vegetative', due_date=übermorgen
WHEN: Nutzer bearbeitet die Task-Instanz:
       - Name ändern: "Ausgeizen + Stütze anbringen"
       - Checkliste hinzufügen: ["Geiztriebe entfernen", "Stab einsetzen", "Pflanze anbinden"]
       - Tags hinzufügen: ["hochbeet-nord", "stab-nötig"]
       - due_date verschieben auf nächste Woche
THEN:
  - Task-Instanz wird aktualisiert (Template bleibt unverändert!)
  - TaskAuditEntry: action='updated', field='name', old_value='Ausgeizen', new_value='Ausgeizen + Stütze anbringen'
  - Weitere AuditEntries für checklist, tags, due_date
  - Workflow-Progress bleibt korrekt (Task gehört weiterhin zur Execution)
```

**Szenario 30: Task mit Checkliste und Pflicht-Prüfung**
```
GIVEN: TaskTemplate "Nährlösung-Wechsel" mit:
       require_all_checklist_items: true
       default_checklist: [
         { text: "Altes Reservoir leeren", order: 0 },
         { text: "Reservoir reinigen", order: 1 },
         { text: "Frische Lösung ansetzen", order: 2 },
         { text: "pH messen und korrigieren", order: 3 },
         { text: "EC messen und dokumentieren", order: 4 }
       ]
WHEN: Workflow instanziiert → Task erhält Kopie der Checkliste
       Nutzer erledigt 3 von 5 Schritten und versucht Task abzuschließen
THEN:
  - Validierung: require_all_checklist_items=true, aber nur 3/5 done
  - Error: "Alle Checklist-Einträge müssen erledigt sein (3/5 abgehakt)"
  - Task bleibt in_progress
  - Nutzer kann Checklist-Items nachhaken und erneut abschließen
```

**Szenario 31: Zusätzliche Tasks zu laufendem Workflow hinzufügen**
```
GIVEN: Laufende Workflow-Execution "Cannabis Mainlining" mit 7 Tasks
       Nutzer merkt, dass ein zusätzlicher LST-Schritt nötig ist
WHEN: POST /workflows/executions/{key}/tasks mit:
       { name: "LST Biegen — Seitentrieb links", category: "training",
         trigger_phase: "vegetative", due_date: "2026-03-20",
         checklist: [{ text: "Trieb sanft biegen", order: 0 }, { text: "Mit Draht fixieren", order: 1 }] }
THEN:
  - Neuer Task erstellt und der Workflow-Execution zugeordnet
  - generated-Edge: Execution → neuer Task
  - has_task-Edge: Plant → neuer Task
  - Workflow-Progress aktualisiert: completion_percentage neu berechnet (z.B. 4/8 statt 4/7)
  - Neuer Task erscheint in der Phase-Timeline an korrekter Position
```

---

**Hinweise für RAG-Integration:**
- Keywords: Workflow, Task, HST, Training, Topping, LST, Dependency, Scheduling, Template, Ausgeizen, Observation, Zimmerpflanzen, Hydroponik-Wartung, GDD-Trigger, Outdoor, Frostschutz, Abhärtung, Überwinterung, Umtopf, Vermehrung, Mondkalender, Gießplan, generate_watering_tasks, Celery-Beat, planting_run_key, watering_event_key, WateringSchedule, Gießplan-Task, Task-Timer, Countdown, timer_duration_seconds, timer_label, Mischvorgang, Einwirkzeit, Burping, Training-Plan, Canopy-Management, TrainingEvent, CanopyMeasurement, Recovery-Timer, Autoflower-Guard, SCROG-Füllgrad, Canopy-Evenness-Score, Mainlining-Workflow, Defoliation-Schedule, Gartenkalender, Seasonal-Month, Phenological, PhenologicalEvent, Forsythienblüte, Holunderblüte, Apfelblüte, Zeigerpflanze, Beetvorbereitung, Gründüngung, Sukzessions-Aussaat, Staudenteilung, Überwinterungs-Checklist, Auswinterung, Rosen-Jahrespflege, Tags, Checkliste, ChecklistItem, Subtasks, Bewertung, difficulty_rating, quality_rating, Recurring, Wiederholung, recurrence_rule, Cron, Task-Klonen, Task-Wiedereröffnung, Reopen, Batch-Operationen, Task-Kommentare, TaskComment, TaskAuditEntry, Änderungshistorie, Audit-Trail, Dormant, Phasengebundene-Tasks, activate_dormant_tasks, Phase-Transition-Hook, User-Zuweisung, assigned_to_user_key, Workflow-Task-Anpassung, trigger_phase_override, scheduled_time
- Fachbegriffe: Auxin-Dominanz, Hermaphroditismus, Mainlining, Lollipopping, SOG, SCROG, Supercropping, Karenzzeit, PHI, Kumulativer Stress, Jasmonsäure, Ethylen, Stretch-Phase, Early Flowering, Geiztrieb, Assimilat-Verteilung, Phototoxizität, Transpiration, cultivar_timing_factor, Dormanz, Akklimatisierung, Canopy-Gleichmäßigkeit, Recovery-Phase, Autoflower, Manifolding, SCROG-Tucking, Netz-Höhe, Netz-Füllgrad, Phänologie, Phänologische Jahreszeiten, Vorfrühling, Erstfrühling, Vollfrühling, Frühsommer, Hochsommer, Sukzessions-Anbau, Gründüngung, Bodenlebewesen, Eisheilige, Starkzehrer, Schwachzehrer
- Verknüpfung: Zentral für REQ-001 (cultivar_timing_factor + Cultivar.flowering_type für Autoflower-Guard + sowing_indoor_weeks_before_last_frost + frost_sensitivity), REQ-002 (climate_zone für regionale Kalender-Anpassung), REQ-003 (Phasen-Trigger + GDD + **Phase-Transition-Hook für Dormant-Aktivierung v3.0**), REQ-005 (canopy_height als Sensorwert), REQ-007 (Harvest-Tasks), REQ-010 (IPM-Tasks + Karenzzeit), REQ-013 (PlantInstance für TrainingEvent/CanopyMeasurement + clone_from_run_key für Sukzession), REQ-018 (Aktor-Verknüpfung), REQ-014 (Hydroponik-Wartung), REQ-019 (Substrat-spezifische Post-HST-Bewässerung), REQ-022 (OverwinteringProfile für Überwinterungs-Checklist), REQ-024 (**User-Zuweisung + Membership-Validierung v3.0**)
- Pflanzenwissenschaft: Stress-Physiologie, Hormon-Regulation, Recovery-Zeiten, artspezifische Metabolismus-Geschwindigkeit, Tageszeit-Einfluss auf Pflanzenphysiologie, Temperatur-Recovery-Modifikation, Dormanz-Management, Abhärtungs-Physiologie
- Software-Engineering (v3.0): CRUD+, Batch-Operationen, Audit-Trail, Recurring-Pattern (Cron), Dormant-State-Machine, Phase-Transition-Hook, One-Way-Template-Instantiation, Checklist-Embedding, Tag-basierte Filterung, User-Assignment, Task-Cloning, Reopen-Semantik
