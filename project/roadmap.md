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

<!-- Einträge werden ausschließlich über `roadmap-plan` hinzugefügt. -->

## Phase 3 — Erweiterung & Intelligenz

### R-1 — Pflanzenfoto-Galerie

```yaml
id: R-1
title: Pflanzenfoto-Galerie
detail: fine
outcomes: [O-2]
target_sprint: 1
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
