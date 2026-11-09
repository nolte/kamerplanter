# SPEC-10 — Test- und Abnahmestrategie

```
Paket: spec/privacy · Version 1.1 · 2026-11-09 · gemessen gegen develop 24d1c2988
Änderung v1.1: TA-237…239 (Identifikationsklassen, Pseudonymformat, Zustandsautomat), TA-409…413 (Klassifizierung,
Pflichtfelder, Fristbeginn), TA-531/532 (Offline-Opt-in), TA-630…632 (Defaults, Flags, Gates), TA-709/710/718
(Spiegel statt Ledger), TA-810.
Test-IDs: TA-nnn (Abnahme), referenziert von jeder PRIV-nnn; TA-Nummern folgen dem
Dokument, zu dem sie gehören (TA-0xx → 01, TA-1xx → 03, TA-2xx → 04, TA-3xx → 05, TA-4xx → 06,
TA-5xx → 07, TA-6xx → 08, TA-7xx → 09, TA-8xx → übergreifende Negativtests)
```

---

## 1. Prinzipien (aus der eigenen Testkultur des Repositorys)

1. **Guards statt Reviews.** Jede Liste, die dieses Paket einführt (Zuordnung, Lineage,
   schwärzbare Felder, Tombstone-Allowlist, Geräte-Speicherschlüssel), erhält einen Guard, der fehlschlägt, wenn
   Code und Liste auseinanderlaufen — das Muster von `scripts/check_privacy_inventory.py` und
   `tests/unit/guards/`.
2. **Reach-Tests gegen eine echte Datenbank.** Der Löschvertrag wird bewiesen in
   `tests/integration/test_account_erasure_reach.py` / `test_tenant_erasure_reach.py`
   (echtes ArangoDB, Pflanze → Lauf → Scan jeder Collection). Neues Verhalten erweitert diese Dateien.
3. **Negativtests, die fehlschlagen können.** Jeder Guard hat einen Test mit eingebrachter Verletzung (das
   Idiom `TestTheMatrixCanFail` des Repos), damit ein leerer Guard auffällt.
4. **Der Test erreicht die Regel über denselben Pfad wie die Produktion** (Erinnerung an frühere Defekte:
   Liste vs. By-Key, escapetes Literal). Jede TA benennt den Einstiegspfad.
5. **Die ganze Suite ausführen**, nie `pytest -k` mit „0 selected"; Backend über
   `.venv/bin/python -m pytest` (28 Tests werden mit dem globalen Interpreter lautlos übersprungen).

---

## 2. Testmatrix nach Anforderungsgruppe

### 2.1 Registry und Guards (01, 02, 08 §2)

