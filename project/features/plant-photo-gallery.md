---
id: F-2
title: Pflanzenfoto-Galerie-Ansicht
status: done
roadmap_item: R-1
sprint: 1
created: 2026-06-20
ended: 2026-06-20
verifies_sprint_value: acceptance-1
consistency_check:
  performed_at: 2026-06-20
  agent_version: feature-consistency-reviewer@cb010f89
  findings:
    - kind: clean
      target: project/features/
      resolution: proceed
      evidence: "project/features/ leer (erste Decomposition) — keine Feature-zu-Feature-Überlappung möglich."
    - kind: prior-art
      target: src/frontend/src/pages/stammdaten/ReferenceImageGallery.tsx:116
      resolution: proceed
      evidence: "MUI ImageList-Galerie mit Lazy-Load, responsivem cols, Skeleton-Loading und Empty-State — als Vorlage wiederverwenden (andere Datenquelle, keine Doppelarbeit)."
    - kind: prior-art
      target: src/frontend/src/pages/stammdaten/ReferenceImageCuration.tsx:163
      resolution: proceed
      evidence: "Tile mit Lösch-IconButton + Bestätigungs-Dialog — Muster für 'Foto entfernen' wiederverwendbar."
    - kind: prior-art
      target: src/frontend/src/pages/pflanzen/PlantInstanceDetailPage.tsx:878
      resolution: proceed
      evidence: "Bestehende Tab-Leiste (useTabUrl); REQ-034 §2.3 nennt genau diese Seite als Galerie-Host (neuer Tab 'Fotos'). Kein neuer Seitentyp."
    - kind: prior-art
      target: src/frontend/src/components/identification/ImageCapturePanel.tsx
      resolution: revisit-after "F-1 liefert POST .../plant-instances/{key}/photos"
      evidence: "REQ-034 §2.2 schreibt Wiederverwendung des Capture-Flows vor; der eigentliche Upload (acceptance-Leerzustand-CTA) wird erst real, wenn F-1 das Endpoint bereitstellt."
    - kind: drift
      target: spec/req/REQ-034_Pflanzenfoto-Galerie.md
      resolution: proceed
      evidence: "Ursprüngliche F-2-ACs waren eine unvollständige Teilmenge von REQ-034 §2.3/§8 (fehlten Lightbox, Cover-Foto, Thumbnail-only, i18n). Aufgelöst: ACs an REQ-034 AC-02/-03/-06/-13/-14 angeglichen."
---

## Description

In der Pflanzen-Detailansicht (`PlantInstanceDetailPage.tsx`) erhalten Nutzer einen
neuen Tab „Fotos" mit einem Thumbnail-Grid (512-px-Variante), einer Lightbox
(1280 px), Aktionen zum Löschen einzelner Fotos und zum Setzen des Titelbilds. Das
Cover-Foto erscheint als Vorschau im Info-Tab und in der Listenansicht; Pflanzen
ohne Foto zeigen einen neutralen Platzhalter. So verfolgen Nutzer den
Wachstumsverlauf visuell über die Zeit und erkennen ihre Pflanzen in der Übersicht
wieder.

Dieses Feature ist der **Frontend-/Anzeige-Anteil** der Pflanzenfoto-Galerie
(REQ-034 §1.3, §2.3). Der Backend-/Upload-/Storage-/Erasure-Anteil liegt in F-1.
Wiederverwendbare Muster bestehen bereits: das MUI-ImageList-Grid samt
Empty-State/Skeleton (`ReferenceImageGallery.tsx`), das Entfernen-mit-Bestätigung
(`ReferenceImageCuration.tsx`) und der Capture-Flow (`ImageCapturePanel.tsx`).

## Acceptance criteria

- [ ] **acceptance-1** Die Pflanzen-Detailseite zeigt einen Tab „Fotos" mit einem chronologisch sortierten Thumbnail-Grid (neueste zuerst).
- [ ] **acceptance-2** Galerie und Listenansichten laden ausschließlich Thumbnails (512 px); das Originalbild wird nur in der Lightbox (1280 px) geladen.
- [ ] **acceptance-3** Ein Klick auf ein Vorschaubild öffnet es in der Lightbox in voller Größe.
- [ ] **acceptance-4** Ein berechtigter Nutzer kann über die UI ein Foto löschen und ein Foto als Titelbild setzen; das Cover erscheint danach als Vorschau im Info-Tab und in der Listenansicht.
- [ ] **acceptance-5** Eine Pflanze ohne Fotos zeigt einen neutralen Platzhalter bzw. Leerzustand mit Upload-Aufforderung.
- [ ] **acceptance-6** Das Frontend referenziert ausschließlich `attachment_id` und die Stable URI (`/api/v1/t/{slug}/attachments/...`) — kein Storage-Backend, kein Bucket, keine Region.
- [ ] **acceptance-7** Ein `viewer` sieht die Galerie, aber ohne Upload-/Löschen-/Cover-Aktionen; alle Galerie-UI-Texte sind i18n DE/EN (DE Default/Fallback).

