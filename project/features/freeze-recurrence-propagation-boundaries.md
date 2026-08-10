---
id: F-10
title: Grenzen einfrieren — zwei mechanische Gates, BACKEND.md, ADR-008 Accepted
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
    - kind: overlap
      target: project/features/recurrence-propagation-inventory-baseline.md
      resolution: proceed
      evidence: "Gate-Scan und Baseline-Zählung sind dieselbe Erkennungslogik. Auflösung: ein Scanner, zwei Modi — F-10 flippt die F-6-Scripts auf Zero-Threshold und ersetzt den Ratchet-Test über dessen Obsoleszenz-Regel."
    - kind: prior-art
      target: scripts/check_layer_imports.py
      resolution: proceed
      evidence: "#1046-Muster ist Hauskonvention (layer-imports, tenant-body-field, workflow-gate-integrity, utc); Vakuum-Selbsttests nach #946 existieren inkl. Load-by-Path-Mechanik — Form kopierbar, nicht neu zu entwerfen."
    - kind: prior-art
      target: spec/req/REQ-006_Aufgabenplanung.md:178
      resolution: proceed
      evidence: "REQ-006 referenziert die Recurrence-Grenze bereits; REQ-022/030 tragen null ADR-008-Referenzen. ADR-008 §Status koppelt Accepted an Phase-0-Inventar UND REQ-Übernahme — Flip und REQ-Updates gehören in denselben Change."
    - kind: drift
      target: src/backend/app/domain/services/notification_service.py:352
      resolution: proceed
      evidence: "Ohne die F-6/F-8-Schreibklassen-Definition wäre das required Gate am ersten Tag rot oder ertränke in Exemptions (NFR-018-§1-Klasse). Die Ausnahmenliste ist eine Eingabe aus F-6/F-8. Zudem: Checks in den bestehenden required Job `static / Static CI Tests` einziehen, keine neuen required Contexts (NFR-018 §4)."
---

## Description

Die Konsolidierung wird vom Zustand zum Invariant: die beiden F-6-Scanner
flippen vom Ratchet- in den Zero-Threshold-Modus und ziehen als Hooks in den
bestehenden required Job `static / Static CI Tests` ein — eine
Next-Occurrence-Berechnung außerhalb der `RecurrenceEngine` oder ein
Propagations-Write am `NotificationPropagationService` vorbei blockiert ab
dann jeden PR mechanisch, mit begründeten Exemption-Markern nach dem
#1046-Muster und Vakuum-Selbsttests nach #946 (synthetische Drift muss das
Gate rot machen). Es entstehen keine neuen required Contexts (NFR-018 §4).

Der Spec-Nachzug schließt das Outcome: die beiden Grenzregeln (inklusive der
Kanten-Unterscheidung der Fehlerpolitiken aus F-9) stehen in `BACKEND.md`,
REQ-022 und REQ-030 übernehmen die Zuständigkeitsgrenzen (REQ-006 trägt sie
bereits), und ADR-008 wird — im selben Change, wie seine eigene Statusregel es
verlangt — von `Proposed` auf `Accepted` gehoben und gemäß seiner
Consequence-Liste in die MkDocs-Serie (DE/EN) gespiegelt.

## Acceptance criteria

- [ ] **acceptance-1** Die beiden F-6-Scanner laufen im Zero-Threshold-Modus als Hooks im bestehenden required Job `static / Static CI Tests`; ein synthetischer Verstoß gegen Grenze (a) oder (b) macht den jeweiligen Hook rot; der F-6-Ratchet-Test ist über seine Obsoleszenz-Regel abgelöst.
- [ ] **acceptance-2** Beide Gates tragen Vakuum-Selbsttests nach dem #946-Muster: synthetische Drift-Quellen (neuer timedelta-Vorschub; direkter Notification-Repo-Write) werden nachweislich erkannt; Exemption-Marker verlangen eine Begründung von Mindestlänge.
- [ ] **acceptance-3** `BACKEND.md` dokumentiert beide Grenzregeln samt der Fehlerpolitik-Grenze (atomar innerhalb des Abschluss-Übergangs, best-effort/Nachhol außerhalb).
- [ ] **acceptance-4** REQ-022 und REQ-030 referenzieren die Zuständigkeitsgrenzen (RecurrenceEngine als einzige Terminautorität; NotificationPropagationService als einziger Propagationspfad), konsistent mit der bestehenden REQ-006-Referenz.
- [ ] **acceptance-5** ADR-008 steht auf `Accepted` — im selben Change wie acceptance-4 (die ADR-eigene Statusregel verlangt Phase-0-Inventar + REQ-Übernahme) — und ist in die MkDocs-Doku-Serie gespiegelt (DE-kanonisch + EN-Mirror, DOCS.md-Konventionen).

## Test hooks

- **acceptance-1** — pre-commit-Hook-Lauf + Selbsttest Zero-Threshold; Obsoleszenz-Nachweis (Ratchet-Test entfernt) — pending
- **acceptance-2** — Vakuum-Selbsttest-Dateien je Gate (synthetische Drift → rot; Marker-Begründungspflicht) — pending
- **acceptance-3** — Review-Check BACKEND.md-Abschnitt — pending
- **acceptance-4** — Grep-/Review-Check REQ-022/REQ-030-Referenzen — pending
- **acceptance-5** — ADR-Statusfeld + docs-Build (`mkdocs build --strict`) über die gespiegelte Seite — pending

## Consistency notes

**overlap F-10 ↔ F-6 (`proceed`, Rationale):** Spiegelbefund zur F-6-Notiz.
Beide Features nutzen **dieselbe** Scanner-Implementierung; F-10 ändert nur den
Modus (Zero-Threshold statt Ratchet) und den Ort (required static-Lane). Der
Ratchet-Test aus F-6 wird nicht gelöscht, sondern über seine eigene
Obsoleszenz-Regel abgelöst — genau der in F-6 acceptance-3 vereinbarte
Mechanismus. Es existiert zu keinem Zeitpunkt eine zweite Erkennungslogik.

**drift Gate-Scharfschaltung (`proceed`):** Das Gate übernimmt die
Schreibklassen-/Zähl-Definition aus F-6 unverändert als Exemption-Vokabular —
sie ist Eingabe, kein F-10-Freihandwerk. Die Checks ziehen in den bestehenden
required Job ein statt neue required Contexts zu erzeugen; eine Promotion
weiterer Contexts bleibt eine NFR-018-§4-Entscheidung auf gemessener Historie.

**prior-art ADR-Statusregel (`proceed`):** Der Accepted-Flip und die
REQ-022/030-Updates landen im selben Change, sonst widerspräche das ADR seiner
eigenen Statusbedingung. REQ-006 ist bereits nachgezogen (ein Drittel erledigt).

## Risks

- Die Gates sind erst nach F-7/F-8 scharf schaltbar (Zählungen auf null);
  ein früherer Einzug wäre am ersten Tag rot — die Feature-Reihenfolge ist
  deshalb Abhängigkeit, nicht Empfehlung.
- required-Lane-Hooks laufen auf jedem PR: die Scanner müssen schnell bleiben
  (AST-Scan über app/, kein Testlauf) — Budget analog check_layer_imports.
