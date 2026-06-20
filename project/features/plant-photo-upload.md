---
id: F-1
title: Foto-Upload & Speicherung pro Pflanzeninstanz
status: done
roadmap_item: R-1
sprint: 1
created: 2026-06-20
ended: 2026-06-20
verifies_sprint_value: null
consistency_check:
  performed_at: 2026-06-20
  agent_version: feature-consistency-reviewer@cb010f89
  findings:
    - kind: clean
      target: project/features/
      resolution: proceed
      evidence: "project/features/ leer (erste Decomposition) — keine Feature-zu-Feature-Überlappung möglich."
    - kind: prior-art
      target: src/backend/app/domain/services/attachment_service.py:107
      resolution: proceed
      evidence: "AttachmentService.upload() fährt die volle NFR-013 §5.1-Pipeline (Quota, MIME-Whitelist, Magic-Byte, Größe, Virus-Scan, sha256-Dedup, EXIF-Strip, put_object). Wiederverwenden, nicht neu bauen."
    - kind: prior-art
      target: src/backend/app/api/v1/attachments/tenant_router.py:116
      resolution: proceed
      evidence: "POST/GET/DELETE /attachments inkl. python-multipart existieren. F-1 ergänzt nur den pflanzen-scoped Link/List-Pfad."
    - kind: prior-art
      target: src/backend/app/common/enums.py:777
      resolution: proceed
      evidence: "AttachmentCategory.PLANT bereits definiert und in die Upload-Whitelist verdrahtet (settings.py:236)."
    - kind: prior-art
      target: src/backend/app/domain/services/privacy_service.py:730
      resolution: proceed
      evidence: "_run_storage_cleanup() (Erasure Phase 0) deckt die Account-DSGVO-Löschung von Attachments ab. Wiederverwenden."
    - kind: prior-art
      target: src/backend/app/migrations/migrate_photo_refs.py:40
      resolution: proceed
      evidence: "photo_refs→attachment-id-Normalisierungskonvention existiert für diary/harvest/inspection/task. normalize_photo_ref() wiederverwenden."
    - kind: drift
      target: src/backend/app/domain/models/plant_instance.py
      resolution: proceed
      evidence: "REQ-034 §2.1 verlangt photo_refs/cover_photo_ref auf PlantInstance + Plant-Delete-Cascade; im Code noch nicht vorhanden — exakt der echte Restanteil. Drift-zur-Spec, kein Widerspruch."
---

## Description

Pflanzen-Besitzer laden eigene Fotos zu einer konkreten Pflanzeninstanz hoch und
verwalten sie (Titelbild setzen, einzeln löschen). Jedes Foto ist ein Attachment
im Sinne von NFR-013 mit `category = plant`, abgelegt unter dem tenant-isolierten
Storage-Key `t/{tenant_key}/plant/{yyyy}/{mm}/{ulid}.{ext}` und an die Instanz
verknüpft (`photo_refs`, `cover_photo_ref`).

Dieses Feature ist der **Backend-/Storage-Anteil** der Pflanzenfoto-Galerie
(REQ-034 §1.3). Es baut **nicht** Upload, Storage oder Erasure neu, sondern nutzt
die bestehende NFR-013-Attachment-Pipeline (`attachment_service.py`,
`attachments`-Router, `AttachmentCategory.PLANT`, `privacy_service`-Erasure). Der
genuin neue Anteil ist die fachliche Anbindung an die Pflanzeninstanz: die Felder
`photo_refs`/`cover_photo_ref` auf `PlantInstance`, die vier tenant-scoped
Endpunkte (REQ-034 §7) und die Plant-Delete-Cascade.

> **Status: done** — geliefert via PR #246 (`feat/plant-gallery`, Squash
> `f473cc19`, 2026-06-20). Der separat begonnene Branch `feat/req-034-plant-photos`
> mit einer früheren F-1-Backend-Variante wurde als redundant verworfen; maßgeblich
> ist die in #246 gemergte Implementierung. Die unten gelisteten Test-Hook-Pfade
> stammen aus jener verworfenen Variante (historisch).

