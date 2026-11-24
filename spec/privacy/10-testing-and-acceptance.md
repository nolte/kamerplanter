# SPEC-10 — Test- und Abnahmestrategie

```
Paket: spec/privacy · Version 1.2 · 2026-11-22 · Gemessen gegen: develop 007a4ea90 (Audit 2026-11-22)
Vorher: v1.1 (2026-11-09, develop 24d1c2988); Nachtrag #2839 (develop 343afbb97)
Änderung v1.1: TA-237…239 (Identifikationsklassen, Pseudonymformat, Zustandsautomat), TA-409…413 (Klassifizierung,
Pflichtfelder, Fristbeginn), TA-531/532 (Offline-Opt-in), TA-630…632 (Defaults, Flags, Gates), TA-709/710/718
(Spiegel statt Ledger), TA-810.
Änderungen 1.2: Abnahmekriterien und Verifikationen der Audit-Maßnahmen PRA-0.01…PRA-3.10 (`12` §6) als Abnahmefälle
eingeordnet — neu TA-031…040, TA-132…144, TA-240…244, TA-310…318, TA-414…427, TA-533…539, TA-633…637, TA-720…725,
TA-811, TA-901…917 (neuer Bereich Betriebs-/Dokumentnachweise); präzisiert statt dupliziert: TA-011, TA-030, TA-102,
TA-111, TA-113, TA-120, TA-121, TA-200, TA-204, TA-209, TA-303, TA-309, TA-409, TA-511, TA-512, TA-520, TA-531, TA-630,
TA-709, TA-710, TA-711, TA-718, TA-801, TA-804; Guards aus dem Audit (§2.14); Erledigt-Stand (TA-120, TA-200, TA-209).
Nachtrag Recovery (2026-11-23, gemessen gegen develop ce7e858d0): die Testfall-Vorschläge TA-R01…TA-R36 aus
`17-privacy-recovery.md` §11.1 sind reguläre Abnahmefälle TA-726…TA-760 (§2.11a; TA-R10 präzisiert TA-721), Abbildung
TA-R → TA in §2.11b; neu TA-918 (PRA-3.11); Rückverfolgung PRIV-800…PRIV-874 → PRA → TA (§2.16); TA-709, TA-718,
TA-720, TA-721, TA-722, TA-723, TA-724, TA-804, TA-910, TA-421, TA-711, TA-915, TA-916 präzisiert (Chart-Vertrag statt helm-unittest, Taxonomie aus `17`,
Incident-Dokument `19-incident-response.md`).
Test-IDs: TA-nnn (Abnahme), referenziert von jeder PRIV-nnn und PRA-x.yy; TA-Nummern folgen dem
Dokument, zu dem sie gehören (TA-0xx → 01, TA-1xx → 03, TA-2xx → 04, TA-3xx → 05, TA-4xx → 06,
TA-5xx → 07, TA-6xx → 08, TA-7xx → 09 und 17 (TA-726 ff.: `17` setzt das Backup-Kapitel `09` §6 fort; TA-705…708
und TA-712…715 bleiben frei, um keine früheren Nummern umzudeuten), TA-8xx → übergreifende Negativtests, TA-9xx →
Betriebs- und Dokumentnachweise ohne CI-Test, neu mit v1.2)
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
6. **Das Messwerkzeug selbst prüfen** (neu v1.2, Audit 2026-11-22). Ein Guard, der eine Schreibweise nicht kennt,
   meldet „grün“ und verbirgt Felder: Der Inventar-Guard R6 erkennt `_by_user` nicht
   (`scripts/check_privacy_inventory.py:214-215`), deshalb blieb `control_events.triggered_by_user` unentdeckt (LEG-29,
   LEG-46). Jede Erweiterung eines Musters wird zuerst am Bestand gemessen — ein roter Lauf ist das erwartete Ergebnis
   (TA-031).

---

## 2. Testmatrix nach Anforderungsgruppe

Neue und präzisierte Zeilen (v1.2) nennen die PRA-Aufgabe aus [`12`](12-implementation-roadmap.md) §6 und den Befund (LEG) aus
dem [decision-log](decision-log.md) — in der Spalte „Bezug“ oder in Klammern im Testtext; die Gegenrichtung steht in §2.13.

### 2.1 Registry und Guards (01, 02, 08 §2)

| TA | Typ | Test | Pfad (neu oder erweitert) |
|----|-----|------|---------------------------|
| TA-001 | Guard | R7: jede `AnonymizationRule`/`PseudonymizationRule` hat `attribution`; jedes kontoförmige Feld hat genau eine; eingebrachte Regel ohne Attribution schlägt fehl | `scripts/check_privacy_inventory.py`, `tests/unit/domain/engines/test_privacy_engines.py` |
| TA-002 | Unit | Mapper kopiert nie über Rollen hinweg: eine Quelle mit nur `created_by` ergibt `performed_by_user_key = None` | `tests/unit/domain/engines/test_care_event_backfill_mapper.py` (existiert seit #2839 für Tombstone → Marker inkl. Near-Miss; Rollen-Fall ergänzen) |
| TA-003 | Unit + API | Bestätigungsakteur = Aufrufer auf allen vier Eintrittspfaden (Detail: TA-120) | siehe TA-120 |
| TA-004 | Komponente + Unit | jeder Leser (Pflegeprotokoll, Plan-Audit, Tagebuch, CSV) stellt `null`, Marker und fehlendes Konto über `PersonRef` identisch dar; ein eingebrachter roher Schlüssel im Antwortfeld schlägt fehl | `src/frontend/src/features/**/PersonRef.test.tsx`, `tests/unit/domain/services/test_identity_reference_service.py` |
| TA-005 | Guard | einziger Resolver: AST-Scan findet kein `DOCUMENT(CONCAT(@users`, dessen Ergebnis ein Antwortfeld erreicht, außer über `IdentityReferenceService`; eingebrachter direkter Join schlägt fehl | `tests/unit/guards/test_person_display_goes_through_the_resolver.py` |
| TA-006 | Guard | kein lokalisiertes Literal: `"anonymisiert"` / `"anonymised"` erscheint in `app/` nur im deprecated Adapter | `tests/unit/guards/test_no_localised_person_literals.py` |
| TA-007 | Unit + Integration | Tombstone außerhalb von `tombstone_allowed_fields()` wird vom Resolver als `erased` dargestellt und von `privacy.consistency` als Befund gemeldet (Detail: TA-202) | `test_identity_reference_service.py`, `tests/integration/test_privacy_consistency.py` |
| TA-010 | Guard (existiert) | neue Collections in `TenantErasureEngine.INVENTORY` oder `NOT_TENANT_SCOPED` | `tests/unit/guards/test_tenant_erasure_inventory_is_complete.py` |
| TA-011 | Guard (existiert, erweitern) | Isolation-Route-Walk deckt `/t/{slug}/privacy/review`, `/privacy/review/{item_key}/decide`, `/privacy/review/suggestions`, `/privacy/redactions`, `/privacy/summary`, `/privacy/attribution-removal` (`08` §4.1) ab; Route-Consumer-Pin für jede neue Route. **Präzisiert v1.2 (PRA-0.06, PRA-2.04, PRA-2.20, PRA-3.02):** zusätzlich `GET /privacy/restrict`, `GET /privacy/export` (Liste), `GET /admin/platform/privacy/restrictions`, `GET /admin/platform/privacy/requests`, `POST /admin/platform/privacy/incidents`; Plattform-Routen 403 für Nicht-Admins | `tests/unit/guards/test_tenant_isolation_route_walk.py`, `test_route_consumers.py` |
| TA-012 | Integration | eine Löschung in Mandant A erzeugt keine Prüf-Items, Marker oder Audit-Zeilen in Mandant B (zwei Mandanten, gleiche Person nur in A) | `test_account_erasure_reach.py::test_no_cross_tenant_propagation` |
| TA-030 | Guard | Doc-Tabelle ⟂ Zeilen von `02` §3 entsprechen der Registry (Collection, Feld, Attribution, Aufbewahrungsklasse, Prüffelder). **Präzisiert v1.2 (PRA-1.01, LEG-46; INV-P1):** jede Collection mit personenbezogen geformtem Feld hat eine Klassifizierungszeile (`data_class`, `attribution_role`, `retention_rule`, `erasure_action`, `export_section`, `recipients`) oder einen dokumentierten Ausschluss; jede `02`-Zeile nennt Zweck, PA-nn, Empfänger, Frist, Löschverhalten; nach dem Fix 0 nicht klassifizierte Felder | `scripts/check_privacy_registry_doc.py` (Pre-commit) |
| TA-031 | Guard | **R6-Muster vollständig** (PRA-1.01, PRA-2.07; LEG-29, LEG-46): das Kontofeld-Muster erkennt zusätzlich `[a-z0-9_]+_user$`, `[a-z0-9_]+_by_user$`, `operator_*`, `*_subject`; am SHA 007a4ea90 schlägt der Lauf mit `control_events.triggered_by_user` fehl (erwartet rot), nach PRA-2.07 grün; ein eingebrachtes Feld `foo_by_user` ohne Inventarzeile schlägt fehl | `scripts/check_privacy_inventory.py`, `tests/unit/scripts/test_check_privacy_inventory.py` |
| TA-032 | Guard | jedes `str`-Feld eines persistierten Modells hat `max_length`; Freitextfelder tragen `free_text=True` in der Registry (PRA-1.01, PRA-2.01; LEG-08); eingebrachtes unbegrenztes Feld schlägt fehl | `tests/unit/guards/test_persisted_strings_are_bounded.py` |
| TA-033 | Guard | **Empfängerregister** (PRA-1.03, LEG-33; INV-P8): jede Datei unter `data_access/external/` und `src/knowledge-service/app/llm/` mit `https://`-Konstante steht in `src/backend/app/config/privacy_recipients.yaml`; ein Test-Adapter ohne Eintrag schlägt fehl | `tests/unit/guards/test_external_adapters_are_registered_recipients.py` |
| TA-034 | Guard | **einziger Klassifizierungsleser** (PRA-1.02, LEG-30; INV-P3): `organization_kind`/`record_keeping` werden außerhalb von Modell, Enum, Migration, Mandantenexport nur in `resolve_tenant_privacy_profile` gelesen (Grep mit Ausnahmeliste); eingebrachter direkter Leser schlägt fehl | `tests/unit/guards/test_tenant_classification_read_only_via_resolver.py` |
| TA-035 | Helm + Integration | **Valkey-Authentifizierung** (PRA-3.08, LEG-59): gerenderte Valkey-Konfiguration enthält `requirepass` aus `kamerplanter-secrets`, `REDIS_URL` enthält das Passwort; Verbindung ohne Passwort wird abgewiesen (Testinstallation) | helm-unittest unter `helm/kamerplanter/tests/`, Verbindungstest in der Integrations-Lane |
| TA-036 | E2E + Unit | **Zweiter Faktor für privilegierte Zugänge** (PRA-2.19, LEG-45): bei aktivem Flag erhält ein Plattform-Admin bzw. `technical`-Scope ohne TOTP/WebAuthn 403 auf `/admin/platform/*`; mit zweitem Faktor 200 | `tests/api/test_admin_second_factor.py`, `tests/e2e/` (Marker `req023`) |
| TA-037 | API | **Pannenregister** (PRA-3.02, LEG-32): `POST /admin/platform/privacy/incidents` → 403 für Nicht-Admins; Anlage verlangt Art, Datenkategorien, Zahl der Betroffenen, Folgen, Maßnahmen, Meldezeitpunkt (Art. 33 Abs. 5), sonst 422; jede Anlage schreibt eine Audit-Zeile | `tests/api/test_admin_privacy_incidents.py` |
| TA-038 | Helm | **Sicherheits-Alerts** (PRA-3.02, LEG-32): `monitoring.enabled=true` rendert mindestens eine `PrometheusRule` mit einem Sicherheits-Alert (z. B. `refresh_token_replay`, gehäufte `permission.denied` je API-Key, Spitze bei Tenant-Exporten, Admin-Login neue IP/UA) | helm-unittest |
| TA-039 | Helm (optional) | **verschlüsselte StorageClass** (PRA-3.07, LEG-42): mit `security.requireEncryptedStorageClass=true` und einer nicht gelisteten StorageClass schlägt `helm template` fehl | helm-unittest |
| TA-040 | Skript | **PRIV ohne TA** (PRA-3.10, LEG-61): Pre-commit-Skript meldet PRIV-IDs ohne zugeordnete TA nur aus einer dokumentierten Ausnahmeliste (Audit-Heuristik: 76 von 182 PRIV ohne TA-Bezug, teils fehlpositiv, z. B. PRIV-310 → TA-304; PRIV-407 → TA-312) | `scripts/check_privacy_ta_coverage.py` |
| TA-200 | Guard | eine Definition von Marker/Regex/`REDACTED` im Anwendungscode; eingebrachtes zweites Literal schlägt fehl; `app/migrations/versions/` ist ausgenommen (eingefrorene Kopien in v0107, NFR-016 M-7) und die Ausnahme ist im Guard benannt. **Erledigt (Audit 2026-11-22: `ALREADY_FIXED`, PRIV-201):** `domain/models/privacy.py:17, 25`; Kopien nur in v0107/v0109/v0114 | `tests/unit/guards/test_privacy_marker_and_tombstone_have_one_definition.py` (existiert; ersetzt den Drei-Kopien-Pin in `test_garden_plan_retention.py`) |
| TA-606 | Guard | R8-Lineage: jede Kopierstelle eines Kontofelds steht in `DERIVED_FIELDS`; eingebrachte Kopie schlägt fehl | `scripts/check_privacy_inventory.py` |

### 2.2 Kontolöschung (03 §2)

| TA | Typ | Test | Pfad |
|----|-----|------|------|
| TA-100 | Integration | nach `request_erasure` rendern Pflegeereignis-Liste / Plan-Audit / Tagebuch-Antworten für das Subjekt `erased` gegenüber einem grower; die Plattform-Löschvorschau zeigt den Namen | `tests/integration/test_account_erasure_reach.py` (+ API-Client) |
| TA-101 | Unit | Resolver: `is_active=false` + Löschanfrage → `erased` | `tests/unit/domain/services/test_identity_reference_service.py` |
| TA-102 | Integration | **Rückstand**: nach Abschluss hält keine geteilte Collection den rohen Schlüssel **oder** den Tombstone außerhalb von `tombstone_allowed_fields()`; eine eingebrachte Kopie in `care_events` markiert den Lauf als `partially_completed` mit `residue`. **Präzisiert v1.2 (PRA-1.07):** der Scan läuft nach dem Commit der **Kontolöschung** (heute nur bei Mandantenlöschung, `grep residue` in `erasure_executor.py` = 0) je kontoförmigem Feld | `test_account_erasure_reach.py::test_residue_scan_catches_a_planted_copy` |
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
| TA-111 | Integration | nach `RETENTION_FORMER_MEMBER_NAME_DAYS` (Uhr fixiert, das uhrverankerte Idiom des Repos) liefert der Resolver `former_member` ohne Namen für viewer/grower/lead/management; vor Ablauf der Frist wird der Name angezeigt; die Nutzerseite des Plattform-Admins zeigt das Konto weiterhin. **Präzisiert v1.2 (PRA-2.03, LEG-06):** 91 Tage nach `MEMBERSHIP_LEFT` gilt `performed_by_kind="former_member"`, `performed_by=null` in Liste, Historie, CSV, Plan-Audit und Site-Plan | `tests/integration/test_former_member_rendering.py` |
| TA-112 | Integration | Wiedereintritt → `member`; PRIV-116-Marker unverändert | gleich |
| TA-113 | API | Filter nach unterdrücktem ehemaligem Mitglied → 422 `care_event.filter_target_unavailable`; CSV rendert den Zustand. **Präzisiert v1.2 (PRA-2.03):** gilt für jede Rolle; die CSV enthält „ehemaliges Mitglied“ ohne Namen | `tests/api/test_care_events_api.py` |
| TA-114 | Unit | Austrittszeitpunkt aus `security_audit_log` gelesen; fehlende Zeile → sofort unterdrückt | `test_identity_reference_service.py` |

### 2.4 Zuordnung zum Schreibzeitpunkt (03 §4)

| TA | Typ | Test | Pfad |
|----|-----|------|------|
| TA-120 | Unit + API | vier Bestätigungspfade (REST, Benachrichtigungsaktion, Task-Queue-Abschluss, MCP) speichern `performed_by_user_key = principal` und `created_by = principal`; MCP speichert den Service-Account-Schlüssel. **Erledigt (Audit 2026-11-22: `ALREADY_FIXED`, PRIV-003/119, #2961):** REST `api/v1/care_reminders/router.py:159-170`, Benachrichtigung `api/v1/notifications/tenant_router.py:215-220`, Queue `task_service.py:1840-1855` → `care_reminder_service.py:1290-1368`, MCP `mcp_server/tools/care.py:77-86`; Guard vorhanden | `tests/unit/guards/test_care_confirmation_names_its_performer.py` (existiert); `tests/unit/domain/services/test_care_confirmation_bed_event.py`, `tests/unit/mcp_server/test_tools.py`, `tests/api/test_tasks_api.py` |
| TA-121 | Unit | `carry_account_reference`: Tombstone → Marker (Marker-Ziel) / `None` (Tombstone-Ziel); Label → `None`; aktueller Schlüssel passiert. **Präzisiert v1.2 (PRA-1.07):** an allen Kopierstellen — `account_of`, `task_completion_engine.py:125, 256`, Plan-Audit, Mandantenimport (heute nur `account_of`, `care_event_backfill_mapper.py:183-191`) | `tests/unit/domain/models/test_privacy_constants.py`, `tests/unit/domain/engines/test_task_completion_engine.py` |
| TA-122 | Integration | Mandant mit `record_keeping = none`: die vier gesetzlichen Collections erhalten bei der Löschung den Marker und Prüf-Items; Mandant mit `pflschg_professional` unverändert (Tombstone) | `test_account_erasure_reach.py` |
| TA-123 | Unit | Durchführender beim Aufgabenabschluss = Token, nie Body oder Zugewiesener (existiert: `test_task_completion_service.py:140`) — beibehalten | existierend |

### 2.4a Betroffenenrechte Art. 12/18/19/21, Legal Hold, Fotos (03; neu v1.2)

| TA | Typ | Test | Bezug | Pfad |
|----|-----|------|-------|------|
| TA-132 | Integration + API | **Art.-18/21-Anträge erreichen den Betreiber**: Antrag (`POST /privacy/restrict` bzw. `/privacy/object`) anlegen → Mail-Double empfängt genau eine Nachricht an `privacy_data_controller_email` (Antragsart, `scope`, Zeitpunkt, pseudonymer Kontoverweis, kein Freitext); `GET /privacy/restrict` liefert den Eintrag nach Reload; `GET /admin/platform/privacy/restrictions` zeigt ihn mit Fälligkeit (Anlage + 1 Monat); Statuswechsel erzeugt eine `security_audit_log`-Zeile und eine Mitteilung an die Person; 403 für Nicht-Admins | PRA-0.06 · LEG-23 | `tests/integration/test_processing_restriction_channel.py`, `tests/api/test_privacy_restrictions_api.py` |
| TA-133 | Integration | **Processing-Hold-Guard** (REQ-025 AK-11): aktive Einschränkung `sensor_analytics` → betroffene Route 423; `scope = all` → Konto im Lesemodus (423 auf verarbeitende Routen außer `/privacy/*`); `scope` ist ein Enum, Bestandseinträge werden übergeleitet | PRA-1.06 · LEG-23 | `tests/integration/test_processing_hold_guard.py`, `tests/unit/migrations/versions/test_*_restriction_scope_enum.py` |
| TA-134 | Integration | **Hold in Lösch-/Purge-Jobs**: Hold auf Mandant → `anonymize_expired_care_events` und `purge_expired_garden_plan_audit` lassen Zeilen unverändert und melden `held=n`; aktive Einschränkung mit `scope ∈ {all, retention}` wirkt als Hold; Kontolöschung einer gehaltenen Person bleibt `scheduled`/`held` mit `held_reason` (Schließung ja, Hard-Delete nein); Aufhebung → nächster Lauf verarbeitet; Anlage/Aufhebung eines `legal_holds`-Eintrags nur Plattform-Admin mit Audit-Zeile | PRA-1.06 · LEG-35 | `tests/integration/test_legal_hold.py` |
| TA-135 | Guard | **jeder Retention-/Purge-/Anonymisierungs-Task und der Erasure-Executor ruft den Hold-Filter** (statische Prüfung; INV-P2); eingebrachter Task ohne Aufruf schlägt fehl; kein Retention-Beat ohne Regel, keine `beat`-Regel ohne Beat | PRA-1.06, PRA-3.06 · LEG-35 | `tests/unit/guards/test_retention_tasks_respect_holds.py` |
| TA-136 | Unit | **Beweissicherung**: `RETENTION_LEGAL_HOLD_SECURITY_AUDIT` aktiv → `purge_expired_security_audit` löscht nichts | PRA-1.06, PRA-3.02 · LEG-32 | `tests/unit/tasks/test_security_audit_tasks.py` |
| TA-137 | API + Guard | **Selbstlöschung eigener Fotos**: `grower` löscht eigenes Galeriefoto/eigenen Anhang → 204, fremdes → 403, `lead` → 204; alle Foto-Löschrouten (Galerie, Anhänge, Beetfotos) nutzen dasselbe Uploader-Prädikat im Service mit `tenant_key`/`user_key` als Pflichtargumenten (Guard) | PRA-2.12 · LEG-39 | `tests/api/test_plant_photo_delete.py`, `tests/unit/guards/test_photo_delete_routes_share_the_uploader_predicate.py` |
| TA-138 | Unit | **externe Bewertung fremder Fotos**: Assess eines Fotos mit `created_by != user_key` auf einem externen Adapter → 403 (bzw. Einwilligung des Uploaders geprüft); der Adapter erhält EXIF-freie Bytes (`strip_exif` strict) auch bei `storage_strip_exif=False` | PRA-2.12 · LEG-40 | `tests/unit/domain/services/test_plant_photo_service.py` |
| TA-139 | Unit | **Beetfotos/Plan-Unterlagen einer gelöschten Person**: Erasure-Plan leert `caption` (`anonymize_user_metadata`), Regelbegründung ohne CanG/PflSchG-Bezug für `location`/`garden_plan_underlay`, Regeltext ohne die nicht existierenden Kategorien `profile`/`user_notes`; nach DSB-Antwort je Variante B (Löschen) / C (Wahlrecht, Flag am Erasure-Request) ein Plan-Test | PRA-2.12 · LEG-20 | `tests/unit/domain/engines/test_erasure_engine.py` |
| TA-140 | Integration | **EXIF-Nachstrip in verlassenen Mandanten**: Foto mit EXIF (Strip aus) in Mandant B, Person verlässt B, löscht ihr Konto → Objekt in B EXIF-frei, `created_by = _anonymized`; Reihenfolge Strip vor Marker | PRA-2.13 · LEG-55 | `tests/integration/test_erasure_exif_strip_reach.py` (existiert, erweitern) |
| TA-141 | Unit | **EXIF-Strip fail-closed**: JPEG mit gültigem APP1/GPS-Segment und abgeschnittenem Scan → Upload abgelehnt (415/422), kein Objekt geschrieben; bei `storage_strip_exif=False` Startwarnung im Log und Health-Hinweis | PRA-2.13 · LEG-57 | `tests/unit/domain/engines/storage/test_exif_stripper.py`, `tests/unit/config/test_startup_warnings.py` |
| TA-142 | Unit | **Fristüberwachung**: jeder Export-, Lösch- und Art.-18/21-Antrag erzeugt genau einen `privacy_requests`-Eintrag mit `due_at` = Eingang + 1 Monat (Verlängerung nur mit Begründung) | PRA-2.20 · LEG-23 | `tests/unit/domain/services/test_privacy_requests.py` |
| TA-143 | Unit (Beat) | `privacy_requests.overdue_check` (Uhr fixiert): Antrag 24 Tage alt und offen → genau eine Warnung an den Verantwortlichenkontakt, Metrik `privacy_requests_overdue_total` steigt; erledigte Anträge zählen nie | PRA-2.20 · LEG-23 | `tests/unit/tasks/test_privacy_requests_overdue.py` |
| TA-144 | Service | **Art. 19**: Löschabschluss bei aktivem externem Adapter erzeugt `notification_art19` mit der Empfängerliste aus dem Register; ohne Lösch-API des Empfängers entsteht eine Betreiberaufgabe | PRA-2.20 · LEG-33 | `tests/unit/domain/services/test_privacy_requests.py` |

### 2.5 Anonymisierung und Schwärzung (04)

| TA | Typ | Test | Pfad |
|----|-----|------|------|
| TA-201 | Unit | siehe TA-121 | — |
| TA-202 | Integration | `privacy.consistency` meldet einen eingebrachten Tombstone in `care_events.performed_by_user_key` und einen eingebrachten Marker in `treatment_applications.applied_by_key`; korrigiert nichts | `tests/integration/test_privacy_consistency.py` |
| TA-203 | API | `performed_by=anon_<16hex>` → 422 für lead und grower | `tests/api/test_care_events_api.py`, `test_bed_history_api.py` |
| TA-204 | Unit + Integration | Schwärzung und R-25-Patch decken `material` und Messwert-Strings ab; `undo` bleibt. **Präzisiert v1.2 (PRA-2.01, LEG-08):** `material` und `measurements[].source/extraction_method` sind nach `redact` und nach R-25 `[redacted]`; der Nährstoffhinweis (`nutrient_hint_engine.py`) toleriert `[redacted]` ohne Fehler | `tests/unit/domain/services/test_garden_plan_retention.py`, `test_care_event_service.py`, `tests/unit/domain/engines/test_nutrient_hint_engine.py` |
| TA-205 | Integration | siehe TA-103 + vollständige Entdeckung: mit `PRIVACY_REVIEW_DISCOVERY_PAGE_SIZE = 10` im Test und 35 Treffern entstehen 35 Items über vier Seiten; der Cursor am Löschauftrag wandert; kein Item wird ausgelassen; Überschreiten von `PRIVACY_REVIEW_ITEMS_ESCALATE_AT` erzeugt nur eine Eskalation, keinen Abbruch | `test_privacy_review_items.py` |
| TA-206 | API | generische Schwärzung: nicht auf der Allowlist stehendes Feld → 422; idempotent 200; Audit-Zeile nur Kategorie; alter Wert fehlt in DB und Audit (den gesamten Dokumentspeicher nach dem eingebrachten String durchsuchen) | `tests/api/test_privacy_redactions.py` |
| TA-207 | Integration | `garden_plan_audit.user_key` erhält bei der Löschung den Marker; eingebrachter Tombstone wird von Consistency gemeldet | `test_account_erasure_reach.py`, `test_privacy_consistency.py` |
| TA-208 | Integration | Rückstands-Scan (siehe TA-102) | — |
| TA-209 | Integration | `original_filename` geleert; `caption` behalten + Prüf-Item. **Stand v1.2 (Audit 2026-11-22):** `original_filename` `ALREADY_FIXED` (`erasure_engine.py:372`, v0109; im selben Schreibvorgang `attachment_repository.py:404-430`). Für Beetfotos und Plan-Unterlagen (`location`, `garden_plan_underlay`) gilt abweichend TA-139: `caption` wird geleert (PRA-2.12, LEG-20) | `test_account_erasure_reach.py` |
| TA-210 | API | Lineage-Vorschläge für einen Vorlagennamen listen die Standorte mit `template_key` und deren Audit-Zeilen; Annehmen schwärzt alle; Ablehnen schwärzt nur die Vorlage | `test_privacy_redactions.py` |
| TA-211 | Unit | `management` darf schwärzen; grower 403 (existiert für lead/grower — erweitern) | `test_care_event_service.py` |
| TA-226 | Unit + API | offene Prüf-Items älter als `PRIVACY_REVIEW_SLA_DAYS` (Uhr fixiert) erscheinen als `overdue` in `GET /t/{slug}/privacy/summary` und in der Metrik `privacy_review_items_overdue`; entschiedene Items zählen nie | `tests/unit/tasks/test_privacy_consistency_task.py`, `tests/api/test_privacy_review_api.py` |
| TA-237 | Guard | jede Verwendung von „anonymisiert“/„anonymised“ in API-Schemas, UI-Texten und Doku ist einer Identifikationsklasse aus `04` §1a zugeordnet; `anonymized`-Felder, die Tombstones tragen, heißen in der API `pseudonymized` oder `attribution_removed` | `tests/unit/guards/test_anonymisation_vocabulary.py` |
| TA-238 | Unit + Integration | neue Pseudonymisierung erzeugt `anon2_` aus HMAC(salt, `tombstone:<tenant>:<user>`); dieselbe Person erhält in zwei Mandanten verschiedene Werte; Bestand `anon_` bleibt unverändert; `is_tombstone` erkennt beide; die Art.-15-Suche findet beide Generationen | `tests/unit/domain/models/test_privacy_constants.py`, `test_privacy_export_tombstone.py` |
| TA-239 | Unit + Integration | Zustandsautomat: nur die Übergänge aus `04` §5.1a sind erlaubt (eingebrachter `REDACTED → REVIEW_REQUIRED` schlägt fehl); `keep` ohne `legal_basis_ref` → 422 `privacy_review.legal_basis_required`; nach `PRIVACY_REVIEW_SLA_DAYS` mit Flag aus: Eskalation + `overdue`, kein Zustandswechsel; mit Flag an: Items eigener Zeilen → `REDACTED`, Items mit Namens-Token Dritter bleiben `REVIEW_REQUIRED`; Löschauftrag erreicht `erasure_completed` erst, wenn `review_discovery_completed_at` gesetzt ist und kein Item der Löschung in `REVIEW_REQUIRED`, `REDACTION_PENDING` oder `FAILED` steht (`04` §5.1a) | `tests/unit/domain/services/test_privacy_review_state_machine.py`, `tests/api/test_privacy_review_api.py` |
| TA-240 | Unit + Integration | **Import-Regel für Pseudonyme** (PRA-1.07, LEG-54): `anon_…` aus fremder Installation (Archiv-`installation_id`) → `_anonymized`; aus gleicher Installation nur in einer Allowlist-Zelle unverändert, sonst Marker; nach dem Import meldet der Konsistenz-Beat 0 Tombstones außerhalb der Allowlist; kein Codepfad außer `compute_tombstone_hash` erzeugt `anon_` für neue mandantenbezogene Zeilen | `tests/unit/domain/engines/test_tenant_import_engine.py`, `test_privacy_consistency.py` |
| TA-241 | Integration | **Entdeckung über drei Mandanten mit Abbruch** (PRA-2.01, LEG-08): Kontolöschung einer Person in drei Mandanten; die Entdeckung wird nach der ersten Seite abgebrochen und wiederaufgenommen; Ergebnis identisch zur ununterbrochenen Vollzählung | `test_privacy_review_items.py` |
| TA-242 | Guard | **jede Collection in `review_fields` hat einen Schwärzungspfad** über `REDACTABLE_FIELDS` der Registry (PRA-2.01); eingebrachte Collection ohne Pfad schlägt fehl | `tests/unit/guards/test_review_fields_are_redactable.py` |
| TA-243 | Komponente + i18n | **Eingabehinweise an Freitextfeldern** (PRA-2.01, LEG-08): Formulare mit Freitextfeldern zeigen den Hinweis „keine Gesundheits- oder Kontaktdaten“ (DE/EN gleichlautend vorhanden); keine automatische Inhaltsklassifikation | `src/frontend/src/**/__tests__/*FreeTextHint*.test.tsx`, i18n-Vollständigkeitsprüfung |
| TA-244 | Integration | **Plan-Snapshots** (PRA-2.02, LEG-34): Location-Notiz schwärzen → alle Snapshots in `garden_plan_audit` derselben Site enthalten für diesen `key` `[redacted]` (Blattfelder `locations[].name/notes/description`, `objects[].label/notes`, `zones[].name`); Restore eines älteren Snapshots → Live-Notiz bleibt `[redacted]`; Kontolöschung einer Person mit Beetvorlage → Prüfeintrag referenziert auch die Snapshot-Zeile | `tests/integration/test_garden_plan_snapshot_redaction.py` |

### 2.6 Mandantenisolation und rollenbasierte Sichtbarkeit (05)

| TA | Typ | Test | Pfad |
|----|-----|------|------|
| TA-300 | API | `leads_and_self`: grower sieht `R` für andere, `N` für eigene; lead sieht `N`; viewer `R` | `tests/api/test_attribution_visibility.py` |
| TA-301 | API (Pin) | `all_members` entspricht den heutigen Antworten (Golden-Vergleich an einem Fixture-Mandanten) | gleich |
| TA-302 | API | `GET /members` lässt `email` ohne `management` weg; enthält sie für `management`, Plattform-Admin | `tests/api/test_tenants_members_api.py` |
| TA-303 | API | CSV durch viewer → `R`; durch lead → Namen + `ATTRIBUTION_EXPORTED`-Audit-Zeile mit `row_count`. **Präzisiert v1.2 (PRA-2.05, LEG-02):** CSV durch `viewer`/`grower` enthält Namen nur für eigene Zeilen, sonst „Mitglied“; genau eine Audit-Zeile je Export (Akteur, Mandant, Zeilenzahl, kein Inhalt) | `tests/api/test_care_events_api.py`, `tests/integration/test_care_events_csv_export.py` |
| TA-304 | Unit | MCP-Diary/ipm-Tools liefern `PersonRef`, nie einen String, der `^[0-9a-f-]{20,}$`/der Form eines users-Schlüssels entspricht | `tests/unit/mcp_server/test_tools.py` |
| TA-305 | API | Plattform-Admin: Prüf-Items 403; `/admin/platform/privacy/consistency` zählt nur (Antwort enthält kein `row_key`, keinen Text) | `tests/api/test_admin_privacy_operations.py` |
| TA-306 | API (Pin) | Filter nach einem anderen Mitglied als grower → 403 (existiert) | existierend |
| TA-307 | Integration | **Route-Walk**: jede `/t/{slug}/privacy/*`-Route verweigert einen fremden Mandanten mit demselben 404-Body, DB byteidentisch | `tests/integration/test_garden_plan_tenant_isolation.py` (Matrix erweitern) oder ein Geschwister `test_privacy_tenant_isolation.py` |
| TA-308 | Unit | Benachrichtigungstext enthält unter keiner Einstellung den Anzeigenamen eines anderen Mitglieds (Fixture mit Namen, die kollidieren würden) | `tests/unit/domain/services/test_notification_propagation_service.py` |
| TA-309 | Guard | kein Endpunkt aggregiert pro Person: AST-Scan auf `COLLECT … performed_by_user_key` / `created_by` mit `COUNT` in `app/`; eingebrachte Abfrage schlägt fehl. **Präzisiert v1.2 (PRA-2.06, LEG-28; INV-P9):** zusätzlich liefert kein Antwortschema ein Dauer-/Bewertungsfeld (`actual_duration_minutes`, `quality_rating`, `difficulty_rating`, `started_at`) zusammen mit einem Personenfeld ohne Rollenfilter; rot auf dem Bestand (`api/v1/tasks/schemas.py:332-351`), grün nach dem Fix; schließt die fehlende TA zu PRIV-407 | `tests/unit/guards/test_no_per_person_aggregation.py`, `tests/unit/guards/test_no_performance_fields_without_role_filter.py` |
| TA-310 | API | **Audit der Filternutzung** (PRA-2.05, LEG-02/LEG-05): jede Abfrage mit `performed_by`-Filter schreibt genau eine `ATTRIBUTION_FILTER_USED`-Zeile (Akteur, Mandant, Zeilenzahl, kein Inhalt) | `tests/api/test_care_events_api.py` |
| TA-311 | API | **`commercial` erzwingt `leads_and_self`** (PRA-2.05, LEG-05): Mandant mit `organization_kind = commercial` erfüllt die Sichtbarkeitsmatrix `05` §3 für `leads_and_self`; Umschalten auf `all_members` ohne Flag wird abgewiesen; der Default kommt aus `resolve_tenant_privacy_profile` | `tests/api/test_attribution_visibility.py` |
| TA-312 | API | **Aufgaben-Leistungsdaten** (PRA-2.06, LEG-28): als `viewer` liefert `GET /tasks/{key}` einer fremden Aufgabe weder Kontoschlüssel noch `actual_duration_minutes`, `quality_rating`, `difficulty_rating`, `started_at`; `assigned_to` kommt als `PersonRef`/Anzeigename, nie als `assigned_to_user_key`; die zuständige Person und Leads sehen die Felder | `tests/api/test_tasks_api.py` |
| TA-313 | Unit | **`commercial` ohne Leistungsfelder** (PRA-2.06): `tasks.performance_fields_enabled` aus dem Resolver ist für `commercial` aus; Dauer und Bewertungen werden beim Abschließen verworfen (dokumentiert); persönliche Mandanten unverändert | `tests/unit/domain/services/test_task_service.py` |
| TA-314 | Integration | **`control_events` im Lebenszyklus** (PRA-2.07, LEG-29): nach Kontolöschung keine `control_events`-Zeile mit dem Schlüssel (Marker); das Art.-15-Bündel enthält die eigenen manuellen Schaltvorgänge; die API-Antwort (`api/v1/actuators/schemas.py`) enthält keinen Kontoschlüssel, sondern `PersonRef` nach `attribution_visibility`; Migration mit Dry-Run (PRIV-718) | `test_account_erasure_reach.py`, `tests/api/test_actuators_api.py`, `tests/unit/migrations/versions/` |
| TA-315 | Unit | **MCP-Freitextpolitik, Option A** (PRA-2.10, LEG-51): Grower-Schlüssel ruft `get_diary_entry` für einen fremden, unmarkierten Eintrag → `text`, `title`, `photo_refs` fehlen bzw. `null`; `get_diary_entry_photos` → `not_found` (keine Existenzpreisgabe); Leitung → vollständig; Snapshot-Test Einwilligungstext ↔ Setting `mcp_member_free_text` | `tests/unit/mcp_server/test_tools.py` |
| TA-316 | Unit + Red-Team | **Agentensicherheit** (PRA-2.10, LEG-52): `read_only`-Key ruft ein WRITE-Werkzeug → `permission.denied` mit Audit `denied`; `get_diary_entry` kennzeichnet `text` als `untrusted_content` mit `authored_by_self`; `archive_plant`/`generate_succession_runs` ohne gültiges Bestätigungs-Token aus `dry_run` → 422; ein Prompt-Injection-Testfall in einem Tagebucheintrag löst keinen Schreibaufruf aus | `tests/unit/mcp_server/test_dispatcher.py`, `tests/unit/mcp_server/test_prompt_injection.py` |
| TA-317 | Unit | **Plattform-Admin-Export** (PRA-2.11, LEG-53): `POST /admin/platform/tenants/{key}/exports` ohne `reason` (Enum) → 422; die Audit-Zeile enthält `reason` und optional `instruction_ref` (ohne Freitext-PII); Export eines `orphaned`-Mandanten benachrichtigt alle aktiven Mitglieder oder wird als „ohne Empfänger“ auditiert | `tests/unit/domain/services/test_tenant_export_service.py` |
| TA-318 | Unit | **Leseaudit Löschvorschau** (PRA-2.19, PRIV-316, LEG-45): jeder Aufruf von `get_user_erasure_preview` schreibt genau eine `ERASURE_PREVIEW_READ`-Zeile | `tests/unit/domain/services/test_admin_platform_service.py` |

### 2.7 Durchsetzung der Aufbewahrung (06)

| TA | Typ | Test | Pfad |
|----|-----|------|------|
| TA-400 | Unit | neue Beats in `TENANT_AGNOSTIC_BEATS`/`TENANT_WRITING_BEATS`; NFR-011-§3.1-Tabelle entspricht dem Beat (Guard existiert) | `tests/unit/guards/test_nfr011_task_table_matches_the_beat.py`, `test_beats_skip_inactive_tenants.py` |
| TA-401 | Unit | Ober-/Untergrenzen für jede neue Einstellung (`08` §8) | `tests/unit/config/test_retention_ceilings.py` |
| TA-402 | Unit | R-43 löscht entschiedene Items > 3 J., behält offene; R-45 löscht Journal-Einträge nach `expires_at` und schreibt das Journal-Objekt gefiltert neu (v1.2: Journal statt Spiegel, PRA-1.04) | `tests/unit/tasks/test_retention_tasks.py` |
| TA-403 | Unit | R-48 Benachrichtigungen: 90 d nach `read_at`, 180 d ungelesen | gleich |
| TA-404 | Integration | Reklassifizierungs-Job bei `record_keeping → none` (TA-703) | `tests/integration/test_record_keeping_reclassify.py` |
| TA-405 | Unit (Pin) | R-25 Untergrenze = Obergrenze = 5; `pest_control` wartet auf `max(R-25, R-17)` (existiert) | existierend |
| TA-409 | API + Unit | Anlage eines Organisationsmandanten ohne `organization_kind`/`record_keeping` → 422 `tenant.classification_required`; persönlicher Mandant erhält `none`/`all_members`; `None` im Bestand liest als `legacy`/`all_members` und zählt als `undeclared`. **Präzisiert v1.2 (PRA-1.02, LEG-30):** Änderung nur durch `lead ∧ management`, erzeugt genau eine Audit-Zeile (`TENANT_RECORD_KEEPING_CHANGED` bzw. neu `TENANT_ORGANIZATION_KIND_CHANGED`); die Leitung sieht einen Hinweis bis zur Klassifizierung (`undeclared`/`unknown_legacy`); Betreiberzähler (PRIV-110); der v0110-Docstring beschreibt keinen nicht existierenden Anlagepfad | `tests/api/test_tenants_api.py`, `tests/unit/domain/services/test_tenant_service.py` |
| TA-410 | Unit | Feldgenaue Statutory-Zuordnung: nur Felder der Tabelle `06` §3.2 erhalten bei Löschung in `kcang_association` die Pflichtbehandlung; `harvested_by_key` → Marker (mit Flag), `notes` → Prüfeintrag | `tests/unit/domain/engines/test_privacy_engines.py`, `test_account_erasure_reach.py` |
| TA-412 | Unit | PflSchG-Fristbeginn: eine Behandlung vom 15.03.2026 läuft bis 01.01.2030 (3 J. ab 01.01.2027), nicht bis 15.03.2029; `care_event_pflschg_cutoff` folgt | `tests/unit/domain/services/test_legal_retention_purge.py`, `test_retention_service.py` |
| TA-413 | Doku/Guard | kein UI-/Doku-Text nennt `treatment_applications` „Nachweis“; Text „unterstützt die Aufzeichnung“ | Doku-Lane, i18n-Guard |
| TA-414 | Integration | **KI-Cloud-Gate am tatsächlichen Provider** (PRA-0.09, LEG-31): KS-Double meldet `provider_type=anthropic`, Mandant ohne Provider-Datensatz, Person ohne `ai_cloud_processing` → `refresh_tips`, `refresh_daily_tip`, `explain`, `stream_chat` und Diagnose antworten 403 `consent_required`, das Double erhält keinen `/ask`; mit `ai_allow_cloud_providers=false` → 403 `ai.disabled_for_tenant`; Health-Fehler des KS → Einstufung Cloud (fail-closed); `ai_audit_log.uses_cloud_provider` und der Indikator „Cloud-Verarbeitung“ = Wert des Doubles; `/ask` (`ask_knowledge`) bleibt unverändert korrekt | `tests/integration/test_ai_cloud_gate.py` |
| TA-415 | Guard | **jede Methode mit `self._ks.ask` ruft vorher `CloudGate.require`** (PRA-0.09; INV-P4); eingebrachter Aufruf ohne Gate schlägt fehl | `tests/unit/guards/test_knowledge_service_calls_pass_the_cloud_gate.py` |
| TA-416 | Unit (Beat) | **R-47 Aufgaben-Leistungsfelder** (PRA-2.06, LEG-28): Beat (Uhr fixiert) leert Dauer-/Bewertungsfelder und `started_at` abgeschlossener Aufgaben nach 90 d | `tests/unit/tasks/test_retention_tasks.py` |
| TA-417 | Unit (Beat) | **Frist `control_events`** (PRA-2.07, LEG-29): Retention-Beat anonymisiert Zeilen älter als die neue R-nn-Frist (Vorschlag 90 d); NFR-011-Tabelle nennt den Beat (TA-400) | `tests/unit/tasks/test_retention_tasks.py` |
| TA-418 | Unit | **Schalter Zurechnungskopie** (PRA-2.08, LEG-07): `PRIVACY_BACKFILL_COPIES_PERFORMER=false` → Mapper und `CareEventConsistencyService` liefern `performed_by_user_key is None` für Behandlungen/Ernten; `organization_kind = commercial` → keine Kopie unabhängig vom Schalter; Default = Bestand; die Konfigurationsdoku nennt den Schalter | `tests/unit/domain/engines/test_care_event_backfill_mapper.py`, `tests/unit/domain/services/test_care_event_consistency_service.py` |
| TA-419 | Integration + Komponente | **Pflichtzeilen nach Mandantenlöschung** (PRA-2.09, LEG-47): Klasse `none` mit Flag an → nach der Löschung keine Pflichtzeilen mehr; `pflschg_professional` → Zeilen bleiben, Herausgabe an eine Behörde erzeugt eine Audit-Zeile; Löschdialog ohne Bestätigung „Aufzeichnungen wurden exportiert“ nicht absendbar | `test_tenant_erasure_reach.py`, Frontend-Dialogtest |
| TA-420 | Unit + Guard | **Koordinaten vergröbert** (PRA-2.14, LEG-49): je Wetteradapter mit gemocktem `httpx` wird `(52.520008, 13.404954)` mit höchstens 2 Nachkommastellen gesendet (Open-Meteo, OpenWeatherMap, Bright Sky, NASA POWER); Guard: jeder Aufrufer von `fetch_daily`/`fetch_climate_normals` außerhalb der Tests läuft über `coarsen_coordinates` (Typ `CoarseCoordinates`) | `tests/unit/data_access/external/test_weather_adapters_coarse.py`, `tests/unit/guards/test_weather_calls_are_coarsened.py` |
| TA-421 | API | **Art.-13-Angaben** (PRA-2.18, LEG-50, LEG-22): `GET /privacy/policy` enthält `recipients[]` (nicht leer, sobald ein externer Adapter aktiv ist), `third_country_transfers[]`, `supervisory_authority_complaint`, `consent_withdrawal`, Art. 77 in `rights_summary`; `RetentionCategoryInfo` enthält `photos_and_attachments` mit Unterkategorien; nach PRA-1.05 die Zeile „Sicherungskopien: ≤ N Tage; Löschungen werden nach Wiederherstellung erneut angewendet“ (PRIV-708). **Präzisiert (Recovery-Nachtrag):** zusätzlich Journal-Frist R-63 (≤ 90 d, nur Pseudonyme) und Wiederanwendung von Widerrufen und Sperren (PRIV-874) | `tests/api/test_privacy_policy_api.py` |
| TA-422 | Startup | **kein Start mit Platzhalter-Verantwortlichem** (PRA-2.18, LEG-50): `full` + `production` mit einem Verantwortlichenkontakt auf `.example` → Startverweigerung mit wertfreier Meldung (analog `insecure_default_secrets`); `light` bzw. Entwicklung startet | `tests/unit/test_main_startup_checks.py` |
| TA-423 | Guard | **jede Manifest-Collection hat eine Policy-Zeile** (PRA-2.18, LEG-41): jede Collection aus `USER_DATA_MANIFEST` ist einer Zeile der Datenschutzinformation zugeordnet | `tests/unit/guards/test_manifest_collections_have_policy_rows.py` |
| TA-424 | Guard | **AttachmentCategory-Guard** (PRA-2.18, LEG-22): jede `AttachmentCategory` (`common/enums.py`) ist einer Zeile von `RetentionCategoryInfo` (`photos_and_attachments`: `location`, `garden_plan_underlay`, `plant`, `diary`/`ipm`/`harvest`/`task`, `pest_reference`, `id_recognition`) zugeordnet; eine neue Kategorie ohne Zeile schlägt fehl | `tests/unit/guards/test_attachment_categories_have_retention_rows.py` |
| TA-425 | API + Unit | **Zurechnungsfrist R-25a** (PRA-2.05, LEG-02): Setting getrennt von der Inhaltsfrist (Default = Bestand bis zur Entscheidung); Zeilen jenseits der Zurechnungsfrist liefern `performed_by = anonymisiert` bei unverändertem Inhalt | `tests/api/test_care_events_api.py`, `tests/unit/tasks/test_retention_tasks.py` |
| TA-426 | API | **DSFA-Kopplung** (PRA-3.04, LEG-48): Mandant `commercial` ohne Bestätigung „DSFA durchgeführt / Betriebsrat beteiligt / nicht erforderlich (Begründung)“ → Lead-Hinweis unabhängig vom Hosting-Modell; die Bestätigung erzeugt eine Audit-Zeile | `tests/api/test_tenants_api.py` |
| TA-427 | Unit | **Waisenobjekte** (PRA-3.06, LEG-60): Metrik `orphan_objects_total`; Warnung, wenn Waisen länger als 30 d bestehen (Fixture: 31 d alt) | `tests/unit/tasks/test_storage_tasks.py` |
| TA-630 | Unit | Jeder Default aus `08` §3.2 hat einen Test (persönlich, association, commercial, community, Bestand). **Präzisiert v1.2 (PRA-1.02):** die Defaults kommen aus `resolve_tenant_privacy_profile` (je Klasse die Tabellen in `12` §3, einschließlich der Audit-Ergänzungen) | `tests/unit/domain/models/test_tenant_settings_defaults.py`, `tests/unit/domain/services/test_tenant_privacy_profile.py` |
| TA-631 | Unit | Feature-Flags (`08` §8a): bei `false` keine datenvernichtende Aktion; Aktion liefert 409 `privacy.feature_disabled` bzw. Zustand `reclassification_pending`; bei `true` Ausführung | `tests/unit/config/test_privacy_flags.py` |
| TA-632 | Guard | Jede LEG-Zeile im Decision-Log mit Gate `nein (bis …)` nennt ein Flag oder einen Helm-Precheck, das/der im Code existiert | `scripts/check_privacy_gates.py` |

### 2.8 Offline (07)

| TA | Typ | Test | Pfad (Frontend-vitest, sofern nicht anders angegeben) |
|----|-----|------|-------------------------------------------------------|
| TA-500 | Skript | REQ-025-§10-Tabelle ↔ Speicherschlüssel im Code (Audit: tatsächlicher Sprachschlüssel `kamerplanter-lang`, kein `redux_state`) | `scripts/check_device_storage_table.py` (Pre-commit) |
| TA-501 | Unit (Pin) | Namespace-Filter bei jedem Lesen | `features/gardenPlanner/offline/queue.test.ts`, `planCache.test.ts` |
| TA-502 | Guard | keine API-Nutzdaten im Web-Storage; PRIV-512-Schlüssel beim Logout geleert | `src/test/guards/noApiDataInWebStorage.test.ts` (existiert?) — `offlineDataClearedOnSessionChange.test.ts` erweitern |
| TA-505 | Unit | Byte-basierte Verdrängung im Plan-Cache | `planCache.test.ts` |
| TA-509 | Unit | Byte-Obergrenze für Fotos | `queue.test.ts` |
| TA-511 | Unit | Sweep-Zeiträume aus der Runtime-Config; 60-Tage-Hinweis einmalig. **Präzisiert v1.2 (PRA-2.15, LEG-10):** `OFFLINE_QUEUE_PENDING_MAX_DAYS` (Default 90, ≤ 365), `OFFLINE_QUEUE_UNSENDABLE_MAX_DAYS` (30, ≤ 90), `OFFLINE_DEAD_SESSION_GRACE_DAYS` (14, ≤ 30) aus `runtime-config.js`/Helm; heute hart kodiert 365/90 d (`retention.ts:13, 15`) | `retention.test.ts`, `OfflineSyncHost.test.tsx` |
| TA-512 | Unit | nach dem Logout fehlen die aufgelisteten Schlüssel; Theme/Sprache/Einwilligung bleiben erhalten. **Präzisiert v1.2 (PRA-0.08):** die Liste steht zentral in `pwa/sessionKeys.ts` und umfasst mindestens `kp_local_data_owner`, `kp-garden-field-mode`, `kp.gardenPlanner.planting.lastUsed.*`, `kp.emailChange.address`, `kp.stepUp.*`; Logout, Kontolöschung und toter Refresh entfernen alle | `offlineData.test.ts` |
| TA-514 | Guard | Logout wartet die Bereinigung vor der Navigation ab; eingebrachter nicht abgewarteter Aufruf schlägt fehl (PRA-0.08: `handleLogout` wartet `clearOfflineData({discardWriteQueueOf})` ab, dann `window.location.replace('/login')`) | `src/test/guards/offlineDataClearedOnSessionChange.test.ts` |
| TA-516 | Unit (SW) | `KP_CLEAR_DATA` → kein `kp-sw-state`; `KP_CLEAR_DONE` gesendet (PRA-0.08: per `MessageChannel`, Fenster wartet mit 2-s-Timeout; `persistState()` erzeugt den Zustand nach dem Löschen nicht neu) | `src/test/pwa/offlineData.test.ts`, `swApiCachePerClient.test.ts` |
| TA-519 | Unit | Quarantäne / Wiederherstellung / Löschung toter Sitzungen | `sync.test.ts`, `queue.test.ts` |
| TA-520 | API (Backend) | `401 account.closed` beim Refresh für ein geschlossenes Konto; `403 membership.ended` nur, wenn eine beendete Mitgliedschaft verzeichnet ist; sonst generisches 403 | `tests/api/test_auth_router.py`, `tests/api/test_care_events_api.py` |
| TA-521 | Unit | Client-Reaktion auf beide Codes | `sync.test.ts` |
| TA-523 | Unit | Kill-Switch bei `visibilitychange` | `src/test/pwa/killSwitch.test.ts` |
| TA-524 | Unit | Idle-Bereinigung im Shared-Device-Modus, TTL 5 min, Löschung nach einem Versuch | neu `sharedDeviceMode.test.ts` |
| TA-528 | API (Backend) | Replay entschwärzt nie; Replay durch geschlossenen Autor abgelehnt; fremder Abschluss 409 | `tests/integration/test_client_event_idempotency.py` |
| TA-529 | Komponente | Konfliktdialog rendert keinen Gewinnernamen | `ConflictDialog.test.tsx` |
| TA-530 | Komponente | Geräteseiten-Inhalt und Bereinigungs-Button (PRA-2.15: Modus, Anzahl/Alter ungesendeter Einträge, Fristen, Knopf „Daten auf diesem Gerät löschen“; Zähler ungesendeter Einträge im Kontomenü, PRIV-525) | `AccountSettingsPage.test.tsx` |
| TA-531 | Unit + Komponente | Offline-Modus ist für jedes Gerät standardmäßig aus (keine Installationsklasse ausgenommen); ohne Opt-in schreibt der Client nichts in `kp-plan-cache`/`kp-write-queue` und registriert keinen SW-Cache; Opt-in speichert nur das Flag; Opt-out löscht beide Speicher und wartet `KP_CLEAR_DONE` ab. **Präzisiert v1.2 (PRA-2.15, LEG-09):** ohne Schalter `kp-offline-mode` sendet `postNamespace` `userKey=null`, `cacheUsable()`/`writeQueueAvailable()` = false, kein `kp:*`-Cache; die App-Shell bleibt verfügbar | `retention.test.ts`, `planCache.test.ts`, `OfflineSettings.test.tsx` |
| TA-532 | Unit + E2E | Übergang bestehender Installationen: vorhandener Cache ohne Flag wird beim ersten Start gelöscht, der Dialog erscheint einmal und maximal 7 Tage lang erneut, bis entschieden; „später“ lässt den Speicher leer; TC-053-094 | `src/test/pwa/offlineOptIn.test.ts`, `tests/e2e/test_req053_wave9_offline.py` |
| TA-533 | Unit + E2E | **SW-Cache projiziert** (PRA-0.07, LEG-27): `createApiCachePlugin().cacheWillUpdate` mit `plan.plan_updated_by_name="Sabine"` und `locations[0].notes="x"` → gespeicherter Body enthält beide als `null`, ebenso `description` und `cover_photo_ref`; die Antwort an die Seite bleibt vollständig; E2E: nach der Planansicht enthält `caches.open('kp:…')` keinen Mitgliedernamen | `src/test/pwa/apiCacheProjection.test.ts`, `tests/e2e/test_req053_wave9_offline.py` |
| TA-534 | Guard | **jede Allowlist-Route des SW-Caches hat eine Projektion** (PRA-0.07; INV-P7): Schlüssel von `pwa/cachePolicy.ts` (Allowlist) und `pwa/offlineProjection.ts` sind identisch; ein neuer Allowlist-Pfad ohne Projektion schlägt fehl | `src/test/guards/swCacheAllowlistIsProjected.test.ts` |
| TA-535 | Guard | **Speicherschlüssel mit Personenbezug zentral gelistet** (PRA-0.08, LEG-10): jeder `localStorage`/`sessionStorage`-Schlüssel im Code mit `userKey`, E-Mail oder Mandanten-Slug steht in `pwa/sessionKeys.ts`; ein neuer, ungelisteter Schlüssel schlägt fehl | `src/test/guards/personalStorageKeysAreListed.test.ts` |
| TA-536 | Unit | **Puffer nicht mehr wählbarer Mandanten** (PRA-2.15, LEG-10): Puffer-Einträge für Mandanten außerhalb der aktuellen Mandantenliste werden wie `membership.ended` verworfen und bleiben nicht 365 d `pending` | `sync.test.ts`, `queue.test.ts` |
| TA-537 | Unit (SW) | **physische Frist des SW-Caches** (PRA-2.16, LEG-36; Uhr fixiert): Sweep bei `activate`, bei `KP_SET_NAMESPACE` und gedrosselt (≥ 5 min) in `fetch` — ein 16 min alter Eintrag fehlt danach in `cache.keys()`; ein leerer Cache wird gelöscht; `kp-sw-state` ist nach einem Prune ohne lebende Clients nicht vorhanden | `src/test/pwa/swCacheSweep.test.ts` |
| TA-538 | Unit | **Hinweisspeicher `notices`** (PRA-2.16, LEG-56): Einträge tragen `createdAt`; ein Hinweis älter als `OFFLINE_DEAD_SESSION_GRACE_DAYS` fehlt nach `purgeExpiredEntries`; Login eines anderen `user_key` löscht ihn | `queueDb.test.ts`, `queue.test.ts` |
| TA-539 | Komponente + API + E2E | **Shared-Device-Modus** (PRA-2.17, LEG-37): bei `OFFLINE_SHARED_DEVICE_MODE=true` keine Checkbox „Angemeldet bleiben“; Backend: Login mit `remember_me=true` im Modus → Refresh-Cookie ohne `max_age`; Idle-Logout nach 15 min (Vitest, Uhr fixiert); E2E: Kiosk ⇒ Modus | `LoginPage.test.tsx`, `tests/api/test_auth_router.py`, `tests/e2e/` |
| TA-540 | Spec-/Doku-Review | **Fern-Widerruf von Sitzungen dokumentiert** (PRA-2.15 Teil (6), PRIV-539, LEG-10): Nutzerdoku und `07` §8a nennen den Fern-Widerruf von Sitzungen (`DELETE /users/me/sessions/{key}`) mit seiner Grenze (Gerätespeicher bleibt bis zum nächsten Start bzw. zur Frist). | `docs/de/user-guide/privacy.md`, `spec/privacy/07-offline-privacy.md` |
| E2E | Selenium | TC-053-091 Logout leert jeden Nutzerschlüssel; TC-053-092 Quarantäne toter Sitzungen; TC-053-093 Idle-Bereinigung im Shared-Device-Modus | `tests/e2e/test_req053_wave9_offline.py` (erweitern; Marker `req053`) |

### 2.9 Datenexporte (Art. 15/20, CSV, Mandantenarchiv)

| TA | Typ | Test | Pfad |
|----|-----|------|------|
| TA-600 | Integration (existiert, erweitern) | Art.-15-Bündel enthält keinen Schlüssel eines anderen Mitglieds (Pin `_CARE_EVENT_EXPORT_FIELDS`) und, neu, kein `PersonRef.display_name` anderer in den Abschnitten des persönlichen Gartens | `tests/integration/test_privacy_export_walk.py` |
| TA-601 | Integration | Bündel findet gesetzliche Zeilen per Tombstone für eine weiterhin aktive Person nach einer Mandantenlöschung (existiert: `test_privacy_export_tombstone.py`) — beibehalten | existierend |
| TA-602 | Integration | nach einer Reklassifizierung `record_keeping → none` listet das Bündel die Zeilen der Person als `attribution_gap`? — nein: das Konto der Person existiert, die Zeilen tragen bis zur Löschung ihren lebenden Schlüssel; pinnen, dass sich für lebende Konten nichts ändert | `test_privacy_export_walk.py` |
| TA-603 | Guard (existiert) | R2-Reziprozität für die neuen Collections (`privacy_review_items`, `privacy_journal_outbox` (v1.2 statt `erasure_mirror`), `migration_reports`, `privacy_requests`, `legal_holds`, `privacy_incidents` in `EXCLUDED_FROM_DISCLOSURE` oder im Manifest, je mit Begründung) | `scripts/check_privacy_inventory.py` |
| TA-604 | Integration | Mandantenarchiv `members.jsonl` enthält keine E-Mail (existiert gemäß REQ-056 E-09 — pinnen) | `tests/integration/test_tenant_export*.py` |
| TA-633 | Integration | **verlassene Mandanten** (PRA-2.04, LEG-06 Teil b): Person verlässt Mandant B → ihr Art.-15-Export enthält ihre server-gestempelten Zeilen aus B (oder einen `disclosure_gap` mit Begründung, je nach Rechtsantwort) | `test_privacy_export_walk.py` |
| TA-634 | Integration | **Fotos im Bündel** (PRA-2.04, LEG-21): Sektion `attachments` enthält `_key`, `created_at` und das Elternobjekt, nie `storage_key`, plus Hinweis zur Dateibeschaffung; nach Entscheidung ZIP-Variante (`files/<key>.<ext>` eigener Uploads, auch aus verlassenen Mandanten) | `test_privacy_export_walk.py` |
| TA-635 | API | **Export-Absicherung** (PRA-2.04, LEG-38): `POST /privacy/export`, `GET /privacy/export/{key}` und `/download` mit `Authorization: Bearer kp_…` (ungescopter API-Key) → 403; Sitzung ohne Step-up `data_export` → 401 `STEP_UP_*`; Mail-Double empfängt „Export angefordert“ bei Anlage und bei Download | `tests/api/test_privacy_export_api.py` |
| TA-636 | API | **Exportliste und Dritten-Prozess** (PRA-2.04): `GET /privacy/export` listet die eigenen Anfragen nach Reload; Admin-Foto-Suche/-Löschung für Anfragen abgebildeter Dritter erzeugt eine Audit-Zeile | `tests/api/test_privacy_export_api.py`, `tests/api/test_admin_photo_requests.py` |
| TA-637 | Unit | **Art. 15 Abs. 1 lit. a–h und Art. 19 S. 2 im Bündel** (PRA-2.18, PRA-2.20; LEG-41): Abschnitt `processing_information` aus derselben Quelle wie `GET /privacy/policy`; jede Bündelsektion trägt `purpose`, `legal_basis`, `retention`, `recipients`; fester Satz zu Art. 22; auf Verlangen die Empfänger nach Art. 19 | `tests/unit/domain/engines/test_data_export_engine.py` |

### 2.10 Migrationen (09)

| TA | Typ | Test | Pfad |
|----|-----|------|------|
| TA-700…TA-703, TA-716, TA-717, TA-719 | Unit + Integration | wie in `09` §12 aufgeführt | `tests/unit/migrations/versions/test_v0109_*.py`, `tests/integration/migrations/` |
| TA-701a | Unit | Berichts-Schwärzungsfilter: ein eingebrachter Nutzerschlüssel / Name in `details` wird abgelehnt | `tests/unit/migrations/test_migration_report_redaction.py` |
| TA-704 | Guard | Privacy-Migrationen deklarieren `kind`; ein `data_backfill` nutzt `ActiveTenants`, eine `privacy_correction` nicht | `tests/unit/guards/test_migration_tenant_gate_kind.py` |

### 2.11 Backup-Wiederherstellung (09 §6, 17)

Geändert mit v1.2 (Audit 2026-11-22, LEG-24/LEG-25): Der Löschungs-Spiegel mit Beat-Sync ist durch das
**Privacy-&-Security-Journal mit Outbox (write-through)** ersetzt (`12` E14, PRA-1.04); das Journal umfasst auch
Widerrufe und Sicherheitsereignisse. Die Tests unten sind entsprechend angepasst. **Recovery-Nachtrag 2026-11-23:**
Mechanik, Ereignistaxonomie und Restore-Lebenszyklus stehen in [`17`](17-privacy-recovery.md); wo eine Zeile unten
ältere Namen nennt (`account_erased` …, `privacy.journal_flush`, `instance_state.journal_high_watermark`, R-45), gilt die
Abbildung `17` §0.4/§3.3, und die präzisierende TA aus §2.11a ist maßgeblich.

| TA | Typ | Test | Bezug | Pfad |
|----|-----|------|-------|------|
| TA-709 | Integration | Journal-Eintrag (nur Tombstone bzw. Datensatz-ID, kein Rohschlüssel — Assertion: der Rohschlüssel kommt in der Outbox, im Bucket-Objekt und im entschlüsselten Objekt nicht vor, Regex-Scan) wird im selben Schreibschritt wie der Löschabschluss geschrieben und **ohne Dump-Lauf** innerhalb des konfigurierten SLA nach `privacy/journal/<seq>.jsonl.fernet` übertragen (MinIO mit Object Lock); HMAC-Kette gültig; Bereinigung (R-45) filtert. **Präzisiert (Recovery-Nachtrag):** keine gefilterte Bereinigung — Segmente laufen nach R-63 ab (PRIV-808, TA-740); Minimierungs-Scan TA-728 | PRA-1.04 · LEG-25 | `tests/integration/test_privacy_journal.py` (vorher `test_erasure_mirror.py`) |
| TA-710 | Integration (Restore-Drill, nightly) | Dump vor Löschung → Löschung → Restore → Replay erkennt das Konto per Tombstone-Abgleich (beide Formate) → Rohschlüssel in keiner Collection; Residue 0; Prüf-Items idempotent. **Präzisiert v1.2 (PRA-1.05):** Szenarien S3–S7 — Konto löschen / Einwilligung widerrufen / API-Key widerrufen / Passwort ändern vor dem Restore; nach dem Restore Backend 503 bis zum Replay; danach kein Rohschlüssel, Consent-Guard 403 `ConsentRequiredError`, API-Key 401, Login mit altem Passwort schlägt fehl, Refresh-Tokens von vor dem Restore 401; Replay erfasst ArangoDB, TimescaleDB, Objektspeicher und `vectordb`; Bericht `migration_reports/restore_replay` | PRA-1.05 · LEG-11, LEG-24 | `tests/integration/test_restore_replay.py` (markiert `slow`, Nightly-Lane) |
| TA-711 | Doku | Restore-Anleitung enthält den Replay-Schritt; `mkdocs build --strict`. **Erweitert v1.2 (PRA-0.10, LEG-26):** `backup-restore.md` (DE/EN) enthält den Warnblock „nicht in Produktion aktivieren, bevor Replay verfügbar ist“, das manuelle Runbook (Löschaufträge mit `completed_at > dump_ts` erneut ausführen, JWT-Secret rotieren, Refresh-Tokens widerrufen) und den Abschnitt Bucket-Lifecycle (Versionierung nur mit `NoncurrentVersionExpiration ≤ 35 d` und `ExpiredObjectDeleteMarker`, Beispiel-JSON AWS/MinIO); der Light/Docker-Pfad verweist auf den Replay-Schritt. **Erweitert (Recovery-Nachtrag, PRA-0.12, PRIV-873):** Runbook nennt alle `celery-worker*`-Deployments (inkl. `-default`, `-bulk`) mit Prüfung „0 Pods“, leert Valkey vor dem Einspielen, startet Backend → `critical` → übrige Worker → Beat, Rückfallbasis als Pflichtschritt; Backup-Tabelle nennt `vectordb` und Anhänge; DE/EN strukturgleich | PRA-0.10, PRA-1.05, PRA-0.12 · LEG-26, LEG-62, LEG-69, LEG-70 | Docs-Lane |
| TA-718 | Helm | `backup.enabled=true` ohne `privacy.mirror.enabled` → Template-Fehler. **Angepasst v1.2 (PRA-0.10, PRA-1.04):** Precheck auf `privacy.journal.enabled`; `helm template --set backup.enabled=true --set backup.s3.bucket=x` → Render-Fehler; mit ausdrücklichem Override `backup.acknowledgeNoErasureReplay=true` → rendert (Override entfällt, sobald PRA-1.04 gemergt ist) | PRA-0.10 · LEG-11 | `helm template` im CI, Chart-Vertrag `scripts/ci/assert_chart_contracts.sh` (Recovery-Nachtrag: es gibt kein helm-unittest im Repo; PRIV-855) |
| TA-720 | Helm | **Backup-Frist begrenzt** (PRA-0.10, LEG-11/LEG-26; INV-P10): `--set backup.retentionDays=0` und `=36` → Render-Fehler; `1…35` rendert; ebenso negative und nicht-numerische Werte → Render-Fehler (heute = unbegrenzt, `helm/kamerplanter/values.yaml:1418`) | PRA-0.10 | Chart-Vertrag `scripts/ci/assert_chart_contracts.sh` (statt helm-unittest) |
| TA-721 | Integration | **Outbox je Ereignistyp** (PRA-1.04, LEG-24; INV-P5): für `account_erased`, `tenant_erased`, `consent_revoked`, `restriction_set`/`restriction_lifted`, `objection_recorded`, `api_key_revoked`, `sessions_revoked`, `password_changed`, `membership_removed`, `role_lowered`, `tenant_suspended` je ein Test, dass die fachliche Änderung ohne Outbox-Eintrag nicht committet (eingebrachter Fehler beim Outbox-Schreiben rollt die Änderung zurück); Sequenz monoton. **Präzisiert (Recovery-Nachtrag, = TA-R10):** je Ereignistyp der Taxonomie `17` §3.3 (Abbildung alt → neu dort), in derselben Stream-Transaktion über RC-01 (PRIV-802); `aggregate.version` im selben Commit hochgezählt | PRA-1.04 · LEG-24, LEG-25 | `tests/integration/test_privacy_journal_outbox.py` |
| TA-722 | Unit | **Journal-Überwachung** (PRA-1.04): Metrik `privacy_journal_outbox_age_seconds` wird exportiert; ein Eintrag älter als 1 h löst den Alarm aus; `instance_state.journal_high_watermark` wird nach dem Flush fortgeschrieben. **Präzisiert (Recovery-Nachtrag):** Relay `privacy.journal_relay` schreibt `watermark_seq`/`watermark_hash` in `system_meta/privacy_recovery` (RC-06); Metriken und Alarme nach `17` §11.4 (PRIV-871) | PRA-1.04, PRA-3.02 | `tests/unit/tasks/test_privacy_journal_flush.py` |
| TA-723 | Integration | **Restore-Erkennung** (PRA-1.05, LEG-11; INV-P6): DB-Hochwassermarke < höchste Sequenz im Bucket ⇒ Backend-Lifespan und Worker-Initialisierung gehen in den Wartungsmodus (503 außer Health und Admin-Replay); kein Beat läuft. **Präzisiert (Recovery-Nachtrag):** Gate-Gründe `17` §5.3 über TA-738, TA-742, TA-750 | PRA-1.05 | `tests/integration/test_restore_detection.py` |
| TA-724 | Integration | **Journal-Verlust und Rückfall** (PRA-1.05): fehlt das Journal, verweigert das Replay „abgeschlossen“ ohne ausdrückliche Betreiberbestätigung; der Rückfallpfad rotiert das JWT-Secret, löscht alle Refresh-Tokens und setzt alle API-Keys auf „Bestätigung erforderlich“. **Präzisiert (Recovery-Nachtrag):** Rückfall nur über `FALLBACK_REVIEW` mit `JOURNAL_GAP_ACKNOWLEDGED` (PRIV-832, TA-748) | PRA-1.05 · LEG-24 | `tests/integration/test_restore_replay.py` |
| TA-725 | Doku + Skript | **Docker-Backup** (PRA-3.07, LEG-43): `scripts/backup-docker.sh` übergibt das DB-Passwort nicht als Argument (Expansion wie im Helm-Job), löscht Dumps nach ≤ 35 d (`find … -mtime +30 -delete`), optional `age`/`gpg`; `docker-dauerbetrieb.md` nennt Frist und Löschpropagation (Replay) | PRA-3.07 | `tests/scripts/test_backup_docker.sh` (bats) bzw. Shellcheck + Docs-Lane |

### 2.11a Privacy Recovery: Journal, Restore-Lebenszyklus, Reconciliation (17; Recovery-Nachtrag 2026-11-23)

Reguläre Abnahmefälle der Testfall-Vorschläge aus [`17`](17-privacy-recovery.md) §11.1 (Spalte „TA-R“ dort; Abbildung
§2.11b). Akzeptanzkriterien sind die messbaren Kriterien aus `17` §11.1. Ein Restore gilt im Test **nur** als
erfolgreich, wenn INTEGRITY_VALIDATED erreicht ist (`17` §5.6); ein grüner Dokumentzähler (Drill 2026-10-04) genügt nicht.
Pfade sind Vorschläge; Status aller Fälle: `spezifiziert` (kein Test im Repo).

| TA | Typ | Test | Bezug | Pfad (neu) |
|----|-----|------|-------|------------|
| TA-726 | Unit | **Event-Schema** (TA-R01; PRIV-803): jedes Ereignis jedes Typs aus `17` §3.3 validiert gegen `kp.privacy-journal/v1`; unbekannter Typ und unbekannte Hauptversion ⇒ Reader-Fehler (kein stilles Überspringen) | PRA-1.04 · LEG-24 | `tests/unit/domain/privacy_journal/test_event_schema.py` |
| TA-727 | Unit | **Pseudonyme** (TA-R02; PRIV-804): `jsub_`/`jten_`/`jrec_` deterministisch, domänengetrennt (≠ `anon_` für denselben Schlüssel), 32 Hex | PRA-1.04 · LEG-11 | `tests/unit/domain/privacy_journal/test_pseudonyms.py` |
| TA-728 | Unit | **Minimierung** (TA-R03; PRIV-804, PRIV-807): Regex-Scan über alle erzeugten Test-Ereignisse und Segmente — kein Rohschlüssel, keine E-Mail, kein Freitext, kein Speicherschlüssel; ergänzt TA-709 | PRA-1.04 · LEG-11 | `tests/unit/domain/privacy_journal/test_journal_minimisation.py` |
| TA-729 | Integration (MinIO) | **Relay-Einzelschreiber** (TA-R04; PRIV-805, PRIV-806, PRIV-810): zwei parallele Relays ⇒ genau eine lückenlose `jseq`-Folge; ein zweites Segment gleicher Startnummer wird abgewiesen (bedingtes Schreiben bzw. Object Lock; Unterstützung des Anbieters wird hier geprüft); der Relay-Zugang hat kein `DeleteObject` | PRA-1.04 · LEG-25 | `tests/integration/test_privacy_journal_relay.py` |
| TA-730 | Integration | **Dump-Konsistenz und Manifest** (TA-R05; PRIV-814, PRIV-828): Dump während laufender Ereignisse; das Manifest trägt `journal_seq_at_start` (vor dem Dump gelesen); Replay ab `min(DB-Marke, journal_seq_at_start)` erfasst jedes Ereignis, das `users` im Dump nicht enthält | PRA-2.22, PRA-1.05 · LEG-11 | `tests/integration/test_restore_dump_consistency.py` |
| TA-731 | Unit | **Reihenfolge** (TA-R06; PRIV-815): Folgen `CONSENT_WITHDRAWN, CONSENT_GRANTED` und `CONSENT_GRANTED, CONSENT_WITHDRAWN` je Aggregat ⇒ Endzustand nach `17` §3.6 (eine Erteilung nach T0 wird nicht wiederhergestellt) | PRA-1.04 · LEG-24 | `tests/unit/domain/services/recovery/test_replay_ordering.py` |
| TA-732 | Unit | **Duplikate** (TA-R07; PRIV-805, PRIV-841): gleiche `event_id` doppelt im Store ⇒ genau eine Anwendung, Zähler `duplicate=1` | PRA-1.04, PRA-1.05 | `tests/unit/domain/services/recovery/test_replay_idempotency.py` |
| TA-733 | Unit | **Lücke** (TA-R08; PRIV-809): fehlende `jseq` ⇒ Verifier `JOURNAL_INTEGRITY`, Gate zu | PRA-1.05 · LEG-11 | `tests/unit/data_access/journal/test_journal_verifier.py` |
| TA-734 | Unit | **Korruption** (TA-R09; PRIV-807, PRIV-809): verändertes Byte im Segment ⇒ MAC-Fehler; verändertes `prev_hash` ⇒ Kettenfehler; kein Eintrag wird übersprungen | PRA-1.04, PRA-1.05 | `tests/unit/data_access/journal/test_journal_verifier.py` |
| TA-735 | Guard (statisch) | **Emittenten-Vollständigkeit** (TA-R11; PRIV-801; INV-P5): jede Mutationsmethode der Ereignisliste `17` §3.3 ruft RC-01 (Muster `test_membership_mutations_write_the_security_audit.py`); eine eingebrachte Mutation ohne Emit schlägt fehl | PRA-1.04 · LEG-24 | `tests/unit/guards/test_privacy_mutations_emit_a_journal_event.py` |
| TA-736 | Integration | **Abschlussregel** (TA-R12; PRIV-811): Store nicht erreichbar ⇒ Löschung bleibt `completed_pending_journal`, UI/Admin zeigt „in Bearbeitung“; nach dem Ack `completed` mit `journal_seq` | PRA-1.04 · LEG-11 | `tests/integration/test_privacy_journal_completion.py` |
| TA-737 | Unit + API + Guard | **fail-closed Widerruf** (TA-R13; PRIV-812): Repository-Fehler bei `revoke` ⇒ Exception, Route 5xx, kein Erfolgs-Log, kein Outbox-Eintrag; Guard gegen `except Exception: return False` in Widerrufsmethoden | PRA-2.21 · LEG-66 | `tests/unit/data_access/arango/test_api_key_revoke_fails_closed.py`, `tests/unit/guards/test_revocations_do_not_swallow_errors.py` |
| TA-738 | Integration | **Absturzfenster** (TA-R14; PRIV-809, PRIV-821): Store bestätigt, DB-Ack fehlt ⇒ Start erkennt keinen Restore, Ack wird nachgeholt, Gate offen; fehlt auch nur eine `event_id` in der Outbox ⇒ Restore erkannt | PRA-1.05 · LEG-11 | `tests/integration/test_restore_detection.py` |
| TA-739 | Integration | **Salt-Identität** (TA-R15; PRIV-813): Start mit anderem Salt gleicher Länge ⇒ Gate `SECRET_MISMATCH`, Backend 503 bzw. Startverweigerung, Worker verweigern Aufgaben | PRA-2.22 · LEG-67 | `tests/integration/test_secret_identity_gate.py` |
| TA-740 | Helm (Chart-Vertrag) | **Fristen** (TA-R16; PRIV-808, PRIV-855): `privacy.journal.retentionDays < L_eff + 14` oder `> 90` ⇒ Render-Fehler; `backup.enabled` ohne `privacy.journal.enabled` ⇒ Fehler (wie TA-718); ergänzt TA-718, TA-720 | PRA-0.10, PRA-1.04 · LEG-11 | `scripts/ci/assert_chart_contracts.sh` |
| TA-741 | Helm (Chart-Vertrag) | **Restore-Modus** (TA-R17; PRIV-822, PRIV-824, PRIV-855): `privacy.restore.isolate=true` rendert jedes `celery-worker*` (auch `-default`, `-bulk` bei `celeryWorkers.dedicatedQueues`) und Beat mit 0 Replikas, Backend mit `KP_RESTORE_MODE`, MCP aus | PRA-1.05, PRA-0.10 · LEG-62 | `scripts/ci/assert_chart_contracts.sh` |
| TA-742 | Integration | **Worker-/Beat-Gate** (TA-R18; PRIV-823, PRIV-827): Gate zu ⇒ `task_prerun` verweigert, Beat plant über zwei Ticks 0 Aufgaben; Migrationskopf alt ⇒ Worker `SCHEMA_BEHIND` | PRA-1.05 · LEG-70 | `tests/integration/test_worker_restore_gate.py` |
| TA-743 | Integration | **Valkey** (TA-R19; PRIV-825): nach RESTORE_ISOLATED `DBSIZE = 0`; keine MCP-Sitzung eines gelöschten Kontos auflösbar | PRA-1.05, PRA-0.12 · LEG-69 | `tests/integration/test_restore_isolation_valkey.py` |
| TA-744 | E2E-Restore (nightly) | **Szenario A** (TA-R20; PRIV-800, PRIV-840, PRIV-845): Dump → Löschung (Antrag und sofortiger Vollzug) → Restore ⇒ Gate 503 → Replay ⇒ Rohschlüssel in 0 Collections, `erasure_requests` mit Tombstone vorhanden, Login 401; präzisiert TA-710, TA-723 | PRA-1.05, PRA-1.07, PRA-3.09 · LEG-11, LEG-24 | `tests/integration/test_restore_lifecycle.py` (markiert `slow`, Nightly-Lane) |
| TA-745 | E2E-Restore | **Szenario B** (TA-R21; PRIV-840, PRIV-843): Mandant nach dem Dump gelöscht ⇒ nach der Freigabe kein Dokument mit `tenant_key`, kein Objekt mit Präfix (inkl. Versionen), keine TimescaleDB-Zeile, keine `vectordb`-Zeile; Pflichtzeilen pseudonymisiert und aus Produktfunktionen ausgeschlossen; präzisiert TA-804 | PRA-1.05, PRA-2.09, PRA-3.09 · LEG-11 | `tests/integration/test_restore_lifecycle.py` |
| TA-746 | E2E-Restore | **Szenario C** (TA-R22; PRIV-840): Widerruf nach dem Dump ⇒ Consent-Guard 403 `ConsentRequiredError`; spätere Erteilung ⇒ weiterhin widerrufen, erneute Einwilligung angefordert; präzisiert TA-710 | PRA-1.05, PRA-3.09 · LEG-24 | dto. |
| TA-747 | E2E-Restore | **Szenario D** (TA-R23; PRIV-840, PRIV-842): Sperre `all` nach dem Dump ⇒ nach dem Replay 423 auf verarbeitenden Routen; Retention-Nachlauf meldet `held ≥ 1`, Zeilen unverändert (Bezug TA-133…TA-136) | PRA-1.05, PRA-1.06, PRA-3.09 · LEG-23, LEG-35 | dto. |
| TA-748 | E2E-Restore | **Szenario E** (TA-R24; PRIV-821, PRIV-832): Store aus bzw. Lücke ⇒ Zustand `RESTORE_BLOCKED`, Readiness 503; Freigabe ohne `JOURNAL_GAP_ACKNOWLEDGED` unmöglich; präzisiert TA-724 | PRA-1.05, PRA-3.09 · LEG-11 | dto. |
| TA-749 | E2E-Restore | **Szenario F** (TA-R25; PRIV-850): Foto nach dem Dump gelöscht (versionierter MinIO) ⇒ nach der Freigabe liefert `list-object-versions` für Original und Renditions nichts; präzisiert TA-804 | PRA-1.08, PRA-3.09 · LEG-26 | dto. |
| TA-750 | E2E-Restore | **Szenario G** (TA-R26; PRIV-806, PRIV-821, PRIV-826): Journal-Kopf < DB-Marke ⇒ `JOURNAL_BEHIND_DATABASE`, keine Phase nach DATA_RESTORED | PRA-1.05, PRA-3.09 · LEG-11 | dto. |
| TA-751 | E2E-Restore | **Szenario H** (TA-R27; PRIV-820, PRIV-828, PRIV-841): Abbruch in ERASURE_RECONCILIATION ⇒ Fortsetzung wendet keine Aktion doppelt an (Zähler `applied` = Plan), System bis zur Freigabe 503 | PRA-1.05, PRA-3.09 · LEG-11 | dto. |
| TA-752 | E2E-Restore | **Zugänge S7** (TA-R28; PRIV-829): widerrufener API-Key 401; altes Passwort scheitert; vor dem Restore ausgestellter Refresh-Token 401; gesenkte Rolle bleibt gesenkt; präzisiert TA-710, TA-811 | PRA-1.05 · LEG-24 | dto. |
| TA-753 | Integration | **Waisen** (TA-R29; PRIV-853): nach dem Dump hochgeladenes Objekt ⇒ nach dem Restore in Quarantäne, nicht auslieferbar (404), nach R-65 gelöscht | PRA-1.08, PRA-3.06 · LEG-60 | `tests/integration/test_storage_restore_reconciler.py` |
| TA-754 | Integration | **Caches und abgeleitete Speicher** (TA-R30; PRIV-840): `ai_tip_cache` und Glossar-Cache nach der Freigabe leer; `vectordb` ohne Beiträge gelöschter Subjekte | PRA-1.05 · LEG-11 | `tests/integration/test_restore_derived_stores.py` |
| TA-755 | E2E-Restore | **Wiederholter Restore** (TA-R31; PRIV-841): zweiter Restore desselben Backups ⇒ identischer Endzustand und identische Report-Zähler (außer `restore_id`) | PRA-1.05 · LEG-11 | `tests/integration/test_restore_lifecycle.py` |
| TA-756 | Integration | **Mandanten-Import gegen Löschungen** (TA-R32; PRIV-844): Archiv mit einem nach dem Export gelöschten Mitglied ⇒ Marker, Fotos dieses Mitglieds nicht importiert, Zuordnung gesperrt, Bericht zählt 1 (ohne Kennung); präzisiert TA-806 | PRA-1.07 · LEG-65 | `tests/integration/test_tenant_import_erased_members.py` |
| TA-757 | Doku + Skript | **Docker-Restore und Anhänge-Volume** (TA-R33; PRIV-833): Anleitung stoppt alle App-Dienste vor `arangorestore`, leert Valkey, führt den Reconcile per Override aus; Passwort nie als Argument; Compose mountet `attachments` für `backend` und `celery-worker`; ergänzt TA-725 | PRA-0.12, PRA-2.23, PRA-3.07 · LEG-63, LEG-64 | Docs-Lane, Shellcheck/bats, Container-Smoke-Test |
| TA-758 | Betrieb (Nachweis wie TA-9xx) | **Lifecycle** (TA-R34; PRIV-851, PRIV-852, PRIV-854): Lifecycle-JSON für Backup- und Anhangs-Bucket abgelegt (inkl. `Expiration` = `retentionDays + 1`, `NoncurrentVersionExpiration`, `ExpiredObjectDeleteMarker`, `AbortIncompleteMultipartUpload`; kein Object Lock auf Anhängen); Drill „Objekt löschen → nach Frist + 1 d keine Version“; ergänzt TA-903 | PRA-0.10, PRA-0.03 · LEG-26, LEG-68 | Evidenzablage (PRA-3.09) |
| TA-759 | Unit (Frontend) | **Offline-Restore-Epoche** (TA-R35; PRIV-846): Antwort mit neuer `X-KP-Restore-Epoch` ⇒ Client verwirft Plan-Cache und SW-API-Cache, Puffer-Einträge gehen in den Bestätigungsdialog statt automatisch an den Server; ergänzt TA-803 | PRA-2.15 · LEG-24 | `src/frontend/src/features/gardenPlanner/offline/*.test.ts` |
| TA-760 | Betrieb + Unit | **Evidence-Report** (TA-R36; PRIV-831, PRIV-870): Report enthält alle Pflichtfelder `17` §11.5, keine Pseudonyme oder Personendaten (Regex), liegt außerhalb der DB; Freigaben nach Betriebsmodell (`17` §2.2) eingetragen; ergänzt TA-916 | PRA-1.05, PRA-3.09 · LEG-11 | `tests/unit/domain/services/recovery/test_evidence_report.py`, Evidenzablage |

### 2.11b Abbildung TA-R (17 §11.1) → TA (Recovery-Nachtrag 2026-11-23)

Belegung geprüft am 2026-11-23 über `spec/` (Grep `TA-7nn`): belegt TA-700…704, 701a, 709…711, 716…725; frei 705…708,
712…715 und ab TA-726. Vergeben wird fortlaufend ab TA-726; die Lücken bleiben frei (keine Umdeutung früherer Nummern).
TA-R10 erhält keine neue Nummer, weil der Fall TA-721 (Outbox je Ereignistyp) ist und dort präzisiert wird
(„präzisiert statt dupliziert“). Die Zuordnung in `17` §11.1 bleibt unverändert; dort werden die TA-R-IDs durch die
Hauptsession ersetzt.

| TA-R | TA | Kurz | TA-R | TA | Kurz |
|---|---|---|---|---|---|
| TA-R01 | TA-726 | Event-Schema | TA-R19 | TA-743 | Valkey |
| TA-R02 | TA-727 | Pseudonyme | TA-R20 | TA-744 | Szenario A |
| TA-R03 | TA-728 | Minimierung | TA-R21 | TA-745 | Szenario B |
| TA-R04 | TA-729 | Relay-Einzelschreiber | TA-R22 | TA-746 | Szenario C |
| TA-R05 | TA-730 | Dump-Konsistenz, Manifest | TA-R23 | TA-747 | Szenario D |
| TA-R06 | TA-731 | Reihenfolge | TA-R24 | TA-748 | Szenario E |
| TA-R07 | TA-732 | Duplikate | TA-R25 | TA-749 | Szenario F |
| TA-R08 | TA-733 | Lücke | TA-R26 | TA-750 | Szenario G |
| TA-R09 | TA-734 | Korruption | TA-R27 | TA-751 | Szenario H |
| TA-R10 | TA-721 (präzisiert) | Outbox-Atomarität je Typ | TA-R28 | TA-752 | Zugänge S7 |
| TA-R11 | TA-735 | statischer Emittenten-Guard | TA-R29 | TA-753 | Waisen |
| TA-R12 | TA-736 | Abschlussregel | TA-R30 | TA-754 | Caches, abgeleitete Speicher |
| TA-R13 | TA-737 | fail-closed Widerruf | TA-R31 | TA-755 | wiederholter Restore |
| TA-R14 | TA-738 | Absturzfenster | TA-R32 | TA-756 | Mandanten-Import |
| TA-R15 | TA-739 | Salt-Identität | TA-R33 | TA-757 | Docker-Restore |
| TA-R16 | TA-740 | Fristen (Chart-Vertrag) | TA-R34 | TA-758 | Lifecycle |
| TA-R17 | TA-741 | Restore-Modus (Chart-Vertrag) | TA-R35 | TA-759 | Offline-Epoche |
| TA-R18 | TA-742 | Worker-/Beat-Gate | TA-R36 | TA-760 | Evidence-Report |

Bezug zu bestehenden Fällen (aus `17` §11.1 „Bezug bestehend“): TA-728 ergänzt TA-709; TA-740 ergänzt TA-718/TA-720;
TA-744 präzisiert TA-710/TA-723; TA-745, TA-749 präzisieren TA-804; TA-746, TA-752 präzisieren TA-710; TA-747 ↔
TA-133…TA-136; TA-748 präzisiert TA-724; TA-756 präzisiert TA-806; TA-757 ergänzt TA-725; TA-758 ergänzt TA-903; TA-759
ergänzt TA-803; TA-760 ergänzt TA-916. Ohne TA-R, aber mit Abnahmefall: PRIV-860 → TA-915, PRIV-861 → TA-918 (neu),
PRIV-871 → TA-722, PRIV-872 → TA-916, PRIV-873 → TA-711, PRIV-874 → TA-421 (§2.16).

### 2.12 Betriebs- und Dokumentnachweise (TA-9xx, neu v1.2)

Nachweise, die kein CI-Test erbringen kann (Konfiguration einer Installation, Verträge, Rechtsentscheidungen,
Dokumentinhalte). Ablage: Nachweisvorlage und Evidenzablage nach PRA-3.09 (je Installation ein datiertes Dokument im
Betriebs-Repo, außerhalb des Produkt-Repos); Dokumentnachweise per Review, Grep und `mkdocs build --strict`. Ein
TA-9xx gilt als bestanden, wenn der datierte Eintrag vorliegt.

| TA | Art | Nachweis | Bezug |
|----|-----|----------|-------|
| TA-901 | Betrieb | Für jede Installation ein datierter Eintrag „`LLM_PROVIDER` des Knowledge-Service = …“ (Helm-Values/ArgoCD, Pod-Env); bei Cloud-Wert Umstellung auf `ollama` oder Abschaltung der betroffenen KI-Funktionen mit Zeitpunkt | PRA-0.01 · LEG-31 |
| TA-902 | Betrieb + Doku | Datierte Aussage von Product Owner und Betreiber „BM-001 nicht vor PRA-3.02“ oder Termin; die DEC-32-Checkliste nennt PRA-3.02 als Release-Blocker (Grep) | PRA-0.02 · LEG-32 |
| TA-903 | Betrieb | Je Installation datiert: (1) `backup.enabled`, (2) Versionierung und Lifecycle von Backup- und Anhangs-Bucket (bei Versionierung die gesetzte Lifecycle-Regel als JSON), (3) ob seit Aktivierung ein Restore stattfand; Drill: `list-object-versions` zeigt nach Frist + 1 d keine Version eines gelöschten Testobjekts | PRA-0.03 · LEG-11, LEG-24, LEG-26 |
| TA-904 | Betrieb | Datierte Aussage je Installation, ob Mandanten mit Beschäftigten bestehen; bei „ja“ ist PRA-2.06 als nächste Lane eingeplant und der Hinweis auf § 87 BetrVG/DSFA an die Leitungen versandt | PRA-0.04 · LEG-05, LEG-28 |
| TA-905 | Doku | Grep über `docs/` findet keine DSFA-Behauptung (W-10) und nicht den Satz „nicht mehr aktiv verarbeitet“; i18n DE/EN gleichlautend geändert; Offline-Texte entsprechen dem Ist-Stand (SW-Cache); `07` §8a unterscheidet „mit/ohne Angemeldet bleiben“; Login-Tooltip „nicht auf geteilten Geräten“; `mkdocs build --strict` grün | PRA-0.05 · LEG-23, LEG-12, LEG-27, LEG-37 |
| TA-906 | Doku | `SECURITY.md` im Root (Meldeadresse, unterstützte Versionen, Reaktionszeiten); Runbook `docs/{de,en}/deployment/incident-response.md` in der Nav; jeder genannte Hebel (`POST /auth/logout-all`, API-Key-Widerruf, Konto-/Mandantensperre, Secret-Rotation) verweist auf eine existierende Route oder Einstellung; `mkdocs build --strict` grün | PRA-0.11 · LEG-32 |
| TA-907 | Doku | Register `spec/privacy/18-recipients-and-subprocessors.md` und YAML-Quelle vorhanden; `06` §2 enthält PA-13…PA-17 mit Rechtsgrundlage und Evidenzklasse; `13` enthält V-12 und V-13; Abgleich mit den Verträgen des Betreibers | PRA-1.03 · LEG-33, LEG-16 |
| TA-908 | Doku | `14` enthält W-30; REQ-049 P4 nennt die abschließende Ausnahmeliste, REQ-056 §8 verweist darauf; `11` RISK-15 entspricht dem Code (GPS im Archiv ungerundet oder gerundet nach Entscheidung Q-PO-20) | PRA-2.11 · LEG-53, LEG-13 |
| TA-909 | Doku | Für jede in PRA-3.01 genannte LEG-ID steht im decision-log §B ein Status (`decided` oder `open` mit Prüfdatum); jede `decided`-Zeile verweist auf die umsetzende PRA-Aufgabe; `16` enthält alle neuen DSB-/Rechtsfragen des Audits (Grep-Abgleich LEG ↔ decision-log) | PRA-3.01 |
| TA-910 | Doku + Betrieb | `spec/privacy/19-incident-response.md` (umnummeriert im Recovery-Nachtrag 2026-11-23; `17` ist SPEC-17 Privacy Recovery) existiert, ist im README verlinkt und referenziert TA-037/TA-038/TA-136; Tabletop-Übung protokolliert | PRA-3.02 · LEG-32 |
| TA-911 | Doku | `06` §1 nennt für jedes Betriebsmodell Rolle und Pflichtdokument; AVV-Muster mit TOM- und Unter-AV-Anlage und Klausel zum Plattform-Export liegt vor; Art.-26-Vorlage liegt vor; LEG-01 `decided` | PRA-3.03 · LEG-01, LEG-13 |
| TA-912 | Doku | `11` enthält RISK-21…RISK-24 und die Zeile „selbst gehostet, gewerblich/Anbauvereinigung“, bewertet KI und MCP, Art.-36-Aussage auf dem Ist-Stand; Betreiberdoku „Für Betriebe“ mit DSFA-/Betriebsrat-Hinweis und Mustertext (PRIV-406) | PRA-3.04 · LEG-12, LEG-48 |
| TA-913 | Doku | `06` §4.4 enthält die vierstufige LIA-4 (Zweck, Erforderlichkeit, Abwägung, Maßnahmen); Register nennt Anbieter, Region, Übermittlungsgrundlage des Fehlertrackers; bestehende Scrub-Tests (`errorTracking.test.ts`, Backend) bleiben grün | PRA-3.05 · LEG-16 |
| TA-914 | Doku + Betrieb | Jede Zeile der Speicher-Matrix (R-49 ff.: Logs, Valkey-AOF, `vectordb`, Snapshots, nicht-aktuelle S3-Versionen, Fehlertracker) hat ID, Frist, Durchsetzung; `06` und `data-retention.md` konsistent (Spec-Drift-Check); Betreiber bestätigt die Log-Frist | PRA-3.06 · LEG-44, LEG-60 |
| TA-915 | Betrieb | Betreiber bestätigt die verschlüsselte StorageClass; Backup-Drill mit rclone-`crypt`-Remote dokumentiert. **Präzisiert (Recovery-Nachtrag, PRIV-860):** Schlüssel je Backup-Generation, Vernichtung `L_eff + 7 d` nach dem letzten Dump der Generation nachgewiesen; Pflicht für BM-001 (Q-OP-16) | PRA-3.07 · LEG-42 |
| TA-916 | Betrieb | Erster Drill-Bericht mit den Szenarien S3, S5, S6, S7 grün (TA-710) — **präzisiert (Recovery-Nachtrag, PRIV-872):** Szenarien A–H aus `17` §9 (TA-744…TA-751), Evidence-Report nach `17` §11.5 (TA-760); Tabletop-Protokoll vorhanden; Nachweisvorlage in der Doku; Einträge zu TA-901…TA-904 abgelegt | PRA-3.09 · LEG-11, LEG-24, LEG-32 |
| TA-918 | Doku | Entscheidungsvorlage „Mandantenschlüssel für den Objektspeicher (BM-001)“ mit Variantenvergleich im decision-log §A eingetragen (neue DEC oder begründete Ablehnung, Q-PO-24); Betreiberdoku nennt die Grenzen des Crypto-Shredding nach `17` §8.3 (PRIV-861) | PRA-3.11 · LEG-11 |
| TA-917 | Doku | Grep `ConfirmCareTask.*null` in `spec/privacy` → 0; DEC-09/DEC-14 `accepted` mit Datum; einheitliche Paketversion in allen Köpfen; NFR-011 R-40 als umgesetzt geführt (#2138) und in der Task-Tabelle; TA-040 meldet nur Ausnahmen; TA-237 grün | PRA-3.10 · LEG-58, LEG-61 |

### 2.13 Zuordnung PRA → Abnahmefälle (neu v1.2)

Gegenrichtung zu `12` §6 („Abnahmefälle (`10`)“); jede PRA-Aufgabe hat mindestens einen Abnahmefall. Recovery-Nachtrag
2026-11-23: Ergänzungen mit „Rec:“ markiert; die sechs neuen Aufgaben stehen in den letzten Zeilen.

| PRA | TA | PRA | TA |
|---|---|---|---|
| 0.01 | 901 | 2.04 | 633, 634, 635, 636 |
| 0.02 | 902 | 2.05 | 300…309 (303 präz.), 310, 311, 425 |
| 0.03 | 903; Rec: 758 | 2.06 | 309 (präz.), 312, 313, 416 |
| 0.04 | 904 | 2.07 | 031, 314, 417 |
| 0.05 | 905 | 2.08 | 418, 801 (präz.) |
| 0.06 | 132, 011 (präz.) | 2.09 | 419; Rec: 745 |
| 0.07 | 533, 534 | 2.10 | 304, 315, 316 |
| 0.08 | 512, 514, 516 (präz.), 535 | 2.11 | 317, 908 |
| 0.09 | 414, 415 | 2.12 | 137, 138, 139 (209 präz.) |
| 0.10 | 711, 718 (präz.), 720; Rec: 740, 741, 758 | 2.13 | 140, 141 |
| 0.11 | 906 | 2.14 | 420 |
| 1.01 | 030 (präz.), 031, 032 | 2.15 | 500, 511, 519…521, 530…532 (präz.), 536; Rec: 759 |
| 1.02 | 409, 630 (präz.), 034 | 2.16 | 537, 538 |
| 1.03 | 033, 907 | 2.17 | 524, 539 |
| 1.04 | 709, 718 (angepasst), 721 (präz.), 722; Rec: 726…729, 731, 732, 734…736, 740 | 2.18 | 421 (präz.), 422, 423, 424, 637 |
| 1.05 | 710, 711, 804 (präz.), 723, 724, 811; Rec: 730, 733, 738, 741…755, 760 | 2.19 | 036, 318 |
| 1.06 | 133, 134, 135, 136; Rec: 747 | 2.20 | 142, 143, 144, 637 |
| 1.07 | 102/208 (präz.), 121 (präz.), 238, 240; Rec: 744, 756 | 3.01 | 909 |
| 2.01 | 204 (präz.), 205, 206, 239, 241, 242, 243 | 3.02 | 037, 038, 136, 910 (präz.); Rec: 722 (präz.) |
| 2.02 | 244 | 3.03 | 911 |
| 2.03 | 110…114 (111, 113 präz.) | 3.04 | 426, 912 |
| | | 3.05 | 913 |
| | | 3.06 | 135, 427, 914; Rec: 753 |
| | | 3.07 | 039, 725, 915 (präz.); Rec: 757 |
| | | 3.08 | 035 |
| | | 3.09 | 916 (präz.); Rec: 744…751, 760 |
| | | 3.10 | 040, 917 |
| **0.12** (Rec) | 711 (erw.), 743, 757 | **2.21** (Rec) | 737 |
| **1.08** (Rec) | 749, 753 | **2.22** (Rec) | 739, 730 |
| | | **2.23** (Rec) | 757 |
| | | **3.11** (Rec) | 918 |

### 2.14 Guards aus dem Audit (neu v1.2)

Das Audit 2026-11-22 benennt Invarianten (INV-P1…P10) und Guards, die das Paket noch nicht hatte; sie gehören in das
Pre-commit-Set bzw. die Lane `backend-guards` (PRIV-900). Jeder Guard hat einen Fehlfall-Test (Prinzip 3).

| Guard | TA | Invariante / Zweck | PRA |
|---|---|---|---|
| Feld-Register-Guard: jede Collection mit personenbezogenem Feld klassifiziert (`check_privacy_registry_doc.py`) | TA-030 | INV-P1 | PRA-1.01 |
| R6-Muster `_by_user`, `_user`, `operator_*`, `*_subject` | TA-031 | Messwerkzeug-Lücke, die LEG-29 verursachte | PRA-1.01 |
| `max_length` für jedes persistierte `str`-Feld | TA-032 | Freitext begrenzt (LEG-08) | PRA-1.01 |
| Empfängerregister ↔ externe Adapter | TA-033 | INV-P8 | PRA-1.03 |
| `organization_kind` nur im Resolver gelesen | TA-034 | INV-P3 | PRA-1.02 |
| Retention-Tasks rufen den Hold-Filter | TA-135 | INV-P2 | PRA-1.06, PRA-3.06 |
| Foto-Löschrouten teilen das Uploader-Prädikat | TA-137 | Drift zwischen Geschwistern (LEG-39) | PRA-2.12 |
| `review_fields` ⇒ Schwärzungspfad | TA-242 | jede geprüfte Zeile schwärzbar | PRA-2.01 |
| Leistungsfelder nicht ohne Rollenfilter | TA-309 | INV-P9 | PRA-2.06 |
| `CloudGate.require` vor `self._ks.ask` | TA-415 | INV-P4 | PRA-0.09 |
| Wetteraufrufe über `coarsen_coordinates` | TA-420 | DP-002 (LEG-49) | PRA-2.14 |
| Manifest-Collection ↔ Policy-Zeile | TA-423 | Art. 13/15 aus einer Quelle | PRA-2.18 |
| AttachmentCategory-Guard | TA-424 | Fotokategorie in Verzeichnis und Hinweis (LEG-22) | PRA-2.18 |
| SW-Allowlist ↔ Projektion | TA-534 | INV-P7 | PRA-0.07 |
| Speicherschlüssel mit Personenbezug gelistet | TA-535 | Logout-Wipe vollständig (LEG-10) | PRA-0.08 |
| Outbox je Ereignistyp | TA-721 | INV-P5 | PRA-1.04 |
| Emittenten-Vollständigkeit Journal (statisch, Recovery-Nachtrag) | TA-735 | INV-P5 (statisch, PRIV-801) | PRA-1.04 |
| Widerrufsmethoden verschlucken keine Exceptions (Recovery-Nachtrag) | TA-737 | fail-closed (LEG-66, PRIV-812) | PRA-2.21 |
| Chart-Vertrag: Journal-Frist und Restore-Modus (Recovery-Nachtrag) | TA-740, TA-741 | INV-P10, INV-P6 (LEG-62) | PRA-0.10, PRA-1.05 |
| Restore-Erkennung | TA-723 | INV-P6 | PRA-1.05 |
| Helm: Backup ohne Journal bzw. Frist ∉ [1, 35] (Chart-Vertrag `scripts/ci/assert_chart_contracts.sh`, Recovery-Nachtrag) | TA-718, TA-720 | INV-P10 | PRA-0.10 |
| PRIV ohne TA | TA-040 | Paketpflege (LEG-61) | PRA-3.10 |

Bereits vorhanden und durch das Audit bestätigt (VERIFIED_CODE): `test_privacy_marker_and_tombstone_have_one_definition.py`
(TA-200), `test_care_confirmation_names_its_performer.py` (TA-120), `test_keyed_service_writes_take_the_tenant.py`
(`_REMAINING = frozenset()`, Ownership-Prädikat vollständig), Log-Privacy-Guards (TA-808), `test_erasure_exif_strip_reach.py`
(Basis für TA-140).

---

### 2.15 Rückverfolgung der in v1.2 neu vergebenen PRIV-IDs (neu v1.2)

Die Fachdokumente haben bei der Integration des Audits 2026-11-22 neue Anforderungen vergeben. Jede ist über ihre PRA-Aufgabe ([`12`](12-implementation-roadmap.md) §6) an Abnahmefälle dieses Dokuments gebunden.

| PRIV | Dokument | Inhalt | PRA | TA |
|---|---|---|---|---|
| PRIV-135 | [`03`](03-account-and-membership-lifecycle.md) | Residue-Scan der Kontolöschung | PRA-1.07 | TA-102, TA-121 |
| PRIV-136 | [`03`](03-account-and-membership-lifecycle.md) | Art. 18/21 wirksam | PRA-0.06, PRA-1.06 | TA-011, TA-132, TA-133, TA-134 |
| PRIV-137 | [`03`](03-account-and-membership-lifecycle.md) | Legal Hold | PRA-1.06 | TA-135, TA-136 |
| PRIV-138 | [`03`](03-account-and-membership-lifecycle.md) | Mandantenmenge der Folgearbeiten einer Kontolöschung aus den Daten | PRA-2.13 | TA-140, TA-141 |
| PRIV-240 | [`04`](04-anonymization-and-redaction.md) | Plan-Snapshots in Schwärzung und Restore | PRA-2.02 | TA-244 |
| PRIV-241 | [`04`](04-anonymization-and-redaction.md) | Import-Regel für `anon_` | PRA-1.07 | TA-240 |
| PRIV-242 | [`04`](04-anonymization-and-redaction.md) | Art.-9/10-Hinweise ohne automatischen Scan | PRA-2.01 | TA-032, TA-243 |
| PRIV-317 | [`05`](05-access-and-visibility.md) | Betriebsmodus „Organisation mit Beschäftigten“ | PRA-1.02, PRA-2.06 | TA-034, TA-313, TA-409 |
| PRIV-318 | [`05`](05-access-and-visibility.md) | Aufgaben: `assigned_to` als `PersonRef`, Leistungsfelder begrenzt | PRA-2.06 | TA-312, TA-313 |
| PRIV-319 | [`05`](05-access-and-visibility.md) | Aktorbefehl-Auslöser als `PersonRef` | PRA-2.07 | TA-314 |
| PRIV-320 | [`05`](05-access-and-visibility.md) | Export per API-Key nur mit Step-up bzw. 403 | PRA-2.04 | TA-635 |
| PRIV-321 | [`05`](05-access-and-visibility.md) | Selbstlöschung eigener Uploads ab `grower` | PRA-2.12 | TA-137 |
| PRIV-322 | [`05`](05-access-and-visibility.md) | MCP-Freitextpolitik | PRA-2.10 | TA-315 |
| PRIV-323 | [`05`](05-access-and-visibility.md) | MCP gegen indirekte Prompt-Injection | PRA-2.10 | TA-316 |
| PRIV-324 | [`05`](05-access-and-visibility.md) | Plattform-Export nur mit Grund aus Ausnahmeliste | PRA-2.11 | TA-317 |
| PRIV-415 | [`06`](06-retention-and-legal-basis.md) | Pflichtexport im Löschdialog des Mandanten | PRA-2.09 | TA-419 |
| PRIV-416 | [`06`](06-retention-and-legal-basis.md) | Art.-13-Pflichtangaben in `PrivacyPolicyInfo` | PRA-2.18 | TA-421, TA-422, TA-423 |
| PRIV-534 | [`07`](07-offline-privacy.md) | SW-Cache speichert nur die Projektion | PRA-0.07 | TA-533, TA-534 |
| PRIV-535 | [`07`](07-offline-privacy.md) | Physische Frist für SW-Cache und `kp-sw-state` | PRA-2.16 | TA-537 |
| PRIV-536 | [`07`](07-offline-privacy.md) | `notices` mit `createdAt` und Frist | PRA-2.16 | TA-538 |
| PRIV-537 | [`07`](07-offline-privacy.md) | Shared-Device-Modus ohne „Angemeldet bleiben“ | PRA-2.17 | TA-539 |
| PRIV-538 | [`07`](07-offline-privacy.md) | Puffer nicht mehr wählbarer Mandanten löschen | PRA-2.15 | TA-536 |
| PRIV-539 | [`07`](07-offline-privacy.md) | Fern-Widerruf von Sitzungen dokumentiert | PRA-2.15 | TA-540 |

### 2.16 Rückverfolgung PRIV-800…PRIV-874 (17; Recovery-Nachtrag 2026-11-23)

Kette Finding (LEG) → Requirement (PRIV, [`17`](17-privacy-recovery.md) §12) → Komponente (RC, `17` §2.3) → Task (PRA,
[`12`](12-implementation-roadmap.md) §6) → Test (TA) → Evidence (Testlauf bzw. Nachweis nach PRIV-903). Status aller
Anforderungen: `spezifiziert`, außer PRIV-802, PRIV-824, PRIV-840, PRIV-842, PRIV-855 (`teilweise implementiert`, Bausteine
in `17` §12); keine ist `implementiert und getestet`.

| PRIV | Inhalt (kurz) | RC | LEG | PRA | TA |
|---|---|---|---|---|---|
| PRIV-800 | Zielinvariante: kein Restore macht eine Entscheidung (E/H/C/A/D) unbemerkt rückgängig | alle | LEG-11, LEG-24 | PRA-1.04, PRA-1.05 | TA-744…TA-752 |
| PRIV-801 | Taxonomie verbindlich, statischer Emittenten-Guard | RC-01 | LEG-24 | PRA-1.04 | TA-735 |
| PRIV-802 | Outbox im selben Commit (präz. PRIV-709) | RC-01, RC-02 | LEG-25 | PRA-1.04 | TA-721 |
| PRIV-803 | Schema `kp.privacy-journal/v1`, Reader fail-closed | RC-05 | LEG-24 | PRA-1.04 | TA-726 |
| PRIV-804 | Pseudonyme `jsub_`/`jten_`/`jrec_`, kein Rohschlüssel (präz. A-JRN-3) | RC-01 | LEG-11 | PRA-1.04 | TA-727, TA-728 |
| PRIV-805 | Relay Einzelschreiber, `jseq`, Kette, idempotent (präz. PRIV-710) | RC-03 | LEG-25 | PRA-1.04 | TA-729, TA-732 |
| PRIV-806 | Journal-Store außerhalb der DB, ohne Delete, nie im Backup; Replik | RC-04 | LEG-11 | PRA-1.04 | TA-729, TA-750 |
| PRIV-807 | Verschlüsselung und MAC mit `PRIVACY_JOURNAL_KEY` | RC-03, RC-05 | LEG-11 | PRA-1.04 | TA-728, TA-734 |
| PRIV-808 | Journal-Frist R-63 per Segmentablauf (ersetzt R-45) | RC-04 | LEG-11, LEG-44 | PRA-1.04, PRA-0.10 | TA-740 |
| PRIV-809 | Lücken-, Ketten-, DB↔Store-Prüfung inkl. Absturzfenster | RC-05, RC-06 | LEG-11 | PRA-1.05 | TA-733, TA-734, TA-738 |
| PRIV-810 | Zugriffsschutz, protokollierte Store-Zugriffe | RC-04 | LEG-11 | PRA-1.04 | TA-729 |
| PRIV-811 | Löschung erst nach Journal-Ack `completed` | RC-03 | LEG-11 | PRA-1.04 | TA-736 |
| PRIV-812 | Widerrufspfade fail-closed | RC-01 | LEG-66 | PRA-2.21 | TA-737 |
| PRIV-813 | Identität von Salt, Journal-Schlüssel, Fernet (ergänzt PRIV-714) | RC-06, RC-07 | LEG-67 | PRA-2.22 | TA-739 |
| PRIV-814 | Backup-Manifest mit `journal_seq_at_start` | RC-11 | LEG-11 | PRA-2.22 | TA-730 |
| PRIV-815 | `aggregate.version`, Konfliktregel | RC-01, RC-09 | LEG-24 | PRA-1.04 | TA-731 |
| PRIV-820 | Zustandsmodell, Checkpoints | RC-06, RC-08 | LEG-11 | PRA-1.05 | TA-751 |
| PRIV-821 | Restore-Gate, auch bei `DEBUG` (präz. PRIV-711, INV-P6) | RC-07 | LEG-24 | PRA-1.05 | TA-738, TA-748, TA-750 |
| PRIV-822 | Restore-Modus Helm/Compose | RC-13 | LEG-62 | PRA-1.05, PRA-0.12 (Interim) | TA-741 |
| PRIV-823 | Worker-/Beat-Gate mit Migrationskopf | RC-07 | LEG-70 | PRA-1.05 | TA-742 |
| PRIV-824 | Isolationsumfang (MCP, Registrierung, PWA, extern, ArgoCD) | RC-13 | LEG-62 | PRA-1.05 | TA-741 |
| PRIV-825 | Valkey leeren, Queues leer | RC-08 | LEG-69 | PRA-0.12, PRA-1.05 | TA-743 |
| PRIV-826 | Backup-Validierung vor dem Einspielen | RC-08 | LEG-11 | PRA-1.05 | TA-750 |
| PRIV-827 | Migrationen vor Replay und vor Workern | RC-08 | LEG-70 | PRA-1.05 | TA-742 |
| PRIV-828 | Replay-Startpunkt, Plan, fortsetzbar | RC-08 | LEG-11 | PRA-1.05 | TA-730, TA-751 |
| PRIV-829 | globale Token-Entwertung nach jedem Restore | RC-09 | LEG-24 | PRA-1.05 | TA-752 |
| PRIV-830 | Freigabe nur bei allen Kriterien `17` §5.6 | RC-07, RC-08 | LEG-11 | PRA-1.05 | TA-744…TA-755 |
| PRIV-831 | Freigabe nach Betriebsmodell und Reihenfolge | RC-08 | LEG-11 | PRA-1.05, PRA-3.09 | TA-760 |
| PRIV-832 | Rückfall nur über `FALLBACK_REVIEW` (präz. A-BAK-5) | RC-08, RC-12 | LEG-11 | PRA-1.05 | TA-748 |
| PRIV-833 | Docker-Restore gestoppt, Journal-/Anhänge-Volume | RC-13 | LEG-63, LEG-64, LEG-43 | PRA-0.12, PRA-2.23, PRA-3.07 | TA-757 |
| PRIV-840 | Reconciliation je Datenbereich (präz. A-BAK-4) | RC-09 | LEG-24 | PRA-1.05 | TA-744…TA-747, TA-754 |
| PRIV-841 | Idempotenzschlüssel `(restore_id, event_id, action)` | RC-08, RC-09 | LEG-11 | PRA-1.05 | TA-732, TA-751, TA-755 |
| PRIV-842 | Retention-Nachlauf mit Hold-Filter | RC-09 | LEG-23, LEG-35 | PRA-1.05, PRA-1.06 | TA-747 |
| PRIV-843 | Aufbewahrtes nicht in Produktfunktionen | RC-09 | LEG-47 | PRA-2.09 | TA-745 |
| PRIV-844 | Mandanten-Import gegen abgeschlossene Löschungen | RC-09 | LEG-65, LEG-54 | PRA-1.07 | TA-756 |
| PRIV-845 | Residue-Scan über alle Speicher | RC-08 | LEG-11 | PRA-1.05, PRA-1.07 | TA-744 |
| PRIV-846 | Restore-Epoche für Clients | RC-07 | LEG-24 | PRA-2.15 | TA-759 |
| PRIV-850 | versionsvollständige Objektlöschung | RC-10 | LEG-26 | PRA-1.08 | TA-749 |
| PRIV-851 | Lifecycle-Regeln (präz. PRIV-713) | — (Betrieb) | LEG-26 | PRA-0.10, PRA-0.03 | TA-758 |
| PRIV-852 | kein Object Lock auf dem Anhangs-Bucket | — (Betrieb) | LEG-26 | PRA-0.10 | TA-758 |
| PRIV-853 | Waisen-Quarantäne, Löschung nach R-65 | RC-10 | LEG-60 | PRA-1.08, PRA-3.06 | TA-753 |
| PRIV-854 | Dump-Ablauf unabhängig vom CronJob | RC-11 | LEG-68 | PRA-0.10 | TA-758 |
| PRIV-855 | Chart-Vertrag statt helm-unittest (präz. INV-P10) | RC-13 | LEG-11 | PRA-0.10 | TA-740, TA-741 |
| PRIV-860 | Backup-Verschlüsselung je Generation | RC-11 | LEG-42 | PRA-3.07 | TA-915 (präz.) |
| PRIV-861 | Grenzen von Crypto-Shredding dokumentiert | — | LEG-11 | PRA-3.11 | TA-918 |
| PRIV-870 | Evidence-Report je Restore (R-64) | RC-12 | LEG-11 | PRA-1.05, PRA-3.09 | TA-760 |
| PRIV-871 | Metriken und Alarme `17` §11.4 | RC-14 | LEG-25, LEG-68 | PRA-1.04, PRA-3.02 | TA-722 (präz.) |
| PRIV-872 | Quartals-Drill A–H (präz. PRIV-712) | — | LEG-11 | PRA-3.09 | TA-916 (präz.), TA-744…TA-751 |
| PRIV-873 | Runbooks in `docs/{de,en}/deployment/` | — | LEG-62, LEG-63 | PRA-0.12 | TA-711 (erw.) |
| PRIV-874 | Transparenz: Journal-Frist, Wiederanwendung (ergänzt PRIV-708) | — | LEG-11 | PRA-2.18 | TA-421 (präz.) |

Bestehende IDs, die `17` präzisiert oder ersetzt (`17` §0.4): PRIV-707…714 (`09`), PRIV-E14 (`12`), A-JRN-1…4,
A-BAK-1…5, A-AUD-3, A-HOLD-1…3, INV-P5, INV-P6, INV-P10 (`01`). Ihre bisherigen TA (TA-709…711, TA-718, TA-720…724)
bleiben gültig und sind in §2.11 präzisiert.

## 3. Negativtests — „gelöschte Identitäten können nicht wieder auftauchen"

Dies sind die Tests, die die zentrale Behauptung des Pakets beweisen. Jeder bringt ein gelöschtes Subjekt
ein (echter Schlüssel `K`, Tombstone `T`, Anzeigenamen-Tokens `N…`) und prüft die Abwesenheit.

| TA | Kanal | Assertion |
|----|-------|-----------|
| TA-800 | **Migrationen** | alle ausstehenden Migrationen nach einer Löschung auf einer Fixture-DB ausführen; alle Collections scannen: `K` abwesend; `T` nur in `tombstone_allowed_fields()`; `N…` abwesend in jedem Feld, das die Prüfwarteschlange als entschieden `redact` aufgeführt hat |
| TA-801 | **Backfill / Consistency-Job** | gesetzliche Zeile mit `T` einbringen; v0104-äquivalenten Mapper und `care_events.consistency` ausführen; `care_events` hält `_anonymized`, nie `T`. **Präzisiert v1.2 (PRA-2.08, LEG-07):** der tägliche Konsistenzjob nutzt denselben Mapper (`care_event_consistency_service.py:129`, Fenster 7 d) — der Test deckt beide Aufrufer und den Schalter `PRIVACY_BACKFILL_COPIES_PERFORMER` (TA-418) |
| TA-802 | **Exporte** | Art.-15-Bündel eines anderen Mitglieds, Pflegeereignis-CSV (lead), Plan-JSON/SVG/PDF, Mandantenarchiv, MCP-Lese-Tools: keines enthält `K`, `T` oder (für CSV/Archiv nach Schwärzung) `N…` |
| TA-803 | **Offline-Synchronisation** | Gerät A puffert eine Notiz mit `K` → `K` anderswo gelöscht → Gerät A spielt erneut ab: 401 `account.closed` (Phase geschlossen) oder generisches 401 (gelöscht) → Quarantäne → Löschung; der Server speichert die Notiz nie; Gerät B (anderer Nutzer), das den Mandanten öffnet, erhält keine Cache-Zeile von `K` (v1.2: auch nicht aus dem SW-Cache, TA-533) |
| TA-804 | **Backup-Wiederherstellung** | TA-710. **Präzisiert v1.2 (PRA-1.05):** zusätzlich Plan-Snapshots (TA-244) und Objektspeicher-Versionen (TA-903) — nach Restore + Replay keine wiederhergestellte Kopie von `K` oder geschwärztem `N…`. **Präzisiert (Recovery-Nachtrag):** Szenarien A–H aus `17` §9 (TA-744…TA-751); ein Restore gilt nur als bestanden, wenn INTEGRITY_VALIDATED erreicht ist |
| TA-810 | **Prüfwarteschlange** | nach `ERASURE_COMPLETED` existiert keine Zeile im Mandanten, deren Prüffeld einen Namens-Token von `N…` enthält und deren Eintrag nicht `RETAINED_WITH_LEGAL_BASIS` mit `legal_basis_ref` ist; kein Eintrag wurde durch die Eskalationsschwelle ausgelassen (Vergleich mit einer unabhängigen Vollzählung) |
| TA-805 | **Wiedereintritt** | nach PRIV-116 und einem Wiedereintritt behalten die alten Zeilen den Marker (keine Rück-Anonymisierung durch erneutes Auftauchen des Schlüssels) |
| TA-806 | **Mandantenimport** | Import eines Archivs, das `K` enthält (vor der Löschung exportiert), bildet `K` auf `_anonymized` ab (Regel für nicht zugeordnete Konten existiert [v]; pinnen, dass ein gelöschter Schlüssel als nicht zugeordnet behandelt wird, auch wenn `members.jsonl` des Archivs ihn aufführt); für `T` im Archiv gilt TA-240 |
| TA-807 | **Benachrichtigungen** | keine nach der Schließung erzeugte Benachrichtigung nennt oder adressiert `K`; bestehende werden bei der Löschung gelöscht (existiert) |
| TA-808 | **Logs** | structlog-Capture während des gesamten Ablaufs enthält weder `K` noch `N…` (Guards `test_privacy_logs_carry_no_plaintext_subject` existieren — Szenario erweitern) |
| TA-809 | **Suche** | `GET /diary?q=<name token>` nach der Schwärzung liefert keine der geschwärzten Zeilen |
| TA-811 | **Widerrufe nach Restore** (neu v1.2, PRA-1.05, LEG-24) | vor dem Dump aktive Einwilligung, API-Key, Sitzung und Passwort von `K`; danach Widerruf, Key-Widerruf, `logout-all`, Passwortwechsel; Restore + Replay: Consent-Guard 403, API-Key 401, alte Refresh-Tokens 401, altes Passwort abgelehnt, Art.-18-Einschränkung wieder aktiv (TA-133) — kein Widerruf kehrt durch den Restore zurück |

---

## 4. Abdeckung und Gates

**PRIV-900** Die neuen Guards kommen in das Pre-commit-Set (`scripts/check_privacy_inventory.py`
ist bereits dort) und in die erforderliche Lane `backend-guards`. Integrationstests laufen in der
bestehenden ArangoDB-gestützten Lane; der Restore-Drill (TA-710) läuft nightly. Ergänzt v1.2: die Guards aus §2.14;
Helm-Prüfungen (TA-035, TA-038, TA-039, TA-718, TA-720) im Chart-Vertrag `scripts/ci/assert_chart_contracts.sh` (Lane `skaffold-verify`); das Journal (TA-709, TA-721) läuft
gegen MinIO mit Object Lock in der Integrations-Lane. **Recovery-Nachtrag:** Das Repo hat keine helm-unittest-Lane;
TA-718, TA-720, TA-740, TA-741 laufen im Chart-Vertrag `scripts/ci/assert_chart_contracts.sh` (ebenso TA-035, TA-038,
TA-039; W-56 in `14` aufgelöst); Restore-Szenarien TA-744…TA-755 in der Nightly-Lane neben TA-710; TA-758, TA-760 per
Nachweis (PRIV-903).

**PRIV-901** Frontend-Tests folgen `FRONTEND.md` (`cleanup()` zuerst in `afterEach`; jsdom-
IndexedDB über `fake-indexeddb`, wie Welle 9 es tut).

**PRIV-902** E2E-Ergänzungen tragen den Marker `req053` (und einen neuen Marker `req025` für
reine Privacy-Abläufe), damit die conftest-Auswahl nach Anforderung funktioniert
(`spec/e2e-testcases/`-Matrixzeilen GP-REQ/PRIV).

**PRIV-903** (neu v1.2) TA-9xx sind keine CI-Tests. Sie werden in der Evidenzablage (PRA-3.09) bzw. per Review
nachgewiesen; ein TA-9xx-Nachweis ist datiert und verweist auf die Installation oder das Dokument. Ein Gate
(`deployment_allowed`, `processing_allowed`), das an eine PRA-Aufgabe mit TA-9xx gebunden ist, gilt erst mit dem Nachweis
als erfüllt (z. B. BM-001: TA-902, TA-906, TA-910, TA-911).

---

## 5. Abnahme des Pakets als Ganzes

Das Paket ist **fertig**, wenn: jede PRIV-Anforderung in `01`–`09` mit Status P0/P1 in `12`
eine bestandene TA hat; jede PRA-Aufgabe mit Priorität P0/P1 in `12` §6 ihre Abnahmefälle aus §2.13 bestanden hat
(TA-9xx per Nachweis); die drei Guards (R7, R8, Konstanten) und die Guards aus §2.14 im Pre-commit bzw. in
`backend-guards` sind; die Registry-Dokumentprüfung (TA-030) besteht; TA-800…TA-811 bestehen; die DSFA-Vorprüfung
(`11`) mit der LEG-Liste an den Datenschutzbeauftragten übergeben wurde; und die Spec-Änderungsvorschläge aus `06` §9
in versionierte Änderungen von REQ-025 / NFR-011 / REQ-053 / REQ-024 / REQ-049 überführt wurden (nicht stillschweigend
— jeweils mit einer Changelog-Zeile, die dieses Paket referenziert).
