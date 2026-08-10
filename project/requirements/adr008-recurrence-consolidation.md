# Requirements — ADR-008-Konsolidierung: eine Recurrence-Engine, ein Propagationspfad (Issue #1061, R-15)

<!--
Produced via the `requirements-elicit` skill, following
spec/project/requirements-elicitation/.
`c_d` is an uncertainty proxy (self-consistency-derived), not a calibrated
probability. A requirement is `confirmed` only after an explicit teach-back.
-->

## Bounded context

- **Was:** Ausführung der ADR-008-Migration (`spec/decisions/ADR-008-task-care-notification-consolidation.md`):
  Wiederholung und Propagation bekommen je genau einen Besitzer. Tasks (REQ-006),
  Care-Reminders (REQ-022) und Notifications (REQ-030) behalten ihre Fachlichkeit,
  eigene Modelle, UI-Flächen und Rechte — konsolidiert wird ausschließlich die
  geteilte Mechanik. 5 Phasen, jede einzeln shippbar (0 Inventar-Baseline →
  1 Recurrence → 2 Propagation → 3 Completion-Transition → 4 Freeze).
- **Für wen:** Outcome O-8 (Maintainer: Änderungen driften nicht mehr — die
  #489/#508–511/#548/#619/#622/#742/#769-Klasse endet strukturell) und Endnutzer
  (Termin- und Benachrichtigungskonsistenz über alle drei Teilsysteme).
- **Explizit außerhalb:**
  - Zusammenlegung der drei REQs/Modelle auf ein „Fällig-Objekt" (ADR-Alternative B, verworfen).
  - Asynchrone Event-Kette für die In-App-Propagation (Alternative C, verworfen);
    die **Kanalzustellung** (HA, E-Mail, Web Push) bleibt asynchron wie gebaut.
  - Neue Fachlogik in den Intervall-Bestimmungen — die Care-Engine bleibt die
    Intervall-Autorität (Grenze 2 des ADR).

## Understanding KPI

- Thresholds: `τ_low = 0.4`, `τ_high = 0.8`, self-consistency `k = 2`, question budget = `5` (5 verbraucht)
- `U_gate = min_d c_d` over required dimensions = **0.8**
- Termination: `saturation` nach Teach-back (alle fünf entscheidungstragenden Fragen
  beantwortet und im Teach-back bestätigt; verbleibende Randfälle als benannte
  Restrisiken unten)

### Gap matrix

| Dimension | Applicable | `c_d` | Uncertainty source | Evidence event |
|---|---|---|---|---|
| `functional` | yes | 0.85 | specification | ADR-008 §Decision (4 Grenzen) + Q1/Q3 beantwortet + Teach-back 2026-08-10 |
| `non_functional` | yes | 0.85 | specification | Q4 (Atomarität) + ADR-Idempotenz-/Fail-closed-Regeln; Teach-back |
| `constraints` | yes | 0.85 | interpretation | ADR-Alternativen B/C verworfen; Grenze 2 (Intervall-Autorität); Teach-back |
| `domain_objects` | yes | 0.8 | interpretation | RecurrenceEngine (#510), NotificationPropagationService (#742), RRULE (REQ-015), group_key |
| `actors` | yes | 0.8 | interpretation | Rechte/Modelle unverändert (ADR §Nicht Teil); Maintainer + Endnutzer via O-8 |
| `acceptance_criteria` | yes | 0.8 | specification | Issue-ACs + Phasen-Exits + Q5 (Gate-Form); Teach-back |
| `edge_cases` | yes | 0.7 | specification | Q2/Q3/Q4 decken die teuersten Fälle; Rest als Restrisiken benannt |
| `scope_boundaries` | yes | 0.9 | interpretation | Issue + ADR §Nicht Teil, explizit |

`edge_cases` bleibt unter `τ_high` — die verbleibenden Fälle sind unten als
Restrisiken benannt und blockieren die Dekomposition nicht (sie werden je Phase
als Testfälle konkretisiert).

## Requirements

### R1 — Ein Besitzer für den Abschluss-Übergang `confirmed`

WHEN eine Aufgabe, eine Pflegeerinnerung oder deren Benachrichtigung als
done/skipped/rescheduled markiert wird, THE SYSTEM SHALL diesen Übergang über
einen **neuen geteilten Transition-Service im Service-Layer**
(Arbeitstitel `CompletionTransitionService`) ausführen, der Task, Reminder und
Notification **gemeinsam** bewegt; kein Router und kein anderer Service
implementiert eine eigene Hälfte dieses Übergangs.
*(Q1, Teach-back 2026-08-10; schließt die #548/#619/#622-Klasse)*

### R2 — Atomarität des Übergangs `confirmed`

WHEN der geteilte Übergang schreibt, THE SYSTEM SHALL alle beteiligten
Schreibvorgänge in **einer ArangoDB-Stream-Transaktion** ausführen: entweder
alles oder nichts; ein halber Übergang ist nie sichtbar. Der Repository-Layer
erhält dafür Transaktions-Support (eigenes Arbeitspaket).
*(Q4, Teach-back)*

### R3 — Idempotente Nachhol-Semantik außerhalb des Übergangs `confirmed`

WHERE Propagation **außerhalb** des Abschluss-Übergangs stattfindet
(z. B. Umterminierung nach Quelländerung), THE SYSTEM SHALL die bestehende
dokumentierte Semantik des `NotificationPropagationService` beibehalten:
idempotent über `group_key`, fail-closed je Mandant, bei Teilfehlern geloggt und
nachholbar.
*(Q4-Abgrenzung, Teach-back)*

### R4 — Intervalländerung ist eine Quelländerung `confirmed`

WHEN die Care-Engine ein Intervall neu bestimmt (Saison, Phase, adaptiv),
THE SYSTEM SHALL die noch offene Aufgabe **sofort** über den Propagationspfad
umterminieren und die zugehörige Benachrichtigung im selben Zug nachziehen.
Ein Test MUSS fehlschlagen, wenn eine der beiden Hälften fehlt
(#622 + #742-Regressionspaar, AC des Issues).
*(Q2, Teach-back)*

### R5 — Fortschreibungs-Anker `confirmed` *(rev. 2026-08-10)*

- Die Fortschreibung ist **einheitlich abschluss-verankert** — für
  Care-Reminders UND generische Tasks: WHEN eine wiederkehrende
  Aufgabe/Pflegeaufgabe erledigt wird, THE SYSTEM SHALL die nächste Fälligkeit
  aus dem **Abschlussdatum** berechnen (Beispiel: fällig Mo, erledigt Mi,
  Intervall 6 Tage → nächste Fälligkeit Di). Die RRULE wird je Zyklus mit
  `DTSTART=Abschlussdatum` neu aufgesetzt.
- Der **Kalender-Export** (REQ-015) bleibt rasterbasiert-exportkonsistent in
  seiner bestehenden Form; nur die Fortschreibungs-Semantik ist geregelt.
- Beide rechnet **ausschließlich** die `RecurrenceEngine`.
*(Q3, Teach-back; adressiert die Drift-Klasse #508–#511.)*

> **Revision 2026-08-10** (requirements-revisit im feature-decompose-Gate):
> Die ursprüngliche Fassung sah generische Tasks **raster-verankert** vor. Der
> `feature-consistency-reviewer` wies nach, dass generische Tasks heute faktisch
> abschluss-verankert fortgeschrieben werden (Engine seedet `dtstart=jetzt`,
> kein DTSTART persistiert) — Raster-Verankerung wäre eine Verhaltens- und
> Datenmodell-Änderung (Anker-Feld, Migration, Terminsprung für Bestandsserien).
> Operator-Entscheidung: an das Ist-Verhalten angleichen; einheitlich
> abschluss-verankert, keine Migration. Teach-back der revidierten Form im
> selben Zug bestätigt.

### R6 — Zwei mechanische Grenz-Gates, required, vakuumfest `confirmed`

Phase 4 SHALL die beiden Grenzen als **zwei `check_*.py`-Script-Gates nach dem
#1046-Muster** (AST-Scan, begründete Ausnahme-Marker) in der **required
`static`-Lane** einfrieren:
(a) keine Next-Occurrence-Berechnung außerhalb der `RecurrenceEngine`,
(b) kein Notification-Write außerhalb des Propagationspfads.
ZUSÄTZLICH erhalten beide Gates Selbsttest-Pins gegen Vakuum (Muster #946:
synthetische Drift-Quellen müssen das Gate rot machen).
*(Q5, Teach-back)*

### R7 — Computed Phase-0-Baseline `confirmed`

Phase 0 SHALL die Zählung „Sites außerhalb der Engine / außerhalb des
Propagationspfads" **computed** erheben (NFR-018 §2.1, nie als versionierte
Konstante) und als Ratchet-Baseline für die Phasen 1–2 mit Obsoleszenz-Regel
testen; Exit der Phasen 1/2 ist Baseline (a) bzw. (b) auf null.
*(Issue-Scope, operator-verfasst; bestätigt durch Route-Kommentar 2026-08-09)*

### R8 — Spec-Nachzug `confirmed`

WHEN die Phasen abgeschlossen sind, THE SYSTEM SHALL ADR-008 auf **Accepted**
heben, die beiden Grenzregeln in `BACKEND.md` aufnehmen, die
Zuständigkeitsgrenzen aus REQ-006/022/030 referenzieren und das ADR gemäß
seiner eigenen Consequence-Liste in die MkDocs-Serie spiegeln.
*(Issue-AC; ADR §Status nennt die Acceptance-Bedingung: Phase-0-Inventar liegt
vor UND die REQs haben die Grenzen übernommen)*

## Surviving assumptions / open risks

- **DST/Zeitzonen bei abschluss-verankerter Neuaufsetzung** (`assumed`): die
  RRULE-Neuaufsetzung nutzt die bestehende UTC-Konvention des Projekts
  (check_utc_calendar_day-Gate); kein Sonderverhalten spezifiziert. Je Phase-1-Test
  zu konkretisieren.
- **Pausierte/archivierte Pflanzen während Sofort-Umterminierung** (`assumed`):
  die Umterminierung respektiert die bestehenden Sichtbarkeits-/Statusregeln der
  Quelle; eine pausierte Quelle erzeugt keine neue Fälligkeit.
- **Transaktions-Reichweite** (`assumed`): die Stream-Transaktion umfasst genau
  die Collections des Übergangs (tasks, care_reminders/…, notifications); die
  asynchrone Kanalzustellung ist nie Teil der Transaktion.
- `edge_cases` bei `c_d = 0.7` unter `τ_high`: bewusst akzeptiert; die Fälle
  oben sind benannt und werden in den Phasen-Features als Testfälle ausgeprägt.

## Consumer contract

Nachgelagerte Konsumenten (`feature-decompose` für R-15, `sprint-plan`):
`U_gate = 0.8` erreicht `τ_high` — die Dekomposition darf auf diesem Artefakt
aufsetzen. Die fünf Kernentscheidungen (R1–R6) sind teach-back-bestätigt am
2026-08-10; Herkunft: Interview im issue-orchestrate-Folgelauf zu #1061.
