---
id: F-8
title: Jeder Propagations-Write durch den einen NotificationPropagationService
status: draft
roadmap_item: R-15
sprint: null
created: 2026-08-10
ended: null
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-08-10
  agent_version: feature-consistency-reviewer@66bd4c0fe
  findings:
    - kind: prior-art
      target: src/backend/app/domain/services/notification_propagation_service.py:22
      resolution: proceed
      evidence: "group_key-Idempotenz und Fail-closed-Tenant sind implementiert (#742); Task- und Care-Service sind best-effort verdrahtet. Der Rest sind die unverdrahteten Kanten (#769-Klasse) und das Nullstellen von Counter (b)."
    - kind: prior-art
      target: src/backend/app/domain/services/care_reminder_service.py:238
      resolution: proceed
      evidence: "Der Profil-Edit-Pfad paart Task-Retiming und Notification-Nachzug bereits (#622+#742+#769); das wörtlich gedraftete Paar-AC wäre dort vakuös. Operator entschied 2026-08-10: AC rescoped auf ENGINE-getriebene Intervall-Neubestimmung (Saison/Phase/adaptiv)."
    - kind: drift
      target: src/backend/app/domain/engines/notification_engine.py:107
      resolution: proceed
      evidence: "Drei legitime Nicht-Propagations-Schreibklassen existieren (Engine-Dispatch/Eskalation, Nutzer-Aktionen mark_read/mark_acted, Event-Erzeugung); 'alle Writes durch den Pfad' wäre gegen die dokumentierte Doppel-Push-Vermeidung unterdefiniert. Auflösung: F-6-Schreibklassen-Definition ist das Exit-Vokabular."
    - kind: overlap
      target: project/features/atomic-completion-transition.md
      resolution: proceed
      evidence: "F-9 schreibt Notifications innerhalb der Stream-Transaktion. Operator entschied 2026-08-10: der Propagationsdienst erhält einen optionalen Transaktions-Kontext und läuft INNERHALB der Transaktion — 'ein Pfad' bleibt wörtlich wahr, keine Gate-Ausnahme."
---

## Description

Jede **Propagation** — eine Quelländerung (Aufgabe verschoben, zugewiesen,
gelöscht; Erinnerung umgeplant; Intervall neu bestimmt), die abgeleitete
Benachrichtigungen nachziehen muss — läuft über den einen
`NotificationPropagationService` mit seinen beiden Invarianten: idempotent über
`group_key` (kein Doppel-Push) und fail-closed je Mandant. Was legitim
**außerhalb** bleibt, definiert die F-6-Schreibklassen-Definition: die
Event-Erzeugung der Notification-Engine, Kanal-Dispatch/Eskalation und
Nutzer-Aktionen (`mark_read`/`mark_acted`) sind keine Propagation.

