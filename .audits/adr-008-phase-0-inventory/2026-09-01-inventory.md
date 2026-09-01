# ADR-008 Phase 0 — Bestandsaufnahme mit Nachweis

**Datum:** 2026-09-01 · **Issue:** #1061 · **Feature:** F-6
(`project/features/recurrence-propagation-inventory-baseline.md`) ·
**ADR:** `spec/decisions/ADR-008-task-care-notification-consolidation.md` (Status *Proposed*)

ADR-008 nennt seine eigene Annahmebedingung: das ADR wird angenommen, **wenn
diese Bestandsaufnahme vorliegt** und REQ-006/022/030 die Zuständigkeitsgrenzen
übernommen haben. Dieses Dokument liefert die erste Hälfte davon.

Gezählt wird, was **noch nicht** umgezogen ist:

- **(a)** jede Stelle, die einen nächsten Termin **außerhalb** von
  `RecurrenceEngine` berechnet;
- **(b)** jede Stelle, die Notification-Zustand **außerhalb** von
  `NotificationPropagationService` schreibt.

---

## 1. Die Zahlen

Beide Zahlen werden bei jedem Lauf aus dem Baum erhoben und sind **nirgends als
Konstante eingecheckt** (NFR-018 §2.1). Reproduzieren:

```bash
task check:recurrence-boundary        -- --inventory
task check:notification-write-boundary -- --inventory
```

| Grenze | Gesamt | **Offen (= Baseline)** | Schriftlich begründet |
|---|---:|---:|---:|
| **(a)** Kadenz-Vorschub außerhalb `RecurrenceEngine` | 18 | **11** | 7 |
| **(b)** Notification-Write außerhalb `NotificationPropagationService` | 7 | **1** | 6 |

*Stand des Baums:* `chore/adr008-phase0-inventory`, abgezweigt von `develop`
(`b23f39400`).

Die **offene** Zahl ist die Ratchet-Baseline der Phasen 1–2. Die begründeten
Stellen sind kein Nebenposten, sondern der Kern der Zähldefinition: sie tragen
die Begründung **am Ort**, wo ein Reviewer ihr widersprechen kann, statt in einer
Ausschlussliste im Scanner.

### Das Messinstrument

| Artefakt | Zweck |
|---|---|
| `scripts/check_recurrence_boundary.py` | zählt (a); Gate-Modus + `--inventory`, `--list`, `--json` |
| `scripts/check_notification_write_boundary.py` | zählt (b); dieselben Modi |
| `src/backend/tests/unit/test_recurrence_boundary_check.py` | Erkennungslogik (synthetische Bäume) + Ratchet-Register für (a) |
| `src/backend/tests/unit/test_notification_write_boundary_check.py` | dasselbe für (b) |
| `task check:recurrence-boundary`, `task check:notification-write-boundary` | lokale Aufrufe |

**Bewusst nicht verdrahtet.** Beide Scanner sind im Gate-Modus heute **rot** —
das ist der Befund, nicht ein Defekt. Ein Gate, das nicht grün werden kann,
gehört nach NFR-018 §2 nicht in eine required Lane. Die Verdrahtung ist
ADR-008 Phase 4 (F-10) und braucht genau eines von beidem:

1. die offene Zahl auf null (Phasen 1–2) — dann wird derselbe Scanner im
   Gate-Modus als pre-commit-Hook in die `static`-Lane gehängt; **oder**
2. eine schriftliche Begründung an jeder verbleibenden Stelle — was für die
   elf offenen (a)-Stellen falsch wäre: sie sind Schulden, keine Ausnahmen.

Bis dahin liegt der **Wachstums-Ratchet** in den beiden Unit-Tests: ein neuer,
nicht registrierter Verstoß macht die Backend-Suite rot, und eine
Register-Zeile, deren Stelle repariert wurde, ebenfalls (Obsoleszenz-Regel).

---

## 2. (a) — Kadenz-Vorschübe außerhalb `RecurrenceEngine`

### 2.1 Offen: 11 Stellen (die Baseline für Phase 1)

