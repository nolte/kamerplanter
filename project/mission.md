---
mission_statement: "Kamerplanter begleitet Pflanzen-Besitzer, Selbst-Hoster und Mitwirkende in einem selbst-gehosteten, mandantenfähigen System von der Aussaat bis zur Nacherntebehandlung mit phasengenauen Pflege-, Dünge- und Umgebungsempfehlungen, datenschutzfreundlich und vollständig in eigener Hand betreibbar."
relevant_outcomes: [O-1, O-2, O-3, O-5, O-8]
audiences:
  - Home grower / hobby gardener / houseplant owner
  - Self-hoster
  - "Maintainer (`nolte`)"
verifies_via: F-2:acceptance-1
time_bound:
  kind: mvp_completion
mvp_status: in_progress
created: 2026-07-02
revised_at: null
---

## Statement

Kamerplanter begleitet Pflanzen-Besitzer, Selbst-Hoster und Mitwirkende in einem
selbst-gehosteten, mandantenfähigen System von der Aussaat bis zur
Nacherntebehandlung mit phasengenauen Pflege-, Dünge- und Umgebungsempfehlungen,
datenschutzfreundlich und vollständig in eigener Hand betreibbar.

- **Specific** — die Aussage benennt *was* (ein selbst-gehostetes System für das
  Pflanzen-Lifecycle-Management) und *für wen* (Pflanzen-Besitzer, Selbst-Hoster
  und Mitwirkende, aufgelöst in `audiences`).
- **Measurable** — `verifies_via: F-2:acceptance-1`: ein Nutzer sieht die Fotos
  einer Pflanze als chronologische Galerie in der Detailansicht.
- **Achievable** — die aktuell definierte MVP-Scheibe ist die
  Pflanzenfoto-Galerie; Roadmap-Eintrag R-1 trägt `mvp: true`, `detail: fine`,
  `target_sprint: 1`. Weitere MVP-Scope-Einträge kommen über `roadmap-plan` hinzu,
  während sich die Lifecycle-Vision entfaltet.
- **Relevant** — `relevant_outcomes: [O-1, O-2, O-3, O-5, O-8]`, jeder Eintrag
  löst zu einem Outcome in `project/goals.md` auf.
- **Time-bound** — `time_bound: { kind: mvp_completion }`; der Anker ist der
  Moment, in dem der MVP-Scope als `achieved` erreicht wird, kein Kalenderdatum.

## Audiences

- **Home grower / hobby gardener / houseplant owner** — der aktuelle
  MVP-Baustein liefert eine chronologische Pflanzenfoto-Galerie, mit der
  Pflanzen-Besitzer den Wachstumsverlauf je Pflanze visuell dokumentieren; die
  phasengenauen Pflege- und Düngeempfehlungen folgen im weiteren MVP-Scope.
- **Self-hoster** — das System ist reproduzierbar auf eigener Hardware
  betreibbar; Selbst-Hoster behalten Upgrades, Backups und Aufbewahrung in
  eigener Hand, mit der Foto-Galerie in das bestehende Object-Storage-Backend
  (NFR-013) eingebunden.
- **Maintainer (`nolte`)** — Änderungen sind spec-gestützt und durch grüne CI
  abgesichert; die Foto-Galerie ist über die kanonische Anforderung REQ-034 und
  Feature F-2 verifiziert, sodass Mitwirkende mit Vertrauen erweitern.

## Verification

Die Mission wird durch Feature **F-2 — Pflanzenfoto-Galerie-Ansicht**,
Acceptance-Kriterium 1 verifiziert: *„Die Pflanzen-Detailseite zeigt einen Tab
‚Fotos' mit einem chronologisch sortierten Thumbnail-Grid (neueste zuerst)."*
Dies ist das `verifies_sprint_value`-Kriterium für Sprint 0001 und ist über PR
#246 (`develop@f473cc19`) erfüllt.

## Source

- **Audience-Artefakt**: `AUDIENCES.md` im Wurzelverzeichnis von `kamerplanter`
  (konsultiert am aktuellen develop-Stand); die drei `audiences`-Einträge sind
  der Pflanzen-Besitzer, der Selbst-Hoster und der Maintainer.
- **Referenzierte Outcomes**: O-1, O-2, O-3, O-5, O-8 aus `project/goals.md`.
- **Autor**: die `mission-define`-Kaskade (Issue nolte/claude-shared#262
  Mission-Authoring-Backfill), 2026-07-02. Anders als die reifen Single-Capability
  Repos ist Kamerplanter ein aktiv in Entwicklung befindliches System: Der
  Roadmap-Scope umfasst bisher R-1 (Pflanzenfoto-Galerie, geliefert). `mvp_status`
  steht daher auf `in_progress`; der Maintainer erweitert den MVP-Scope über
  `roadmap-plan`, während sich die Lifecycle-Vision (O-1..O-8) entfaltet.
