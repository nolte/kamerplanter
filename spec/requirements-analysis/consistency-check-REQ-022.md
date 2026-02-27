# Konsistenzpruefung: REQ-022 (Pflegeerinnerungen) gegen referenzierte Anforderungen

**Erstellt:** 2026-02-27
**Analysierte Dokumente:** 10 (REQ-022, REQ-006, REQ-001, REQ-003, REQ-020, REQ-021, REQ-014, NFR-001, NFR-003, NFR-006, NFR-010)
**Analysierte Anforderungen:** ~45 funktionale, ~30 non-funktionale
**Widersprueche/Inkonsistenzen gesamt:** 9

---

## Executive Summary

REQ-022 ist insgesamt gut strukturiert und integriert sich weitgehend konsistent in die bestehende Spezifikationslandschaft. Es gibt jedoch **3 mittlere und 6 niedrige Inkonsistenzen**, die vor der Implementierung geklaert werden sollten. Die kritischsten Probleme betreffen: (1) die `category`-Erweiterung des Task-Modells in REQ-006, die dort explizit als Literal definiert ist und `care_reminder` nicht enthaelt, (2) das Dormanz-Phasen-Mapping, bei dem REQ-022 Phasennamen referenziert, die in REQ-003 nicht alle definiert sind, und (3) das `growth_habit`-Mapping, das einen Wert `succulent` referenziert, der in REQ-001 nicht existiert.

**Keine kritischen Widersprueche gefunden.** Alle gefundenen Inkonsistenzen sind durch Ergaenzungen oder Praezisierungen loesbar, ohne architektonische Aenderungen.

---

## 1. REQ-006 (Aufgabenplanung) -- Task-Modell-Kompatibilitaet

### W-001: `category: 'care_reminder'` nicht im REQ-006 Literal definiert

**Schweregrad:** MITTEL
**Typ:** Scope-Widerspruch

**Betroffene Anforderungen:**
- REQ-022, Zeile ~80: `category: 'care_reminder'` (neue Task-Kategorie, ergaenzt die bestehende Liste in REQ-006)
- REQ-006, Zeile ~55-65: Task-Kategorien definiert als: Training, Pruning, Ausgeizen, Transplanting, Feeding, IPM, Harvest, Observation, Maintenance
- REQ-006, Zeile ~555: TaskTemplate Pydantic-Modell: `category: Literal['training', 'pruning', 'transplant', 'feeding', 'ipm', 'harvest', 'maintenance']`
- REQ-006, Zeile ~131: `:Task` Node: `category: str` (untypisiert, freier String)

**Konflikt:**
REQ-022 fuehrt `care_reminder` als neue Task-Kategorie ein. In REQ-006 gibt es eine Diskrepanz: Die `:Task`-Node definiert `category` als freien `str`, waehrend die `:TaskTemplate`-Node ein geschlossenes `Literal[...]` verwendet. Ausserdem fehlen in der TaskTemplate-Literal-Definition die Kategorien `observation` und `ausgeizen`, die in der textuellen Beschreibung von REQ-006 genannt werden.

REQ-022 sagt korrekt, dass `care_reminder` die "bestehende Liste ergaenzt" -- aber REQ-006 selbst muesste aktualisiert werden, um diesen Wert in den Literal-Typ aufzunehmen. Andernfalls koennten care_reminder-Tasks nicht aus TaskTemplates generiert werden.

**Auswirkung:** Implementierung ist moeglich (da `:Task.category` ein freier `str` ist), aber TaskTemplate-Erstellung fuer care_reminder wuerde mit dem Literal-Constraint kollidieren.

**Loesungsoptionen:**
1. REQ-006 `TaskTemplate.category` Literal um `'care_reminder'` erweitern
2. REQ-006 `TaskTemplate.category` auf `str` aendern (wie `:Task`)
3. REQ-022 care_reminder-Tasks ohne TaskTemplate erstellen (nur direkte Task-Instanzen) -- das ist vermutlich die beabsichtigte Variante, da REQ-022 keinen eigenen TaskTemplate definiert