| # | Ort | Funktion | Was dort steht |
|---|---|---|---|
| a1 | `domain/engines/care_reminder_engine.py:365` | `calculate_due_date` | `base + timedelta(days=last_confirmation.snooze_days)` |
| a2 | `domain/engines/care_reminder_engine.py:366` | `calculate_due_date` | `base + timedelta(days=interval)` |
| a3 | `domain/engines/inspection_scheduler.py:54` | `next_inspection_date` | `ensure_aware_utc(last_inspection_at) + timedelta(days=interval_days)` |
| a4 | `domain/engines/succession_plan_engine.py:54` | `generate_batch_run` | `plan.start_date + timedelta(days=(sequence - 1) * plan.interval_days)` |
| a5 | `domain/engines/tank_engine.py:492` | `calculate_next_maintenance` | `last_log.performed_at + timedelta(days=schedule.interval_days)` |
| a6 | `domain/engines/watering_forecast_engine.py:57` | `generate_forecast` | `current = current + timedelta(days=interval)` |
| a7 | `domain/engines/watering_schedule_engine.py:40` | `get_next_watering_dates` | WEEKDAYS-Modus: Tage durchlaufen und `weekday()` testen — eine `BYDAY`-Regel von Hand |
| a8 | `domain/engines/watering_schedule_engine.py:56` | `get_next_watering_dates` | INTERVAL-Modus: erste Fälligkeit per Modulo aufs Kadenz-Raster legen |
| a9 | `domain/engines/watering_schedule_engine.py:64` | `get_next_watering_dates` | `next_date += timedelta(days=schedule.interval_days)` — der Vorschub selbst |
| a10 | `tasks/tank_maintenance_tasks.py:44` | `generate_tank_maintenance_tasks` | `last_log.performed_at + timedelta(days=schedule.interval_days)` |
| a11 | `tasks/tank_maintenance_tasks.py:73` | `generate_tank_maintenance_tasks` | dieselbe Zeile ein zweites Mal, 29 Zeilen tiefer |

**Der Befund hinter den Zahlen.** a5/a10/a11 sind **dieselbe Regel an drei
Stellen**, zwei davon in einer einzigen Funktion: der Celery-Job rechnet
`tank_engine.calculate_next_maintenance` nach, statt sie aufzurufen. Das ist die
These von ADR-008 in einem Dateipaar — nicht als Argument, sondern als Zeilen.

a1/a2 sind die Care-Seite, die #510 nur zur Hälfte umgestellt hat:
`CareReminderService._next_watering_due_date` routet den Fixintervall-Fall
bereits über die Engine, benennt aber Snooze und Bootstrap ausdrücklich als
„dokumentierte Grenze" und lässt sie in `calculate_due_date`. Genau diese Grenze
löst F-7 auf (Snooze als **neu geimpfte Regel**).

### 2.2 Begründet: 7 Stellen (die Zähldefinition am Ort)

| Ort | Klasse | Begründung (Auszug) |
|---|---|---|
| `domain/engines/safety_interval_engine.py:62` | Einmal-Frist | Karenz zwischen Behandlung und Ernte (PflSchG) — nichts wiederholt sich |
| `domain/engines/watering_schedule_engine.py:61` | Horizont | `days_ahead` begrenzt die Aufzählung, es ist die Wand, nicht der Takt |
| `domain/services/dashboard_service.py:203` | Fenster | feste Sieben-Tage-Abfrage des Dashboards |
| `domain/services/ical_generator.py:47` | Format | RFC 5545 `DTEND` eines Ganztages-VEVENT ist die exklusive nächste Mitternacht |
| `domain/services/task_service.py:841` | Template-Versatz | wann die **erste** Aufgabe eines Laufs fällig ist |
| `domain/services/task_service.py:1206` | Clone-Versatz | ein einzelnes Datum für eine geklonte Aufgabe |
| `domain/services/task_service.py:1419` | Template-Versatz | `days_after_phase` ab Phaseneintritt, feuert einmal pro Übergang |