| TA | Typ | Test | Pfad (neu oder erweitert) |
|----|-----|------|---------------------------|
| TA-001 | Guard | R7: jede `AnonymizationRule`/`PseudonymizationRule` hat `attribution`; jedes kontoförmige Feld hat genau eine; eingebrachte Regel ohne Attribution schlägt fehl | `scripts/check_privacy_inventory.py`, `tests/unit/domain/engines/test_privacy_engines.py` |
| TA-002 | Unit | Mapper kopiert nie über Rollen hinweg: eine Quelle mit nur `created_by` ergibt `performed_by_user_key = None` | `tests/unit/domain/engines/test_care_event_backfill_mapper.py` |
| TA-003 | Unit + API | Bestätigungsakteur = Aufrufer auf allen vier Eintrittspfaden (Detail: TA-120) | siehe TA-120 |
| TA-004 | Komponente + Unit | jeder Leser (Pflegeprotokoll, Plan-Audit, Tagebuch, CSV) stellt `null`, Marker und fehlendes Konto über `PersonRef` identisch dar; ein eingebrachter roher Schlüssel im Antwortfeld schlägt fehl | `src/frontend/src/features/**/PersonRef.test.tsx`, `tests/unit/domain/services/test_identity_reference_service.py` |
| TA-005 | Guard | einziger Resolver: AST-Scan findet kein `DOCUMENT(CONCAT(@users`, dessen Ergebnis ein Antwortfeld erreicht, außer über `IdentityReferenceService`; eingebrachter direkter Join schlägt fehl | `tests/unit/guards/test_person_display_goes_through_the_resolver.py` |
| TA-006 | Guard | kein lokalisiertes Literal: `"anonymisiert"` / `"anonymised"` erscheint in `app/` nur im deprecated Adapter | `tests/unit/guards/test_no_localised_person_literals.py` |
| TA-007 | Unit + Integration | Tombstone außerhalb von `tombstone_allowed_fields()` wird vom Resolver als `erased` dargestellt und von `privacy.consistency` als Befund gemeldet (Detail: TA-202) | `test_identity_reference_service.py`, `tests/integration/test_privacy_consistency.py` |
| TA-010 | Guard (existiert) | neue Collections in `TenantErasureEngine.INVENTORY` oder `NOT_TENANT_SCOPED` | `tests/unit/guards/test_tenant_erasure_inventory_is_complete.py` |
| TA-011 | Guard (existiert, erweitern) | Isolation-Route-Walk deckt `/t/{slug}/privacy/review-items*`, `/privacy/redactions*`, `/privacy/summary` ab; Route-Consumer-Pin für jede neue Route | `tests/unit/guards/test_tenant_isolation_route_walk.py`, `test_route_consumers.py` |
| TA-012 | Integration | eine Löschung in Mandant A erzeugt keine Prüf-Items, Marker oder Audit-Zeilen in Mandant B (zwei Mandanten, gleiche Person nur in A) | `test_account_erasure_reach.py::test_no_cross_tenant_propagation` |
| TA-030 | Guard | Doc-Tabelle ⟂ Zeilen von `02` §3 entsprechen der Registry (Collection, Feld, Attribution, Aufbewahrungsklasse, Prüffelder) | `scripts/check_privacy_registry_doc.py` (Pre-commit) |
| TA-200 | Guard | eine Definition von Marker/Regex/`REDACTED`; eingebrachtes zweites Literal schlägt fehl | `tests/unit/guards/test_privacy_constants_are_defined_once.py` (ersetzt den Drei-Kopien-Pin in `test_garden_plan_retention.py`) |
| TA-606 | Guard | R8-Lineage: jede Kopierstelle eines Kontofelds steht in `DERIVED_FIELDS`; eingebrachte Kopie schlägt fehl | `scripts/check_privacy_inventory.py` |

### 2.2 Kontolöschung (03 §2)

| TA | Typ | Test | Pfad |
|----|-----|------|------|
| TA-100 | Integration | nach `request_erasure` rendern Pflegeereignis-Liste / Plan-Audit / Tagebuch-Antworten für das Subjekt `erased` gegenüber einem grower; die Plattform-Löschvorschau zeigt den Namen | `tests/integration/test_account_erasure_reach.py` (+ API-Client) |
| TA-101 | Unit | Resolver: `is_active=false` + Löschanfrage → `erased` | `tests/unit/domain/services/test_identity_reference_service.py` |
| TA-102 | Integration | **Rückstand**: nach Abschluss hält keine geteilte Collection den rohen Schlüssel **oder** den Tombstone außerhalb von `tombstone_allowed_fields()`; eine eingebrachte Kopie in `care_events` markiert den Lauf als `partially_completed` mit `residue` | `test_account_erasure_reach.py::test_residue_scan_catches_a_planted_copy` |
| TA-103 | Integration | Prüf-Items: eines pro verfasster/durchgeführter Zeile mit Prüffeldern und eines pro Namens-Token-Zeile; Items speichern keinen Text/Token/Schlüssel (Assertion: das serialisierte Item enthält weder die Anzeigenamen-Tokens noch den Schlüssel); ein zweiter Lauf erzeugt keine | `tests/integration/test_privacy_review_items.py` |
| TA-104 | API | `GET /admin/platform/privacy/operations?status=partially_completed` listet eine eingebrachte; Metrik `privacy_operations_open` spiegelt sie | `tests/api/test_admin_privacy_operations.py` |
| TA-105 | Unit | gleiche Eskalationsschwelle für Konto- und Mandantenlöschung (liest die gemeinsame Einstellung) | `tests/unit/domain/services/test_erasure_retry_lifecycle.py`, `test_tenant_erasure_async.py` |
| TA-106 | Integration | Löschbericht trägt `review_items_created` pro Mandant und `tombstone_copies_corrected` | `test_account_erasure_reach.py` |
| TA-108 | Unit | Fehler in der Post-Commit-Phase rollt die Löschung nicht zurück; die Anfrage wird mit `post_commit_pending` markiert; der Folge-Beat wiederholt idempotent | `tests/unit/domain/services/test_privacy_erase_account.py` |
| TA-130 | Unit (Client) | ein abgelehnter Refresh setzt die Schreibwarteschlange in Quarantäne; `401 account.closed` leert sie sofort; `403 membership.ended` verwirft nur die Einträge des betroffenen Mandanten | `src/frontend/src/features/gardenPlanner/offline/sync.test.ts`, `queue.test.ts` |
| TA-131 | API | gepufferter Schreib-Replay (`client_event_id`) nach Kontoschließung → 401 `account.closed` auf `/care-events`, `/tasks/{k}/complete`, Foto-Uploads | `tests/integration/test_client_event_idempotency.py` (erweitern) |