**Empfehlung:** Option 3 ist wahrscheinlich beabsichtigt (REQ-022 erstellt Tasks direkt, nicht ueber TaskTemplates). Dies sollte explizit dokumentiert werden.

### W-002: `skill_level` und `stress_level` auf Task vs. TaskTemplate

**Schweregrad:** NIEDRIG
**Typ:** Redaktionelle Inkonsistenz

**Betroffene Anforderungen:**
- REQ-022, Zeile ~81-83: `skill_level: 'beginner'`, `stress_level: 'none'` als Properties der Task-Instanzen
- REQ-006, Zeile ~117-121: `skill_level` und `stress_level` sind auf `:TaskTemplate` definiert, NICHT auf `:Task`

**Konflikt:**
REQ-022 referenziert `skill_level` und `stress_level` als Properties, die auf den Task-Instanzen gesetzt werden. In REQ-006 existieren diese Felder aber nur auf `:TaskTemplate`, nicht auf `:Task`. Die `:Task`-Node hat `category`, `priority`, `status`, `due_date` etc., aber weder `skill_level` noch `stress_level`.

**Auswirkung:** Bei der Implementierung muesste entweder das `:Task`-Modell erweitert oder die Felder ueber die `instance_of`-Edge vom TaskTemplate geerbt werden.

**Loesungsoptionen:**
1. `:Task`-Node um `skill_level` und `stress_level` erweitern (da REQ-022 Tasks ohne Template erstellt, ist das noetig)
2. REQ-022 verzichtet auf diese Felder auf Task-Ebene und nutzt stattdessen `priority`-Mapping

### W-003: `priority`-Werte -- REQ-022 nutzt `high`/`medium`/`low`, REQ-006 hat auch `critical`

**Schweregrad:** NIEDRIG
**Typ:** Kompatibel, aber unvollstaendig

**Betroffene Anforderungen:**
- REQ-022, Zeile ~57-62: Prioritaeten `high`, `medium`, `low`
- REQ-006, Zeile ~135: `priority: Literal['low', 'medium', 'high', 'critical']`

**Konflikt:** Kein echter Widerspruch -- REQ-022 nutzt eine Teilmenge der REQ-006-Prioritaeten. Die Frage ist, ob ueberfaellige Giess-Erinnerungen `critical` statt `high` werden sollten.

**Empfehlung:** Konsistent, keine Aenderung noetig. Optional: Stark ueberfaellige Erinnerungen (>3 Tage) koennten `critical` nutzen.

### W-004: `status`-Wert `completed` -- REQ-022 setzt implizit, kompatibel mit REQ-006

**Schweregrad:** NIEDRIG (kompatibel)

REQ-022 Zeile ~678: "Markiere zugehoerigen Task als `completed`" -- das passt zu REQ-006 `status: Literal['pending', 'in_progress', 'completed', 'skipped', 'failed']`. Kein Widerspruch.

---

## 2. REQ-001 (Stammdaten) -- Species, RequirementProfile, growth_habit

### W-005: `growth_habit: 'succulent'` existiert nicht in REQ-001

**Schweregrad:** MITTEL
**Typ:** Referenz auf nicht-existierenden Wert

**Betroffene Anforderungen:**
- REQ-022, Zeile ~660: Mapping `growth_habit → care_style`: "Species mit growth_habit 'succulent' → 'succulent'"
- REQ-001, Zeile ~42: `growth_habit: Literal['herb', 'shrub', 'tree', 'vine', 'groundcover']`
- REQ-001, Zeile ~570-575: `GrowthHabit` Enum: `HERB`, `SHRUB`, `TREE`, `VINE`, `GROUNDCOVER`

**Konflikt:**
REQ-022 referenziert `growth_habit: 'succulent'` im care_style-Mapping. Dieser Wert existiert nicht in der REQ-001 `GrowthHabit`-Enum. Sukkulenten wie Echeveria oder Aloe wuerden in REQ-001 als `herb` (krautig) oder `shrub` (strauchig) klassifiziert, nicht als `succulent`.

