# SPEC-09 — Migrations- und Backfill-Strategie

```
Package: spec/privacy · Version 1.0 · 2026-11-09 · gemessen gegen develop 24d1c2988
Requirement IDs: PRIV-700 … PRIV-739
Depends on: NFR-016 / ADR-009 (migration framework), 04 §7 (legacy findings), 08 (model)
```

---

## 1. Framework-Fakten, auf die sich die Migrationen stützen [verifiziert]

- Versionen `app/migrations/versions/vNNNN_<slug>.py`, lückenlos, ein `migration`-Objekt; `up(db,
  *, dry_run=False) -> MigrationReport` idempotent (M-3), `dry_run` wird beachtet (M-5); das Standard-
  `down` wirft `IrreversibleMigrationError` (M-6); angewendete Quellen sind durch
  `test_applied_migration_sources_are_frozen` eingefroren.
- `MigrationReport {version, name, scanned, changed, dry_run, duration_ms,
  precondition_unmet, details}`; das CLI gibt nur Zähler aus, `details` erreichen stdout nur
  über die eigene structlog-Zeile der Migration; **kein Dry-Run-Bericht wird persistiert** — der
  Betreiber schreibt `.audits/prod-release/*.md` von Hand aus erfassten Logs.
- Kein Mandanten-Scoping auf Framework-Ebene: jede Migration begrenzt sich selbst; Unique-Indizes beginnen mit
  `tenant_key`. Läuft beim Start (`run_pending_migrations`), Sperre in `schema_migrations`
  (`__lock__`, TTL 300 s); eine fehlschlagende Migration ist für den Start fatal (M-4).
- Reversibilität ist die Ausnahme (v0104 ist über seinen Marker `trigger=backfill` +
  `source_ref` umkehrbar, ausgenommen Zeilen, die eine Person seither bearbeitet hat).
- Neueste Version: `v0106_client_event_id_index`.

**PRIV-700** Jede Migration dieses Pakets MUSS idempotent sein (zweiter Lauf `changed == 0`),
in ihrem AQL mandantengebunden (`FILTER doc.tenant_key == @tenant_key` oder eine Schleife pro Mandant mit
einmal gelesener Mandantenliste) und beobachtbar (eine structlog-Zeile mit dem `details`-Dict **und**
ein persistierter Dry-Run-Bericht, §2).

---

## 2. Dry-Run-Berichte werden persistierte Artefakte