### 2.3 Beendigung der Mitgliedschaft (03 §3)

| TA | Typ | Test | Pfad |
|----|-----|------|------|
| TA-110 | Integration (Pin) | Verlassen ändert keine Domänenzeile; Zuweisung geleert; Kalender-Feeds gelöscht; Audit-Zeile geschrieben | `tests/unit/domain/services/test_tenant_service.py` (existiert teilweise) + Reach-artiger Scan |
| TA-111 | Integration | nach `RETENTION_FORMER_MEMBER_NAME_DAYS` (Uhr fixiert, das uhrverankerte Idiom des Repos) liefert der Resolver `former_member` ohne Namen für viewer/grower/lead/management; vor Ablauf der Frist wird der Name angezeigt; die Nutzerseite des Plattform-Admins zeigt das Konto weiterhin | `tests/integration/test_former_member_rendering.py` |
| TA-112 | Integration | Wiedereintritt → `member`; PRIV-116-Marker unverändert | gleich |
| TA-113 | API | Filter nach unterdrücktem ehemaligem Mitglied → 422 `care_event.filter_target_unavailable`; CSV rendert den Zustand | `tests/api/test_care_events_api.py` |
| TA-114 | Unit | Austrittszeitpunkt aus `security_audit_log` gelesen; fehlende Zeile → sofort unterdrückt | `test_identity_reference_service.py` |

### 2.4 Zuordnung zum Schreibzeitpunkt (03 §4)

| TA | Typ | Test | Pfad |
|----|-----|------|------|
| TA-120 | Unit + API | vier Bestätigungspfade (REST, Benachrichtigungsaktion, Task-Queue-Abschluss, MCP) speichern `performed_by_user_key = principal` und `created_by = principal`; MCP speichert den Service-Account-Schlüssel | `tests/unit/domain/services/test_care_confirmation_bed_event.py` (der Task-Queue-Fall prüft heute nur Trigger/Kategorie — **erweitern, um den Durchführenden zu prüfen**), `tests/unit/mcp_server/test_tools.py`, `tests/api/test_tasks_api.py` |
| TA-121 | Unit | `carry_account_reference`: Tombstone → Marker (Marker-Ziel) / `None` (Tombstone-Ziel); Label → `None`; aktueller Schlüssel passiert | `tests/unit/domain/models/test_privacy_constants.py` |
| TA-122 | Integration | Mandant mit `record_keeping = none`: die vier gesetzlichen Collections erhalten bei der Löschung den Marker und Prüf-Items; Mandant mit `pflschg_professional` unverändert (Tombstone) | `test_account_erasure_reach.py` |
| TA-123 | Unit | Durchführender beim Aufgabenabschluss = Token, nie Body oder Zugewiesener (existiert: `test_task_completion_service.py:140`) — beibehalten | existierend |

### 2.5 Anonymisierung und Schwärzung (04)