**Auswirkung:** Das automatische CareProfile-Mapping (`growth_habit → care_style`) wuerde fuer Sukkulenten nie den Style `succulent` waehlen, da der growth_habit-Wert nicht existiert. Der Fallback waere `tropical`.

**Loesungsoptionen:**
1. REQ-001 `GrowthHabit`-Enum um `SUCCULENT` erweitern
2. REQ-022 Mapping aendern: Sukkulenten-Erkennung ueber `native_habitat` oder `common_names` (wie bereits fuer Orchideen und Calatheen beschrieben)
3. REQ-022 Mapping praezisieren: Kaktus/Sukkulenten-Erkennung ueber BotanicalFamily (Cactaceae, Crassulaceae, Aizoaceae etc.)

**Empfehlung:** Option 2 oder 3 -- das Mapping sollte nicht auf einem nicht-existierenden GrowthHabit-Wert basieren. Eine Familie-basierte Erkennung (Option 3) waere botanisch am praezisesten.

### W-006: `RequirementProfile` wird referenziert, ist aber in REQ-003 definiert, nicht REQ-001

**Schweregrad:** NIEDRIG
**Typ:** Redaktionelle Inkonsistenz

**Betroffene Anforderungen:**
- REQ-022, Zeile ~33: "via `RequirementProfile` und `care_style`-Preset"
- REQ-022, Abhaengigkeiten, Zeile ~1072: "REQ-001 | Liest | Species + RequirementProfile"
- REQ-003, Zeile ~52-53: `requirement_profiles` Collection definiert
- REQ-003, Zeile ~113: Edge `requires_profile: growth_phases -> requirement_profiles`

**Konflikt:**
REQ-022 listet `RequirementProfile` als Abhaengigkeit von REQ-001. Tatsaechlich ist `RequirementProfile` in REQ-003 (Phasensteuerung) definiert, nicht in REQ-001. REQ-001 definiert Species und LifecycleConfig.

**Empfehlung:** Abhaengigkeitstabelle korrigieren: REQ-003 statt REQ-001 fuer RequirementProfile referenzieren, oder beide REQs auflisten.

---

## 3. REQ-003 (Phasensteuerung) -- Dormanz-Phasen

### W-007: Dormanz-Phasen-Namen teilweise inkonsistent mit REQ-003

**Schweregrad:** MITTEL
**Typ:** Impliziter Widerspruch (Referenz auf nicht-definierte Werte)

**Betroffene Anforderungen:**
- REQ-022, Zeile ~67-68: `DORMANCY_PHASES = frozenset(['dormancy', 'dormant', 'senescence', 'hardening_off'])`
- REQ-003, Zeile ~872-873: `PhaseType = Literal['seedling', 'vegetative', 'flowering', 'ripening', 'dormancy', 'flushing', 'bud_break', 'fruit_development', 'senescence']`
- REQ-020, Zeile ~287-290: Zimmerpflanzen-Phasen: `acclimatization`, `active_growth`, `maintenance`, `repotting_recovery`

**Konflikte im Detail:**

| Phase in REQ-022 DORMANCY_PHASES | In REQ-003 PhaseType? | In REQ-020 Zimmerpflanzen-Phasen? | Status |
|---|---|---|---|
| `dormancy` | Ja | Nein | OK |
| `dormant` | NEIN | Nein | INKONSISTENT -- vermutlich Synonym fuer `dormancy`, aber nicht definiert |
| `senescence` | Ja | Nein | OK |
| `hardening_off` | NEIN | Nein | INKONSISTENT -- nicht in REQ-003 PhaseType |

Zusaetzlich: REQ-020 definiert `maintenance` als Winterphase fuer Zimmerpflanzen ("Erhaltungspflege / Winter-Verlangsamung. Weniger giessen, nicht duengen"). Diese Phase fehlt in den DORMANCY_PHASES von REQ-022, obwohl die REQ-020-Beschreibung explizit "nicht duengen" angibt.

