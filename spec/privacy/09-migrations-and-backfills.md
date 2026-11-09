# SPEC-09 — Migrations- und Backfill-Strategie

```
Paket: spec/privacy · Version 1.1 · 2026-11-09 · gemessen gegen develop 24d1c2988; Nachtrag #2839 (develop 343afbb97)
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
- `MigrationReport {version, name, scanned, changed, dry_run, duration_ms, precondition_unmet, details}`; CLI gibt nur
  Zähler aus; `details` nur über die structlog-Zeile der Migration; **kein Dry-Run-Bericht wird persistiert**.
- Kein Mandanten-Scoping auf Framework-Ebene; Unique-Indizes beginnen mit `tenant_key`. Start-Migration mit Sperre
  `schema_migrations/__lock__` (TTL 300 s); Fehler ist startfatal (M-4). `precondition_unmet` hält die Migration
  ausstehend und stoppt die Schleife.
- Konsistenz-Job `care_events.consistency` existiert (05:10 UTC, `ActiveTenants`-Gate, Fenster 7 d); ein
  allgemeiner Datenschutz-Konsistenz-Beat existiert **nicht**.
- Neueste Version: `v0107_care_event_tombstone_performer` (#2839, gemergt 2026-11-09, VERIFIED_CODE): ersetzt
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

**Stand (#2839, VERIFIED_CODE):** `v0107_care_event_tombstone_performer` hat Schritt 1 für `performed_by_user_key`
(Generation `anon_`) bereits ausgeführt. Offen bleiben `created_by`-Tombstones, die zweite Generation `anon2_`
(E03), Schritte 2–4, `verify` und der persistierte Bericht. Die Nummer dieser Migration ist von v0107 auf v0108
verschoben (W-26).

**Migration `v0108_privacy_tombstone_copies`** (`kind = privacy_correction`; umkehrbar: nein).

| Schritt | AQL (je Mandant, alle Status außer `deleted`) | Berichts-Bucket |
|---------|-----------------------------------------------|-----------------|
| 1 | `care_events`: `performed_by_user_key` **und** `created_by` mit `=~ TOMBSTONE_REGEX` (beide Generationen) → `_anonymized` — Rest nach v0107 (#2839), das nur `performed_by_user_key` der Generation `anon_` erfasst | `care_events.tombstone_to_marker{tenant_key: count}` |
| 2 | `garden_plan_audit.user_key =~ TOMBSTONE_REGEX` → `_anonymized` (DEC-16) | `garden_plan_audit.tombstone_to_marker` |
| 3 | jede andere **nicht** auf der Allowlist stehende Collection/Feld-Kombination mit kontoförmigem Feld: **nur zählen** | `undeclared_tombstones{collection.field: count}` |
| 4 | `attachments.created_by == _anonymized AND original_filename != ""` → `""` | `attachments.filename_cleared` |
| verify | Schritte 1, 2, 4 erneut zählen → muss 0 sein; Schritt 3 wird als Befund gemeldet, nicht korrigiert | `verify.residual` |

**PRIV-703 (neu gefasst, löst W-02)** Vorbedingungen von v0108 sind **ausschließlich**: (a) die Inventaränderung
`garden_plan_audit` Tombstone → Marker und `attachments.clear_fields += original_filename` im selben Build (Precheck
importiert die Regel und prüft `replacement_strategy`/`clear_fields`); (b) `TOMBSTONE_REGEX`/Allowlist aus
`domain/models/privacy.py` (E03). Die **Nachprüfung** erfolgt innerhalb der Migration (`verify`) und durch
`tests/unit/migrations/versions/test_v0108_*.py`; der Beat `privacy.consistency` ist **keine** Vorbedingung. Der
Beat wird in **E04 in seiner Minimalform** (nur lesende Zählabfragen des Bucket 3 + Metrik, kein Endpunkt) eingeführt,
damit Bucket 3 ab dem Folgetag überwacht ist; Metriken-Endpunkt und Operations-Listing bleiben E15. (DEC-28)

**PRIV-704** Trockenlauf gegen einen Produktions-Snapshot vor P-8; Bericht im Release-Dokument.

**Erwartung Produktion:** klein (Backfill lief 2026-11-07, P-6-Bericht).

---

## 4. M-P2 — Aufzeichnungsprofil und Klassifizierung (E09)

**Migration `v0109_tenant_record_keeping_default`** (`kind = privacy_correction`; umkehrbar: entfernt `legacy`):
setzt bei jedem bestehenden Mandanten ohne Wert `settings.record_keeping = "legacy"` und `settings.organization_kind =
"unknown_legacy"`; persönliche Mandanten erhalten `record_keeping = "none"` (L-07). Neue Mandanten erhalten
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

**Migration `v0110_keyed_performers`** (`kind = data_backfill` für die Feldanlage; additiv):

| Collection | Schritt |
|------------|---------|
| `watering_events`, `watering_logs`, `tank_fill_events`, `maintenance_logs` | `performed_by_user_key = null`, `performed_by_label = performed_by[:80]`; `performed_by` ein Release deprecated |
| `nutrient_plans`, `propagation`-Chargen | `author_user_key = null`, `author_label = author[:80]` |
| `inspections` mit `inspector LIKE "mcp:%"` | `inspected_by_key = <key>` **nur wenn** aktuelles Service-Konto; sonst `null`; `inspector = ""` |
| `workflow_templates` | `created_by_user_key = null`; `created_by` als Label |

**PRIV-705** Kein Konto aus einem getippten Namen ableiten (REQ-025 Regel 4; #1662/#1663); Ausnahme nur das
deterministische Präfix `mcp:` [VERIFIED_CODE]. **PRIV-706** Labels, die einem aktuellen Mitgliedsnamen entsprechen,
KÖNNEN als Prüfeinträge `legacy_unkeyed_name` gelistet werden; die Migration ändert sie nie.

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
Eintrag in den **Löschungs-Spiegel** schreiben: `{kind: account|tenant, tombstone | tenant_key, erasure_key,
completed_at, plan_fingerprint}` — **kein Rohschlüssel, kein Name**. Der Spiegel lebt (a) in ArangoDB
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
2. Für **jede** wiederhergestellte `users`-Zeile: `compute_tombstone_hash(_key, salt)` (beide Formate, DEC-25) → Treffer
   in der Liste ⇒ Konto wurde gelöscht ⇒ `erase_account_now`-Äquivalent erneut ausführen (idempotent; Tombstone
   deterministisch).
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
| v0108 | keiner (Information absichtlich zerstört); Dry-Run-Bericht ist der Nachweis | je Mandant transaktional; Wiederholung beim nächsten Start |
| v0109 | entfernt explizites `legacy`/`unknown_legacy` | idempotent |
| v0110 | entfernt neue Felder, wenn alle `null`/Kopien | je Collection transaktional |
| Reklassifizierung | keiner | je Mandant; Zustand `reclassification_pending` bis Erfolg |
| Restore-Replay | keiner (wendet Löschungen erneut an) | Residue > 0 ⇒ Wartungsmodus bleibt |

---

## 12. Verifikation

| ID | Kriterium |
|----|-----------|
| TA-700 | Zweiter Lauf `changed == 0`; AQL bindet `tenant_key`; Bericht nur mit erlaubten Schlüsseln; Phasen `precheck/dry_run/apply/verify` im Bericht. |
| TA-701 | v0108: Dry-Run schreibt nichts; echter Lauf wandelt präparierte Tombstones um, zählt einen nicht deklarierten Tombstone ohne Änderung, leert `original_filename`; `verify.residual = 0`; ein Fehler in Mandant X lässt die übrigen fertig werden und die Migration nicht als angewendet gelten. |
| TA-701a | Berichtsfilter weist Nutzerschlüssel/Namen in `details` ab. |
| TA-702 | v0110 setzt nie einen `*_user_key` aus einem Namen; `mcp:<key>` nur für existierendes Service-Konto. |
| TA-703 | Reklassifizierung wirkt nur mit gesetztem Flag; ohne Flag `reclassification_pending` + Metrik. |
| TA-704 | Guard: `kind` deklariert; Backfill nutzt `ActiveTenants`, Korrektur nicht. |
| TA-709 | Spiegel-Eintrag (ohne Rohschlüssel) bei Abschluss; Objekt verschlüsselt, HMAC-Kette gültig; Bereinigung filtert. |
| TA-710 | Restore-Drill: Dump vor Löschung → Löschung → Restore → Replay erkennt das Konto über den Tombstone-Abgleich → Rohschlüssel in keiner Collection; Residue 0. |
| TA-711 | Restore-Doku enthält Replay; `mkdocs build --strict`. |
| TA-716 | Korrektur verarbeitet `suspended`; Backfill überspringt. |
| TA-717 | Resume-Job listet und plant erneut. |
| TA-718 | Helm: `backup.enabled=true` ohne `privacy.mirror.enabled` schlägt im Template-Precheck fehl. |