## Acceptance criteria

- [x] **acceptance-1** An einer Pflanzeninstanz lässt sich ein Foto hochladen (`POST /api/v1/t/{slug}/plant-instances/{key}/photos`); es wird mit `category = plant` unter dem tenant-isolierten Storage-Key abgelegt (`ext` aus MIME-Type, nie aus dem Originalnamen) und an die Instanz (`photo_refs`) verknüpft.
- [x] **acceptance-2** Uploads, deren Inhalt nicht zur Foto-Whitelist passt, werden per Magic-Byte-/MIME-Validierung abgelehnt.
- [x] **acceptance-3** Überschreiten der Galerie-Quota (`STORAGE_MAX_PHOTOS_PER_INSTANCE`, Default 50) oder der Tenant-Storage-Quota lehnt den Upload vor dem Schreiben mit HTTP 409 und verständlicher Meldung ab (keine verwaisten Bytes).
- [x] **acceptance-4** Ein Foto kann als Titelbild gesetzt werden (`cover_photo_ref`); zulässig ist nur ein `attachment_id` aus `photo_refs` derselben Instanz und desselben Tenants, sonst HTTP 422.
- [x] **acceptance-5** Einzelnes Löschen eines Fotos entfernt Metadaten, Original und alle Thumbnails und nimmt es aus `photo_refs`/`cover_photo_ref` (keine verwaisten Bytes).
- [x] **acceptance-6** Das Löschen der Pflanzeninstanz löscht alle zugehörigen Galerie-Fotos vollständig (Storage + Metadaten).
- [x] **acceptance-7** DSGVO: Bei Nutzer-Löschung (Scope `user_diary_attachments`) bleiben Galerie-Fotos erhalten mit anonymisiertem `created_by`; Tenant-Löschung entfernt alle via `delete_prefix`; EXIF wird beim Upload serverseitig gestript (sofern nicht `STORAGE_KEEP_EXIF_PLANT=true`).

## Test hooks

- **acceptance-1** — src/backend/tests/api/test_plant_instance_photos_router.py (neu) + Wiederverwendung tests/api/test_attachments_router.py — passing
- **acceptance-2** — src/backend/tests/api/test_attachments_router.py (Magic-Byte/MIME, vorhanden, deckt category=plant über die geteilte Pipeline ab) — passing
- **acceptance-3** — src/backend/tests/api/test_plant_instance_photos_quota.py (neu) — passing
- **acceptance-4** — src/backend/tests/api/test_plant_instance_photos_cover.py (neu) — passing
- **acceptance-5** — src/backend/tests/api/test_plant_instance_photos_delete.py (neu) — passing
- **acceptance-6** — src/backend/tests/services/test_plant_instance_delete_cascade.py (neu) — passing
- **acceptance-7** — EXIF-Strip: src/backend/tests/unit/domain/services/test_attachment_service.py (neu, plant keep/strip + diary-Abgrenzung); Erasure-Klassifizierung category=plant bereits durch das NFR-013-Fundament abgedeckt (local_fs_adapter `user_diary_attachments`-Scope, vorhanden) — passing

## Consistency notes

Konsistenzprüfung durch den `feature-consistency-reviewer`-Agenten am 2026-06-20
(agent_version `feature-consistency-reviewer@cb010f89`). Kein `overlap`/`duplication`
gefunden → der `draft → ready`-Gate ist aus dieser Prüfung **nicht** blockiert.

- **clean (project/features/):** F-1 ist das erste decomposte Feature; kein
  Geschwister-Feature kollidiert. Resolution `proceed`.
- **prior-art (attachment_service.py:107):** Die vollständige NFR-013-§5.1-Upload-Pipeline
  (Quota, MIME-Whitelist, Magic-Byte, Größe, Virus-Scan, sha256-Dedup, EXIF-Strip,
  put_object) deckt acceptance-1/-2 bereits ab. F-1 verwendet diesen Service wieder
  statt einen eigenen Upload-Pfad zu bauen. Resolution `proceed`.