**Auswirkung:**
1. `dormant` als Phase existiert nirgends -- wenn eine PlantInstance diese Phase haette, wuerde der Duenge-Guard greifen, aber die Phase kann nie gesetzt werden.
2. `hardening_off` ist ebenfalls nicht in REQ-003 definiert. Es wird in REQ-003 im Fliesstext erwaehnt ("Stress-Phasen: Temporaere Zustaende wie Hardening-Off"), aber nicht im PhaseType-Literal.
3. `maintenance` (die Zimmerpflanzen-Winter-Phase aus REQ-020) fehlt in DORMANCY_PHASES, obwohl waehrend `maintenance` nicht geduengt werden soll.

**Loesungsoptionen:**
1. `dormant` aus DORMANCY_PHASES entfernen (Duplikat von `dormancy`)
2. `hardening_off` entweder in REQ-003 PhaseType aufnehmen oder aus DORMANCY_PHASES entfernen
3. `maintenance` (aus REQ-020 Zimmerpflanzen-Phasen) zu DORMANCY_PHASES hinzufuegen
4. REQ-003 PhaseType-Literal um `maintenance`, `acclimatization`, `active_growth`, `repotting_recovery` erweitern (Zimmerpflanzen-Phasen)

**Empfehlung:** Kombination aus Option 1, 3 und 4. Die Zimmerpflanzen-Phasen aus REQ-020 muessen in REQ-003 als offizielle PhaseType-Werte aufgenommen werden. Die DORMANCY_PHASES in REQ-022 sollten `maintenance` einschliessen und `dormant` entfernen.

---

## 4. REQ-020 (Onboarding) -- UserPreference

### W-008: Keine direkte Inkonsistenz, aber fehlende Zimmerpflanzen-Phasen-Integration

**Schweregrad:** NIEDRIG
**Typ:** Luecke / fehlende Verknuepfung

**Betroffene Anforderungen:**
- REQ-022, Abhaengigkeiten, Zeile ~1074: "REQ-020 | Liest | Zimmerpflanzen-Phasen + UserPreference fuer Erfahrungsstufe"
- REQ-020, Zeile ~77-82: `UserPreference` mit `experience_level: Literal['beginner', 'intermediate', 'expert']`

**Befund:**
REQ-022 referenziert `UserPreference` korrekt. Die `experience_level`-Werte (`beginner`, `intermediate`, `expert`) stimmen zwischen REQ-020 und REQ-022 ueberein. Die Referenz auf "Zimmerpflanzen-Phasen" aus REQ-020 (Zeile 282-290) ist ebenfalls korrekt.

Allerdings nutzt REQ-022 die `experience_level` nicht direkt -- die Abhangigkeit besteht nur indirekt ueber REQ-021 (Navigations-Tiering). Die Abhaengigkeitstabelle koennte praeziser sein.

**Empfehlung:** Klarstellen, ob REQ-022 die UserPreference direkt liest oder nur indirekt ueber REQ-021.

---

## 5. REQ-021 (UI-Erfahrungsstufen) -- Navigations-Integration und Pflegekarte

### Navigations-Integration: KONSISTENT

REQ-022, Zeile ~1019-1027 definiert die Navigations-Integration:
- Einsteiger: "Pflege" an Position 3
- Fortgeschritten: "Pflege" an Position 3
- Experte: "Pflege & Erinnerungen" an Position 6

REQ-021, Zeile ~141-174 definiert die Navigations-Tiers:
- Einsteiger (5 Punkte): Dashboard, Meine Pflanzen, Aufgaben, Kalender, Einstellungen
- Fortgeschritten (8 Punkte): + Standorte, Duengung, Stammdaten
- Experte (alle): 15 Punkte

**Befund:** REQ-022 fuegt "Pflege" als neuen Menuepunkt hinzu. Im Einsteiger-Modus wuerde das die Anzahl von 5 auf 6 erhoehen (oder "Aufgaben" ersetzen). Im Fortgeschrittenen-Modus von 8 auf 9. Dies ist kein Widerspruch, sondern eine Erweiterung -- aber die konkreten Zahlen in REQ-021 (5/8/alle) sollten aktualisiert werden.

### Pflegekarte-Erweiterung: KONSISTENT