## Test hooks

- **acceptance-1** — src/frontend vitest PlantPhotoGalleryTab.test.tsx (neu) — pending
- **acceptance-2** — src/frontend vitest PlantPhotoGallery.test.tsx (thumbnails-only) — pending
- **acceptance-3** — src/frontend vitest PlantPhotoGallery.test.tsx (lightbox) — pending
- **acceptance-4** — src/frontend vitest PlantPhotoGallery.test.tsx (delete + set-cover) — pending
- **acceptance-5** — src/frontend vitest PlantPhotoGallery.test.tsx (empty-state) — pending
- **acceptance-6** — manueller Code-Review / src/frontend API-Layer-Test: nur attachment_id + Stable URI — pending
- **acceptance-7** — src/frontend vitest PlantPhotoGallery.test.tsx (viewer-permissions) + i18n-Key-Check — pending

## Consistency notes

Konsistenzprüfung durch den `feature-consistency-reviewer`-Agenten am 2026-06-20
(agent_version `feature-consistency-reviewer@cb010f89`). Kein `overlap`/`duplication`
gefunden → der `draft → ready`-Gate ist aus dieser Prüfung **nicht** blockiert. Im
Backend existiert kein `/plant-instances/{key}/photos`-Endpoint und kein
`cover_photo_ref`; das vorhandene `photo_refs` hängt an `PlantDiaryEntry` (REQ-013),
nicht an der Instanz — F-2 implementiert also kein vorhandenes Verhalten neu.

- **clean (project/features/):** Erstes decomptes Feature; keine Geschwister-Kollision.
  Resolution `proceed`.
- **prior-art (ReferenceImageGallery.tsx:116):** MUI-ImageList-Grid mit
  responsivem `cols`, Skeleton und Empty-State — Vorlage für acceptance-1/-5.
  Bedient REQ-029-A-Referenzbilder (andere Datenquelle), daher Wiederverwendung,
  keine Duplikation. Resolution `proceed`.
- **prior-art (ReferenceImageCuration.tsx:163):** Entfernen-mit-Bestätigung-Muster
  für acceptance-4 (Löschen). Semantik dort = Soft-Deselect; das Hard-Delete-Verhalten
  liegt in F-1. Resolution `proceed`.
- **prior-art (PlantInstanceDetailPage.tsx:878):** Der vorgesehene Einbettungsort;
  die Galerie wird ein zusätzlicher Tab, kein neuer Seitentyp. Resolution `proceed`.
- **prior-art (ImageCapturePanel.tsx):** REQ-034 §2.2 verlangt Wiederverwendung des
  Capture-Flows. acceptance-5 rendert nur den Leerzustand-Call-to-Action; der
  eigentliche Upload (Capture + `POST .../photos`) ist F-1-Scope. Bei
  `ready → in_progress` erneut prüfen, sobald F-1 das Endpoint liefert
  (`revisit-after`).
- **drift (REQ-034):** Die ursprünglichen F-2-ACs ließen Lightbox, Cover-Foto,
  Thumbnail-only-Performance und i18n aus REQ-034 §2.3/§8 aus. **Aufgelöst:** Die ACs
  oben sind an REQ-034 AC-02/-03/-06/-13/-14 angeglichen (Single-Source). Resolution
  `proceed`.

## Risks

- Die F-1/F-2-Grenze berührt sich bei acceptance-5 („Upload-Aufforderung"):
  sicherstellen, dass F-2 nur den CTA im Leerzustand rendert und der
  Upload-Mechanismus selbst F-1 bleibt. Bei `ready → in_progress` Konsistenzprüfung
  re-run (s. `revisit-after`-Befund).

## References

- `spec/req/REQ-034_Pflanzenfoto-Galerie.md` (kanonische Anforderung, §2.3, §8 AC-01..AC-14)
- `spec/nfr/NFR-013_Speicheranbindung-Object-Storage.md` (Stable URI, Thumbnails)
- Schwester-Feature: F-1 (Foto-Upload & Speicherung, Backend)
