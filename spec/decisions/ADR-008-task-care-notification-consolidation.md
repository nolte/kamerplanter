# ADR-008: Konsolidierung von Tasks, Care-Reminders und Notifications auf eine Recurrence-Engine und einen Propagationspfad

## Status

Proposed — 2026-08-08

Hergeleitet aus der Issue-Muster-Analyse vom 2026-08-08
(`.audits/issue-pattern-analysis/2026-08-08-report.md`, Cluster I / Meta-Muster
M5). Angenommen wird dieses ADR, wenn die Phase-0-Bestandsaufnahme aus
§"Migrationsskizze" vorliegt und die betroffenen REQs (006, 022, 030) die
Zuständigkeitsgrenzen übernommen haben.

**Stand der Annahmebedingung (2026-09-01).** Die erste Hälfte liegt vor:
`.audits/adr-008-phase-0-inventory/2026-09-01-inventory.md` zählt (a) **11**
offene Kadenz-Vorschübe außerhalb der `RecurrenceEngine` und (b) **1** offenen
Notification-Write außerhalb des Propagationsdienstes, je Stelle attribuiert und
mit einem Ratchet abgesichert. Die zweite Hälfte steht aus: REQ-006, REQ-022 und
REQ-030 verweisen bislang auf keine der vier Zuständigkeitsgrenzen. Der Status
bleibt deshalb *Proposed*.

Die Bestandsaufnahme korrigiert außerdem eine Annahme dieses ADR: das
Abschlusskriterium von Phase 2 („Baseline (b) auf null“) trägt nicht allein,
weil (b) bereits bei 1 steht und null erreichen kann, ohne dass eine einzige
fehlende Propagationskante geschlossen wurde — siehe §4.2 und §6 dort.

## Context

Kamerplanter führt heute **drei Teilsysteme, die dieselbe Sache tun** — „etwas
ist zu einem Zeitpunkt fällig, muss sichtbar werden, wiederholt sich und ändert
sich, wenn sich seine Quelle ändert":

| Teilsystem | Spec | Kern-Artefakte |
|---|---|---|
| Aufgaben | REQ-006 | `task_service.py` (1246 Z.), `recurrence_engine.py` (63 Z.) |
| Pflegeerinnerungen | REQ-022 | `care_reminder_service.py` (1415 Z.), `care_reminder_engine.py` (763 Z.) |
| Benachrichtigungen | REQ-030 | `notification_service.py` (566 Z.), `notification_engine.py` (465 Z.), `notification_propagation_service.py` (452 Z.) |

Die drei sind nicht unabhängig: Eine Pflegeerinnerung **erzeugt eine Aufgabe**
(`build_care_reminder_task`), eine Aufgabe **erzeugt eine Benachrichtigung**, und
eine bestätigte Pflegeerinnerung muss beide nachziehen. Jede dieser Kanten wurde
einzeln gebaut, und jede wurde einzeln nachgebessert.

**Die Belege sind Symptome derselben Duplikation, nicht unabhängige Bugs:**

| Issue | Symptom | Gemeinsame Wurzel |
|---|---|---|
| #489 (Analyse) | Bestandsaufnahme der drei parallelen Teilsysteme | — |
| #508–#511 | Wiederholung driftete zwischen Task-Pfad und Care-Pfad auseinander | zwei Implementierungen von „nächster Termin" |
| #510 | eigene Next-Occurrence-Rechnung je Pfad | dito — mit `RecurrenceEngine` bereits behoben |
| #548 | Zustand von Aufgabe und Erinnerung lief auseinander | zwei Zustandsbesitzer für einen Vorgang |
| #619, #622 | Erledigen/Überspringen wirkte nur auf einer Seite | Abschluss war kein gemeinsamer Übergang |
| #742 | Quelländerung erreichte die Benachrichtigung nicht | kein Propagationspfad — mit `NotificationPropagationService` bereits behoben |
| #769 | dieselbe Klasse an einer weiteren Kante | Propagation war pro Aufrufer verdrahtet |

