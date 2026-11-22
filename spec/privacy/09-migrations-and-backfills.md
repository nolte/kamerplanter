# SPEC-09 — Migrations- und Backfill-Strategie

```
Paket: spec/privacy · Version 1.1 · 2026-11-09 · gemessen gegen develop 24d1c2988; Nachtrag #2839 (develop 343afbb97);
Nachtrag #2976 (2026-11-16, develop 9809d3952): §5a Migration v0114 `rooting_protocols.author` → `author_user_key`
Anforderungs-IDs: PRIV-700 … PRIV-739
Hängt ab von: NFR-016 / ADR-009 (Migrationsframework), 04 §7 (Altbefunde), 08 (Modell), 06 §3 (Pflichtfelder)
Änderung v1.1: E04/E15-Konflikt aufgelöst (§3), Vor-/Nachprüfungen je Migration (§2a), Backup-Konzept auf
Tombstone-Spiegel umgestellt (§6, DEC-26), Flags für datenvernichtende Schritte, Behandlung inaktiver Mandanten.
```

---

## 1. Framework-Fakten [VERIFIED_CODE]

- Versionen `app/migrations/versions/vNNNN_<slug>.py`, lückenlos, ein `migration`-Objekt; `up(db, *, dry_run=False)
  -> MigrationReport` idempotent (M-3), `dry_run` wird beachtet (M-5); Standard-`down` wirft
  `IrreversibleMigrationError` (M-6); angewendete Quellen sind durch `test_applied_migration_sources_are_frozen`
  eingefroren.
- `MigrationReport {version, name, scanned, changed, dry_run, duration_ms, precondition_unmet, incomplete, details}`;
  CLI gibt Zähler aus und markiert eine ausstehend gelassene Migration; `details` über die structlog-Zeile der
  Migration. **Seit v0109 (2026-11-15, VERIFIED_CODE):** eine Migration mit `kind` (`privacy_correction` |
  `data_backfill`, `framework/base.py`) wird nach dem Redaktionsfilter in `migration_reports` persistiert (Dry-Run und
  echter Lauf, `framework/report_store.py`, §2); `incomplete = true` (Status `partial`/`verify_failed`) behandelt der
  Runner wie `precondition_unmet` (nicht aufgezeichnet, Schleife stoppt, nächster Start wiederholt).
- Kein Mandanten-Scoping auf Framework-Ebene; Unique-Indizes beginnen mit `tenant_key`. Start-Migration mit Sperre
  `schema_migrations/__lock__` (TTL 300 s); Fehler ist startfatal (M-4). `precondition_unmet` hält die Migration
  ausstehend und stoppt die Schleife.
- Konsistenz-Job `care_events.consistency` existiert (05:10 UTC, `ActiveTenants`-Gate, Fenster 7 d). Seit v0109
  existiert der Datenschutz-Konsistenz-Beat `privacy.consistency` in **Minimalform** (05:20 UTC, nur lesend, zählt
  Tombstones außerhalb der Allowlist je Zelle, Gauge `privacy_undeclared_tombstones{cell}`, kein Endpunkt; DEC-28).
