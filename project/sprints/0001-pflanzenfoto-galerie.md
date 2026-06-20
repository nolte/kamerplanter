---
number: 1
status: closed
started: 2026-06-20
ended: 2026-06-20
value_statement: Pflanzen-Besitzer fügen ihren Pflanzen eigene Fotos hinzu und sehen sie als Galerie in der Detailansicht.
artifact_ref: develop@f473cc19 (PR #246)
last_commit: f473cc197aa56cfb1423b6e8f32e82b7e58def13
roadmap_items: [R-1]
features: [F-1, F-2]
---

## Goal

Pflanzen-Besitzer können an einer Pflanzeninstanz eigene Fotos hinzufügen (Webcam,
Smartphone-Kamera oder Datei-Upload) und sehen sie als chronologische Galerie in
der Pflanzen-Detailansicht, inklusive Titelbild-Vorschau in Info- und
Listenansicht. Erfolg beim Abschluss: Ein Nutzer lädt ein Foto hoch und es
erscheint im neuen „Fotos"-Tab der Detailseite (verifiziert durch F-2
`acceptance-1`). Der Sprint baut auf dem vorhandenen NFR-013-Storage-Fundament auf
und setzt die kanonische Anforderung REQ-034 um.

## Features

- [F-1](../features/plant-photo-upload.md) — Foto-Upload & Speicherung — status: done
- [F-2](../features/plant-photo-gallery.md) — Pflanzenfoto-Galerie-Ansicht — status: done

## Out of scope

- DINOv2-Referenz-Rückfluss der Galerie-Fotos in den Erkennungs-Index (R-1,
  REQ-034 §4) — DINOv2-Infrastruktur existiert bereits, Verdrahtung als
  `merge-into REQ-034` aus der Decomposition ausgeschlossen.
- Stammdaten-Galerie an Species/Cultivar (REQ-034 §1.3 Out of Scope).
- Bildbearbeitung im Client und Video-Anhänge (REQ-034 §1.3 Out of Scope).

## Review notes

Retroaktive Reconciliation (2026-06-20): REQ-034 wurde out-of-band über **PR #246**
(`feat/plant-gallery`, Squash `f473cc19`) geliefert — Backend (F-1) und
Frontend-Galerie (F-2) plus Foto-Metadaten, Quality-Check, DINOv2-Hook und E2E. Der
Mehrwert-Verifizierer F-2 `acceptance-1` (die Galerie zeigt die Fotos der Pflanze)
ist durch #246 erfüllt; Artefakt `develop@f473cc19`. Sprint und Features wurden daher
nachträglich auf `done`/`closed` gesetzt. Der parallel begonnene Branch
`feat/req-034-plant-photos` (nur F-1-Backend) wurde als redundant verworfen.

Release-Verkettung: nicht angestoßen (reine Reconciliation, kein eigener Release-Cut).