REQ-022, Zeile ~898-906 beschreibt die Integration mit der Einsteiger-Pflegekarte (REQ-021 Sektion 3.5). Die referenzierten Datenquellen (`CareDashboardEntry`, `CareConfirmation`, `CareProfile.care_style`) sind alle in REQ-022 definiert und passen zur Pflegekarten-Spezifikation in REQ-021.

---

## 6. REQ-014 (Tankmanagement) -- Celery-Beat-Pattern

### Celery-Beat: KONSISTENT

**Betroffene Anforderungen:**
- REQ-022, Zeile ~755-761: Celery-Beat mit `crontab(hour=6, minute=0)`
- REQ-014, Zeile ~1552-1554: Celery-Tasks `check_maintenance_due` (taeglich) und `check_tank_alerts` (stuendlich)

**Befund:** Das Pattern ist konsistent:
- REQ-014 nutzt taegliche Celery-Beat-Tasks fuer Wartungspruefungen (`check_maintenance_due`)
- REQ-022 nutzt einen taeglichen Celery-Beat-Task fuer Erinnerungsgenerierung (`care_reminders.generate_due`)
- Beide verwenden das `shared_task`-Pattern und `crontab`-Scheduling
- Beide folgen dem Idempotenz-Prinzip (Duplikat-Pruefung vor Task-Erstellung)
- Der Task-Name folgt dem gleichen Benennungsschema (`module.action`)

REQ-014 definiert seine Celery-Tasks allerdings als Key-Value in den Abhaengigkeiten (Zeile 1552-1554), waehrend REQ-022 ein ausfuehrlicheres Code-Beispiel mit `beat_schedule`-Konfiguration zeigt. Beide Ansaetze sind kompatibel.

---

## 7. NFR-Kompatibilitaet

### NFR-001 (5-Layer-Architektur): KONSISTENT

REQ-022 folgt der 5-Layer-Architektur korrekt:
- **API Layer:** Router `/api/v1/care-reminders` (Zeile 828-838)
- **Service Layer:** `CareReminderService` (Zeile 624-726)
- **Engine Layer:** `CareReminderEngine` (Zeile 414-619)
- **Repository Layer:** `CareReminderRepository` (Zeile 764-824)
- **Persistence Layer:** ArangoDB Collections `care_profiles`, `care_confirmations` + Edges

Die Verantwortlichkeiten sind korrekt getrennt: Engine enthaelt Geschaeftslogik (Intervallberechnung, Adaptive Learning), Service orchestriert, Repository abstrahiert den DB-Zugriff.

### NFR-003 (Code-Standard): KONSISTENT

REQ-022 haelt sich an die Konvention: Spezifikation auf Deutsch, Variablennamen/Code auf Englisch (`CareReminderEngine`, `watering_interval_days`, `is_reminder_due`). Die Pydantic-Modelle verwenden snake_case (Python), der Frontend Redux Slice verwendet camelCase (TypeScript).

### NFR-006 (API-Fehlerbehandlung): KONSISTENT

REQ-022, Zeile ~840-846 definiert Fehlerbehandlung mit HTTP-Statuscodes (404, 409, 422), die zum NFR-006 Error-Code-Katalog passen:
- 404 = `ENTITY_NOT_FOUND` (PlantInstance nicht gefunden)
- 409 = `CONFLICT` (kein offener Task zum Bestaetigen)
- 422 = `VALIDATION_ERROR` (ungueltiges Intervall)

### NFR-010 (UI-Pflegemasken): TEILWEISE KONSISTENT

**W-009: CareProfile CRUD-Vollstaendigkeit**

**Schweregrad:** NIEDRIG
**Typ:** Luecke

**Betroffene Anforderungen:**
- REQ-022, Abhaengigkeiten, Zeile ~1080: "NFR-010 | Erweitert | CRUD-Masken fuer CareProfile mit Validierung"
- NFR-010, Abschnitt 2: CRUD-Anforderungen (Create, Read, Update, Delete)