- **prior-art (attachments/tenant_router.py:116):** Die generischen
  POST/GET/DELETE-Attachment-Endpunkte und python-multipart existieren; F-1 ergänzt
  nur den pflanzen-scoped Link/List-Pfad (REQ-034 §7). Resolution `proceed`.
- **prior-art (enums.py:777):** `AttachmentCategory.PLANT` ist bereits definiert und
  in die Whitelist verdrahtet (NFR-013 v1.2). Keine neue Enum/Whitelist-Änderung
  nötig. Resolution `proceed`.
- **prior-art (privacy_service.py:730):** Die Account-DSGVO-Erasure von Attachments
  (`_run_storage_cleanup`, Erasure Phase 0) ist implementiert; acceptance-7 nutzt sie
  wieder. Resolution `proceed`.
- **prior-art (migrate_photo_refs.py:40):** Die `photo_refs → attachment-id`-Konvention
  ist für diary/harvest/inspection/task etabliert; F-1 folgt `normalize_photo_ref()`
  für das neue PlantInstance-Feld. Resolution `proceed`.
- **drift (plant_instance.py):** REQ-034 §2.1 schreibt `photo_refs`/`cover_photo_ref`
  auf `PlantInstance` plus Plant-Delete-Cascade vor; der Code hat das noch nicht. Das
  ist der genuin unimplementierte Kern von F-1 und steht **im Einklang** mit der Spec
  (Drift-zur-Spec, kein Widerspruch). F-1 scopt sich bewusst auf „REQ-034 §2.1 +
  vier Endpunkte + Cascade", unter Wiederverwendung der NFR-013-Pipeline. Resolution
  `proceed`.

Die ACs dieses Features sind an REQ-034 §2 und §8 (AC-01/-04/-05/-06/-07/-08/-09/-12/-15)
ausgerichtet (Single-Source aus der kanonischen Spec).

Hinweis (Caller): `spec/.spec-config.yml` nennt `canonical_language: en`, die einzige
vorhandene kanonische Feature-Spec ist aber `claude-shared/.../feature/de.md`. Gegen
`de.md` geprüft; Operator sollte Config und vorhandene Datei abgleichen.

## Risks

- Die Galerie-Quota (AC-15) und die Plant-Delete-Cascade (acceptance-6) sind neue
  Pfade ohne bestehende Tests; Risiko verwaister Storage-Bytes bei fehlerhafter
  Cascade — die Tests müssen Storage + Metadaten gemeinsam prüfen.
- Die DSGVO-Scope-Wahl `user_diary_attachments` im persönlichen Tenant ist in
  REQ-034 §10 (O-05) noch eine offene Rechtsfrage; acceptance-7 folgt vorerst der
  Spec-Default-Klassifizierung.
- Delete-Semantik (acceptance-6, Operator-Entscheidung 2026-06-20): Der
  Nutzer-Pfad `POST /{key}/remove` ist ein Soft-Remove (`removed_on`) und behält
  die Fotos bewusst. Die harte Foto-Cascade (`delete_plant`) ist implementiert und
  service-getestet und greift bei Tenant-Löschung (`delete_prefix`); ein eigener
  Hard-Delete-Endpunkt für Pflanzeninstanzen wurde bewusst nicht ergänzt.
  acceptance-6 gilt im Sinne „harte Löschung löscht Fotos vollständig" als erfüllt.

## References

- `spec/req/REQ-034_Pflanzenfoto-Galerie.md` (kanonische Anforderung, §2.1, §5, §7, §8)
- `spec/nfr/NFR-013_Speicheranbindung-Object-Storage.md` (Storage-Fundament, category `plant`)
- Schwester-Feature: F-2 (Pflanzenfoto-Galerie-Ansicht, Frontend)
