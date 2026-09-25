# Pre-Analyse #1770 — deduplizierte Inhalte haben einen einzigen Eigentümer

- Issue: https://github.com/nolte/kamerplanter/issues/1770 (Labels `bug`, `backend`)
- Klassifikation: `security` (sekundär `bug`) — Art. 17 wirkt auf Inhalte Dritter (GDPR-006, SEC-007)
- Anforderungs-Gate: Operator-Override (Repository-Owner, 2026-09-25, volle Autonomie, alle Gates vorab freigegeben); die Akzeptanzkriterien im Issue sind testbar formuliert.
- Route: direkt (ein kohärenter PR-Strang: Eigentümerschaft deduplizierter Inhalte in Attachments + Referenz-Index; keine Roadmap-Änderung).

## Nachgemessene Ursache (established)

| Behauptung | Messung | Ergebnis |
|---|---|---|
| Upload gibt zweitem Hochlader den Datensatz des ersten | `attachment_service.py:146-157` (develop `bd697827a`); `tests/integration/test_attachment_dedup_ownership.py` gegen alten Code: `b.key == a.key`, `b.created_by == A` | bestätigt |
| Löschung A trifft Inhalt B (pest_reference) | Scratch-Messung reale ArangoDB + LocalFs: nach `erase_account(A)` B-Datensatz `None`, Bytes gelöscht | bestätigt |
| Löschung A anonymisiert B-Upload (diary) | gleiche Messung: B-Datensatz `_anonymized`; `erase_account(B)` erreicht nichts | bestätigt |
| Mandantenübergreifende Dedup bei Attachments | `find_by_sha256` filtert `tenant_key`, Storage-Key `t/{tenant}/…` | widerlegt (keine) |
| Referenz-Index behält Provenienz des ersten | `inference-service/app/vectordb/repository.py:105` ON CONFLICT ohne `contributed_by`/`tenant_key`; pgvector-Messung | bestätigt, **mandantenübergreifend** (UNIQUE ohne tenant) |
| Zusätzlich gefunden | `PestImageService.delete` löscht über `AttachmentService.delete` den (fremden) Datensatz samt Bytes | bestätigt (gleiche Klasse) |

## Arbeitspakete

| ID | Problem | AK | Dateien | Spezialist |
|---|---|---|---|---|
| WP1 | Datensatz pro Hochlader, Objekt geteilt, Referenzzählung beim Löschen | Integrationstests rot→grün | attachment_service, attachment_repository, adapters, storage_tasks, collections | Generalist (ein Autor über die Invarianten, wie #1761/#1776) |
| WP2 | Erasure-Bericht zählt entfernt/geteilt-behalten | Report + Checkpoint-Felder | privacy_service, models/privacy | Generalist |
| WP3 | Migration v0062 (Index + Split der Beitrags-Datensätze) | Dry-run schreibt nichts, 2. Lauf 0 Änderungen, Erasure danach korrekt | migrations/versions | Generalist |
| WP4 | Referenz-Index: Record-ID pro Beitragendem | Unit rot→grün, pgvector-Messung | reference_image_service | Generalist |
| WP5 | Reach-Probe geteilte Datei | T2 reached | scripts/reach, project/reach-probes | Generalist (keine Reach-Spezialisten-Schreibrolle) |
| WP6 | Spec + Doku | REQ-025 v1.12, NFR-013 v1.5, Datenschutz-Doku | spec, docs | `mkdocs-documentation` |
| WP7 | Reviews | Befunde behoben/als Issue | — | `nolte-engineering:gdpr-data-protection-reviewer`, `nolte-engineering:code-security-reviewer`, `/code-review medium` |

Abhängigkeiten: WP1 → WP2 → WP3 → WP5; WP4 unabhängig; WP6/WP7 zuletzt.