**PRIV-701** Eine neue Collection `migration_reports` (Plattform, `NOT_TENANT_SCOPED` mit Begründung
„operator proof of a migration run; no personal data") MUSS jeden `MigrationReport`
einer Datenschutz-Migration (`dry_run` und real) mit `details` speichern, **nachdem er einen Redaktionsfilter
durchlaufen hat**: `details` darf nur Zähler, Collection-Namen, Feldnamen, Mandanten-**Schlüssel**
und Stichproben-**Zeilenschlüssel** (≤ 25 pro Bucket, wie v0104) enthalten — nie Nutzerschlüssel, Namen, Text oder
Tombstones. Ein Unit-Test parst den Berichts-Builder jeder Datenschutz-Migration und prüft die
erlaubte Schlüsselmenge.

**PRIV-702** Das CLI `upgrade --dry-run --report-out <path>` MUSS die Berichte als JSON schreiben,
sodass das Dokument `.audits/prod-release` sie wörtlich einbetten kann, statt
Zahlen aus Logs abzuschreiben.

---

## 3. M-P1 — Kopierte Tombstones korrigieren und den Plan-Audit-Akteur auf den Marker umstellen

**Migration `v0107_privacy_tombstone_copies`** (umkehrbar: nein — ein Marker lässt sich nicht
in das Pseudonym zurückverwandeln; die Information ist absichtlich weg).

| Schritt | AQL (pro Mandant) | Berichts-Bucket |
|------|------------------|---------------|
| 1 | `care_events`, wo `performed_by_user_key =~ TOMBSTONE_REGEX` → `_anonymized` (auch `performed_for_user_key`, `created_by`, `voided_by`, `redacted_by`) | `care_events.tombstone_to_marker{tenant_key: count}` |
| 2 | `garden_plan_audit.user_key =~ TOMBSTONE_REGEX` → `_anonymized` (DEC-16) | `garden_plan_audit.tombstone_to_marker` |
| 3 | jede andere **nicht auf der Allowlist stehende** Collection mit einem kontoförmigen Feld (Liste zur Laufzeit aus dem Inventar abgeleitet, `tombstone_allowed_fields()` ausgenommen): nur zählen, nicht schreiben | `undeclared_tombstones{collection.field: count}` → Vorbedingung für den Konsistenz-Beat, nicht blind korrigiert |
| 4 | `attachments.created_by == _anonymized AND original_filename != ""` → `""` | `attachments.filename_cleared` |

**PRIV-703** Vorbedingungen: Die Inventarregel-Änderung für `garden_plan_audit` (Tombstone →
Marker) MUSS im selben PR gemergt werden; der Konsistenz-Beat (`privacy.consistency`) MUSS so
registriert sein, dass Bucket 3 nach der Migration weiter überwacht wird.

**PRIV-704** Der Trockenlauf (Dry-Run) MUSS vor P-8 (dem nächsten REQ-053-Produktionspunkt) gegen einen Produktions-Snapshot ausgeführt
und sein persistierter Bericht dem Release-Dokument beigefügt werden; der echte Lauf
ist Teil der normalen Start-Migration.

Erwartete Produktionszahlen (aus dem v0104-Lauf des P-6-Berichts): klein — der Backfill lief am
2026-11-07; Tombstones existieren nur für Konten, die vor diesem Datum gelöscht wurden und deren
Behandlungen/Ernten in das R-25-Fenster fielen.

---

## 4. M-P2 — Aufzeichnungsprofil und Neuklassifizierung

**Migration `v0108_tenant_record_keeping_default`**: setzt `settings.record_keeping = "legacy"`
ausdrücklich bei jedem Mandanten, der keinen Wert hat (damit späterer Code „nie gefragt" von „keinen
erklärt" unterscheiden kann). Umkehrbar (entfernt den Schlüssel, wo er `legacy` entspricht).

**Job (keine Migration): `privacy.reclassify_statutory_rows`** — läuft, wenn sich das `record_keeping` eines Mandanten
auf `none` ändert (PRIV-402), mandantengebunden, idempotent:

| Zeilen | Aktion |
|------|--------|
| `harvest_batches`, `quality_assessments`, `treatment_applications`, `inspections` mit einem Tombstone in `*_by_key` | → `_anonymized`; `review item` für `notes` (`source_kind = record_keeping_change`) |
| dieselben Collections mit einem lebenden Schlüssel | jetzt nichts (das Konto existiert); die Löschregeln eines `none`-Mandanten behandeln sie ab jetzt als `shared_history` |

Bericht: Zähler pro Collection; auditiert `TENANT_RECORD_KEEPING_CHANGED`.

---

## 5. M-P3 — Freitext-Ausführendenfelder → verschlüsselt (keyed)

**Migration `v0109_keyed_performers`** (additives Schema; umkehrbar für die *Kopie* des Feldes,
nicht für spätere Schreibvorgänge):

| Collection | Schritt |
|------------|------|
| `watering_events`, `watering_logs`, `tank_fill_events`, `maintenance_logs` | `performed_by_user_key = null` hinzufügen, `performed_by_label = performed_by[:80]` (der getippte Text wird zum Dritt-Label — er ist **kein** Schlüssel, REQ-025 Regel 4); `performed_by` für ein Release behalten (deprecated) |
| `nutrient_plans`, `propagation`-Chargen | `author_user_key = null`, `author_label = author[:80]` |
| `inspections`, wo `inspector LIKE "mcp:%"` | `inspected_by_key = substring after "mcp:"` **nur wenn** dieser Schlüssel ein aktuelles `users._key` mit `account_type = service` ist; andernfalls `inspected_by_key = null`; `inspector = ""` |
| `workflow_templates` | `created_by_user_key = null`; `created_by` als Label behalten |

**PRIV-705** Die Migration DARF KEIN Konto aus einem getippten Namen ableiten (REQ-025 §3.1.3 Regel
4; #1662/#1663 haben gemessen, dass es nie das richtige Konto trifft). Die einzige Ausnahme ist das
Präfix `mcp:<key>`, das der MCP-Code deterministisch geschrieben hat [verifiziert
`mcp_server/tools/ipm.py`].

**PRIV-706** Zeilen, deren Label dem **aktuellen Anzeigenamen eines Mitglieds** desselben Mandanten entspricht,
KÖNNEN als Prüfpunkte (`legacy_unkeyed_name`) aufgelistet werden, damit ein Lead entscheiden kann, das
Label zu behalten oder zu löschen; die Migration ändert sie nie. Begrenzt durch PRIV-223.

---

## 6. Backups und Wiederherstellung

### 6.1 Fakten [verifiziert]

- Helm-CronJob `arangodb-backup` (`arangodump` → rclone → S3) existiert, **standardmäßig
  deaktiviert**, `retentionDays: 30`; TimescaleDB und Anhänge werden vom Chart nicht abgedeckt
  (Doku empfiehlt Snapshots/Versionierung); in Produktion ist kein Backup als laufend
  dokumentiert (Audit DR-01…04).
- Die Doku verlangt bei der Wiederherstellung denselben `FERNET_KEY` und `ERASURE_TOMBSTONE_SALT`; NFR-011 §4
  verlangt den Salt im DR-Backup.
- **Kein Verfahren wendet Löschungen nach einer Wiederherstellung erneut an**; keine Prüfung von `erasure_requests` bei
  der Wiederherstellung; Dump-Aufbewahrung vs. Art. 17 ist nicht adressiert.

### 6.2 Anforderungen

**PRIV-707** Backups DÜRFEN in Produktion NICHT aktiviert werden, bevor das Wiederholungs-Ledger (Replay-Ledger, §6.3) und
das Wiederherstellungsverfahren (§6.4) existieren. (Entscheidung des Betreibers; als DEC-13 festgehalten.)

**PRIV-708 [rechtlich LEG-11]** Die Dump-Aufbewahrung MUSS ≤ `BACKUP_RETENTION_DAYS` sein (Standard 30,
Obergrenze 35) und MUSS in der Datenschutzerklärung stehen („Backup-Kopien werden innerhalb von 35
Tagen gelöscht; nach einer Wiederherstellung werden abgeschlossene Löschungen automatisch erneut angewendet"). Die EDPB-/DSK-
Position, dass Backups für eine Löschung nicht bearbeitet werden müssen, wenn sie nach kurzem
Zeitplan gelöscht werden und Löschungen bei der Wiederherstellung erneut angewendet werden, ist die Annahme; die Rechtsberatung bestätigt.

### 6.3 Wiederholungs-Ledger für Löschungen (`08` §3.7)

**PRIV-709** Bei jeder abgeschlossenen Konto-Löschung MUSS die Engine
`erasure_replay_ledger {erasure_key, user_key (raw), tombstone, completed_at, plan_fingerprint,
expires_at = completed_at + BACKUP_RETENTION_DAYS + ERASURE_REPLAY_LEDGER_GRACE_DAYS}` schreiben. Der
Rohschlüssel ist notwendig, weil jede Löschregel den Rohschlüssel trifft; der Tombstone kann keine
Zeilen finden. Das Ledger wird von `privacy.purge_replay_ledger` bereinigt; die Aufbewahrung ist R-45.
Mandanten-Löschungen brauchen kein Ledger: `tenant_erasure_records` (Schlüssel `ter_<tenant_key>`) trägt
den Mandantenschlüssel bereits und bleibt erhalten.

**PRIV-710** Muss das Ledger vom Dump ausgeschlossen werden? — Nein: es muss **im** Dump sein, damit
eine Wiederherstellung eines älteren Dumps die nach ihm entstandenen Einträge findet... was sie nicht kann (sie
sind neuer als der Dump). Korrektes Design: das Ledger lebt in ArangoDB **und** wird
append-only in ein kleines Objekt `privacy/replay-ledger.jsonl` im Backup-Bucket gespiegelt (mit dem Fernet-Schlüssel verschlüsselt)
bei jedem Abschluss einer Löschung; die Wiederherstellung liest die Spiegelung. Die Spiegelung wird
vom Bereinigungs-Beat neu geschrieben (gefiltert). Abnahme TA-709.

### 6.4 Wiederherstellungsverfahren (Erweiterung von `docs/de/deployment/backup-restore.md`)

**PRIV-711** Nach `arangorestore` und bevor das Backend Verkehr annimmt, MUSS der Betreiber
`python -m app.migrations.privacy_restore_replay --from-mirror <path>` ausführen, das:
1. die Ledger-Spiegelung lädt, Einträge überspringt, deren `erasure_key` in den
   wiederhergestellten `erasure_requests` als `completed` existiert **und** deren Tombstone in `users` erscheint?
   — die Nutzerzeile ist in einem konsistenten Dump weg; die Prüfung lautet: `users/<user_key>` **existiert** in den wiederhergestellten Daten
   → der Dump ist älter als die Löschung → das Äquivalent von `erase_account_now` für diesen Schlüssel mit
   dem Tombstone des Ledgers erneut ausführen (ohnehin deterministisch aus dem Salt);
2. Mandanten-Löschungen für `tenant_erasure_records` im Status `completed` erneut ausführt, deren Mandantenzeile
   in den wiederhergestellten Daten existiert;
3. die Erzeugung von Prüfpunkten wiederholt (Replay) (idempotente Schlüssel) und einen Bericht (Zähler) ausgibt, der als
   `migration_reports`-Eintrag `restore_replay` persistiert wird.

**PRIV-712** Die Wiederherstellungsübung (Doku §„Restore-Drill") MUSS ein eingeschleustes gelöschtes Konto enthalten
und TA-710 prüfen: nach Wiederherstellung + Wiederholung (Replay) trägt keine Zeile den Rohschlüssel außerhalb des Ledgers.

**PRIV-713** Bucket-Versionierung der Anhänge und TimescaleDB-Snapshots MÜSSEN derselben
Aufbewahrung folgen (≤ 35 d); Objektversionen hart gelöschter persönlicher Dateien (`user_personal`, Schädlings-
Referenzen) werden durch Lifecycle-Regeln am Bucket bereinigt — dokumentiert, Verantwortung des Betreibers.

---

## 7. Salt-Rotation (außerhalb des Umfangs, Einschränkung festgehalten)

**PRIV-714** `ERASURE_TOMBSTONE_SALT` DARF NICHT rotiert werden ohne eine Re-Keying-Migration, die
jeden Tombstone der Allowlist (`old → new`) in einem Durchgang umschreibt — die Tombstone-Suche nach Art. 15
und die R-06-Bereinigung hängen vom Determinismus ab. Nicht geplant; die Einschränkung geht in die
Betriebsdokumentation.

---

## 8. Bestehende Offline-Datensätze auf Geräten

**PRIV-715** Es gibt keine serverseitige Migration für Gerätedaten. Die Client-Migration
(Dexie `version(3)` auf `kp-write-queue`) MUSS: Unterstützung für `status = quarantined` hinzufügen, `expiresAt`
mit den neuen Standardwerten (90/30) **nur vorwärts** neu berechnen (ein Eintrag, der bereits älter als die
neue Frist ist, wird bei der nächsten Bereinigung mit dem Hinweis gelöscht), und die PRIV-512-Schlüssel beim
nächsten Logout löschen. Eine Frontend-Release-Notiz teilt den Nutzern mit, dass ungesendete Einträge älter als 90 Tage
beim nächsten Start entfernt werden.

---

## 9. Inaktive Mandanten

**PRIV-716** Datenschutz-Migrationen MÜSSEN Mandanten in jedem Status **außer `deleted`** verarbeiten:
`suspended`, `pending_deletion`, `orphaned` und `importing` halten personenbezogene Daten, die
das Recht des Betroffenen aus Art. 17 unabhängig vom Zustand des Mandanten umfasst. (v0104 schreibt in
nicht aktive Mandanten [verifiziert, #2770 Punkt 4] — für einen *Backfill* ist das ein Defekt; für eine
*Datenschutzkorrektur* ist es erforderlich. Die beiden Arten MÜSSEN im Docstring der Migration gekennzeichnet werden:
`kind = "privacy_correction" | "data_backfill"`, und der Guard
`test_beats_skip_inactive_tenants` erhält ein Geschwister für Migrationen, das prüft, dass ein Backfill
`ActiveTenants` verwendet und eine Korrektur nicht.)

---

## 10. Teilweise abgeschlossene Löschvorgänge

**PRIV-717** Ein einmaliger Job `privacy.resume_partial_erasures --older-than 30d` MUSS jede
`partially_completed`-Löschung mit ihren nicht erreichten Schritten und Resten auflisten (heute gibt es keine Liste),
und sie erneut einplanen, wobei `attempt_count` zurückgesetzt wird, damit das Backoff neu startet; Eskalations-
Zeilen gehen an den Betriebs-Endpunkt. Es ist ein Job, keine Migration (er kann jederzeit laufen).

---

## 11. Rollback-Einschränkungen (pro Migration)

| Migration | Rollback |
|-----------|----------|
| v0107 Tombstone-Kopien → Marker | keiner (Information absichtlich zerstört); der Dry-Run-Bericht ist der Nachweis |
| v0108 Aufzeichnungs-Default | entfernt das ausdrückliche `legacy` |
| v0109 verschlüsselte Ausführende (keyed performers) | entfernt die neuen Felder, wenn sie alle `null`/Kopien sind; verweigert sonst |
| Reclassify-Job | keiner (gesetzlich → geteilt ist eine Einbahnstraße) |
| Wiederherstellungs-Replay | keiner (er wendet Löschungen erneut an) |

---

## 12. Verifikation

| ID | Kriterium |
|----|-----------|
| TA-700 | Jede Datenschutz-Migration: zweiter Lauf `changed == 0`; AQL bindet `tenant_key`; Bericht persistiert nur mit erlaubten Schlüsseln. |
| TA-701 | v0107-Trockenlauf (Dry-Run) schreibt nichts; echter Lauf wandelt eingeschleuste Tombstones in `care_events` und `garden_plan_audit` um, zählt einen nicht deklarierten Tombstone in einem eingeschleusten nicht auf der Allowlist stehenden Feld, ohne ihn zu ändern, löscht einen eingeschleusten `original_filename`. |
| TA-702 | v0109 setzt nie einen `*_user_key` aus einem getippten Namen; `mcp:<service-key>` wird nur für ein existierendes Service-Konto abgebildet. |
| TA-703 | Der Reclassify-Job wandelt Tombstones für einen `none`-Mandanten in Marker um und lässt einen `pflschg_professional`-Mandanten unberührt. |
| TA-709 | Ledger-Eintrag beim Abschluss geschrieben; Spiegelobjekt aktualisiert; nach `expires_at` bereinigt; Spiegelung gefiltert. |
| TA-710 | Wiederherstellungsübung: Dump vor einer Löschung erstellt, Löschung abgeschlossen, Wiederherstellung, Wiederholung (Replay) → der Rohschlüssel fehlt in jeder Collection, bis zum Ablauf nur im Ledger vorhanden; Prüfpunkte idempotent neu erzeugt. |
| TA-716 | Eine Datenschutzkorrektur verarbeitet einen `suspended`-Mandanten; ein Datenbackfill überspringt ihn. |
| TA-717 | Der Resume-Job listet eingeschleuste `partially_completed`-Löschungen auf und plant sie erneut ein. |