**Befund:**
REQ-022 definiert fuer CareProfile:
- **Create:** Automatisch (get_or_create_profile), kein expliziter Create-Dialog -- OK, da CareProfile auto-generiert wird
- **Read:** GET `/plants/{plant_key}/profile` -- OK
- **Update:** PATCH `/plants/{plant_key}/profile` + CareProfileEditDialog -- OK
- **Delete:** Nicht vorgesehen -- CareProfile ist 1:1 an PlantInstance gebunden

Die fehlende Delete-Operation ist hier sinnvoll (1:1-Beziehung), widerspricht aber der NFR-010-Anforderung "Jede Entitaet MUSS Delete mit Bestaetigung unterstuetzen". Ein `reset-profile`-Endpoint existiert als Ersatz.

Fuer `CareConfirmation` fehlen CRUD-Masken komplett -- allerdings ist CareConfirmation als immutables Event-Log konzipiert (kein Update, kein Delete), was eine bewusste Ausnahme darstellt.

**Empfehlung:** NFR-010 Vollstaendigkeitsmatrix um CareProfile und CareConfirmation ergaenzen mit dokumentierter Begruendung fuer die Ausnahmen.

---

## Zusammenfassung der Inkonsistenzen

| ID | Schweregrad | Typ | Kurztext | Betroffene REQs |
|----|-------------|-----|----------|-----------------|
| W-001 | MITTEL | Scope | `care_reminder` nicht in REQ-006 TaskTemplate Literal | REQ-022, REQ-006 |
| W-002 | NIEDRIG | Redaktionell | `skill_level`/`stress_level` nur auf TaskTemplate, nicht Task | REQ-022, REQ-006 |
| W-003 | NIEDRIG | Kompatibel | `priority: critical` nicht genutzt | REQ-022, REQ-006 |
| W-004 | NIEDRIG | Kompatibel | `status: completed` passt | REQ-022, REQ-006 |
| W-005 | MITTEL | Referenz | `growth_habit: 'succulent'` existiert nicht in REQ-001 | REQ-022, REQ-001 |
| W-006 | NIEDRIG | Redaktionell | RequirementProfile ist in REQ-003, nicht REQ-001 | REQ-022 |
| W-007 | MITTEL | Implizit | Phasennamen `dormant`, `hardening_off` nicht in REQ-003; `maintenance` fehlt | REQ-022, REQ-003, REQ-020 |
| W-008 | NIEDRIG | Luecke | UserPreference-Abhaengigkeit unpraezise | REQ-022, REQ-020 |
| W-009 | NIEDRIG | Luecke | CareProfile/CareConfirmation CRUD-Ausnahmen undokumentiert | REQ-022, NFR-010 |

---

## Empfehlungen

### Sofortiger Klaerungsbedarf (vor Implementierungsstart):

1. **W-005 (growth_habit):** Entscheidung treffen, wie Sukkulenten erkannt werden (neuer Enum-Wert vs. alternatives Mapping). Dies beeinflusst sowohl REQ-001 als auch REQ-022.

2. **W-007 (Dormanz-Phasen):** Die Zimmerpflanzen-Phasen aus REQ-020 (`acclimatization`, `active_growth`, `maintenance`, `repotting_recovery`) muessen in REQ-003 als offizielle PhaseType-Werte aufgenommen werden. Ohne diese Aenderung gibt es keine valide Phase fuer Zimmerpflanzen. Gleichzeitig DORMANCY_PHASES in REQ-022 um `maintenance` erweitern und `dormant` entfernen.

3. **W-001 (care_reminder category):** Klarstellen, dass REQ-022 Tasks direkt erstellt (ohne TaskTemplate), sodass die TaskTemplate Literal-Beschraenkung irrelevant ist. Falls doch TaskTemplates genutzt werden sollen, REQ-006 Literal erweitern.

### Redaktionelle Korrekturen (kann parallel zur Implementierung):

4. W-002: Dokumentieren, ob `skill_level`/`stress_level` auf Task-Ebene propagiert werden
5. W-006: Abhaengigkeitstabelle korrigieren (RequirementProfile → REQ-003)
6. W-008: UserPreference-Abhaengigkeit praezisieren
7. W-009: NFR-010 Vollstaendigkeitsmatrix aktualisieren