Die drei `task_service`-Einträge sind exakt die Klasse, die das F-6-Review
vorab als Rausch-Risiko benannt hatte („Clone-/Template-Offsets"). Sie stehen
jetzt als Text an der Stelle, statt als Regel im Scanner.

---

## 3. (b) — Notification-Writes außerhalb des Propagationspfads

### 3.1 Offen: 1 Stelle (die Baseline für Phase 2)

| # | Ort | Funktion | Warum Schuld und nicht Ausnahme |
|---|---|---|---|
| b1 | `domain/engines/notification_engine.py:301` | `escalate_overdue` | Die Eskalation stempelt `escalation_level` auf die **bestehende** Care-Benachrichtigung zurück — auf eine Zeile, die `NotificationPropagationService` über denselben `care.*`-`group_key` ebenfalls schreibt. Zwei Schreiber auf einer Zeile ist die #548-Form. Die Zeile wird hier nicht geboren, sie wird nachgezogen; „Event-Erzeugung" trifft also nicht zu. |

### 3.2 Benannt außerhalb: 6 Stellen

| Ort | Klasse | Warum außerhalb |
|---|---|---|
| `domain/engines/notification_engine.py:107` | `event` | Quiet Hours parken das eingehende Ereignis als `PENDING` |
| `domain/engines/notification_engine.py:122` | `event` | kein zustellbarer Kanal — Zeile entsteht trotzdem fürs In-App-Center |
| `domain/engines/notification_engine.py:149` | `event` | erste Materialisierung nach Kanalzustellung (REQ-030 §4.1) |
| `domain/engines/notification_engine.py:225` | `event` | Batch-Materialisierung, eine Zeile je Ereignis |
| `domain/services/notification_service.py:352` | `user-action` | der Leser markiert seine eigene Zeile gelesen (REQ-030 §5.2) |
| `domain/services/notification_service.py:370` | `user-action` | der Leser hat auf seiner eigenen Zeile gehandelt |

### 3.3 Das eigentliche Ergebnis von (b)

**Kein einziger Aufrufer außerhalb des Notification-Teilsystems fasst ein
Notification-Repository an.** `task_service` und `care_reminder_service` gehen
ausschließlich über `NotificationPropagationService`; es gibt keinen rohen
AQL-Schreibzugriff auf die `notifications`-Collection außerhalb des Repositories
(geprüft über jede Verwendung der Collection-Konstante).

Die Aussage „(b) ist fast null" ist damit **wahr und irreführend zugleich**, und
das ist der wichtigste Satz dieses Dokuments: (b) misst Schreibvorgänge am
falschen Ort. Die Fehlerklasse, die #742 und #769 erzeugt hat, ist der
Schreibvorgang, der **gar nicht stattfindet**. Siehe §4.2.

---

## 4. Was die Messung nicht sieht

Ein Scan, der stillschweigend zu niedrig zählt, erzeugt eine Baseline, die besser
aussieht als die Wirklichkeit — schlimmer als gar keine Baseline. Beide Scanner
benennen ihre Grenzen im eigenen Docstring; hier stehen sie zusammengefasst,
plus das, was die Handprüfung darüber hinaus gefunden hat.

### 4.1 Strukturelle Blindstellen des Scans (a)

Alle sind **einseitig** — sie zählen zu niedrig, können also keinen Fortschritt
vortäuschen:

1. **Dauer hinter einem Namen.** `step = timedelta(days=n)`, danach
   `base + step` — unsichtbar. Nur ein literales `timedelta(...)` in der
   Verschiebung wird gesehen.
2. **Kadenz hinter einem Helfer.** `self._advance(base, schedule)` schreibt die
   Arithmetik dem Aufgerufenen zu, nicht dem Aufrufer. In der Praxis richtig
   (die Regel wird einmal gezählt, dort wo sie steht) — aber wer die Aufrufer
   zählen will, zählt hier falsch.
3. **Andere Arithmetik als `timedelta`.** `relativedelta`, Monats-/Jahressprünge
   über `.replace(...)`, Ordinalarithmetik. *Gemessen am 2026-09-01: das Backend
   importiert kein `relativedelta` und konstruiert außerhalb der Engine keine
   `rrule`* — (a) ist heute vollständig `timedelta`-Arithmetik. Nichts hindert
   die nächste Stelle daran, in anderer Form aufzutauchen.
4. **Namenlose Kadenz.** `base + timedelta(days=n)` in einer Funktion `_step`
   trägt kein einziges der drei Signale.

**Ein gemessenes Beispiel für (4), im Baum:** `safety_interval_engine.py`
enthält dieselbe Rechnung zweimal. Zeile 62 wird gesehen (Operand heißt
`period["safety_interval_days"]`), Zeile 32 nicht (derselbe Wert heißt dort
`safety_days`). Beide sind hier legitim — aber wären sie es nicht, hätte der Scan
genau eine der beiden gemeldet. Das ist die Genauigkeit dieses Instruments, an
einem konkreten Fall.

### 4.2 Strukturelle Blindstelle des Scans (b) — die wichtigere

**Der fehlende Rand ist unsichtbar, und er ist die ganze #769-Klasse.**
Scan (b) findet Schreibvorgänge am falschen Ort; er kann den Schreibvorgang, der
**nie passiert**, nicht finden. Eine Handprüfung von `task_service.py` und
`care_reminder_service.py` (intraprozedural: Methoden, die eine Quelle mutieren,
gegen Methoden, die `_propagate*` aufrufen) liefert folgende **Kandidaten** —
zwei davon durch Lesen bestätigt, der Rest ist für F-8 zu prüfen, nicht hier zu
behaupten:

| Ort | Was mutiert wird | Status |
|---|---|---|
| `task_service._create_next_recurring_task:1127` | erzeugt den **Nachfolger** einer wiederkehrenden Aufgabe mit neuem Fälligkeitsdatum, ruft keine Propagation | **bestätigt** — der Aufrufer `complete_task` propagiert nur `on_task_completed` für die *erledigte* Aufgabe |
| `task_service._reschedule_dependents:1093` | verschiebt die Fälligkeitsdaten abhängiger Aufgaben (`update_task`) | **bestätigt** — genau die #742-Form: das Datum wandert, die Benachrichtigung nicht |
| `task_service.instantiate_workflow:806` | erzeugt je Template eine Aufgabe mit Fälligkeitsdatum | Kandidat |
| `task_service.activate_dormant_tasks_for_phase:1396` | dormant → pending **mit** Fälligkeitsdatum | Kandidat |
| `task_service.clone_task:1191` | erzeugt eine Aufgabe mit Fälligkeitsdatum | Kandidat |
| `task_service.reopen_task:1236` | completed → pending; `on_task_completed` hatte die Benachrichtigung erledigt gestempelt | Kandidat (#619/#622-Form) |
| `task_service.add_task_to_workflow_execution:1430` | erzeugt eine Aufgabe | Kandidat |
| `care_reminder_service.snooze_reminder:1007` | schreibt eine `SNOOZED`-Bestätigung, die die nächste Fälligkeit verschiebt | Kandidat |
| `care_reminder_service.record_care_task_completion:791` / `record_care_task_skip:842` | schreiben Bestätigungen | Kandidat |

Die Detektion ist bewusst grob (sie sieht nur den Rumpf einer Methode, nicht
ihre Aufrufkette — `update_profile` erscheint deshalb nicht, obwohl es
transitiv über `_reschedule_pending_care_task` propagiert). Sie ersetzt keinen
Zähler; sie **beschreibt die Messung, die (b) fehlt**.

**Empfehlung für F-8:** Das Exit-Kriterium von Phase 2 darf nicht allein „(b) auf
null" lauten. Der Zähler kann null erreichen, ohne dass ein einziger fehlender
Rand geschlossen wurde — er ist bereits fast null. Die zweite, tragende Prüfung
ist die **Paarungsprüfung**: je Quell-Mutation ein Test, der nach dem Vorgang
beide Seiten prüft. Das ist die #622+#742-Regressionspaarung, die das Issue
ohnehin als Abnahmekriterium führt.

### 4.3 Was die Handprüfung sonst noch gefunden hat

Zwei Stellen implementieren eine Kadenz, **ohne** sie fortzuschreiben — sie
prüfen stattdessen, ob *jetzt* gerade ein Termin ist. Kein `timedelta`, keine
Datumsarithmetik, für beide Scanner unsichtbar:

| Ort | Form |
|---|---|
| `domain/engines/watering_schedule_engine.py:26` (`is_watering_due`) | `days_since >= schedule.interval_days` — das Fälligkeits-Prädikat derselben Kadenz, die a8/a9 fortschreiben. Aufgerufen aus `tasks/watering_tasks.py` (täglicher Beat) und `get_due_channels`. |
| `domain/engines/actuator_control_engine.py:251–256` (`_evaluate_schedule`) | `days_of_week` + Zeitfenster-Vergleich — eine `BYDAY`-Semantik (REQ-018 `ScheduleType.WEEKLY`), als Enthaltensein-Test statt als Regel. |

Das ist eine **dritte Wiederholungsform** neben „Vorschub" und „RRULE":
*täglich pollen und vergleichen*. Ob sie unter Grenze 1 fällt, ist eine
Entscheidung, die Phase 1 treffen muss — ADR-008 formuliert die Grenze als „die
einzige Stelle, die *wann ist das nächste Mal* beantwortet", und ein Prädikat
beantwortet diese Frage nie. Beide Stellen bleiben deshalb **außerhalb der
Baseline**, sind hier aber benannt, damit die Entscheidung bewusst und nicht
durch Auslassung fällt.

**Ausdrücklich außerhalb des Zählbereichs:** der Celery-Beat-Fahrplan
(`tasks/__init__.py`, `crontab(...)`). Das ist Job-Terminierung der Infrastruktur,
keine fachliche Kadenz eines Nutzerartefakts.

---

## 5. Delta zwischen Scan und Handprüfung

Die Handprüfung ging über die sechs im Issue genannten Dateien (`task_service.py`,
`care_reminder_service.py`, `care_reminder_engine.py`, `notification_service.py`,
`notification_engine.py`, `notification_propagation_service.py`) sowie über alle
96 `timedelta`-Stellen unter `src/backend/app`, alle `rrule`/`croniter`/
`relativedelta`-Vorkommen und jede Verwendung der `notifications`-Collection.

| Richtung | Ergebnis |
|---|---|
| Vom Scan gemeldet, von Hand als falsch bewertet | **0** in der offenen Zahl. Die 7 begründeten (a)-Stellen waren zunächst gemeldet und tragen jetzt eine Begründung — das ist der vorgesehene Weg, nicht ein Fehler. |
| Von Hand gefunden, vom Scan übersehen — **innerhalb** der Zähldefinition | **0.** Keine Kadenz-Vorschub-Stelle und kein Repository-Schreibvorgang, den der Scan nicht hat. |
| Von Hand gefunden, **außerhalb** der Zähldefinition | **11+**: 2 Poll-und-Vergleich-Kadenzen (§4.3), 2 bestätigte + 7 kandidierende fehlende Propagationsränder (§4.2). |

Das dritte Feld ist die eigentliche Aussage: Die Zähldefinition ist scharf und
der Scanner deckt sie vollständig ab. Der Rest der Fehlerklasse liegt
**außerhalb dessen, was eine Zählung dieser Form messen kann** — nicht in ihren
Lücken.

---

## 6. Reicht das für `Accepted`?

**Für die Phase-0-Hälfte: ja.** ADR-008 verlangt „alle Stellen auflisten, die (a)
… und (b) … Ergebnis ist eine Zahl, kein Gefühl — sie ist die Ratchet-Baseline
der Phasen 1–3 und wird berechnet, nicht eingecheckt." Beide Zahlen liegen vor,
sind berechnet, per Stelle attribuiert, gegen die Zähldefinition begründet und
mit einem Ratchet plus Obsoleszenz-Regel abgesichert.

**Für den Statuswechsel: nein, noch nicht.** Das ADR nennt zwei Bedingungen,
verbunden mit *und*: die Bestandsaufnahme **und** die Übernahme der
Zuständigkeitsgrenzen durch REQ-006, REQ-022 und REQ-030. Die drei REQs sind in
dieser Arbeit unangetastet. Solange dort kein Verweis auf die vier Grenzen steht,
ist das ADR ein Dokument über den Code und keine Regel, die eine neue Kante
erben würde — genau der Zustand, den Alternative D („Konsolidierung ohne ADR")
als verworfen beschreibt.

**Eine Empfehlung zur Formulierung von Phase 1 und 2, aus der Messung heraus.**
Die Abschlusskriterien der beiden Phasen lauten heute „Baseline auf null".
Für Phase 1 trägt das. Für Phase 2 trägt es nicht: die (b)-Baseline steht bereits
bei 1, und sie kann null erreichen, ohne dass ein einziger fehlender
Propagationsrand geschlossen wurde. Phase 2 braucht als Abschlusskriterium die
Paarungsprüfung aus §4.2 — die Zählung allein würde dort einen Erfolg
bescheinigen, den es nicht gab.

---

## 7. Referenzen

- `spec/decisions/ADR-008-task-care-notification-consolidation.md` — §Migrationsskizze, Phase 0
- `project/features/recurrence-propagation-inventory-baseline.md` — F-6, acceptance-1 bis acceptance-4
- `project/requirements/adr008-recurrence-consolidation.md` — R-15
- `.audits/issue-pattern-analysis/2026-08-08-report.md` — Cluster I, Meta-Muster M5
- `spec/nfr/NFR-018_CI-CD-Pipeline-Integritaet.md` §2, §2.1 — Gate-Regeln, berechnete Ratchet-Baselines
- Issues: #489, #508–#511, #548, #619, #622, #742, #769, #1061
- `src/backend/tests/unit/migrations/test_substrate_invariants.py` — `_KNOWN_OPEN`, Vorbild der Obsoleszenz-Regel