| TA | Typ | Test | Pfad |
|----|-----|------|------|
| TA-201 | Unit | siehe TA-121 | — |
| TA-202 | Integration | `privacy.consistency` meldet einen eingebrachten Tombstone in `care_events.performed_by_user_key` und einen eingebrachten Marker in `treatment_applications.applied_by_key`; korrigiert nichts | `tests/integration/test_privacy_consistency.py` |
| TA-203 | API | `performed_by=anon_<16hex>` → 422 für lead und grower | `tests/api/test_care_events_api.py`, `test_bed_history_api.py` |
| TA-204 | Unit + Integration | Schwärzung und R-25-Patch decken `material` und Messwert-Strings ab; `undo` bleibt | `tests/unit/domain/services/test_garden_plan_retention.py`, `test_care_event_service.py` |
| TA-205 | Integration | siehe TA-103 + vollständige Entdeckung: mit `PRIVACY_REVIEW_DISCOVERY_PAGE_SIZE = 10` im Test und 35 Treffern entstehen 35 Items über vier Seiten; der Cursor am Löschauftrag wandert; kein Item wird ausgelassen; Überschreiten von `PRIVACY_REVIEW_ITEMS_ESCALATE_AT` erzeugt nur eine Eskalation, keinen Abbruch | `test_privacy_review_items.py` |
| TA-206 | API | generische Schwärzung: nicht auf der Allowlist stehendes Feld → 422; idempotent 200; Audit-Zeile nur Kategorie; alter Wert fehlt in DB und Audit (den gesamten Dokumentspeicher nach dem eingebrachten String durchsuchen) | `tests/api/test_privacy_redactions.py` |
| TA-207 | Integration | `garden_plan_audit.user_key` erhält bei der Löschung den Marker; eingebrachter Tombstone wird von Consistency gemeldet | `test_account_erasure_reach.py`, `test_privacy_consistency.py` |
| TA-208 | Integration | Rückstands-Scan (siehe TA-102) | — |
| TA-209 | Integration | `original_filename` geleert; `caption` behalten + Prüf-Item | `test_account_erasure_reach.py` |
| TA-210 | API | Lineage-Vorschläge für einen Vorlagennamen listen die Standorte mit `template_key` und deren Audit-Zeilen; Annehmen schwärzt alle; Ablehnen schwärzt nur die Vorlage | `test_privacy_redactions.py` |
| TA-211 | Unit | `management` darf schwärzen; grower 403 (existiert für lead/grower — erweitern) | `test_care_event_service.py` |
| TA-226 | Unit + API | offene Prüf-Items älter als `PRIVACY_REVIEW_SLA_DAYS` (Uhr fixiert) erscheinen als `overdue` in `GET /t/{slug}/privacy/summary` und in der Metrik `privacy_review_items_overdue`; entschiedene Items zählen nie | `tests/unit/tasks/test_privacy_consistency_task.py`, `tests/api/test_privacy_review_api.py` |
| TA-237 | Guard | jede Verwendung von „anonymisiert“/„anonymised“ in API-Schemas, UI-Texten und Doku ist einer Identifikationsklasse aus `04` §1a zugeordnet; `anonymized`-Felder, die Tombstones tragen, heißen in der API `pseudonymized` oder `attribution_removed` | `tests/unit/guards/test_anonymisation_vocabulary.py` |
| TA-238 | Unit + Integration | neue Pseudonymisierung erzeugt `anon2_` aus HMAC(salt, `tombstone:<tenant>:<user>`); dieselbe Person erhält in zwei Mandanten verschiedene Werte; Bestand `anon_` bleibt unverändert; `is_tombstone` erkennt beide; die Art.-15-Suche findet beide Generationen | `tests/unit/domain/models/test_privacy_constants.py`, `test_privacy_export_tombstone.py` |
| TA-239 | Unit + Integration | Zustandsautomat: nur die Übergänge aus `04` §5.1a sind erlaubt (eingebrachter `REDACTED → REVIEW_REQUIRED` schlägt fehl); `keep` ohne `legal_basis_ref` → 422 `privacy_review.legal_basis_required`; nach `PRIVACY_REVIEW_SLA_DAYS` mit Flag aus: Eskalation + `overdue`, kein Zustandswechsel; mit Flag an: Items eigener Zeilen → `REDACTED`, Items mit Namens-Token Dritter bleiben `REVIEW_REQUIRED`; Löschauftrag erreicht `erasure_completed` erst, wenn kein Item in `DISCOVERY_PENDING` steht | `tests/unit/domain/services/test_privacy_review_state_machine.py`, `tests/api/test_privacy_review_api.py` |

### 2.6 Mandantenisolation und rollenbasierte Sichtbarkeit (05)

