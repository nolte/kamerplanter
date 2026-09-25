# Issue #1771 — Voranalyse (issue-orchestrate)

- **Issue:** #1771 „erasure: pest prototypes orphaned before #1766 are unreachable by account erasure — sweep them" (Autor: nolte, Owner → vertrauenswürdig)
- **Klassifikation:** `bug` (sekundär `security`/Datenschutz) — Art.-17-Rückstand im `pest_embeddings`-Index.
- **Requirements-Gate:** Operator-Override (Repository-Owner, Vollautonomie 2026-09-24/25); das Issue trägt drei prüfbare Akzeptanzkriterien.
- **Route:** direkt (ein Ergebnis, ein PR-Strang, kein Roadmap-Eintrag).

## Ursache — nachgemessen

- established: vor `0c217e570` löschte `PestImageService.delete` nur Link-Dokument + Anhang (`git show 0c217e570^:src/backend/app/domain/services/pest_image_service.py:309-331`), der Index blieb unberührt.
- established: die Art.-17-Löschung findet Prototypen nur über `pest_image_repo.list_for_user(user_key)` → Contribution-Keys (`privacy_service.py:1786-1792`); eine Zeile ohne Dokument ist so unerreichbar.
- established: seit #258 trägt jede Contribution-Zeile `source_record_id = <contribution key>` und `source_url = contribution://<tenant>/<key>` (`pest_image_tasks.py`, `git log -S contribution://`).
- established: der Inference-Service hat keinen Endpunkt, der die Keys der `user_contributed`-Zeilen aufzählt (`main.py` Routen `/pest/reference/*`); `GET /pest/reference/{label}` ist die Galerie-Quelle, pro Klasse, max. 500.
- unestablished: Zahl verwaister Zeilen im Live-Index (Prod nicht gemessen; wird durch den ersten Lauf protokolliert).

## Mechanismus-Entscheidung

Celery-Task auf dem Retention-Beat statt Migration: Migrationen laufen beim Backend-Start und sind bei Fehler fatal (NFR-016/ADR-005) → ein nicht erreichbarer Inference-Service würde den Start crashen; v0061 verzichtet aus demselben Grund auf Service-Aufrufe. Der Task ist idempotent, läuft täglich nach den Erasures, schlägt laut fehl und hält das Ergebnis in `system_settings` fest; er fängt zusätzlich künftige Waisen (erschöpfte Retries von `erase_pest_prototype_task`).

## Arbeitspakete

| ID | Paket | Abnahme | Spezialist |
|----|-------|---------|------------|
| WP1 | inference-service: `POST /pest/reference/contributions/keys` (Keyset-paginiert, nur `user_contributed`, keine Embeddings) | Unit + echte SQL gegen pgvector | Generalist (#1766-Muster) |
| WP2 | backend: Client + Store-Listing, `existing_keys` im Repo, Sweep-Service, Task + Beat, Ergebnis-Record | Red-first über Task→Service→Store→Client | Generalist |
| WP3 | Integrationstest `existing_keys` + Record gegen ArangoDB | grün, `--max-skipped 0` | Generalist |
| WP4 | Reach-Messung + Probe: Waisen weg, lebende/kuratierte bleiben, 2. Lauf 0 | Messung auf Reach-Stack | Generalist |
| WP5 | Doku DE/EN (data-retention, inference-service) | mkdocs strict | `mkdocs-documentation` |
| WP6 | Review | GDPR-Review, `/code-review medium` | `nolte-engineering:gdpr-data-protection-reviewer` |

Abhängigkeiten: WP1 → WP2 → WP3/WP4 → WP5 → WP6.

## Entscheidung AK 3 (deaktivierte Prototypen)

Waisen werden unabhängig von `is_active` gelöscht: ohne Dokument gibt es weder Personenbezug-Auflösung noch Re-Promotion — kein Zweck. Deaktivierte Zeilen MIT Dokument (Demote) bleiben unverändert, bis die DPO-Frage 2 in #1767 beantwortet ist.