Der Punkt ist die **Wiederholung des Fehlerbildes**, nicht seine Schwere. Jeder
Fix war korrekt und keiner war falsch platziert; sie kurieren nur alle dasselbe:
Zwei Kopien einer Regel driften auseinander, sobald eine davon angefasst wird,
und die Drift fällt einem Nutzer auf, nicht der CI.

**Was bereits konsolidiert ist** — dieses ADR beginnt nicht bei null, und das
ist der stärkste Hinweis darauf, dass die Richtung stimmt:

- `RecurrenceEngine` (#510) ist die **eine** Stelle, die aus einer Kadenz den
  nächsten Termin macht. Der generische Task-Pfad und der
  Fixintervall-Care-Pfad rufen sie beide auf; die Care-Engine bleibt die
  *Intervall-Autorität* (Saison/Phase/adaptiv), drückt ihr Ergebnis aber als
  iCal-`RRULE` aus.
- `NotificationPropagationService` (#742) ist der **eine** Weg, auf dem eine
  Quelländerung die zugehörige In-App-Benachrichtigung erreicht, idempotent über
  `group_key` und mandantenfest.

Beides sind Reparaturen, die zufällig die richtige Form haben. Was fehlt, ist
die **Entscheidung**, dass diese Form die Zielarchitektur ist — sonst entsteht
die nächste Kante wieder als vierte Sonderlösung.

## Decision

**Wiederholung und Propagation haben je genau einen Besitzer; die drei
Teilsysteme behalten ihre Fachlichkeit, aber keine eigene Terminmechanik und
keinen eigenen Propagationsweg.**

Ausführlich, als vier verbindliche Zuständigkeitsgrenzen:

1. **Eine Recurrence-Engine.** `RecurrenceEngine` ist die einzige Stelle, die
   „wann ist das nächste Mal" beantwortet. Das kanonische Format ist die
   iCal-`RRULE` (REQ-015-Token, damit derselbe String Task-Wiederholung und
   Kalender-Export trägt). Jeder Pfad, der eine Kadenz hat — generische Aufgabe,
   Pflegeerinnerung, saisonale Winteraufgabe, Sukzessionssatz —, drückt sie als
   Regel aus und lässt sie von dieser Engine fortschreiben. Ein zweites
   `timedelta(days=...)` im Service-Code ist ein Defekt, kein Sonderfall.
2. **Die fachliche Intervall-Bestimmung bleibt verteilt.** Was die Kadenz
   *inhaltlich* ist — Gießintervall nach Saison, Phase und Substrat, Winterschutz
   nach Frosthärte —, bleibt in der jeweiligen Domänen-Engine. Diese Grenze ist
   die Bedingung dafür, dass die Konsolidierung keine Fachlichkeit einebnet: Die
   Care-Engine sagt *"alle 6 Tage"*, die Recurrence-Engine sagt *"also am 14."*.
3. **Ein Propagationspfad.** Jede Zustandsänderung an einer Quelle — Aufgabe
   verschoben, zugewiesen, erledigt, gelöscht; Erinnerung bestätigt, übersprungen,
   umgeplant — läuft über **einen** Propagationsdienst, der die abgeleiteten
   Artefakte nachzieht. Kein Aufrufer ruft mehr direkt Notification-Repositories.
   Die Idempotenz-Regel (`group_key` je Quelle) und die Fail-Closed-Mandantenregel
   gelten für alle Kanten, nicht nur für die drei bereits verdrahteten.
4. **Ein Abschluss-Übergang.** „Erledigt", „übersprungen" und „bestätigt" sind
   ein Übergang mit einem Besitzer, der Aufgabe, Erinnerung und Benachrichtigung
   gemeinsam bewegt. #619/#622 sind genau der Fall, in dem zwei Hälften desselben
   Übergangs an zwei Stellen implementiert waren und eine davon vergessen wurde.

**Nicht Teil dieser Entscheidung:** Die drei REQs werden nicht zusammengelegt.
Aufgaben, Pflegeerinnerungen und Benachrichtigungen bleiben fachlich getrennte
Konzepte mit eigenen Modellen, eigenen UI-Flächen und eigenen Rechten. Konsolidiert
wird ausschließlich die geteilte **Mechanik**.

## Alternatives Considered

**A — Weiter pro Kante fixen (Status quo).** Verworfen. Sieben Issues in dreißig
Tagen zeigen die Trefferquote: Jeder Fix ist billig, die Summe ist es nicht, und
jede neue Kante startet wieder bei null. Der Ansatz ist zudem nicht messbar —
es gibt keine Stelle, an der man sähe, dass eine Kante noch fehlt.

**B — Ein einziges „Fällig-Objekt" für alles.** Aufgabe, Erinnerung und
Benachrichtigung auf ein gemeinsames Modell reduzieren. Verworfen: Die drei
unterscheiden sich in Rechten (Zuweisung nur bei Aufgaben), Lebensdauer
(Benachrichtigungen sind flüchtig, Aufgaben nicht), Sichtbarkeit und
Löschsemantik. Ein gemeinsames Modell würde diese Unterschiede in Flags
ausdrücken — und Flags auf einem Sammelmodell sind die Duplikation von vorn,
nur schlechter auffindbar.

**C — Asynchrone Ereigniskette (Domain-Events über Celery).** Quelle feuert
Event, Konsumenten reagieren. Verworfen für den Propagationspfad, aus dem Grund,
den `NotificationPropagationService` bereits dokumentiert: In-App-Propagation ist
ein reiner Repository-Schreibvorgang und läuft synchron im bestehenden
Service-Layer. Asynchron würde sie eventual-consistent machen — der Nutzer sähe
nach dem Verschieben einer Aufgabe für einen Moment den alten Termin —, und
sie würde einen zweiten Zustellweg neben dem Kanal-Dispatch eröffnen, also
Doppel-Pushes riskieren. Die Kanalzustellung (HA, E-Mail, Web Push) bleibt
asynchron; sie ist bereits so gebaut.

**D — Konsolidierung ohne ADR, rein im Code.** Verworfen, weil die beiden bereits
erfolgten Konsolidierungsschritte (#510, #742) genau das waren: richtige Form,
aber keine festgehaltene Entscheidung. Die nächste Kante wurde trotzdem wieder
einzeln gebaut (#769). Ohne festgehaltene Grenze wiederholt sich das.

## Consequences

**Positiv**

- Eine Regel hat eine Stelle. Eine Änderung an der Wiederholungslogik wirkt
  überall, statt an drei Stellen nachgezogen werden zu müssen.
- Die Fehlerklasse wird *prüfbar*: „Kein Service berechnet Termine selbst" und
  „kein Aufrufer schreibt direkt in Notification-Repositories" sind statisch
  prüfbare Aussagen — im Sinne des NFR-018-Governance-Prinzips („jede MUSS-Regel
  bekommt ein Gate oder eine benannte Auslassung").
- Neue Kanten (Sukzession, Fruchtfolge, Überwinterung) erben Propagation und
  Wiederholung, statt sie mitzubringen.

**Negativ / Risiken**

- `care_reminder_service.py` und `task_service.py` sind zusammen ~2.700 Zeilen
  mit dichter Testabdeckung. Ein Umbau ohne Verhaltensänderung ist möglich, aber
  nicht billig, und er kollidiert mit jeder parallelen Arbeit an denselben
  Dateien (`auth_service` hat dieselbe Klasse siebenfach erlebt).
- Die Grenze zwischen „fachlichem Intervall" und „Terminmechanik" ist eine
  Konvention, keine Typgrenze. Sie muss im Style Guide stehen, sonst wandert
  Fachlichkeit in die Recurrence-Engine zurück.
- Zwischenzustände der Migration sind gefährlicher als beide Endzustände: Ein
  halb umgestellter Propagationspfad kann eine Kante *doppelt* bedienen. Deshalb
  die phasenweise Skizze unten mit Umschaltung erst am Ende jeder Phase.

**Migrationsskizze (Phasen, jede für sich lieferbar)**

- **Phase 0 — Bestandsaufnahme mit Nachweis.** Alle Stellen auflisten, die (a)
  einen nächsten Termin berechnen und (b) Notification-Zustand schreiben. Ergebnis
  ist eine Zahl, kein Gefühl — sie ist die Ratchet-Baseline der Phasen 1–3 und
  wird **berechnet, nicht eingecheckt** (NFR-018 §2.1).
  **Erledigt am 2026-09-01:** `.audits/adr-008-phase-0-inventory/2026-09-01-inventory.md`
  (Zahlen, Stellenliste, Zähldefinition und die benannten Grenzen der Messung).
  Die beiden Zähler sind `scripts/check_recurrence_boundary.py` und
  `scripts/check_notification_write_boundary.py` (`task check:recurrence-boundary`,
  `task check:notification-write-boundary`); ihr Gate-Modus ist heute rot und
  deshalb bewusst in keiner CI-Lane verdrahtet — das leistet Phase 4.
- **Phase 1 — Terminmechanik zusammenführen.** Jeden verbliebenen eigenen
  Datums-Vorschub auf `RecurrenceEngine` umstellen; die fachlichen
  Intervall-Bestimmungen bleiben, wo sie sind, und geben nur noch eine `RRULE`
  aus. Abschlusskriterium: Baseline aus Phase 0 (a) auf null.
- **Phase 2 — Propagation zusammenführen.** Jede verbliebene Direktschreibung an
  Notification-Repositories durch den Propagationsdienst ersetzen und die
  fehlenden Kanten (#769-Klasse) ergänzen. Abschlusskriterium: Baseline (b) auf
  null.
- **Phase 3 — Abschluss-Übergang vereinheitlichen.** „Erledigt/übersprungen/
  bestätigt" auf einen Übergang ziehen, der alle drei Artefakte bewegt.
  Abschlusskriterium: ein Test je Quelle, der nach dem Übergang **alle drei**
  Seiten prüft — nicht nur die, an der er ausgelöst wurde.
- **Phase 4 — Grenzen festschreiben.** Regeln in `BACKEND.md` aufnehmen und, wo
  praktikabel, als statischen Check mit Negativkontrolle absichern. Ohne diese
  Phase ist die Konsolidierung erneut nur eine Momentaufnahme.

**Folgemaßnahmen an Specs**

- REQ-006, REQ-022, REQ-030 erhalten je einen Verweis auf die hier festgelegten
  Zuständigkeitsgrenzen (welche Mechanik dem Teilsystem gehört und welche nicht).
- `spec/style-guides/BACKEND.md` nimmt die zwei Regeln aus Phase 4 auf.
- Nach `Accepted` wird dieses ADR als Doku-ADR auf der MkDocs-Site gespiegelt
  (`docs/{de,en}/adr/`), wie ADR-005 → Docs-ADR-009.

## References

- `.audits/adr-008-phase-0-inventory/2026-09-01-inventory.md` — Phase-0-Bestandsaufnahme (Zahlen, Stellenliste, Blindstellen der Messung)
- `.audits/issue-pattern-analysis/2026-08-08-report.md` — Cluster I, Meta-Muster M5, Maßnahme P6.1
- Issues: #489 (Analyse), #508, #509, #510, #511, #548, #619, #622, #742, #769
- `src/backend/app/domain/engines/recurrence_engine.py` — bestehende Teilkonsolidierung (#510)
- `src/backend/app/domain/services/notification_propagation_service.py` — bestehender Propagationspfad (#742)
- REQ-006 (Aufgabenplanung), REQ-022 (Pflegeerinnerungen), REQ-030 (Notifications), REQ-015 (Kalenderansicht, iCal-Token)
- NFR-018 §2 — Gate-Regeln, Ratchet-Baselines
- ADR-005 (Versioniertes Migrations-Framework) — Vorbild für phasenweise Umstellung mit Abschlusskriterium je Phase