| TA | Typ | Test | Pfad |
|----|-----|------|------|
| TA-300 | API | `leads_and_self`: grower sieht `R` für andere, `N` für eigene; lead sieht `N`; viewer `R` | `tests/api/test_attribution_visibility.py` |
| TA-301 | API (Pin) | `all_members` entspricht den heutigen Antworten (Golden-Vergleich an einem Fixture-Mandanten) | gleich |
| TA-302 | API | `GET /members` lässt `email` ohne `management` weg; enthält sie für `management`, Plattform-Admin | `tests/api/test_tenants_members_api.py` |
| TA-303 | API | CSV durch viewer → `R`; durch lead → Namen + `ATTRIBUTION_EXPORTED`-Audit-Zeile mit `row_count` | `tests/api/test_care_events_api.py`, `tests/integration/test_care_events_csv_export.py` |
| TA-304 | Unit | MCP-Diary/ipm-Tools liefern `PersonRef`, nie einen String, der `^[0-9a-f-]{20,}$`/der Form eines users-Schlüssels entspricht | `tests/unit/mcp_server/test_tools.py` |
| TA-305 | API | Plattform-Admin: Prüf-Items 403; `/admin/platform/privacy/consistency` zählt nur (Antwort enthält kein `row_key`, keinen Text) | `tests/api/test_admin_privacy_operations.py` |
| TA-306 | API (Pin) | Filter nach einem anderen Mitglied als grower → 403 (existiert) | existierend |
| TA-307 | Integration | **Route-Walk**: jede `/t/{slug}/privacy/*`-Route verweigert einen fremden Mandanten mit demselben 404-Body, DB byteidentisch | `tests/integration/test_garden_plan_tenant_isolation.py` (Matrix erweitern) oder ein Geschwister `test_privacy_tenant_isolation.py` |
| TA-308 | Unit | Benachrichtigungstext enthält unter keiner Einstellung den Anzeigenamen eines anderen Mitglieds (Fixture mit Namen, die kollidieren würden) | `tests/unit/domain/services/test_notification_propagation_service.py` |
| TA-309 | Guard | kein Endpunkt aggregiert pro Person: AST-Scan auf `COLLECT … performed_by_user_key` / `created_by` mit `COUNT` in `app/`; eingebrachte Abfrage schlägt fehl | `tests/unit/guards/test_no_per_person_aggregation.py` |

### 2.7 Durchsetzung der Aufbewahrung (06)

| TA | Typ | Test | Pfad |
|----|-----|------|------|
| TA-400 | Unit | neue Beats in `TENANT_AGNOSTIC_BEATS`/`TENANT_WRITING_BEATS`; NFR-011-§3.1-Tabelle entspricht dem Beat (Guard existiert) | `tests/unit/guards/test_nfr011_task_table_matches_the_beat.py`, `test_beats_skip_inactive_tenants.py` |
| TA-401 | Unit | Ober-/Untergrenzen für jede neue Einstellung (`08` §8) | `tests/unit/config/test_retention_ceilings.py` |
| TA-402 | Unit | R-43 löscht entschiedene Items > 3 J., behält offene; R-45 löscht Ledger-Einträge nach `expires_at` | `tests/unit/tasks/test_retention_tasks.py` |
| TA-403 | Unit | R-48 Benachrichtigungen: 90 d nach `read_at`, 180 d ungelesen | gleich |
| TA-404 | Integration | Reklassifizierungs-Job bei `record_keeping → none` (TA-703) | `tests/integration/test_record_keeping_reclassify.py` |
| TA-405 | Unit (Pin) | R-25 Untergrenze = Obergrenze = 5; `pest_control` wartet auf `max(R-25, R-17)` (existiert) | existierend |
| TA-409 | API + Unit | Anlage eines Organisationsmandanten ohne `organization_kind`/`record_keeping` → 422 `tenant.classification_required`; persönlicher Mandant erhält `none`/`all_members`; `None` im Bestand liest als `legacy`/`all_members` und zählt als `undeclared` | `tests/api/test_tenants_api.py`, `tests/unit/domain/services/test_tenant_service.py` |
| TA-410 | Unit | Feldgenaue Statutory-Zuordnung: nur Felder der Tabelle `06` §3.2 erhalten bei Löschung in `kcang_association` die Pflichtbehandlung; `harvested_by_key` → Marker (mit Flag), `notes` → Prüfeintrag | `tests/unit/domain/engines/test_privacy_engines.py`, `test_account_erasure_reach.py` |
| TA-412 | Unit | PflSchG-Fristbeginn: eine Behandlung vom 15.03.2026 läuft bis 01.01.2030 (3 J. ab 01.01.2027), nicht bis 15.03.2029; `care_event_pflschg_cutoff` folgt | `tests/unit/domain/services/test_legal_retention_purge.py`, `test_retention_service.py` |
| TA-413 | Doku/Guard | kein UI-/Doku-Text nennt `treatment_applications` „Nachweis“; Text „unterstützt die Aufzeichnung“ | Doku-Lane, i18n-Guard |
| TA-630 | Unit | Jeder Default aus `08` §3.2 hat einen Test (persönlich, association, commercial, community, Bestand) | `tests/unit/domain/models/test_tenant_settings_defaults.py` |
| TA-631 | Unit | Feature-Flags (`08` §8a): bei `false` keine datenvernichtende Aktion; Aktion liefert 409 `privacy.feature_disabled` bzw. Zustand `reclassification_pending`; bei `true` Ausführung | `tests/unit/config/test_privacy_flags.py` |
| TA-632 | Guard | Jede LEG-Zeile im Decision-Log mit Gate `nein (bis …)` nennt ein Flag oder einen Helm-Precheck, das/der im Code existiert | `scripts/check_privacy_gates.py` |