Der fachlich wichtigste Neuzugang: **engine-getriebene**
Intervall-Neubestimmungen (Saisonwechsel, Phasenübergang, adaptive Anpassung)
werden Quelländerungen erster Klasse — die offene Aufgabe wird sofort
umterminiert und ihre Benachrichtigung im selben Zug nachgezogen (R4). Der
bereits gepaarte Profil-Edit-Pfad (#622/#742/#769) bleibt die Vorlage; der Test
zielt bewusst auf die noch unverdrahteten Engine-Kanten, damit er nicht
Bestandsverhalten zertifiziert.

## Acceptance criteria

- [x] **acceptance-1** Die F-6-Zählung (b) — Propagations-Writes außerhalb des `NotificationPropagationService` gemäß Schreibklassen-Definition — steht auf null.
- [x] **acceptance-2** Auf jeder neu gerouteten Kante gilt die `group_key`-Idempotenz: ein doppelter Propagationslauf erzeugt keine zweite Benachrichtigung (Test je Kante).
- [x] **acceptance-3** Auf jeder neu gerouteten Kante gilt fail-closed je Mandant: ohne auflösbaren Tenant wird nichts geschrieben (Test je Kante).
- [ ] **acceptance-4** Eine ENGINE-getriebene Intervall-Neubestimmung (Saison, Phasenübergang, adaptiv) terminiert die offene Aufgabe sofort um UND zieht die Benachrichtigung im selben Zug nach; der Test schlägt fehl, wenn eine der beiden Hälften fehlt (R4, #622+#742-Regressionspaar auf den Engine-Kanten).

## Test hooks

- **acceptance-1** — F-6-Scanner im Gate-Modus grün (`python3 scripts/check_notification_write_boundary.py`: 0 offen, 6 deklariert); Decke 0 in `src/backend/tests/unit/test_notification_write_boundary_check.py::TestTheRatchet` (`_CEILING = 0`, Register `_KNOWN_OPEN` aufgelöst) — proven 2026-11-25
- **acceptance-2** — Eskalationskante: `src/backend/tests/unit/domain/services/test_notification_escalation_propagation.py::TestEscalationRunIsIdempotent`, Beat-Ebene `src/backend/tests/unit/tasks/test_escalation_beat_escalates_each_row_in_its_own_tenant.py::test_a_second_beat_escalates_nothing_more`, überlappende Läufe gegen ArangoDB `src/backend/tests/integration/test_notification_escalation_claim.py::test_two_overlapping_escalation_runs_claim_the_level_exactly_once`; Saison-/Ruhephasenkante: `src/backend/tests/unit/domain/services/test_season_dormancy_redetermines_open_care_task.py::test_a_repeated_transition_leaves_one_note_and_writes_the_task_once` — proven 2026-11-26
- **acceptance-3** — Eskalationskante: `test_notification_escalation_propagation.py::TestEscalationRunFailsClosedPerTenant` + `TestOnNotificationEscalated`, Beat-Ebene `test_escalation_beat_escalates_each_row_in_its_own_tenant.py` (Zeile von Tenant B nur in Bs Lauf, suspendierter Tenant nie), Repository `test_notification_escalation_claim.py::TestTheRepositoryClaim::test_another_tenant_claims_nothing`; Saison-/Ruhephasenkante: `test_season_dormancy_redetermines_open_care_task.py::test_no_resolvable_tenant_writes_nothing`, `::test_a_plant_of_another_tenant_writes_nothing` — proven 2026-11-26
- **acceptance-4** — teilweise belegt, deshalb nicht abgehakt. **Belegt (Saisonkante):** REQ-047-Saisonübergang mit echtem Wechsel des Ruhephasen-Pflegeregimes → `CareReminderService.redetermine_open_care_task` verschiebt die offene Gießaufgabe und zieht ihre Benachrichtigung im selben Zug nach, nach der ADR-006-Phasenkopplung; `test_season_dormancy_redetermines_open_care_task.py::test_entering_dormancy_retimes_the_open_task_and_its_note_in_the_same_pass`, `::test_leaving_dormancy_retimes_the_open_task_and_its_note_back`, `::test_the_new_growth_phase_feeds_the_retimed_interval`; ohne echten Regimewechsel wird nichts geschrieben (`::test_a_hand_moved_task_of_a_never_dormant_plant_survives_spring_and_growing`). Falsifiziert: Vor-Änderungs-Code, fehlende Task-Hälfte, fehlende Notification-Hälfte → jeweils rot. **Offen:** (1) Wachstumsphasenübergang außerhalb der Saisonkopplung (`PhaseService.transition_phase` ändert `phase_watering_interval`, kennt den Care-Service nicht); (2) adaptive Anpassung (`confirm_reminder` lernt das Intervall, terminiert aber keine offene Aufgabe um); (3) Regime `dormancy_watering="none"`: das Intervall wird `None`, die offene Gießaufgabe bleibt unverändert stehen — fachliche Entscheidung des Betreibers, bewusst weder umgesetzt noch durch einen Test als gewollt festgeschrieben

## Consistency notes

**prior-art Profil-Edit-Pfad (`proceed`, AC rescoped):** Das ursprünglich
gedraftete Paar-AC wäre für den Profil-Edit-Pfad heute schon grün gewesen — ein
Positivtest, der nichts zertifiziert (die teuerste Fehlerklasse dieses
Projekts). Der Operator hat das AC am 2026-08-10 auf die engine-getriebenen
Neubestimmungen rescoped; der Edit-Pfad dient als Vorlage, nicht als Testziel.

**overlap F-8 ↔ F-9 (`proceed`, Rationale):** Der atomare Abschluss-Übergang
(F-9) schreibt Benachrichtigungen innerhalb seiner Stream-Transaktion. Damit er
kein neuer Schreiber außerhalb des Pfads wird, hat der Operator am 2026-08-10
entschieden: der `NotificationPropagationService` erhält einen optionalen
Transaktions-Kontext-Parameter und läuft **innerhalb** der Transaktion. „Ein
Propagationspfad" bleibt damit wörtlich wahr, und das (b)-Gate (F-10) startet
ohne eine einzige Ausnahme. Die Entscheidung ist hier und in F-9 identisch
referenziert — einmal getroffen, nicht zweimal.

**drift Schreibklassen (`proceed`):** „Alle Notification-Writes durch den Pfad"
wäre gegen die dokumentierte Doppel-Push-Vermeidung und die bewusst asynchrone
Kanalzustellung (ADR-Alternative C) falsch. Exit-Vokabular ist die
F-6-Definition (acceptance-1 dort); dieses Feature konsumiert sie unverändert.

## Risks

- Das Rescoping von acceptance-4 hängt daran, dass die Engine-Kanten wirklich
  unverdrahtet sind — stellt die Implementierung fest, dass eine Kante bereits
  gepaart ist, gilt die F-8-Regel: rot-zuerst nachweisen, sonst ist der Test
  vakuös.
- Neue Kanten, die während der Umsetzung entstehen (Parallel-PRs), fängt die
  F-6-Ratchet; acceptance-1 misst am Ende, nicht am Anfang.
