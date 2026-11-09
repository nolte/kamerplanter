# SPEC-02 — Inventar personenbezogener Daten

```
Paket: spec/privacy · Version 1.1 · 2026-11-09 · gemessen gegen develop 24d1c2988; Nachtrag #2839 (develop 343afbb97)
Anforderungs-IDs: PRIV-030 … PRIV-049 (Inventarregeln)
Änderung v1.1: `erasure_mirror` statt Raw-Key-Ledger, `migration_reports`, Ableitungswege jenseits der statischen
Prüfung (§5a); Rechtsgrundlagen-Spalten verweisen auf `06` §2 (PA-nn) und `13` (L-nn).
Quelle der Wahrheit für die Listen: die Code-Inventare, die in REQ-025 §3.1.1 genannt sind; dieses Dokument
ist eine *Klassifizierung* davon, keine von Hand zu pflegende Kopie (siehe §1).
```

---

## 1. Wie sich dieses Inventar zum Code verhält

REQ-025 §3.1 hat entschieden (v1.10, #1719), dass die Listen der Quellen personenbezogener Daten **nur
im Code** liegen und abgesichert sind. Dieses Dokument führt daher nicht jeden Auskunfts- oder
Löschungseintrag erneut auf. Es ergänzt die **Klassifizierung**, die der Code noch nicht trägt (Zurechnungsrolle,
Aufbewahrungsklasse, Prüffelder, Herkunft), und gibt für jedes Feld an, was das Paket
verlangt. Die Klassifizierung wird ebenfalls zu Code (`08` §2: Attribute an den bestehenden
Dataclasses) und wird dann durch `scripts/check_privacy_inventory.py` Regel R7 abgesichert.

**PRIV-030** Jedes in §3 aufgeführte Feld mit nicht leerer Spalte „Erforderlich" MUSS mit den angegebenen Werten in der
Registry erscheinen; der Guard vergleicht die Tabelle dieses Dokuments mit dem Code (ein
Skript `scripts/check_privacy_registry_doc.py` parst die mit `⟂` markierten Tabellenzeilen), sodass
beide nicht unbemerkt auseinanderlaufen können — das Scheitern von #1663/#1700/#1716 (von Hand gepflegte Kopien)
wird vermieden, indem das Dokument zur *Testeingabe* wird, nicht zu einer parallelen Wahrheit.

Konventionen: Eine `⟂`-Zeile wird maschinell geprüft; `[v]` im Code verifiziert; `[?]` nicht verifiziert (dort markiert,
wo die Analyse nicht bestätigen konnte); die Spalten „Löschung"/„Anonymisierung" beschreiben das
Verhalten bei der **Konto**löschung (die Mandantenlöschung löscht fast alles, was dem Mandanten zugeordnet ist —
Ausnahmen sind angegeben). Werte der Rechtsgrundlage sind **Vorschläge** (`06`), außer wo NFR-011
sie bereits nennt.

Kategorien: `IDN` Identifikator (Schlüssel, E-Mail), `PRO` Profil, `AUTH` Zugangsdaten/Sitzung,
`ATTR` Zurechnung (wer hat etwas getan/geschrieben/geändert), `TXT` Freitext, `MED` Medien, `LOC` Standort
(Koordinaten, Adressen), `SENS` Sensor-/Verhaltensdaten, `CONS` Einwilligung/rechtlicher Status, `AUD` Audit,
`DEV` auf dem Gerät.

---

## 2. Entitäten ohne personenbezogene Daten (der Vollständigkeit halber)

[v] Globale Katalogdaten (`species`, `cultivars`, `fertilizers`, `substrates`,
`phase_definitions`, IPM-Katalog) tragen höchstens `tenant_key`, keinen Kontobezug und
konstruktionsbedingt keinen personenbezogenen Freitext. Geometrie (`garden_objects.geometry`, `locations.geometry`)
„sind keine personenbezogenen Daten" (GP-NFR-055) — **aber** Standortkoordinaten sind es (§3.6).
`client_event_tombstones` enthalten ausschließlich zufällige UUIDs [v]. `yield_metrics` hat kein Benutzerfeld [v].

---

## 3. Inventar

### 3.1 Konto und Identität (Verantwortlicher: Betreiber)

| ⟂ | Entität.Feld | Kat | Personenbezogen? | Zweck | Rechtsgrundlage | Sichtbarkeit | Aufbewahrung | Löschung | Anonymisierung | Herkunft / Kopien |
|---|--------------|-----|-------------|---------|-------------|------------|-----------|---------|---------------|------------------|
| ⟂ | `users._key` | IDN | ja (pseudonymer Identifikator) | Primärschlüssel | 6(1)(b) | intern; **nie in API-Antworten** außer eigenes Profil und Admin | Lebensdauer des Kontos | Zeile entfernt | Tombstone in Audit-/gesetzlichen Zeilen; Marker andernorts | referenziert von ca. 30 Feldern (§3.3–3.6) |
| ⟂ | `users.email` | IDN | ja | Login, Benachrichtigungen | 6(1)(b) | selbst; `management` + Plattform-Admin ([v] heute jedes Mitglied über `/members` — PRIV-305) | Lebensdauer; R-01 dann weg | entfernt | — | `invitations.email`, `email_change_requests`, Art.-15-Bündel |
| ⟂ | `users.display_name` | PRO | ja | Anzeige, wer | 6(1)(b) | Mitglieder gemäß Matrix `05` | Lebensdauer | entfernt | Darstellung zeigt `former_member`/`erased` | in jede Zurechnungsdarstellung aufgelöst; `members.jsonl` des Mandantenexports |
| | `users.avatar_url`, `locale`, `timezone` | PRO | ja | UI | 6(1)(b) | selbst | Lebensdauer | entfernt (Avatar-Objekt: Speicherregel `user_personal`) | — | — |
| | `users.password_hash`, Hashes der Verifizierungs-/Reset-Token, `session_generation`, `access_token_generation` | AUTH | ja | Authentifizierung | 6(1)(b) | keine | Lebensdauer; Hashes R-08/R-09 | entfernt; `password_hash` bei Anfrage genullt | — | — |
| | `users.is_active`, `email_verified`, `email_confirmed_at`, `failed_login_attempts`, `locked_until`, `last_login_at` | AUTH | ja (Verhalten) | Sicherheit | 6(1)(f) | selbst/Admin | Lebensdauer | entfernt | — | Sicherheits-Audit-Einträge halten Flag-Änderungen fest |
| | `users.account_type` (`human`/`service`) | PRO | nein (Typ) | — | — | — | — | — | — | Darstellungszustand `service_account` |
| | `auth_providers`, `refresh_tokens` (inkl. `ip_address` R-03, `device_info`) | AUTH | ja | Sitzungen | 6(1)(b)/(f) | keine | Token-Ablauf; IP 7 d | gelöscht | IP anonymisiert | — |
| | `api_keys` (Hash, Label, IP-Allowlist, `tenant_scope`) | AUTH | ja (Label, IPs) | M2M | 6(1)(b) | Eigentümer, `technical` | Lebensdauer des Schlüssels | gelöscht; mandantengebundene Schlüssel mit dem Mandanten | — | `mcp_audit_log` verweist darauf |
| | `user_preferences`, `onboarding_states`, `notification_preferences` (Push-`subscriptions`) | PRO | ja | UI, Zustellung | 6(1)(b) | selbst | Lebensdauer | gelöscht | — | — |
| | `memberships.{user_key, tenant_key, role, admin_scopes, is_active, joined_at}` | IDN | ja | Mandantenzugriff | 6(1)(b) | Mitglieder (`/members`), Plattform-Admin | bis Ende der Mitgliedschaft (Zeile gelöscht) | gelöscht | — | `security_audit_log` (alte Rolle 730 d); `members.jsonl` |
| | `invitations.{email, invited_by_user_key, accepted_by_user_key}` | IDN/ATTR | ja | Onboarding | 6(1)(b) | `management` | R-12 30 d | `invited_by` → Marker; angenommene Zeilen gelöscht | Marker | — |
| | `location_assignments` | ATTR (`assigned_to`) | ja | Zuständigkeitshinweis (REQ-049 §3.5) | 6(1)(b) | Mitglieder ([v]; `(t)` nach PRIV-309) | mit der Mitgliedschaft | gelöscht | — | Beetlisten-CSV `include_assignment` |

### 3.2 Datenschutz- und Audit-Zustand (Verantwortlicher: Betreiber)

| ⟂ | Entität.Feld | Kat | Personenbezogen? | Zweck | Rechtsgrundlage | Sichtbarkeit | Aufbewahrung | Löschung | Anonymisierung | Herkunft |
|---|--------------|-----|-------------|---------|-------------|------------|-----------|---------|---------------|---------|
| ⟂ | `erasure_requests.{user_key, status, step_up, requested_by_subject, members_notified_at, …}` | CONS/AUD | ja → pseudonymisiert | Nachweis Art. 5(2) | 6(1)(c) | selbst (Status), Plattform-Admin | R-06 3 J | `user_key` → Tombstone | Tombstone | `erasure_mirror` (Tombstone, kein Rohschlüssel; `09` §6) |
| | `data_export_requests`, Export-Bündel `privacy/exports/<user_key>/<key>.json` [v nur Objektschlüssel mit einem Benutzerschlüssel] | CONS | ja | Art. 15/20 | 6(1)(c) | selbst | R-05 72 h | gelöscht | — | — |
| | `processing_restrictions`, `email_change_requests` | CONS | ja | Art. 18/16 | 6(1)(c) | selbst | R-13 unbegrenzt / R-07 | gelöscht | — | — |
| ⟂ | `consent_records.{user_key, purpose, granted, ip, user_agent, revoked_at}` | CONS | ja | Art. 7(1) | 6(1)(c) | selbst, Plattform-Admin | R-04 3 J nach Widerruf; IP 7 d | `user_key` → Tombstone, `user_agent` geleert | Tombstone | — |
| ⟂ | `security_audit_log.{actor_user_key, target_user_key, tenant_key, membership_key, old/new role & scopes, request_id}` | AUD (`actor`) | ja | Art. 32 | 6(1)(c)/(f) | Plattform-Admin | R-38 730 d | Schlüssel → Tombstone; Zeile bleibt bei Mandantenlöschung behalten | Tombstone | neue Aktionen `04` §4.2 |
| | `mcp_audit_log.{service_account_key, shortened IP}` | AUD | ja | Art. 32 | 6(1)(f) | selbst (`/privacy/mcp-activity`), Admin | 90 d | → Tombstone | Tombstone | — |
| | `ai_audit_log.user_key`, `ai_conversations.{user_key, title, content}` | AUD/TXT | ja | KI-Funktionen | 6(1)(a) Einwilligungszwecke | selbst | je Einstellung | Audit → Marker; Konversationen gelöscht | Marker | — |
| | `tenant_erasure_records`, `tenant_export_requests.requested_by_user_key`, `tenant_import_requests.requested_by_user_key`, `import_jobs.uploaded_by` | AUD/ATTR | ja | Nachweis / Betrieb | 6(1)(c)/(b) | `management`, Admin | R-06a / R-40 30 d (nicht implementiert) | → Marker | Marker | — |
| ⟂ | **neu** `privacy_review_items.{tenant_key, erasure_key, collection, row_key, fields[], match_kinds[], status, decision, decided_by, reason_code, reason_text}` | AUD | ja (`decided_by`; `reason_text` Freitext) | Folgemaßnahme zu Art. 17 | 6(1)(c) | Mandanten-`lead`/`management`; Admin zählt | R-43 3 J nach Entscheidung; mit Mandant | `decided_by` → Marker | Marker | speichert **keinen** Text/Token/Betroffenenschlüssel (PRIV-221) |
| ⟂ | **neu** `erasure_mirror.{kind, tombstone, tenant_key, erasure_key, completed_at, chain_hmac}` (DEC-26; ersetzt das Raw-Key-Ledger aus v1.0) | AUD (pseudonym) | ja — **pseudonymisiert, kein Rohschlüssel** | Löschung nach Wiederherstellung erneut anwenden (Tombstone-Abgleich, `09` §6.2) | Art. 17 Durchsetzung (6(1)(c)) — LEG-11 | keine (nur Restore-Prozess; Bucket-Objekt Fernet-verschlüsselt) | R-45 = R-06 (3 J.) | harte Löschung per Beat; Spiegel-Objekt gefiltert neu geschrieben | — | Spiegel der `erasure_requests`-Tombstones |
| | **neu** `migration_reports` | — | nein (nur Zähler, Collection-/Feldnamen, Mandanten-/Zeilenschlüssel; Redaktionsfilter PRIV-701) | Betreibernachweis | — | Betreiber | unbegrenzt | — | — | — |

### 3.3 Pflegeprotokoll und Gartenplan (Verantwortlicher: Mandant)

| ⟂ | Entität.Feld | Kat | Personenbezogen? | Zweck | Rechtsgrundlage | Sichtbarkeit (`05`) | Aufbewahrung | Löschung | Anonymisierung | Herkunft / Kopien |
|---|--------------|-----|-------------|---------|-------------|-------------------|-----------|---------|---------------|------------------|
| ⟂ | `care_events.performed_by_user_key` | ATTR `performed_by`, optional | ja | Koordination, Rechenschaft | 6(1)(f) LIA-1 | P (t) | R-25 5 J → Marker | Marker | Marker | aus Aufgabenabschluss (`CompletionActor`), Bestätigungs-Principal, Backfill `account_of` (Tombstone → Marker, PRIV-205); Supersede behält den des Vorgängers |
| ⟂ | `care_events.performed_for_user_key` | ATTR `performed_for` | ja | Stellvertretereintrag | 6(1)(f) | P (t) | R-25 | Marker | Marker | — |
| ⟂ | `care_events.created_by` | ATTR `created_by` | ja | Rechte an eigenen Zeilen, Audit | 6(1)(f) | C: nur `created_by_me` | R-25 | Marker | Marker | `null` beim Backfill (System) |
| ⟂ | `care_events.voided_by`, `redacted_by` | ATTR `modified_by` | ja | Audit | 6(1)(f) | M | R-25 | Marker | Marker | — |
| ⟂ | `care_events.performed_by_label` (≤ 80 Eingabe, 200 gespeichert [v]) | TXT (Dritte) | ja — **Dritte** | Helfer ohne Konto benennen | 6(1)(f); Art.-14-Information durch den Mandanten | alle Mitglieder | R-25 → `[redacted]` | behalten; **Prüfung** | Schwärzung | CSV-Spalte `performed_by` |
| ⟂ | `care_events.summary` (≤ 500), `reason` (≤ 1000), `observed_outcome` (≤ 2000), `product_label` (≤ 200), `void_reason`, `redaction_reason` | TXT | kann | Protokoll | 6(1)(b)/(f) | alle Mitglieder | R-25 → `[redacted]` | behalten; **Prüfung** | Schwärzung (lead/management) | CSV; `garden_plan_audit` kopiert nie Text [v] |
| ⟂ | `care_events.material` (≤ 200) | TXT | kann | Protokoll | 6(1)(b) | alle Mitglieder | **heute nicht in der R-25-Menge [v] → PRIV-213** | behalten; **Prüfung** | Schwärzung | CSV `material` |
| | `care_events.measurements[].source`, `.extraction_method` | TXT | kann | Protokoll | 6(1)(b) | Mitglieder | in die Menge aufnehmen (PRIV-213) | behalten; Prüfung | Schwärzung | — |
| | `care_events.photo_refs` | MED | kann (Personen auf Fotos) | Protokoll | 6(1)(b)/(f) | Mitglieder | R-25 → gelöscht | behalten (Anhangsregeln) | Schwärzung löscht | `attachments` |
| | `care_events.client_event_id`, `client_event_digest`, `client_round_id` [v, Welle 9] | — | Digest mit `erasure_tombstone_salt` geschlüsselt; enthält `user` in der Digest-Eingabe → pseudonym | Replay-Deduplizierung | 6(1)(b) | keine | mit der Zeile | mit der Zeile | — | `client_event_tombstones` (nur IDs) |
| | `care_events.{tenant_key, site_key, location_key, plant_keys, category, performed_at, trigger, task_key, source_ref, quantity…}` | — | kontextuell (Zeitmuster) | Protokoll | 6(1)(b) | Mitglieder | R-25 (nach Anonymisierung behalten) | behalten | — | `source_ref` = Herkunft zur Quell-Collection |
| ⟂ | `care_confirmations.{plant_key, reminder_type, action, confirmed_at, notes, task_key, completion_client_event_id}` | TXT (`notes`) | kann; **kein Akteursfeld [v]** | Erinnerungszustand | 6(1)(b) | Mitglieder | **keine [v]**; mit Mandant | nicht erreicht (kein Kontofeld) | — | abgeleitetes `care_events(trigger=reminder)` trägt den Akteur |
| ⟂ | `garden_plan_audit.user_key` | ATTR `actor` | ja | Änderungsprotokoll | 6(1)(f) | M: `changed_by` ([v] alle Mitglieder sehen den Namen) | R-26 365 d | **heute Tombstone → Marker (DEC-16)** | Marker | — |
| ⟂ | `garden_plan_audit.summary` (≤ 200), `snapshot` | TXT | kann (Kopien von Namen/Labels/Notizen) | Änderungsprotokoll, Wiederherstellung | 6(1)(f) | alle Mitglieder | R-26 | behalten; **Prüfung** | Schwärzung (Blatt-Allowlist) | Kopien von `Location.name`, `GardenObject.label`, `Site.name`, Zonenname; Snapshot = Planexport |
| ⟂ | `garden_objects.created_by` | ATTR `created_by` | ja | Urheberschaft | 6(1)(f) | C | Lebensdauer | Marker | Marker | — |
| ⟂ | `garden_objects.label` (≤ 200), `notes` (≤ 4000) | TXT | kann | Plan | 6(1)(b) | Mitglieder | Lebensdauer | behalten; **Prüfung** | Schwärzung | SVG-/PDF-/JSON-Export, Audit-Zusammenfassung |
| ⟂ | `bed_templates.created_by` | ATTR `created_by` | ja | Urheberschaft | 6(1)(f) | C | Lebensdauer | Marker | Marker | — |
| ⟂ | `bed_templates.name` (≤ 200) | TXT | kann („Omas Hochbeet") | Katalog | 6(1)(b) | Mitglieder; **exportiert über GP-API-070 Template-Austausch [v Spec: „ohne Personenbezüge"]** | Lebensdauer | behalten; **Prüfung** | Schwärzung mit Herkunftsbatch (PRIV-230) | → `locations.name` bei `place_template`; → Audit-`summary`; → Template-Exportdatei |
| ⟂ | `locations.name` (kein gespeichertes Maximum [v]), `description` (≤ 1000), `notes` (≤ 4000), `soil_profile.notes` | TXT | kann | Plan | 6(1)(b) | Mitglieder; SVG/PDF/JSON; **Plan-Cache lässt notes/description weg [v]** | Lebensdauer | behalten; **Prüfung, wenn aus dem Template einer gelöschten betroffenen Person erstellt oder in einem Prüftreffer genannt** | Schwärzung | Herkunft `template_key`; Audit-Zusammenfassung |
| | `locations.photo_refs`, `cover_photo_ref` | MED | kann | Beetfotos | 6(1)(b)/(f) | Mitglieder | Lebensdauer | Anhangsregel | — | `attachments` |
| ⟂ | `sites.plan.plan_updated_by` | ATTR `modified_by` | ja | Plan | 6(1)(f) | M | Lebensdauer | Marker | Marker | Plan-Cache nullt `plan_updated_by_name` [v] |
| ⟂ | `sites.{name, climate_zone}` | TXT | kann | Plan | 6(1)(b) | Mitglieder | Lebensdauer | behalten; Prüfung bei Treffer | Schwärzung | Audit-Zusammenfassung |
| | `irrigation_zones.name` | TXT | unwahrscheinlich | Plan | 6(1)(b) | Mitglieder | Lebensdauer | behalten | — | Audit-Zusammenfassung |
| | `tasks.assigned_to_user_key` | ATTR `assigned_to` | ja | Zuständigkeit | 6(1)(b) | Mitglieder (`(t)` für den Namen) | bis erledigt / Ende der Mitgliedschaft (geleert) | Marker | Marker | Plan-Cache nullt den Zugewiesenen [v] |
| ⟂ | `tasks.{name (≤200), instruction, suggestion_reason, completion_notes, timer_label, tags}` | TXT | kann | Arbeit | 6(1)(b) | Mitglieder | **keine [v] → R-47-Vorschlag** | behalten; Prüfung für Zeilen mit Zugewiesenen | Schwärzung | Benachrichtigungen tragen Aufgabennamen [v]; `care_events` über Abschluss (`reason`, `material`) |
| | `tasks` — `created_by`/`completed_by` | — | **existieren nicht [v]** | — | — | — | — | — | — | Abschließende/r nur als `care_events.performed_by_user_key` |
| ⟂ | `task_comments.{created_by, comment_text (≤2000)}` | ATTR/TXT | ja/kann | Diskussion | 6(1)(b) | Mitglieder | keine → R-47 | Marker; Prüfung | Schwärzung | — |
| | `task_audit_entries.changed_by` | ATTR | immer `'system'` [v Ausschlusshinweis] | — | — | — | — | ausgeschlossen | — | — |
| | `workflow_templates.created_by` | TXT (Freitext, kein Schlüssel [v]) | kann | — | 6(1)(b) | Mitglieder | Lebensdauer | heute ausgeschlossen → **Prüffeld** (PRIV-212) | Schwärzung | — |

### 3.4 Pflanzenpflegeprotokolle und gesetzliche Aufzeichnungen (Verantwortlicher: Mandant)

| ⟂ | Entität.Feld | Kat | Personenbezogen? | Zweck | Rechtsgrundlage | Sichtbarkeit | Aufbewahrung | Löschung | Anonymisierung | Herkunft |
|---|--------------|-----|-------------|---------|-------------|------------|-----------|---------|---------------|---------|
| ⟂ | `harvest_batches.harvested_by_key` | ATTR `performed_by`, **Pflicht im gesetzlichen Profil** | ja | Ernteaufzeichnung | 6(1)(c) (R-16, falls LEG-03) sonst 6(1)(b) | P | ≥ 5 J ab `harvest_date` | → Tombstone (gesetzlich) / Marker (`record_keeping=none`) | Pseudonym | aus der Abschluss-Engine `event.performed_by_user_key` |
| ⟂ | `harvest_batches.harvester` (≤ 200, Freitext) | TXT (eingetippter Name) | ja | Altfeld für Namen | — | Mitglieder (`HarvestBatchResponse` [v]) | — | **geleert** [v] | geleert | Zeilen vor #1669: `*_by_key = null`, Name bleibt → Alt-Prüfeintrag (PRIV-233) |
| | `harvest_batches.notes` | TXT | kann | Protokoll | 6(1)(c)/(b) | Mitglieder | R-16 | behalten (gesetzlich) / Prüfung (`none`) | Schwärzung nur, wenn nicht gesetzlich | — |
| ⟂ | `quality_assessments.{assessed_by_key, assessed_by, notes}` | wie oben | | | R-16 | | | wie Ernte | | |
| ⟂ | `treatment_applications.{applied_by_key, applied_by, notes, applied_at, dosage, product}` | ATTR/TXT | ja | Aufzeichnung nach PflSchG §11 (beruflich) | 6(1)(c) falls LEG-03 | P; Mitglieder | ≥ 3 J | Tombstone + Name geleert [v] — **LEG-04** | Pseudonym | → `care_events(pest_control)` per Backfill (Ausführende/r übernommen, PRIV-205) |
| ⟂ | `inspections.{inspected_by_key, inspector, notes}` | wie oben | ja | Überwachung nach PflSchG | R-18 | | ≥ 3 J | wie Behandlung | | MCP schreibt `inspector = "mcp:<key>"` [v] → PRIV-310 |
| | `watering_events.{performed_by (Freitext), notes}`, `watering_logs.{performed_by, notes}`, `tank_fill_events.{performed_by, notes}`, `maintenance_logs.{performed_by, notes}` | TXT (eingetippter Name) | ja (Name) | Betrieb | 6(1)(b) | Mitglieder; in der UI editierbar [v] | **keine [v] → R-46** | **ausgeschlossen [v] (Freitext)** → **auf Schlüsselfeld + Label migrieren** (`08` §3.4) | nach Migration: Marker | → `care_events(watering/feeding)` ohne Ausführende/n [v] |
| | `feeding_events.{notes, material}` | TXT | kann | Betrieb | 6(1)(b) | Mitglieder | keine → R-46 | behalten | — | → `care_events(feeding)` |
| | `nutrient_plans.author` (Freitext, **kein Maximum [v]**), `propagation.*.author` | TXT (eingetippter Name) | ja | Urheberschaft | 6(1)(b) | Mitglieder; **auf dem Nährstoffplan-PDF gedruckt [v]** | Lebensdauer | **in keiner Regel [v]** → Schlüsselfeld + Label (`08` §3.4) | Marker | Druckvorlage |
| ⟂ | `plant_diary_entries.{created_by, analysis_requested_by, analysis_claimed_by}` | ATTR | ja | Pflanzenprotokoll | 6(1)(b)/(f) | C (t); alle Mitglieder lesen Einträge [v] | Lebensdauer | Marker [v] | Marker | — |
| ⟂ | `plant_diary_entries.{title (≤200), text (≤5000), tags, analysis.summary, analysis.findings}` | TXT | kann | Pflanzenprotokoll | 6(1)(b) | alle Mitglieder; `GET /diary?q=` Teilstringsuche [v] | Lebensdauer | behalten [v]; **Prüfung** | Schwärzung | KI-Analyse aus Text abgeleitet (Einwilligung `diary_ai_analysis`) |
| | `plant_diary_entries.photo_refs` | MED | kann | Protokoll | 6(1)(b) | Mitglieder | Lebensdauer | Speicherbereich `user_diary_attachments` (Bytes behalten, `created_by` Marker, EXIF erneut entfernt) | — | `attachments` |
| | `plant_instances.plant_name`, `planting_runs.{name, notes}`, `propagation.{name, notes, PhenotypeNote.note}`, `post_harvest.*notes`, `succession_plan.notes`, `aquaponik.*`, `care_profiles.notes`, Aktor-/Zeitplan-`notes`, `manual_overrides.reason` (≤500) | TXT | kann (gering) | Domäne | 6(1)(b) | Mitglieder | Lebensdauer | behalten; `manual_overrides.created_by` → Marker [v] | Prüfung nur bei Namenstoken-Treffer | — |

### 3.5 Medien und Anhänge

| ⟂ | Entität.Feld | Kat | Personenbezogen? | Zweck | Rechtsgrundlage | Sichtbarkeit | Aufbewahrung | Löschung | Anonymisierung | Herkunft |
|---|--------------|-----|-------------|---------|-------------|------------|-----------|---------|---------------|---------|
| ⟂ | `attachments.created_by` | ATTR `created_by` | ja | Eigentum | 6(1)(b) | C | Lebensdauer des Elternobjekts | Marker (Speicherbereich) / `pest_reference` gelöscht / `user_personal` gelöscht [v] | Marker | geteilte Bytes (Deduplizierung je Beitragende/n seit #1770, Art.-19-Mitteilung AK-OS-09 **nicht implementiert**) |
| ⟂ | `attachments.original_filename` | TXT (identitätstragend) | oft | Echo des Uploads | 6(1)(b) | Mitglieder; Art.-15-Bündel | Lebensdauer | **heute behalten [v] → geleert (PRIV-211)** | geleert | v0062 leert es bei geteilten Datensätzen [v] |
| ⟂ | `attachments.caption` (≤ 500) | TXT | kann | Galerie | 6(1)(b) | Mitglieder | Lebensdauer | behalten; **Prüfung** | Schwärzung | — |
| | Anhang-Bytes (Fotos; EXIF beim Upload entfernt und bei Löschung erneut entfernt [v]; Speicherschlüssel `t/{tenant}/{category}/{yyyy}/{mm}/{ulid}` — kein Benutzer im Pfad [v]) | MED | kann (Gesichter, Orte) | Protokoll | 6(1)(b)/(f) | Mitglieder; Thumbnails | Lebensdauer des Elternobjekts | behalten für geteilte Kategorien; `user_personal`/Schädlingsreferenz gelöscht | — | Renditions |
| | `attachments.client_event_id/_digest` [v Welle 9] | — | pseudonym | Replay | 6(1)(b) | keine | mit der Zeile | mit der Zeile | — | — |
| | `pest_image_contributions.{contributed_by, promoted_by}`, pgvector `species_embeddings(source='user_contributed', contributed_by, tenant_key)` | ATTR/SENS | ja | Erkennungsindex (Einwilligung) | 6(1)(a) | Admin | bis Widerruf / Löschung | gelöscht / `promoted_by` Marker [v] | Marker | — |

### 3.6 Standort- und Sensordaten

| ⟂ | Entität.Feld | Kat | Personenbezogen? | Zweck | Rechtsgrundlage | Sichtbarkeit | Aufbewahrung | Löschung | Anonymisierung | Herkunft |
|---|--------------|-----|-------------|---------|-------------|------------|-----------|---------|---------------|---------|
| ⟂ | `sites.gps_coordinates` | LOC | **ja** — persönlicher Garten = Wohnadresse (REQ-025 §3.1.2) | Wetter, Frost, Klimazone | 6(1)(b); Koordinaten vor dem Verlassen auf 2 Dezimalstellen gerundet (DP-002) | Mitglieder; Art.-15-Bündel; **Mandantenarchiv (LEG-13)**; GeoJSON WON'T [v] | Lebensdauer des Standorts | mit persönlichem Mandanten; bleibt im geteilten Mandanten | — | Wetteranfragen (gerundet) |
| | `sensor_readings` (TimescaleDB: `tenant_key`, `sensor_key`, Wert, `source`, `metadata` JSONB) — **keine Benutzerspalte [v]**; `metadata` ist ein freies Client-Dict [?] | SENS | kontextuell (CO₂/Bewegung/manuelle Übersteuerung → Anwesenheitsmuster; NFR-001 §6.7 DSFA) | Überwachung | 6(1)(b) | Mitglieder | 90 d roh → 2 J stündlich → 5 J täglich (festes SQL; R-14-Klassifizierung **nicht implementiert [v]**) | mit Mandant (`delete_by_tenant`) | — | Aggregate |
| | `manual_overrides.{created_by, reason}` | ATTR/TXT | ja | Aktor-Übersteuerung (Anwesenheitssignal) | 6(1)(b)/(f) | Mitglieder | keine | Marker [v]; Prüfung | Schwärzung | — |

### 3.7 Benachrichtigungen

| ⟂ | Entität.Feld | Kat | Personenbezogen? | Zweck | Rechtsgrundlage | Sichtbarkeit | Aufbewahrung | Löschung | Anonymisierung | Herkunft |
|---|--------------|-----|-------------|---------|-------------|------------|-----------|---------|---------------|---------|
| ⟂ | `notifications.{user_key, title, body, data, read_at, acted_at}` | ATTR `recipient` / TXT | ja | Zustellung | 6(1)(b) | Empfänger/in | **keine [v] → R-48-Vorschlag** | gelöscht [v] | — | Texte tragen Aufgaben-/Pflanzennamen, keine Mitgliedsnamen [v Messung] |
| | `notification_preferences.pwa.subscriptions`, Apprise-URLs (Fernet) | AUTH | ja | Kanäle | 6(1)(b) | selbst | Lebensdauer | gelöscht | — | — |

### 3.8 Daten auf dem Gerät (Verantwortlicher: Betreiber für Standardwerte; siehe `07`)

| ⟂ | Speicher.Schlüssel | Kat | Personenbezogen? | Zweck | Rechtsgrundlage (TDDDG §25 / DSGVO) | Aufbewahrung | Beim Logout geleert? [v] | Erforderlich |
|---|-----------|-----|-------------|---------|--------------------------------|-----------|------------------------|----------|
| ⟂ | IndexedDB `kp-plan-cache` (`{key, userKey, tenantKey, cachedAt, data}`; keine Namen, Notizen, Zuweisungen [v]) | DEV | ja (Schlüssel, Plan) | Offline-Lesen | §25(2) Nr. 2 unbedingt erforderlich — **Vorschlag, LEG-09**; 6(1)(b) | 15 min TTL; bereinigt bei Start/Lesen/Schreiben | alle Datenbanken außer der Queue gelöscht | behalten |
| ⟂ | IndexedDB `kp-write-queue` (`id`, `userKey`, `tenantKey`, `capturedAt`, `status`, `write` inkl. Notiztext und Fotobytes, `bedName`) | DEV/TXT/MED | ja | Offline-Schreibvorgänge | wie oben | 365 d ausstehend / 90 d nicht sendbar | nur die Zeilen der ausscheidenden Person, nach Bestätigung | verkürzen + Quarantäne (`07`) |
| ⟂ | Cache Storage `kp:{user_key}:{tenant_key}` (latent, leer [v]), `kp-sw-state` | DEV | Schlüssel | SW-Cache | wie oben | 15 min / Sitzung | gelöscht | behalten; die Persist-Race beheben (`07`) |
| | Cache Storage Precache, `kp-static-assets`, `kp-runtime-config` | — | nein | App-Shell | erforderlich | — | behalten | — |
| ⟂ | localStorage `kp_local_data_owner` (**ein `user_key`** [v]) | DEV/IDN | ja | Eigentümerprüfung lokaler Daten | erforderlich | — | **nein [v]** → leeren (PRIV-512) | |
| ⟂ | localStorage `kp-garden-field-mode` (`userKey`, `tenantSlug`, `siteKey`, Tab) | DEV/IDN | ja | Wiederaufnahme des Feldmodus | erforderlich | — | **nein [v]** → leeren | |
| ⟂ | sessionStorage `kp.emailChange.address` (**E-Mail**), `kp.stepUp.{token,resume,error}` | DEV/IDN/AUTH | ja | Abläufe | erforderlich | ablaufgebunden | **nein [v]** → leeren | |
| | localStorage `kp_active_tenant_slug` | DEV | Slug (kann aus einem Namen abgeleitet sein) | Routing | erforderlich | — | ja | — |
| | localStorage `kp.gardenPlanner.planting.lastUsed.{tenantSlug}` | DEV | Mandanten-Slug im Schlüssel | UX | erforderlich | — | nein | beim Logout leeren (Hygiene) |
| | localStorage `kamerplanter:consent:v1`, `plant_identification_consent` | CONS | nur Entscheidung | Einwilligung | erforderlich | — | nein (muss erhalten bleiben) | behalten |
| | localStorage Theme/Sprache/Kiosk/Layout/Modulsichtbarkeit/Seitengrößen/ausgeblendete Tipps/Editor-Einstellungen | DEV | nein | UX | erforderlich | — | nein | behalten |
| | sessionStorage `kamerplanter.pendingInvitation` | AUTH | Token | Onboarding | erforderlich | Ablauf | ja | — |
| | Refresh-Cookie (HttpOnly [Spec; von der Analyse im Backend-Code nicht verifiziert]), CSRF-Cookie | AUTH | ja | Authentifizierung | erforderlich | 30 d | widerrufen | — |

**Nicht vorhanden [v]**: `redux_state` in sessionStorage (Zeile in REQ-025 §10 ist veraltet), `i18next`-/
`theme`-Schlüssel (tatsächliche Schlüssel `kamerplanter-lang`, `kamerplanter-theme`), `device_id` (R-049b
nicht implementiert), jegliche API-Nutzlast in localStorage (G-W9 a hält).

---

## 4. Felder, die die Aufgabe nannte, die aber **nicht** existieren (nicht erfinden)

| Genannt | Befund |
|-------|---------|
| `care_events.note` | kein solches Feld; Notizen gehen in `summary`/`reason` |
| `care_events.origin` als gespeichertes Feld | nur serverseitige Dataclass `CareEventOrigin` |
| `tasks.created_by`, `tasks.completed_by` | nicht vorhanden |
| `CareConfirmation.<actor>` | nicht vorhanden |
| `plant_diary_analyses` | Collection existiert nicht (REQ-051 §5 / REQ-025 AK-DA-04 zielen auf ein Phantom) |
| `TenantType.community/commercial` | nur `personal`/`organization` |
| `Membership.status/left_at` | nicht vorhanden |
| `users.deleted_at/status/name` | nicht vorhanden |
| `plant_instances.nickname` | das Feld heißt `plant_name` |
| `client_event_id` bei `tasks` | gespeichert als `tasks.completion_client_event_id` (Index v0106) [v] |

---

## 5. Herkunft (Quelle → abgeleitete Kopien)

**PRIV-031** Die folgenden Kopien MÜSSEN in `DERIVED_FIELDS` (`08` §2.4) mit einer
Propagierungsregel deklariert werden; der Guard R8 prüft, dass jeder Schreiber eines abgeleiteten Felds aufgeführt ist.

| Quelle | Abgeleitet | Kopiersemantik | Propagierung bei Löschung / Schwärzung |
|--------|---------|----------------|------------------------------------|
| `treatment_applications.applied_by_key`, `harvest_batches.harvested_by_key` | `care_events.performed_by_user_key` (Backfill, Konsistenz) | Kontoreferenz, gleiche Rolle | `carry_account_reference` (Tombstone → Marker); die Löschregel erreicht die Kopie über den Schlüssel |
| `care_events.performed_by_user_key` (Aufgabenabschluss) | `harvest_batches.harvested_by_key` | gleiche Rolle | beide von ihren eigenen Regeln erreicht |
| `care_events.performed_by_user_key` (Vorgänger) | `care_events.performed_by_user_key` (Supersede) | gleiche Rolle | Kettenschwärzung (vorhanden) |
| `bed_templates.name` | `locations.name` (`place_template`) | Inhaltskopie; `template_key` hält die Herkunft | Vorschlag eines Prüfbatches (PRIV-230) |
| `locations.name`, `garden_objects.label`, `sites.name`, `irrigation_zones.name` | `garden_plan_audit.summary` | Inhaltskopie zum Löschzeitpunkt | Prüfung; schwärzbar |
| Planexport (`locations.*`, `garden_objects.*`) | `garden_plan_audit.snapshot` (Import) | vollständige Kopie | Blattschwärzung |
| `users.display_name` | jede Darstellung; `members.jsonl` (Mandantenarchiv); CSV `performed_by`; `changed_by_name` | Live-Auflösung (keine gespeicherte Kopie) außer Archiv-/CSV-Dateien | Archive laufen ab (R-05 72 h); CSV gehört dem Empfänger |
| `task.completion_notes`, `TaskCompletionDetails.{reason, material}` | `care_events.{reason, material}`; `care_confirmations.notes` | Inhaltskopie | beide in Prüfmengen |
| Anhang-Bytes | Renditions, geteilte Datensätze (Deduplizierung) | Bytes | Art.-19-Mitteilung (nicht implementiert) |
| `tenants.slug` (kann aus einem Namen abgeleitet sein) | `kp_active_tenant_slug`, URLs, Logs (`ten_`-Pseudonym) | — | Slug-Umbenennung nicht im Umfang |

### 5a. Ableitungswege, die eine statische Quellcode-Prüfung nicht erfasst (PRIV-609/610; DA-Lineage)

| Weg | Beispiel [VERIFIED_CODE] | Mechanismus | Löschverhalten |
|-----|---------------------------|-------------|----------------|
| Direkte Feldkopie | Backfill-Mapper, Task-Completion-Engine | `DERIVED_FIELDS` + Guard R8 + `source_ref` an der Zielzeile | `carry_account_reference`; Löschregel am Ziel |
| Modelltransformation | `storedProjection` (Plan-Cache), `CareEventView`/`display_performer` | Projektion ohne Persistenz serverseitig; clientseitig TTL | TTL / Wipe (`07`) |
| Event-Handler | Bestätigung → `care_events(trigger=reminder)` in derselben Transaktion | `source_ref` = `care_confirmations/<key>`; registriert | Löschregel am Ziel |
| Hintergrundjobs | `care_events.consistency` (täglich), Retention-Beats, Frost-Warnungen (Benachrichtigungen) | registriert; Laufzeit-Provenienz `source_ref`; Benachrichtigungen ohne Mitgliedsnamen | R-48 (Benachrichtigungen) |
| API-Schreibpfade | `harvested_by_key = event.performed_by_user_key` | registriert (gleiche Rolle) | eigene Regel |
| Exporte | Art.-15-Bundle, Pflegeereignis-CSV, Plan-JSON/SVG/PDF, Mandantenarchiv, Vorlagen-Austauschdatei (GP-API-070) | flüchtig; Lebensdauerregel (R-05 72 h; Download gehört dem Empfänger; Audit PRIV-308) | Ablauf / außerhalb des Systems (Information in der Datenschutzerklärung) |
| Benachrichtigungen | `notifications.{title, body, data}` | Texte tragen Aufgaben-/Pflanzennamen, keine Mitgliedsnamen [VERIFIED_CODE Messung REQ-025 Regel 8] | gelöscht bei Löschung; R-48 |
| Offline-Puffer/-Cache | `kp-write-queue`, `kp-plan-cache` | clientseitig; Opt-in (`07` §2.1); Projektion ohne Namen | TTL, Quarantäne, Übergang |
| Materialisierte Sichten | TimescaleDB Continuous Aggregates (`sensor_hourly`, `sensor_daily`) | keine Kontoreferenz | `delete_by_tenant` |
| Audit-Snapshots | `garden_plan_audit.snapshot` (Import), `summary` | `derived_from` (neu) | Blatt-Schwärzung (PRIV-229), R-26 |
| Spiegel/Backups | `erasure_mirror`, Dumps | Tombstones / vollständige Kopien | R-45; Restore-Replay (`09` §6) |

---

## 6. Durch das Inventar gefundene Lücken (Faktenliste; Lösung in `04`–`09`, `12`)

1. Tombstones in `care_events.performed_by_user_key` über `account_of` erreichbar (#2770) — **behoben #2839**
   (Mapper + v0107, VERIFIED_CODE); die übrigen Kopierstellen (`task_completion_engine`, `garden_plan_audit`) offen.
2. Freitext wird bei der Löschung nie geleert oder aufgelistet; Schwärzung nur für Pflegeereignisse, nur lead,
   keine UI-Aktion über einen Chip hinaus; keine Liste betroffener Zeilen.
3. `care_events.material`, Messwert-Strings außerhalb der Schwärzungsmenge.
4. `original_filename` und `caption` überleben die Löschung; `nutrient_plans.author` und die
   `performed_by`-Freitextfelder der Gieß-/Tank-Protokolle liegen außerhalb jeder Regel.
5. `garden_plan_audit` behält Freitextkopien und einen Tombstone; die UI verwirft `null`-Akteure.
6. Keine Aufbewahrung für `notifications`, `watering_events`/`feeding_events`/Tankprotokolle, Aufgaben und
   Kommentare, `care_confirmations`.
7. Das Ende einer Mitgliedschaft hat keine datenschutzrechtliche Wirkung; kein `left_at`; der Name wird für immer aufgelöst.
8. Geschlossene Konten lösen ihren Anzeigenamen noch bis zu 90 Tage auf.
9. Jedes Mitglied sieht die E-Mail jedes Mitglieds.
10. Das MCP-Tagebuch-Tool gibt rohes `users._key` zurück; MCP-Inspektionen schreiben `inspector = "mcp:<key>"`.
11. Gesetzliche Regeln gelten für jeden Mandanten; `CanG §X` unspezifiziert.
12. Mehrere `localStorage`-/`sessionStorage`-Schlüssel mit einem `user_key` oder einer E-Mail überleben das
    Logout; REQ-025 §10 listet veraltete/nicht existierende Schlüssel und übersieht vorhandene.
13. Keine Backups → kein Verfahren für Löschung nach Wiederherstellung; wenn Backups kommen, wendet nichts
    Löschungen erneut an.
14. Keine Datenschutz-Betriebsmetriken oder Listen-Endpunkt; „Gauge" ist ein Logfeld.
15. Marker-/Regex-Konstanten dupliziert.
16. `security_audit_log` hat keine Aktion für Löschung/Export/Einwilligung/Schwärzung.