### 2.8 Offline (07)

| TA | Typ | Test | Pfad (Frontend-vitest, sofern nicht anders angegeben) |
|----|-----|------|-------------------------------------------------------|
| TA-500 | Skript | REQ-025-§10-Tabelle ↔ Speicherschlüssel im Code | `scripts/check_device_storage_table.py` (Pre-commit) |
| TA-501 | Unit (Pin) | Namespace-Filter bei jedem Lesen | `features/gardenPlanner/offline/queue.test.ts`, `planCache.test.ts` |
| TA-502 | Guard | keine API-Nutzdaten im Web-Storage; PRIV-512-Schlüssel beim Logout geleert | `src/test/guards/noApiDataInWebStorage.test.ts` (existiert?) — `offlineDataClearedOnSessionChange.test.ts` erweitern |
| TA-505 | Unit | Byte-basierte Verdrängung im Plan-Cache | `planCache.test.ts` |
| TA-509 | Unit | Byte-Obergrenze für Fotos | `queue.test.ts` |
| TA-511 | Unit | Sweep-Zeiträume aus der Runtime-Config; 60-Tage-Hinweis einmalig | `retention.test.ts`, `OfflineSyncHost.test.tsx` |
| TA-512 | Unit | nach dem Logout fehlen die aufgelisteten Schlüssel; Theme/Sprache/Einwilligung bleiben erhalten | `offlineData.test.ts` |
| TA-514 | Guard | Logout wartet die Bereinigung vor der Navigation ab; eingebrachter nicht abgewarteter Aufruf schlägt fehl | `src/test/guards/offlineDataClearedOnSessionChange.test.ts` |
| TA-516 | Unit (SW) | `KP_CLEAR_DATA` → kein `kp-sw-state`; `KP_CLEAR_DONE` gesendet | `src/test/pwa/offlineData.test.ts`, `swApiCachePerClient.test.ts` |
| TA-519 | Unit | Quarantäne / Wiederherstellung / Löschung toter Sitzungen | `sync.test.ts`, `queue.test.ts` |
| TA-520 | API (Backend) | `401 account.closed` beim Refresh für ein geschlossenes Konto; `403 membership.ended` nur, wenn eine beendete Mitgliedschaft verzeichnet ist; sonst generisches 403 | `tests/api/test_auth_router.py`, `tests/api/test_care_events_api.py` |
| TA-521 | Unit | Client-Reaktion auf beide Codes | `sync.test.ts` |
| TA-523 | Unit | Kill-Switch bei `visibilitychange` | `src/test/pwa/killSwitch.test.ts` |
| TA-524 | Unit | Idle-Bereinigung im Shared-Device-Modus, TTL 5 min, Löschung nach einem Versuch | neu `sharedDeviceMode.test.ts` |
| TA-528 | API (Backend) | Replay entschwärzt nie; Replay durch geschlossenen Autor abgelehnt; fremder Abschluss 409 | `tests/integration/test_client_event_idempotency.py` |
| TA-529 | Komponente | Konfliktdialog rendert keinen Gewinnernamen | `ConflictDialog.test.tsx` |
| TA-530 | Komponente | Geräteseiten-Inhalt und Bereinigungs-Button | `AccountSettingsPage.test.tsx` |
| TA-531 | Unit + Komponente | Offline-Modus ist für jedes Gerät standardmäßig aus (keine Installationsklasse ausgenommen); ohne Opt-in schreibt der Client nichts in `kp-plan-cache`/`kp-write-queue` und registriert keinen SW-Cache; Opt-in speichert nur das Flag; Opt-out löscht beide Speicher und wartet `KP_CLEAR_DONE` ab | `retention.test.ts`, `planCache.test.ts`, `OfflineSettings.test.tsx` |
| TA-532 | Unit + E2E | Übergang bestehender Installationen: vorhandener Cache ohne Flag wird beim ersten Start gelöscht, der Dialog erscheint einmal und maximal 7 Tage lang erneut, bis entschieden; „später“ lässt den Speicher leer; TC-053-094 | `src/test/pwa/offlineOptIn.test.ts`, `tests/e2e/test_req053_wave9_offline.py` |
| E2E | Selenium | TC-053-091 Logout leert jeden Nutzerschlüssel; TC-053-092 Quarantäne toter Sitzungen; TC-053-093 Idle-Bereinigung im Shared-Device-Modus | `tests/e2e/test_req053_wave9_offline.py` (erweitern; Marker `req053`) |