- Neueste Datenschutz-Version: `v0111_keyed_performers` (2026-11-15, VERIFIED_CODE; §5, erster
  `data_backfill`), davor `v0110_tenant_record_keeping_default` (§4) und `v0109_privacy_tombstone_copies`
  (2026-11-15, VERIFIED_CODE; §3). Davor
  `v0108_location_tent_fields` (REQ-053, keine Datenschutzmigration) und
  `v0107_care_event_tombstone_performer` (#2839, gemergt 2026-11-09, VERIFIED_CODE): ersetzt
  Tombstones in `care_events.performed_by_user_key` durch `_anonymized` (eingefrorene Regex `^anon_[0-9a-f]{16}$`,
  nur dieses Feld, nur diese Generation), Dry-Run zählt, irreversibel, kein persistierter Bericht. Seit #2839 bildet
  `care_event_backfill_mapper.account_of` einen Tombstone auf den Marker ab, und der Mapper überspringt Beete
  inaktiver Mandanten (`SkipReason.INACTIVE_TENANT`); v0104 selbst ist unverändert (NFR-016 M-7).

**PRIV-700** Jede Migration dieses Pakets MUSS idempotent sein (zweiter Lauf `changed == 0`), im AQL
mandantengebunden (`FILTER doc.tenant_key == @tenant_key` je Mandant, Mandantenliste einmal gelesen), beobachtbar
(structlog-Zeile mit `details` **und** persistierter Bericht, §2), explizit zu Teilausfällen (§2a) und sicher für
inaktive Mandanten (§9).

---

## 2. Persistierte Dry-Run-Berichte

**PRIV-701** Collection `migration_reports` (Plattform, `NOT_TENANT_SCOPED`, Begründung „operator proof of a
migration run; no personal data“) speichert jeden `MigrationReport` einer Datenschutz-Migration (`dry_run` und
echt) nach einem **Redaktionsfilter**: nur Zähler, Collection-/Feldnamen, Mandanten-**Schlüssel**, Stichproben-
**Zeilenschlüssel** (≤ 25 je Bucket) — nie Nutzerschlüssel, Namen, Text, Tombstones. Unit-Test prüft den
erlaubten Schlüsselsatz (TA-701a).

**PRIV-702** CLI `upgrade --dry-run --report-out <path>` schreibt die Berichte als JSON für `.audits/prod-release`.

### 2a. Pflichtphasen jeder Datenschutz-Migration

**PRIV-718** Jede Migration MUSS die folgenden Phasen im Bericht ausweisen (`details.phases`):

| Phase | Inhalt | Abbruchregel |
|-------|--------|--------------|
| `precheck` | Vorbedingungen: Inventaränderung im selben Build vorhanden (Import-Check der Regel), Indizes vorhanden, Salt gesetzt, betroffene Collections existieren, Anzahl Kandidaten je Mandant gezählt | fehlt eine Vorbedingung → `precondition_unmet` (Migration bleibt ausstehend, kein Teilschreiben) |
| `dry_run` | identische Logik ohne Schreiben; Bericht persistiert | — |
| `apply` | je Mandant eine Transaktion; Fortschritt je Mandant im Bericht (`tenants_done`, `tenants_failed`) | Fehler in Mandant X: Transaktion X zurück, Mandant in `tenants_failed`, **Weiterlauf** mit den übrigen; am Ende `changed` = Summe, `status = partial`, Migration gilt als **nicht angewendet** (kein Tracking-Dokument), damit der nächste Start sie erneut versucht — idempotent |
| `verify` | Nachprüfung durch Zählabfragen (z. B. Rest-Tombstones in korrigierten Feldern = 0 je Mandant) | Rest > 0 → `status = verify_failed`, Migration nicht als angewendet markiert; Betreiberhinweis |
| `monitor` | Übergabe der Zählabfrage an den Datenschutz-Konsistenz-Beat (§3, `privacy.consistency`), sobald er registriert ist; bis dahin die Nachprüfung durch einen Unit-Test + den Betreiberbericht | — |

Rollback-Grenzen stehen je Migration in §11.

---

## 3. M-P1 — Kopierte Tombstones korrigieren; Plan-Audit-Akteur auf Marker (E04)

**Stand (2026-11-15, VERIFIED_CODE): umgesetzt.** `v0107_care_event_tombstone_performer` (#2839) hatte Schritt 1
für `performed_by_user_key` (Generation `anon_`) ausgeführt; `v0109_privacy_tombstone_copies` erledigt den Rest:
`created_by`, beide Generationen, Schritte 2–4, alle Phasen und den persistierten Bericht. Die Nummer war von v0107
auf v0108 (W-26) und danach auf v0109 verschoben worden (W-27). Umsetzungsdetails:

- Marker und Tombstone-Regex beider Generationen haben genau eine Definition (`domain/models/privacy.py`:
  `ANONYMIZED_MARKER`, `TOMBSTONE_REGEX`, `is_tombstone`; PRIV-201, Guard
  `test_privacy_marker_and_tombstone_have_one_definition`). Die `anon2_`-Ableitung (PRIV-238) ist nicht Teil davon.
- Inventar: `garden_plan_audit.user_key` ist eine Marker-Regel in `ANONYMIZE_COLLECTIONS` (DEC-16);
  `attachments` leert `original_filename` sowohl in der Regel als auch in der Speicherphase
  (`anonymize_user_metadata`), weil die Speicherphase die Zeile vorher markiert und die Regel sie sonst nie erreicht.
- Die Allowlist wird aus dem Inventar abgeleitet (`ErasureEngine.tombstone_allowlist()`), die beobachteten Zellen
  ebenso (`tombstone_watch_fields()` = kontoförmige Inventarfelder ohne Allowlist). Die Migration friert die Zellen
  von Schritt 3 als Literal ein (NFR-016 M-7); Migration und Beat teilen nur die Zählabfrage
  (`data_access/arango/tombstone_census.py`), nicht die Politik.
- Schritt 3 zählt je Zelle für die gesamte Installation, nicht je Mandant: mehrere beobachtete Collections sind
  konto- oder plattformbezogen und tragen kein `tenant_key`; der Schritt schreibt nichts. Schritte 1, 2 und 4 filtern
  `doc.tenant_key == @tenant_key` in der Transaktion des Mandanten.

**Migration `v0109_privacy_tombstone_copies`** (`kind = privacy_correction`; umkehrbar: nein).

| Schritt | AQL (je Mandant, alle Status außer `deleted`) | Berichts-Bucket |
|---------|-----------------------------------------------|-----------------|
| 1 | `care_events`: `performed_by_user_key` **und** `created_by` mit `=~ TOMBSTONE_REGEX` (beide Generationen) → `_anonymized` — Rest nach v0107 (#2839), das nur `performed_by_user_key` der Generation `anon_` erfasst | `care_events.tombstone_to_marker{tenant_key: count}` |
| 2 | `garden_plan_audit.user_key =~ TOMBSTONE_REGEX` → `_anonymized` (DEC-16) | `garden_plan_audit.tombstone_to_marker` |
| 3 | jede andere **nicht** auf der Allowlist stehende Collection/Feld-Kombination mit kontoförmigem Feld: **nur zählen** | `undeclared_tombstones{collection.field: count}` |
| 4 | `attachments.created_by == _anonymized AND original_filename != ""` → `""` | `attachments.filename_cleared` |
| verify | Schritte 1, 2, 4 erneut zählen → muss 0 sein; Schritt 3 wird als Befund gemeldet, nicht korrigiert | `verify.residual` |

**PRIV-703 (neu gefasst, löst W-02)** Vorbedingungen von v0109 sind **ausschließlich**: (a) die Inventaränderung
`garden_plan_audit` Tombstone → Marker und `attachments.clear_fields += original_filename` im selben Build (Precheck
importiert die Regel und prüft `replacement_strategy`/`clear_fields`); (b) `TOMBSTONE_REGEX`/Allowlist aus
`domain/models/privacy.py` (E03). Die **Nachprüfung** erfolgt innerhalb der Migration (`verify`) und durch
`tests/unit/migrations/versions/test_v0109_*.py`; der Beat `privacy.consistency` ist **keine** Vorbedingung. Der
Beat wird in **E04 in seiner Minimalform** (nur lesende Zählabfragen des Bucket 3 + Metrik, kein Endpunkt) eingeführt,
damit Bucket 3 ab dem Folgetag überwacht ist; Metriken-Endpunkt und Operations-Listing bleiben E15. (DEC-28)

**PRIV-704** Trockenlauf gegen einen Produktions-Snapshot vor P-8; Bericht im Release-Dokument.

**Erwartung Produktion:** klein (Backfill lief 2026-11-07, P-6-Bericht).

---

## 4. M-P2 — Aufzeichnungsprofil und Klassifizierung (E09)

**Stand (2026-11-15, VERIFIED_CODE): Migration und Modellfelder umgesetzt** (Betreiberfreigabe 2026-11-15, DEC-30
`accepted`); der Anlagepfad (PRIV-409, 422 `tenant.classification_required`), das `undeclared`-Verhalten und der
Reklassifizierungs-Job sind offen (E09). Umsetzungsdetails:

- `TenantSettings.record_keeping: RecordKeeping | None` und `organization_kind: OrganizationKind | None`
  (`domain/models/tenant.py`, Enums in `common/enums.py`, Werte wie `08` §3.2), **ohne** Default. Kein Request-
  oder Response-Schema trägt die Felder bisher (Lesen in `GET /tenants/{slug}` ist Teil von E09, `08` §5).
- **Persönliche Mandanten erhalten kein `organization_kind`.** PRIV-409 klassifiziert nur Organisationsmandanten
  (`organization_kind ∈ {association, commercial, community, other}`); `unknown_legacy` würde eine Organisation
  behaupten, die es nicht gibt. Ein Mandant ohne `tenant_type` gilt wie im Modell als persönlich.
- Jedes Feld wird für sich geprüft: Ein Organisationsmandant mit erklärtem `record_keeping`, aber ohne Art erhält
  nur `organization_kind = unknown_legacy`; ein vorhandener Wert wird nie überschrieben. Ein `settings`, das weder
  fehlt noch ein Objekt ist, bleibt unberührt (das Modell kann einen solchen Mandanten ohnehin nicht lesen).
- Phasen wie v0109 (§2a); `precheck` prüft zusätzlich, dass das Modell dieses Builds die geschriebenen Werte liest
  und für beide Felder keinen Default hat. `apply` ist je Mandant ein einzelnes Dokument-`UPDATE` (in ArangoDB
  atomar). Buckets `tenants.record_keeping_legacy`, `tenants.record_keeping_none`,
  `tenants.organization_kind_unknown_legacy`.
- `down` entfernt `record_keeping = legacy` und `organization_kind = unknown_legacy` (Werte, die nur v0110 setzt)
  und lässt `record_keeping = none` stehen: Der Wert stammt nicht eindeutig von v0110 (der Anlagepfad setzt ihn
  für neue persönliche Mandanten ebenso, die Herkunft ist nicht gespeichert) und ist für jeden persönlichen
  Mandanten richtig (L-07); ihn zu entfernen machte einen korrekt klassifizierten Mandanten `undeclared`.

**Migration `v0110_tenant_record_keeping_default`** (`kind = privacy_correction`; umkehrbar: entfernt `legacy`):
setzt bei jedem bestehenden Mandanten ohne Wert `settings.record_keeping = "legacy"` und `settings.organization_kind =
"unknown_legacy"`; persönliche Mandanten erhalten `record_keeping = "none"` (L-07) und kein `organization_kind`. Neue Mandanten erhalten
**keinen** Default (`undeclared`, PRIV-409) — der Anlagepfad verlangt die Angabe.

**Job `privacy.reclassify_statutory_rows`** (läuft bei Wechsel auf `none` oder bei PRIV-411-Anwendung; mandanten-
gebunden; idempotent; **nur wenn `PRIVACY_RECORD_KEEPING_RECLASSIFY = true`**, sonst `reclassification_pending`):

| Zeilen | Aktion |
|--------|--------|
| `harvest_batches`, `quality_assessments`, `treatment_applications`, `inspections` mit Tombstone in `*_by_key` | → `_anonymized`; Prüfeintrag `notes` (`source_kind = record_keeping_change`) |
| dieselben mit lebendem Schlüssel | nichts (Konto existiert); künftige Löschregeln behandeln sie nach Klasse |

Bericht: Zähler je Collection; Audit `TENANT_RECORD_KEEPING_CHANGED`. Rollback: keiner.

---

## 5. M-P3 — Freitext-Ausführendenfelder → Schlüsselfelder (E13)

**Stand (2026-11-15, VERIFIED_CODE): Migration und Modellfelder umgesetzt**; Request-Schemas („Ich war es /
jemand anderes“), serverseitiges Stempeln, Marker-Regeln der Löschung, Beats und `data_controller` sind offen
(Rest von E13). Discovery-Ergebnis gegen den Code (Abweichungen von der Tabelle v1.1, Code maßgeblich):

- **`propagation`-Chargen haben kein `author`.** Das einzige `author` der Vermehrung trägt
  `rooting_protocols` (Bewurzelungsprotokolle), und es ist **kein Freitext**: beide Schreibwege
  (`propagation/tenant_router.py`, Anlegen und Ändern) setzen `author = ctx.user_key`, also den rohen
  Kontoschlüssel der zuletzt ändernden Person; `RootingProtocolResponse.author` gibt ihn aus, und das
  Löschinventar erreicht ihn nicht (R6 sieht den Feldnamen `author` nicht). Eine Label-Kopie würde einen
  Kontoschlüssel in ein Feld für Dritte schreiben; `rooting_protocols` ist deshalb **nicht** Teil von v0111.
  Der Befund ist eine eigene Datenschutzkorrektur: #2976, §5a (v0114).
- **`maintenance_logs` und `tank_fill_events` tragen kein `tenant_key`** (Modell ohne Feld; nur Altbestand aus
  v0004 hat eines). Das Mandantenprädikat sitzt am Anker, dem Tank (`tank.tenant_key == @tenant_key`, dann
  `doc.tank_key == tank._key`; #706).
- **`inspections.inspected_by_key` existiert seit #1669** (serverseitig gestempelt; v0056 schrieb `null` auf
  ältere Zeilen) und ist bereits im Löschinventar (`tombstone_hash`, `clear_fields = [inspector]`). Der MCP-Weg
  schreibt heute beides: `inspector = "mcp:<key>"` **und** `inspected_by_key = <key>`. Schritt 4 füllt daher nur
  Zeilen mit `inspected_by_key = null`; die Prüfung „aktuelles Service-Konto“ verlangt zusätzlich eine
  Mitgliedschaft (`is_active != false`) im Mandanten der Inspektion — ein Service-Konto eines fremden Mandanten
  wird nie zugeordnet.
- **Längen:** `nutrient_plans.author` unbegrenzt, `workflow_templates.created_by` ≤ 200, `performed_by`
  unbegrenzt; Labels werden auf 80 Zeichen gekürzt (`PERSON_LABEL_MAX_LENGTH`, `domain/models/privacy.py`),
  das alte Feld bleibt vollständig.
- **Globale Katalogzeilen** (`tenant_key = ""`: System-Nährstoffpläne, System-Workflowvorlagen) gehören keinem
  Mandanten und bleiben unberührt.

**Migration `v0111_keyed_performers`** (`kind = data_backfill`; nur aktive Mandanten, §9; additiv; umkehrbar §11):

| Collection | Schritt | Berichts-Bucket |
|------------|---------|-----------------|
| `watering_events`, `watering_logs` (Prädikat am Dokument), `maintenance_logs`, `tank_fill_events` (Prädikat am Tank) | `performed_by_user_key = null`, falls das Attribut fehlt; `performed_by_label = performed_by[:80]`, falls das Label `null` und `performed_by` ein nicht-leerer Text ist; `performed_by` ein Release deprecated | `<collection>.performer_keyed` |
| `nutrient_plans` | `author_user_key = null`, `author_label = author[:80]` (dieselbe Regel) | `nutrient_plans.author_keyed` |
| `inspections` mit `inspector` beginnend mit `mcp:` | `inspected_by_key = <key>` **nur wenn** das Feld `null` ist und `<key>` ein bestehendes Konto mit `account_type = service` und Mitgliedschaft im Mandanten ist; sonst bleibt es `null`; danach `inspector = ""` | `inspections.mcp_inspector_cleared`, Teilmenge `inspections.service_account_keyed` |
| `workflow_templates` | `created_by_user_key = null`; `created_by` bleibt das Label (kein eigenes Label-Feld) | `workflow_templates.creator_keyed` |

Phasen wie §2a: `precheck` prüft zusätzlich, dass die Modelle dieses Builds die neuen Felder mit Default `None`
(Label: Grenze 80) tragen und dass jedes neue Schlüsselfeld im Löschinventar
(`ErasureEngine.EXCLUDED_USER_REFERENCES` — die Felder sind bis E13 immer `null`; E13 ersetzt die Ausnahme durch
eine Marker-Regel, sobald es stempelt) und im Mandantenexport (`TenantExportEngine.COLLECTION_REFERENCES`, Art
`account`) deklariert ist. `apply` ist je Mandant eine Stream-Transaktion über alle Schritte; `verify` zählt alle
Schritte erneut. Kein Request-Schema trägt ein `*_user_key` (PRIV-705, Unit-Test), die Response-Schemas sind
unverändert.

**PRIV-705** Kein Konto aus einem getippten Namen ableiten (REQ-025 Regel 4; #1662/#1663); Ausnahme nur das
deterministische Präfix `mcp:` [VERIFIED_CODE]. **PRIV-706** Labels, die einem aktuellen Mitgliedsnamen entsprechen,
KÖNNEN als Prüfeinträge `legacy_unkeyed_name` gelistet werden; die Migration ändert sie nie.

### 5a. `rooting_protocols.author` → `author_user_key` (#2976)

**Stand (2026-11-16, VERIFIED_CODE): umgesetzt** (Betreiberentscheidung D3 vom 2026-11-16 in #2976).

- **Befund [VERIFIED_CODE, develop 9809d3952].** Beide Schreibwege (`propagation/tenant_router.py`, Anlegen und
  Ändern) stempelten `author = ctx.user_key`; `RootingProtocolResponse.author` gab den rohen Kontoschlüssel an jedes
  Mitglied aus; das Löschinventar erreichte ihn nicht, weil R6 (`scripts/check_privacy_inventory.py`) einen
  Kontoverweis an der Form seines Namens erkennt und `author` keine dieser Formen hat.
- **Modell.** `RootingProtocol.author_user_key: str | None = None` ersetzt `author` (R6-Form `*_user_key`, wie
  `performed_by_user_key`); nur der Server stempelt es (PRIV-705: `RootingProtocolCreate` trägt das Feld nicht).
- **Antwort.** `RootingProtocolResponse.author` bleibt als Feldname, trägt aber den Anzeigenamen des Kontos oder
  `anonymisiert` (Konto gelöscht oder Marker) — nie den Schlüssel; dieselbe Regel wie `performed_by` der
  Pflegeeinträge (GP-API-034, `display_performer`). Globale Vorlagen haben keinen Autor (`null`).
- **Löschung.** `AnonymizationRule(rooting_protocols, author_user_key, Marker)`; das Protokoll bleibt als
  Arbeitsvorlage des Mandanten erhalten. Der Mandantenexport leitet den Kontoverweis aus der Regel ab
  (`TenantExportEngine.account_fields`); Art. 15 legt die Protokolle als Quelle „Rooting protocols you saved“ offen
  (R2), ohne den Schlüssel selbst.
- **Klassen-Guard.** `tests/unit/guards/test_caller_account_stamps_use_a_reference_shaped_name.py`: jedes
  Domänenmodell, dem der Kontoschlüssel des Aufrufers (`*.user_key`) übergeben wird, speichert ihn unter einem
  Namen in R6-Form; abweichende, entschiedene Fälle stehen mit Begründung in der Liste des Guards.

**Migration `v0114_rooting_protocol_author_key`** (`kind = privacy_correction`; jeder Mandantenstatus außer
`deleted`, §9; umkehrbar: nein, §11):

| Fall (Zeile des Mandanten mit Attribut `author`) | `author_user_key` | Berichts-Bucket |
|-----------------------------------------------|-------------------|-----------------|
| `author_user_key` schon gesetzt | bleibt | `rooting_protocols.author_dropped` |
| `author` nennt ein bestehendes Konto (`users/<author>` existiert) | `author` | `rooting_protocols.author_keyed` |
| `author` nicht-leerer Text, Konto gelöscht/fehlt (oder schon der Marker) | `_anonymized` | `rooting_protocols.author_to_marker` |
| sonst (`null`, leer, kein Text) | `null` | `rooting_protocols.author_dropped` |

In jedem Fall wird `author` entfernt (`UNSET`). Globale Vorlagen (`tenant_key = ""`) gehören keinem Mandanten;
kein Pfad schreibt dort einen Autor, sie bleiben unberührt. Phasen wie §2a: `precheck` prüft zusätzlich, dass das
Modell dieses Builds `author_user_key` (Default `None`) und kein `author` mehr trägt, die Löschregel den Marker
schreibt und der Mandantenexport das Feld als Kontoverweis kennt; `apply` je Mandant eine Stream-Transaktion;
`verify` zählt Zeilen mit `author` erneut (muss 0 sein); `monitor` entfällt (das Feld existiert nicht mehr, R6 und
der Klassen-Guard verhindern seine Rückkehr). Der Schlüssel stammt nie aus einem getippten Namen (`author` trug
keinen, PRIV-705 berührt das nicht). Tests: `tests/unit/migrations/versions/test_v0114_*.py`,
`tests/integration/test_v0114_*.py`.

**Erwartung Produktion:** klein (Bewurzelungsprotokolle werden selten angelegt); der Dry-Run-Bericht beziffert es.

---

## 6. Backups und Wiederherstellung (DEC-26 ersetzt das Raw-Key-Ledger aus v1.0)

### 6.1 Fakten [VERIFIED_CODE / VERIFIED_SPEC]

- Helm-CronJob `arangodb-backup` (`arangodump` → rclone → S3), standardmäßig **aus**, `retentionDays: 30`;
  TimescaleDB und Anhänge nicht durch das Chart abgedeckt; kein Backup als laufend dokumentiert (Audit DR-01…04).
- Doku verlangt beim Restore denselben `FERNET_KEY` und `ERASURE_TOMBSTONE_SALT`; NFR-011 §4 verlangt den Salt im DR-Backup.
- `erasure_requests` behält nach Abschluss den **Tombstone** der Person (`user_key` pseudonymisiert) für R-06 (3 J.);
  `tenant_erasure_records` behält den Mandantenschlüssel (`ter_<tenant_key>`) [VERIFIED_CODE].
- EDSA 01/2022 Rn. 110 (L-19): Löschungen schlagen in Backups erst beim nächsten Zyklus durch; keine deutsche
  Aufsichtsaussage zu Backups gefunden (L-21) → LEG-11 ohne Primärbeleg.

### 6.2 Kernidee: Erkennung wiederhergestellter gelöschter Konten **ohne** Rohschlüssel-Speicher

Nach einem Restore existiert die `users`-Zeile einer bereits gelöschten Person wieder — **mit ihrem rohen Schlüssel**.
Weil `compute_tombstone_hash(user_key, salt)` deterministisch ist (VERIFIED_CODE), lässt sich für **jede
wiederhergestellte `users`-Zeile** der Tombstone berechnen und gegen die Liste abgeschlossener Löschanträge
abgleichen. Der Abgleich braucht nur die **Tombstones** der abgeschlossenen Löschungen — keine Rohschlüssel. Das
Raw-Key-Ledger aus v1.0 entfällt (W-09; weniger personenbezogene Daten, DEC-26).

### 6.3 Löschungs-Spiegel (`erasure_mirror`)

**PRIV-709 (neu gefasst)** Bei jedem Abschluss einer Konto- oder Mandantenlöschung MUSS der Betreiber-Dienst einen
Eintrag in den **Löschungs-Spiegel** schreiben: `{kind: account|tenant, tombstone (instanzweit, = erasure_requests.user_key),
tenant_tombstones[] (mandantengebundene anon2_-Werte, PRIV-238) | tenant_key, erasure_key, completed_at,
plan_fingerprint}` — **kein Rohschlüssel, kein Name**. Der Spiegel lebt (a) in ArangoDB
(`erasure_mirror`, Plattform, `NOT_TENANT_SCOPED`) und (b) **append-only** als Objekt `privacy/erasure-mirror.jsonl`
im Backup-Bucket, verschlüsselt mit dem Fernet-Schlüssel (`FERNET_KEY`, VERIFIED_CODE: vorhanden für OIDC-Secrets),
mit HMAC-Kette über die Einträge (Integrität). Zugriff: nur der Backup-/Restore-Prozess (Bucket-Policy); Aufbewahrung:
wie R-06 (3 J.) bzw. R-06a — danach Bereinigung durch `privacy.purge_erasure_mirror` (Objekt wird gefiltert neu
geschrieben, HMAC-Kette neu). Der Spiegel enthält **pseudonymisierte** Daten (Tombstones) → personenbezogen, aber ohne
Rohschlüssel; Rechtsgrundlage Art. 17-Durchsetzung (R-45, LEG-11).

**PRIV-710** Der Spiegel MUSS **vor** der Dump-Erstellung aktualisiert sein (Reihenfolge im CronJob: Spiegel-Sync →
Dump). Verlust des Spiegels: Rückfall auf die im Dump enthaltenen `erasure_requests`/`tenant_erasure_records`
(decken alle Löschungen **vor** dem Dump) plus den Spiegel-Objektversionen (Bucket-Versionierung); Lücke bleibt für
Löschungen zwischen Dump und Spiegelverlust → dokumentierte Restrisiko-Zeile (RISK-10) und Pflicht, beide Quellen
zu vereinigen.

### 6.4 Wiederherstellungsverfahren

**PRIV-711 (neu gefasst)** Nach `arangorestore` und **vor** Verkehrsannahme führt der Betreiber
`python -m app.migrations.privacy_restore_replay --mirror <path>` aus:
1. Vereinigung der Tombstone-Liste aus dem Spiegel-Objekt (entschlüsselt, HMAC geprüft) und den wiederhergestellten
   `erasure_requests` (`status = completed`, `user_key =~ TOMBSTONE_REGEX`).
2. Für **jede** wiederhergestellte `users`-Zeile: instanzweiter `compute_tombstone_hash(_key, salt)` → Treffer in der
   Liste ⇒ Konto wurde gelöscht ⇒ `erase_account_now`-Äquivalent erneut ausführen (idempotent; der instanzweite
   Tombstone existiert für jede Löschung genau einmal, PRIV-238). Die mandantengebundenen `anon2_`-Werte werden
   dabei aus den wiederhergestellten Mitgliedschaften neu abgeleitet und gegen `tenant_tombstones` geprüft
   (Residue-Scan, Schritt 4) — sie sind nie der Schlüssel des Abgleichs.
3. Für jede `tenant_erasure_records`-Zeile `completed` (Spiegel ∪ Dump), deren Mandantenzeile existiert ⇒ Mandanten-
   löschung erneut ausführen.
4. Prüfeinträge (idempotente Schlüssel) neu erzeugen; Bericht (Zähler) als `migration_reports`-Eintrag `restore_replay`.
5. Residue-Scan (`04` §8) über alle Collections; Rest > 0 ⇒ Restore gilt als **nicht abgeschlossen**, Backend bleibt
   im Wartungsmodus.

**PRIV-712** Restore-Drill (Doku, nightly TA-710) mit präpariertem gelöschtem Konto: nach Replay fehlt der Rohschlüssel
in jeder Collection; keine Zeile außerhalb der Allowlist trägt den Tombstone.

**PRIV-713** Anhänge-Bucket-Versionierung und TimescaleDB-Snapshots folgen derselben Aufbewahrung (≤ 35 d); hart
gelöschte persönliche Objekte werden durch Lifecycle-Regeln bereinigt (Betreiberpflicht, Doku).

**PRIV-707** Backups DÜRFEN in Produktion NICHT aktiviert werden, bevor Spiegel (6.3) und Verfahren (6.4) existieren
(Helm: `backup.enabled` erfordert `privacy.mirror.enabled`; Precheck im Chart). **PRIV-708 [LEG-11]** Dump-Aufbewahrung
≤ `BACKUP_RETENTION_DAYS` (Standard 30, Obergrenze 35); Datenschutzinformation nennt Frist und Replay.

---

## 7. Salt-Rotation und Re-Keying (Verfahren spezifiziert, nicht geplant)

**PRIV-714** `ERASURE_TOMBSTONE_SALT` DARF NICHT rotiert werden ohne Re-Keying-Migration. Verfahren (für den Fall):
(1) neuer Salt als `ERASURE_TOMBSTONE_SALT_NEXT`; (2) Migration `vNNNN_rekey_tombstones`: für jede Allowlist-Zelle
mit Tombstone **ohne** Kenntnis des Rohschlüssels ist eine Neuberechnung **unmöglich** — daher kann Re-Keying nur
Tombstones betreffen, deren Rohschlüssel noch existiert (aktive Konten in gelöschten Mandanten); für alle anderen
bleibt der alte Tombstone gültig und die Allowlist-Regex kennt beide Generationen (`anon_`, `anon2_`, DEC-25); (3) der
Spiegel (§6.3) wird um die neue Generation ergänzt. Folge: Eine Kompromittierung des Salts ist nicht durch Rotation
heilbar; Schutz liegt in Zugriffsbeschränkung des Secrets (Betriebsdoku, RISK-20).

---

## 8. Bestehende Offline-Datensätze auf Geräten (DEC-29)

**PRIV-715** Client-Migration (Dexie `version(3)` auf `kp-write-queue`, Versionssprung des Plan-Caches): beim ersten
Start der neuen Version (a) `kp-plan-cache` vollständig löschen; (b) vorhandene Puffer-Einträge in einen Übergangs-
dialog „jetzt senden / verwerfen“ geben; ohne Entscheidung werden sie nach 7 Tagen gelöscht (Hinweis mit Anzahl);
(c) Offline-Modus steht auf **aus**, bis der Nutzer ihn einschaltet (`07` §2.1); (d) `expiresAt` neuer Einträge nach
den neuen Fristen; (e) PRIV-512-Schlüssel beim nächsten Logout löschen. Release-Notiz informiert.

---

## 9. Inaktive Mandanten

**PRIV-716** Datenschutzkorrekturen (`kind = privacy_correction`) verarbeiten Mandanten in **jedem** Status außer
`deleted` (Art. 17 gilt unabhängig vom Mandantenzustand); Daten-Backfills (`kind = data_backfill`) verwenden
`ActiveTenants` [VERIFIED_CODE: seit #2839 überspringt der gemeinsame Mapper Beete inaktiver Mandanten
(`SkipReason.INACTIVE_TENANT`, Scan liefert `site_tenant_active`); v0104 selbst bleibt unverändert, NFR-016 M-7]. Guard `test_migration_tenant_gate_kind`
(TA-704).

---

## 10. Teilweise abgeschlossene Löschvorgänge

**PRIV-717** Job `privacy.resume_partial_erasures --older-than 30d` listet jede `partially_completed`-Löschung mit
unerreichten Schritten und Resten und plant sie mit zurückgesetztem `attempt_count` erneut ein; Eskalation an den
Betriebsendpunkt (E15).

---

## 11. Rollback-Einschränkungen

| Migration / Job | Rollback | Teilausfall |
|-----------------|----------|-------------|
| v0109 | keiner (Information absichtlich zerstört); Dry-Run-Bericht ist der Nachweis | je Mandant transaktional; Wiederholung beim nächsten Start |
| v0110 | entfernt explizites `legacy`/`unknown_legacy`; `none` persönlicher Mandanten bleibt (§4) | je Mandant ein Dokument-`UPDATE`; Wiederholung beim nächsten Start; idempotent |
| v0111 | entfernt je Zeile ein Schlüsselfeld, das `null` ist, und ein Label, das noch die Kopie seiner Quelle ist; ein später gestempelter Schlüssel oder ein geändertes Label bleibt. Schritt 4 (`inspector = ""`, zugeordneter Service-Schlüssel) wird nicht zurückgenommen: der Text war ein Pseudo-Schlüssel, kein Name | je Mandant transaktional (PRIV-718, statt „je Collection“ in v1.1); Wiederholung beim nächsten Start; idempotent |
| v0114 | keiner: den Schlüssel nach `author` zurückzuschreiben stellte den Befund wieder her; ein älterer Build liest ein Protokoll ohne `author` als eines ohne Autor | je Mandant transaktional; Wiederholung beim nächsten Start; idempotent |
| Reklassifizierung | keiner | je Mandant; Zustand `reclassification_pending` bis Erfolg |
| Restore-Replay | keiner (wendet Löschungen erneut an) | Residue > 0 ⇒ Wartungsmodus bleibt |

---

## 12. Verifikation

| ID | Kriterium |
|----|-----------|
| TA-700 | Zweiter Lauf `changed == 0`; AQL bindet `tenant_key`; Bericht nur mit erlaubten Schlüsseln; Phasen `precheck/dry_run/apply/verify` im Bericht. |
| TA-701 | v0109: Dry-Run schreibt nichts; echter Lauf wandelt präparierte Tombstones um, zählt einen nicht deklarierten Tombstone ohne Änderung, leert `original_filename`; `verify.residual = 0`; ein Fehler in Mandant X lässt die übrigen fertig werden und die Migration nicht als angewendet gelten. |
| TA-701a | Berichtsfilter weist Nutzerschlüssel/Namen in `details` ab. |
| TA-702 | v0111 setzt nie einen `*_user_key` aus einem Namen; `mcp:<key>` nur für existierendes Service-Konto. |
| TA-703 | Reklassifizierung wirkt nur mit gesetztem Flag; ohne Flag `reclassification_pending` + Metrik. |
| TA-704 | Guard: `kind` deklariert; Backfill nutzt `ActiveTenants`, Korrektur nicht. |
| TA-709 | Spiegel-Eintrag (ohne Rohschlüssel) bei Abschluss; Objekt verschlüsselt, HMAC-Kette gültig; Bereinigung filtert. |
| TA-710 | Restore-Drill: Dump vor Löschung → Löschung → Restore → Replay erkennt das Konto über den Tombstone-Abgleich → Rohschlüssel in keiner Collection; Residue 0. |
| TA-711 | Restore-Doku enthält Replay; `mkdocs build --strict`. |
| TA-716 | Korrektur verarbeitet `suspended`; Backfill überspringt. |
| TA-719 | v0114: nach dem Lauf trägt keine Mandantenzeile `rooting_protocols.author`; ein lebendes Konto wird zum Schlüssel, ein gelöschtes zum Marker; ein schon gesetztes `author_user_key` bleibt. |
| TA-717 | Resume-Job listet und plant erneut. |
| TA-718 | Helm: `backup.enabled=true` ohne `privacy.mirror.enabled` schlägt im Template-Precheck fehl. |
