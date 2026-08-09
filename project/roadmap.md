# Roadmap

Diese Datei ist die Arbeits-Queue, die von `spec/project/roadmap/` geregelt wird.
Jeder Eintrag ist eine Level-3-Überschrift, gefolgt von einem `yaml`-Codeblock
(`id`, `title`, `detail`, `outcomes`, `target_sprint`, `mvp`, `status` — in dieser
Reihenfolge) und einem Freitext-Body. Der Detailgrad (`detail`: `fine` /
`coarse` / `backlog`) und der Status-Lebenszyklus (`status`: `proposed` →
`active` → `done`, dazu `cancelled` aus `proposed`/`active`) werden durch
`roadmap-plan` (Hinzufügen/Ändern) und `roadmap-refine` (Detail-Invariante)
durchgesetzt — nicht von Hand in dieser Datei.

Roadmap-Einträge tragen die IDs `R-1`, `R-2`, … monoton aufsteigend; eine ID wird
über die gesamte Projekt-Lebenszeit nie wiederverwendet. Die Queue startet leer:
Der erste von `roadmap-plan` vergebene Eintrag ist `R-1`. Outcome-IDs (`O-n` in
`goals.md`) sind ein davon unabhängiger Zähler — die Ströme nicht kreuzen.

Die folgenden Phasen sind reine Dokumentation (kein Schema). Einträge werden
ihnen über `roadmap-plan` zugeordnet.

## Phase 1 — Fundament & Kernpflege

<!-- Einträge werden ausschließlich über `roadmap-plan` hinzugefügt. -->

## Phase 2 — Stabilisierung & Betrieb

### R-14 — Stammdaten-Mandanten-Scoping (Species & Cultivar)

```yaml
id: R-14
title: Stammdaten-Mandanten-Scoping (Species & Cultivar)
detail: fine
outcomes: [O-4]
target_sprint: 2
mvp: true
status: done
```

**MVP-Flip (Operator-Entscheid 2026-08-09):** `mvp: false → true`. Erlaubt, weil
`mvp_status` (mission.md) noch nicht `stabilised` ist (`in_progress`) — der
Mission-Spec erlaubt den Flip jederzeit vor der Stabilisierung. Der Operator hat
Species-Mandanten-Isolation (O-4) bewusst in den MVP-Scope gezogen, um Sprint 2
jetzt umzusetzen (überschreibt die frühere Zurückstellung).

Species und Cultivar erhalten echte Mandanten-Ownership (REQ-001 v4.0): ein
`tenant_key` auf beiden Modellen, auf jedem Write-Pfad gesetzt, plus ein
geteiltes #324-Union-Leseprädikat statt der heute 3–4-fach duplizierten
Inline-AQL — so bleiben globale Seed-Stammdaten für alle sichtbar, während
tenant-eigene Records nicht mehr an fremde Mandanten leaken. Umfasst als
Architektur-Teil die bislang fehlende Tenant-Auflösung für globale-aber-
tenant-bewusste Routen (heute ist `get_current_tenant` an `/t/{slug}/` gebunden)
und eine Migration, die die zu bestätigende **Cutover-Backfill-Policy** trägt
(Bestands-`origin:tenant`-Species bleiben per Policy global). Entblockt durch
#780 / REQ-049.

Sprint 2 liefert den **species-only**-Schnitt (Cultivar und die
`tenant_has_access`-Edge sind bewusst als Folge-Requirement zurückgestellt,
Operator-Entscheid „Species-only zuerst"). Backfill = **Cutover-Regel** (final,
teach-back-bestätigt). Requirement: `project/requirements/species-tenant-ownership.md`.

- [x] F-3 — Species-Mandanten-Ownership: Feld, Write-Stamping & Cutover-Migration (`species-tenant-key-and-cutover`)
- [x] F-4 — Geteiltes Mandanten-Union-Leseprädikat (Extraktion) (`tenant-scope-union-predicate`)
- [x] F-5 — Tenant-bewusstes Species-Lesen auf der globalen Route (`species-tenant-aware-read`)

<!-- Herkunft: Issue #808 (issue-orchestrate → roadmap-plan, 2026-08-09).
Requirements-Override (Operator): die τ_high-Erhebung via `requirements-elicit`
erfolgt beim `promote`→`fine` / Sprint-Pull, nicht jetzt (Item ist `coarse` und
ungeplant). Die Backfill-Cutover-Policy ist ein Kandidat, final in der
Feature-Zerlegung zu bestätigen. -->

## Phase 3 — Erweiterung & Intelligenz

### R-1 — Pflanzenfoto-Galerie

```yaml
id: R-1
title: Pflanzenfoto-Galerie
detail: fine
outcomes: [O-2]
target_sprint: 1
mvp: true
status: done
```

Pflanzen-Besitzer laden eigene Fotos ihrer Pflanzen hoch und sehen sie als
chronologische Galerie je Pflanze — so dokumentieren und verfolgen sie den
Wachstumsverlauf visuell über die gesamte Lebensphase. Die Bilder werden über
das bestehende, admin-konfigurierbare Object-Storage-Backend (local-fs/S3,
NFR-013) abgelegt und sind in die DSGVO-Löschung eingebunden. Kanonische
Anforderung ist die bereits vorhandene Spec REQ-034.

**Status: abgeschlossen (`done`).** Geliefert via PR #246 (`feat/plant-gallery`,
Squash `f473cc19`, 2026-06-20) — Backend und Frontend-Galerie vollständig.

- [ ] F-1 — Foto-Upload & Speicherung (`plant-photo-upload`)
- [ ] F-2 — Pflanzenfoto-Galerie-Ansicht (`plant-photo-gallery`)

<!-- Der ursprünglich vorgesehene `dinov2-embedding-hook` entfällt als eigenes
Feature: Die DINOv2-Infrastruktur existiert bereits (REQ-029-A), und der optionale
Referenz-Rückfluss ist in REQ-034 §4 spezifiziert. Konsistenzprüfung 2026-06-20,
resolution: merge-into REQ-034. -->