### 2.9 Datenexporte (Art. 15/20, CSV, Mandantenarchiv)

| TA | Typ | Test | Pfad |
|----|-----|------|------|
| TA-600 | Integration (existiert, erweitern) | Art.-15-Bündel enthält keinen Schlüssel eines anderen Mitglieds (Pin `_CARE_EVENT_EXPORT_FIELDS`) und, neu, kein `PersonRef.display_name` anderer in den Abschnitten des persönlichen Gartens | `tests/integration/test_privacy_export_walk.py` |
| TA-601 | Integration | Bündel findet gesetzliche Zeilen per Tombstone für eine weiterhin aktive Person nach einer Mandantenlöschung (existiert: `test_privacy_export_tombstone.py`) — beibehalten | existierend |
| TA-602 | Integration | nach einer Reklassifizierung `record_keeping → none` listet das Bündel die Zeilen der Person als `attribution_gap`? — nein: das Konto der Person existiert, die Zeilen tragen bis zur Löschung ihren lebenden Schlüssel; pinnen, dass sich für lebende Konten nichts ändert | `test_privacy_export_walk.py` |
| TA-603 | Guard (existiert) | R2-Reziprozität für die neuen Collections (`privacy_review_items`, `erasure_mirror`, `migration_reports` in `EXCLUDED_FROM_DISCLOSURE` mit Begründungen) | `scripts/check_privacy_inventory.py` |
| TA-604 | Integration | Mandantenarchiv `members.jsonl` enthält keine E-Mail (existiert gemäß REQ-056 E-09 — pinnen) | `tests/integration/test_tenant_export*.py` |

### 2.10 Migrationen (09)

| TA | Typ | Test | Pfad |
|----|-----|------|------|
| TA-700…TA-703, TA-716, TA-717 | Unit + Integration | wie in `09` §12 aufgeführt | `tests/unit/migrations/versions/test_v0107_*.py`, `tests/integration/migrations/` |
| TA-701a | Unit | Berichts-Schwärzungsfilter: ein eingebrachter Nutzerschlüssel / Name in `details` wird abgelehnt | `tests/unit/migrations/test_migration_report_redaction.py` |
| TA-704 | Guard | Privacy-Migrationen deklarieren `kind`; ein `data_backfill` nutzt `ActiveTenants`, eine `privacy_correction` nicht | `tests/unit/guards/test_migration_tenant_gate_kind.py` |

### 2.11 Backup-Wiederherstellung (09 §6)

| TA | Typ | Test | Pfad |
|----|-----|------|------|
| TA-709 | Integration | Spiegel-Eintrag (nur Tombstone, kein Rohschlüssel — Assertion: der Rohschlüssel kommt im Spiegel-Dokument und im entschlüsselten Objekt nicht vor) beim Abschluss geschrieben; HMAC-Kette gültig; Bereinigung filtert | `tests/integration/test_erasure_mirror.py` |
| TA-710 | Integration (Restore-Drill, nightly) | Dump vor Löschung → Löschung → Restore → Replay erkennt das Konto per Tombstone-Abgleich (beide Formate) → Rohschlüssel in keiner Collection; Residue 0; Prüf-Items idempotent | `tests/integration/test_restore_replay.py` (markiert `slow`, Nightly-Lane) |
| TA-711 | Doku | Restore-Anleitung enthält den Replay-Schritt; `mkdocs build --strict` | Docs-Lane |
| TA-718 | Helm | `backup.enabled=true` ohne `privacy.mirror.enabled` → Template-Fehler | `helm template` im CI |

---

## 3. Negativtests — „gelöschte Identitäten können nicht wieder auftauchen"

Dies sind die Tests, die die zentrale Behauptung des Pakets beweisen. Jeder bringt ein gelöschtes Subjekt
ein (echter Schlüssel `K`, Tombstone `T`, Anzeigenamen-Tokens `N…`) und prüft die Abwesenheit.

| TA | Kanal | Assertion |
|----|-------|-----------|
| TA-800 | **Migrationen** | alle ausstehenden Migrationen nach einer Löschung auf einer Fixture-DB ausführen; alle Collections scannen: `K` abwesend; `T` nur in `tombstone_allowed_fields()`; `N…` abwesend in jedem Feld, das die Prüfwarteschlange als entschieden `redact` aufgeführt hat |
| TA-801 | **Backfill / Consistency-Job** | gesetzliche Zeile mit `T` einbringen; v0104-äquivalenten Mapper und `care_events.consistency` ausführen; `care_events` hält `_anonymized`, nie `T` |
| TA-802 | **Exporte** | Art.-15-Bündel eines anderen Mitglieds, Pflegeereignis-CSV (lead), Plan-JSON/SVG/PDF, Mandantenarchiv, MCP-Lese-Tools: keines enthält `K`, `T` oder (für CSV/Archiv nach Schwärzung) `N…` |
| TA-803 | **Offline-Synchronisation** | Gerät A puffert eine Notiz mit `K` → `K` anderswo gelöscht → Gerät A spielt erneut ab: 401 `account.closed` (Phase geschlossen) oder generisches 401 (gelöscht) → Quarantäne → Löschung; der Server speichert die Notiz nie; Gerät B (anderer Nutzer), das den Mandanten öffnet, erhält keine Cache-Zeile von `K` |
| TA-804 | **Backup-Wiederherstellung** | TA-710 |
| TA-810 | **Prüfwarteschlange** | nach `ERASURE_COMPLETED` existiert keine Zeile im Mandanten, deren Prüffeld einen Namens-Token von `N…` enthält und deren Eintrag nicht `RETAINED_WITH_LEGAL_BASIS` mit `legal_basis_ref` ist; kein Eintrag wurde durch die Eskalationsschwelle ausgelassen (Vergleich mit einer unabhängigen Vollzählung) |
| TA-805 | **Wiedereintritt** | nach PRIV-116 und einem Wiedereintritt behalten die alten Zeilen den Marker (keine Rück-Anonymisierung durch erneutes Auftauchen des Schlüssels) |
| TA-806 | **Mandantenimport** | Import eines Archivs, das `K` enthält (vor der Löschung exportiert), bildet `K` auf `_anonymized` ab (Regel für nicht zugeordnete Konten existiert [v]; pinnen, dass ein gelöschter Schlüssel als nicht zugeordnet behandelt wird, auch wenn `members.jsonl` des Archivs ihn aufführt) |
| TA-807 | **Benachrichtigungen** | keine nach der Schließung erzeugte Benachrichtigung nennt oder adressiert `K`; bestehende werden bei der Löschung gelöscht (existiert) |
| TA-808 | **Logs** | structlog-Capture während des gesamten Ablaufs enthält weder `K` noch `N…` (Guards `test_privacy_logs_carry_no_plaintext_subject` existieren — Szenario erweitern) |
| TA-809 | **Suche** | `GET /diary?q=<name token>` nach der Schwärzung liefert keine der geschwärzten Zeilen |

---

## 4. Abdeckung und Gates

**PRIV-900** Die neuen Guards kommen in das Pre-commit-Set (`scripts/check_privacy_inventory.py`
ist bereits dort) und in die erforderliche Lane `backend-guards`. Integrationstests laufen in der
bestehenden ArangoDB-gestützten Lane; der Restore-Drill (TA-710) läuft nightly.

**PRIV-901** Frontend-Tests folgen `FRONTEND.md` (`cleanup()` zuerst in `afterEach`; jsdom-
IndexedDB über `fake-indexeddb`, wie Welle 9 es tut).

**PRIV-902** E2E-Ergänzungen tragen den Marker `req053` (und einen neuen Marker `req025` für
reine Privacy-Abläufe), damit die conftest-Auswahl nach Anforderung funktioniert
(`spec/e2e-testcases/`-Matrixzeilen GP-REQ/PRIV).

---

## 5. Abnahme des Pakets als Ganzes

Das Paket ist **fertig**, wenn: jede PRIV-Anforderung in `01`–`09` mit Status P0/P1 in `12`
eine bestandene TA hat; die drei Guards (R7, R8, Konstanten) im Pre-commit sind; die Registry-
Dokumentprüfung (TA-030) besteht; TA-800…TA-809 bestehen; die DSFA-Vorprüfung (`11`) mit der LEG-Liste
an den Datenschutzbeauftragten übergeben wurde; und die Spec-Änderungsvorschläge aus `06` §9
in versionierte Änderungen von REQ-025 / NFR-011 / REQ-053 / REQ-024 / REQ-049 überführt wurden (nicht stillschweigend
— jeweils mit einer Changelog-Zeile, die dieses Paket referenziert).
