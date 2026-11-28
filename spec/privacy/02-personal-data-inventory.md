# SPEC-02 — Inventar personenbezogener Daten

```
Paket: spec/privacy · Version 1.2 · 2026-11-22 · gemessen gegen develop 24d1c2988; Nachtrag #2839 (develop 343afbb97);
Nachtrag #2976 (2026-11-16, develop 9809d3952): `rooting_protocols.author_user_key` (Marker-Regel, v0114)
Gemessen gegen: develop 007a4ea90 (Audit 2026-11-22)
Nachtrag #3025 (2026-11-28): Zweck `browser_error_reports` für Browser-Fehlerberichte (UI-NFR-013 v1.3, REQ-025 v1.41)
Anforderungs-IDs: PRIV-030 … PRIV-049 (Inventarregeln)
Änderung v1.1: `erasure_mirror` statt Raw-Key-Ledger, `migration_reports`, Ableitungswege jenseits der statischen
Prüfung (§5a); Rechtsgrundlagen-Spalten verweisen auf `06` §2 (PA-nn) und `13` (L-nn).
Änderungen 1.2: Kategorienübersicht mit Betroffenen, Empfängern, Speicherort, Frist, Zugriff (§3.0); fehlende Zeilen
nach LEG-46 (Aufgaben-Leistungsfelder LEG-28, `tenants.owner_user_key`, `calendar_feeds`, `user_favorites`,
Kontofelder in `weather_source_configs`/`ai_tip_cache`/`workflow_templates`/`nutrient_plans`; §3.9 Aktorik mit
`control_events.triggered_by_user` LEG-29; §3.10 Erkennung/Diagnose; §3.11 Telemetrie und externe Empfänger); Ist-Korrekturen
SW-Cache (LEG-27, LEG-36, LEG-56), GPS ungerundet (LEG-49), `user_personal`-Scope leer (LEG-22), EXIF-Nachstrip/-Upload
(LEG-55, LEG-57), R-40 umgesetzt (LEG-58), gesetzliche Zeilen ohne Klassifizierungsleser (LEG-30); Freitextinventar
verwiesen auf `04` §3.4; Lückenliste §6 auf den gemessenen Stand gebracht.
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

**Stand der Absicherung (Audit 2026-11-22, LEG-46) [VERIFIED_CODE]:** Der Guard aus PRIV-030
(`scripts/check_privacy_registry_doc.py`) existiert noch nicht; `⟂`-Zeilen werden heute von keinem Werkzeug
geprüft. Der Inventar-Guard R6 (`scripts/check_privacy_inventory.py:214–215`) erkennt nur die Muster
`user_key|*_user_key|*_by_key|*_account_key|*_by` und übersieht damit Schreibweisen wie `*_by_user`
(`control_events.triggered_by_user`, §3.9) — eine Messwerkzeug-Lücke. Soll (PRA-1.01): R6 um `[a-z0-9_]+_user$`,
`[a-z0-9_]+_by_user$`, `operator_*`, `*_subject` erweitern und den Bestand neu messen; der PRIV-030-Guard verlangt
für jede Collection mit personenbezogen geformtem Feld eine Zeile in diesem Dokument oder einen dokumentierten
Ausschlussgrund; ein weiterer Guard verlangt `max_length` für jedes `str`-Feld eines persistierten Modells.

---

## 2. Entitäten ohne personenbezogene Daten (der Vollständigkeit halber)

[v] Globale Katalogdaten (`species`, `cultivars`, `fertilizers`, `substrates`,
`phase_definitions`, IPM-Katalog) tragen höchstens `tenant_key`, keinen Kontobezug und
konstruktionsbedingt keinen personenbezogenen Freitext. Geometrie (`garden_objects.geometry`, `locations.geometry`)
„sind keine personenbezogenen Daten" (GP-NFR-055) — **aber** Standortkoordinaten sind es (§3.6).
`client_event_tombstones` enthalten ausschließlich zufällige UUIDs [v]. `yield_metrics` hat kein Benutzerfeld [v].

---

## 3. Inventar

### 3.0 Kategorienübersicht (Ist-Stand am geprüften SHA, Audit 2026-11-22)

Die Übersicht fasst die Feldzeilen aus §3.1–§3.11 zu 21 Verarbeitungskategorien zusammen und nennt für jede die
Angaben, die Art. 30 Abs. 1 und Art. 13/14 verlangen (LEG-46). Die Rechtsgrundlage ist ein Verweis auf die
Verarbeitungstätigkeit in `06` §2 (PA-nn); PA-13 bis PA-17 sind dort durch LEG-33 neu vorgeschlagen (KI-Assistent,
Erkennung/Diagnose, Benachrichtigung/E-Mail, Wetter/Klima, MCP/Agenten; PRA-1.03). Das Register der externen
Empfänger mit Rolle, Sitz und Übermittlungsgrundlage gehört nach `06` (LEG-33); hier steht nur, **dass** und
**wohin** Daten abfließen. Frist „—“ = keine implementierte Frist. Zugriff: V = viewer, G = grower, L = lead,
M = `management`, PA = Plattform-Admin. Evidenz: VERIFIED_CODE am SHA `007a4ea90`, soweit nicht anders vermerkt.

| # | Kategorie | Betroffene | Datenkategorien (Felder) | Zweck | Rechtsgrundlage (`06` §2) | Empfänger | Speicherort | Frist | Löschverhalten Konto / Mandant | Zugriff | Detail |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Konten | Kontoinhaber | `users` (E-Mail, Anzeigename, Hashes, `last_login_at`, Sperrzähler) | Login, Anzeige, Sicherheit | PA-01 | PA; OIDC-Provider bei Föderation | ArangoDB | Lebensdauer; R-01 90 d | Zeile entfernt / — | selbst; PA (inkl. `last_login_at`) | §3.1 |
| 2 | Sitzungen/Token | Kontoinhaber | `refresh_tokens` (IP 7 d), `api_keys`, `auth_providers` | Authentifizierung | PA-01 | — | ArangoDB | Ablauf; IP 7 d | gelöscht | keine | §3.1 |
| 3 | Mitgliedschaften | Mitglieder | `memberships`, `invitations`, `location_assignments`, `tenants.owner_user_key` | Mandantenzugriff | PA-03 | alle Mitglieder (`/members` inkl. E-Mail, LEG-14) | ArangoDB | mit Mitgliedschaft; Einladung R-12 | gelöscht bzw. Marker (`owner_user_key`) / gelöscht | V/G/L/M | §3.1 |
| 4 | Pflegeprotokoll | Mitglieder, in Labels genannte Dritte | `care_events` (5 Kontoverweise, Freitexte, Zeit, Ort, Fotos) | Koordination, Historie | PA-04 (Inhalt lit. b, Zurechnung lit. f, LEG-02) | Mitglieder; Empfänger der CSV | ArangoDB | R-25 5 J. | Marker, Freitext bleibt / gelöscht | V/G/L/M lesen + CSV; Personenfilter L/M | §3.3 |
| 5 | Bestätigungen | Mitglieder | `care_confirmations` (kein Akteur, `notes`) | Erinnerungszustand | PA-04 | Mitglieder | ArangoDB | — | nicht erreicht / gelöscht | V/G/L/M | §3.3 |
| 6 | Aufgaben | Mitglieder | `tasks` (Zuständige, Start/Ende, **Ist-Dauer, Ratings**, Notizen), `task_comments` | Arbeitsorganisation | PA-04 für Zuständigkeit; Leistungsfelder **ohne dokumentierte Grundlage** (LEG-28) | alle Mitglieder | ArangoDB | — (R-47 Vorschlag) | `assigned_to` Marker, Kommentar-`created_by` Marker / gelöscht | V/G/L/M (roher Kontoschlüssel) | §3.3 |
| 7 | Ernte (KCanG) | Erntende | `harvest_batches.harvested_by_key`, `harvester`, Mengen; `quality_assessments` | Ernteaufzeichnung | PA-05 (lit. c nur `kcang_association`, sonst lit. b) | Behörde auf Verlangen | ArangoDB | R-16 ≥ 5 J. | Tombstone, Name geleert / pseudonymisiert behalten (LEG-47) | V/G/L/M | §3.4 |
| 8 | Pflanzenschutz | Anwendende | `treatment_applications` (`applied_by_key`, Mittel, Dosis, Zeit), `inspections` | PflSchG § 11 (beruflich) | PA-05 (lit. c nur `pflschg_professional`) | Behörde | ArangoDB | R-17 3 J. (Fristbeginn heute `applied_at`, PRIV-412) | Tombstone / pseudonymisiert behalten (LEG-47) | V/G/L/M | §3.4 |
| 9 | Freitext/Kommentare | Mitglieder, Dritte | Tagebuch, Beschriftungen, Vorlagennamen, Notizen (> 50 Felder, `04` §3.4) | Dokumentation | PA-06 | Mitglieder | ArangoDB | Lebensdauer (Ausnahme `care_events`: R-25) | bleibt; Prüfwarteschlange nicht gebaut (LEG-08) / gelöscht | V/G/L/M | §3.3–3.4, `04` §3.4 |
| 10 | Bilder/Anhänge | Mitglieder, abgebildete Personen | `attachments` (Bytes, `created_by`, `original_filename`, `caption`) | Dokumentation | PA-06 (LEG-20) | Mitglieder; externe Erkennungsdienste bei Einwilligung (LEG-40) | Objektspeicher + ArangoDB | Lebensdauer des Elternobjekts | Marker, Dateiname geleert, Bytes bleiben / gelöscht | V/G/L/M; Löschen nur L (LEG-39) | §3.5 |
| 11 | Erkennung/Diagnose | Kontoinhaber | `identification_requests`, `pest_detections`, `plant_diagnosis_requests` (Metadaten, Ergebnisse, `image_hash` — **kein Bild**), `pest_image_contributions`, Embeddings | KI-Funktionen | PA-14 (Vorschlag LEG-33; Einwilligung `plant_identification`/`plant_diagnosis`) | externe Erkennungsdienste (Pl@ntNet, Kindwise) | ArangoDB, pgvector | bis Widerruf/Löschung | gelöscht bzw. Marker / gelöscht | selbst, PA | §3.10 |
| 12 | Aktorik | Mitglieder (Anwesenheit) | `control_events.triggered_by_user`, `manual_overrides.{created_by, reason}` | Steuerung, Nachvollziehbarkeit | PA-10 | Mitglieder; Home Assistant | ArangoDB | — | `control_events` **nicht erreicht** (LEG-29), Overrides Marker / gelöscht | V/G/L/M (roher Kontoschlüssel) | §3.6, §3.9 |
| 13 | Sensordaten | Haushaltsmitglieder, Beschäftigte (indirekt) | `sensor_readings` (kein Personenfeld; freie `metadata`) | Kulturüberwachung | PA-10 | Mitglieder | TimescaleDB | 90 d roh → 2 J. → 5 J. | — / gelöscht | V/G/L/M | §3.6 |
| 14 | Benachrichtigungen/Push | Empfänger/in | `notifications`, Push-Subscriptions, Apprise-URLs | Zustellung | PA-15 (Vorschlag LEG-33) | Push-Dienste der Browserhersteller, SMTP-Dienst, Apprise-Ziele | ArangoDB | — (R-48 Vorschlag) | gelöscht | selbst | §3.7, §3.11 |
| 15 | Kalender-Feeds | Kontoinhaber | `calendar_feeds` (`user_key`, Token-Hash, Name, Filter) | Aufgaben im Kalender | PA-01 [INFERRED] | Kalenderdienst des Nutzers (ruft iCal ab) | ArangoDB | `expires_at` optional | gelöscht; bei Mitgliedschaftsende die Feeds des Mandanten gelöscht | selbst | §3.1 |
| 16 | Audit-Logs | alle | `security_audit_log` (730 d), `mcp_audit_log` (90 d), `ai_audit_log`, `garden_plan_audit` (365 d), `task_audit_entries` | Art. 32, Nachweis | PA-02 | PA | ArangoDB | wie angegeben | Tombstone bzw. Marker | PA; Plan-Audit alle Mitglieder | §3.2, §3.3 |
| 17 | Datenschutzzustand | Antragsteller | `consent_records`, `erasure_requests`, `data_export_requests`, `processing_restrictions` | Art. 7, 15–21 | PA-07a | — | ArangoDB; Objektspeicher (Export 72 h) | R-04/R-05/R-06/R-13 | Tombstone | selbst, PA | §3.2 |
| 18 | Offline-Daten | Gerätenutzer, andere Mitglieder (Namen im SW-Cache, LEG-27) | IndexedDB `kp-plan-cache`, `kp-write-queue`, Cache Storage, Web Storage | Offline | PA-08 | — | Endgerät | 15 min / 365 d / 90 d (physisch teils unbefristet, LEG-36, LEG-56) | lokal; beim Logout teilweise | Gerätenutzer | §3.8 |
| 19 | Exporte | Mitglieder | Pflegeprotokoll-CSV, Beetlisten-CSV, Plan-JSON/SVG/PDF, Mandantenarchiv (`members.jsonl`, GPS), Art.-15-Bündel | Portabilität, Arbeit | PA-04/PA-11/PA-07a | Download-Empfänger (außerhalb der Kontrolle) | Download; Archiv 72 h | Archiv R-05 | — | CSV: alle Mitglieder; Archiv `management` und PA (LEG-53) | §5a |
| 20 | Kennungen/Pseudonyme | gelöschte Konten, alle Nutzer (Telemetrie) | Tombstone `anon_…` (instanzweit), Marker `_anonymized`, `log_subject` `sub_…`, `log_tenant` `ten_…`, `client_event_digest` | Verknüpfbarkeit Pflichtzeilen, Telemetrie | PA-02/PA-05 | — | ArangoDB, Logs | wie Trägerzeile | — | intern | `04` §2.1a, §3.11 |
| 21 | Betriebstelemetrie | alle Nutzer | Logs (pseudonymes Subjekt, Route, Zeit, gekürzte IP), GlitchTip-Ereignisse (`user` nur mit Einwilligung), Prometheus (ohne Personenlabels), Rate-Limit-Schlüssel je Konto, Celery-Nachrichten | Betrieb, Sicherheit | PA-02 (GlitchTip LEG-16) | Betreiber von Log-Pipeline und GlitchTip | Cluster (außerhalb des Repos) | **nicht im Repo festgelegt** (LEG-44) | — | Betreiber | §3.11 |

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
| | `location_assignments` (inkl. `notes`, Freitext) | ATTR (`assigned_to`) | ja | Zuständigkeitshinweis (REQ-049 §3.5) | 6(1)(b) | Mitglieder ([v]; `(t)` nach PRIV-309) | mit der Mitgliedschaft | gelöscht | — | Beetlisten-CSV `include_assignment` |
| ⟂ | `tenants.owner_user_key` (`domain/models/tenant.py:47`) | IDN | ja | Eigentümer des persönlichen Mandanten; verleiht kein Recht (REQ-049) | 6(1)(b) (PA-03) | Plattform-Admin | Lebensdauer des Mandanten | Marker; persönlicher Mandant bei `retained_late_joiner` umbenannt (`erasure_engine.py:458–485`) [v, Audit 2026-11-22] | Marker | **neu aufgenommen (LEG-46)** |
| | `user_favorites` (Kante `_from` = Konto, `_to` = Art/Nährstoffplan/Dünger) | IDN | ja | Favoriten (serverseitig) | 6(1)(b) (PA-01) | selbst | Lebensdauer | gelöscht (`erasure_engine.py:600`) [v] | — | **neu aufgenommen (LEG-46)** |
| ⟂ | `calendar_feeds.{user_key, token_hash, name (≤200), filters, expires_at}` (`domain/models/calendar.py:51–66`) | IDN/AUTH | ja | Aufgaben als iCal-Feed | 6(1)(b) (PA-01) [INFERRED] | selbst; **der Kalenderdienst des Nutzers ruft den Feed mit dem Token ab** (Empfänger) | bis `expires_at` (optional) oder Löschung | gelöscht (`erasure_engine.py:768`); bei Mitgliedschaftsende die Feeds dieses Mandanten gelöscht (`tenant_service.py:3798–3806`) [v] | — | Token nur als SHA-256-Digest gespeichert (#2171); **neu aufgenommen (LEG-46)** |

### 3.2 Datenschutz- und Audit-Zustand (Verantwortlicher: Betreiber)

| ⟂ | Entität.Feld | Kat | Personenbezogen? | Zweck | Rechtsgrundlage | Sichtbarkeit | Aufbewahrung | Löschung | Anonymisierung | Herkunft |
|---|--------------|-----|-------------|---------|-------------|------------|-----------|---------|---------------|---------|
| ⟂ | `erasure_requests.{user_key, status, step_up, requested_by_subject, members_notified_at, …}` | CONS/AUD | ja → pseudonymisiert | Nachweis Art. 5(2) | 6(1)(c) | selbst (Status), Plattform-Admin | R-06 3 J | `user_key` → Tombstone | Tombstone | `erasure_mirror` (Tombstone, kein Rohschlüssel; `09` §6) |
| | `data_export_requests`, Export-Bündel `privacy/exports/<user_key>/<key>.json` [v nur Objektschlüssel mit einem Benutzerschlüssel] | CONS | ja | Art. 15/20 | 6(1)(c) | selbst | R-05 72 h | gelöscht | — | — |
| | `processing_restrictions`, `email_change_requests` | CONS | ja | Art. 18/16 | 6(1)(c) | selbst | R-13 unbegrenzt / R-07 | gelöscht | — | — |
| ⟂ | `consent_records.{user_key, purpose, granted, ip, user_agent, revoked_at}` | CONS | ja | Art. 7(1) | 6(1)(c) | selbst, Plattform-Admin | R-04 3 J nach Widerruf; IP 7 d | `user_key` → Tombstone, `user_agent` geleert | Tombstone | — |
| ⟂ | `security_audit_log.{actor_user_key, target_user_key, tenant_key, membership_key, old/new role & scopes, request_id}` | AUD (`actor`) | ja | Art. 32 | 6(1)(c)/(f) | Plattform-Admin | R-38 730 d | Schlüssel → Tombstone; Zeile bleibt bei Mandantenlöschung behalten | Tombstone | neue Aktionen `04` §4.2 |
| | `mcp_audit_log.{service_account_key, shortened IP}` | AUD | ja | Art. 32 | 6(1)(f) | selbst (`/privacy/mcp-activity`), Admin | 90 d | → Tombstone | Tombstone | — |
| | `ai_audit_log.user_key`, `ai_conversations.{user_key, title, content}` | AUD/TXT | ja | KI-Funktionen | 6(1)(a) Einwilligungszwecke (PA-13, Vorschlag LEG-33) | selbst; KI-Provider (LEG-31, `06`) | je Einstellung | Audit → Marker; Konversationen gelöscht; bei Mandantenlöschung bleibt `ai_audit_log.user_key` roh bis 30 d (`tenant_erasure_engine.py:253–260`) [v, Audit 2026-11-22] | Marker | — |
| | `ai_tip_cache.dismissed_by` (`ai_assistant.py:192`) | ATTR | ja | ausgeblendeter Tagestipp gilt für den ganzen Mandanten (REQ-031 §7.5) | 6(1)(b) | Mitglieder | Lebensdauer | Marker, `dismissed_at` bleibt (`erasure_engine.py:440`) [v] | Marker | **neu aufgenommen (LEG-46)** |
| | `tenant_erasure_records`, `tenant_export_requests.requested_by_user_key`, `tenant_import_requests.requested_by_user_key`, `import_jobs.uploaded_by` | AUD/ATTR | ja | Nachweis / Betrieb | 6(1)(c)/(b) | `management`, Admin | R-06a / R-40 30 d — **umgesetzt** (`tenant_export_service.py:170–171, 1406–1407`; Audit 2026-11-22: NFR-011 führt R-40 fälschlich als „nicht implementiert“, LEG-58) | → Marker | Marker | `import_jobs.filename` identitätstragend möglich, wird nicht geleert (`04` §3.4) |
| ⟂ | **neu** `privacy_review_items.{tenant_key, erasure_key, collection, row_key, fields[], match_kinds[], status, decision, decided_by, reason_code, reason_text}` — **nicht gebaut** (`grep privacy_review_items` = 0, Audit 2026-11-22) | AUD | ja (`decided_by`; `reason_text` Freitext) | Folgemaßnahme zu Art. 17 | 6(1)(c) | Mandanten-`lead`/`management`; Admin zählt | R-43 3 J nach Entscheidung; mit Mandant | `decided_by` → Marker | Marker | speichert **keinen** Text/Token/Betroffenenschlüssel (PRIV-221) |
| ⟂ | **neu** `erasure_mirror.{kind, tombstone, tenant_key, erasure_key, completed_at, chain_hmac}` (DEC-26; ersetzt das Raw-Key-Ledger aus v1.0) — **nicht gebaut** (`grep erasure_mirror` = 0, Audit 2026-11-22; LEG-11, `09`) | AUD (pseudonym) | ja — **pseudonymisiert, kein Rohschlüssel** | Löschung nach Wiederherstellung erneut anwenden (Tombstone-Abgleich, `09` §6.2) | Art. 17 Durchsetzung (6(1)(c)) — LEG-11 | keine (nur Restore-Prozess; Bucket-Objekt Fernet-verschlüsselt) | R-45 = R-06 (3 J.) | harte Löschung per Beat; Spiegel-Objekt gefiltert neu geschrieben | — | Spiegel der `erasure_requests`-Tombstones |
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
| ⟂ | `feeding_events.product_label` (≤ 200) [v, #2854] | TXT | kann | Kopie des `care_events.product_label` einer Düngungs-/Bodenverbesserungszeile für die Düngebilanz | 6(1)(b)/(f) | alle Mitglieder | R-25 → `[redacted]` mit der Quellzeile (`care_event_repository.REDACT_FEEDING_LABELS_AQL`) | behalten wie die Quellzeile (#2411) | Schwärzung der Quellzeile schwärzt die Kopie | Mandantenlöschung löscht das Dokument |
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
| ⟂ | `locations.name` (kein gespeichertes Maximum [v]), `description` (≤ 1000), `notes` (≤ 4000), `soil_profile.notes` | TXT | kann | Plan | 6(1)(b) | Mitglieder; SVG/PDF/JSON; **der IndexedDB-Plan-Cache lässt notes/description weg [v]; der SW-API-Cache `kp:{user}:{tenant}` speichert die Rohantwort mit beiden Feldern (Audit 2026-11-22, LEG-27; Sachverhalt `07`)** | Lebensdauer | behalten; **Prüfung, wenn aus dem Template einer gelöschten betroffenen Person erstellt oder in einem Prüftreffer genannt** | Schwärzung | Herkunft `template_key`; Audit-Zusammenfassung |
| | `locations.photo_refs`, `cover_photo_ref` | MED | kann | Beetfotos | 6(1)(b)/(f) | Mitglieder | Lebensdauer | Anhangsregel | — | `attachments` |
| ⟂ | `sites.plan.plan_updated_by` | ATTR `modified_by` | ja | Plan | 6(1)(f) | M | Lebensdauer | Marker | Marker | **Korrektur (Audit 2026-11-22, LEG-27):** nur der IndexedDB-Plan-Cache nullt `plan_updated_by_name` (`planCache.ts:347–348`); der SW-API-Cache speichert den Anzeigenamen mit der Rohantwort auf dem Gerät (`07`, PRA-0.07) |
| ⟂ | `sites.{name, climate_zone}` | TXT | kann | Plan | 6(1)(b) | Mitglieder | Lebensdauer | behalten; Prüfung bei Treffer | Schwärzung | Audit-Zusammenfassung |
| | `irrigation_zones.name` | TXT | unwahrscheinlich | Plan | 6(1)(b) | Mitglieder | Lebensdauer | behalten | — | Audit-Zusammenfassung |
| | `tasks.assigned_to_user_key` | ATTR `assigned_to` | ja | Zuständigkeit | 6(1)(b) | Mitglieder (`(t)` für den Namen) — **Ist: roher Kontoschlüssel an jedes Mitglied** (`api/v1/tasks/schemas.py:342`, UI `TaskDetailPage.tsx:910–912`; widerspricht GP-API-034, Audit 2026-11-22) | bis erledigt / Ende der Mitgliedschaft (geleert) | Marker | Marker | Plan-Cache nullt den Zugewiesenen [v] |
| ⟂ | `tasks.{started_at, completed_at, reopened_at, actual_duration_minutes, difficulty_rating, quality_rating}` (`domain/models/task.py:181–205`; gesetzt in `task_service.py:1469–1475`, `:1720–1745`) | SENS (Leistungs-/Verhaltensdaten) | **ja** — zusammen mit Zuständigkeit und `care_events.performed_by_user_key` je Person Beginn, Ist-Dauer, Bewertung, Überfälligkeit | keine dokumentierte; Koordination braucht sie nicht (Q-PO-13) | **keine dokumentierte Grundlage** (PA-04 deckt sie nicht; LEG-28); im Beschäftigtenkontext Art. 88/§ 26 BDSG, § 87 Abs. 1 Nr. 6 BetrVG (`05` §11) | **alle Mitglieder inkl. `viewer`** über `GET /tasks`, `/tasks/queue`, `/tasks/overdue`, `/tasks/{key}` (`api/v1/tasks/schemas.py:304–357`; Router nur `get_current_tenant`) [v] | **keine [v]** → R-47 (Vorschlag: Leistungsfelder abgeschlossener Aufgaben nach 90 d leeren) | behalten | — | **neu aufgenommen (LEG-28)**; widerspricht PRIV-407 (`06` §5); Soll: PRIV-318 (`05`), PRA-2.06 |
| ⟂ | `tasks.{name (≤200), instruction, suggestion_reason, completion_notes, timer_label, tags}` | TXT | kann | Arbeit | 6(1)(b) | Mitglieder | **keine [v] → R-47-Vorschlag** | behalten; Prüfung für Zeilen mit Zugewiesenen | Schwärzung | Benachrichtigungen tragen Aufgabennamen [v]; `care_events` über Abschluss (`reason`, `material`) |
| | `tasks` — `created_by`/`completed_by` | — | **existieren nicht [v]** | — | — | — | — | — | — | Abschließende/r nur als `care_events.performed_by_user_key` |
| | `workflow_templates.created_by_user_key` (`task.py:32`; v0111) | ATTR | ja, sobald gestempelt | Urheberschaft | 6(1)(b) | Mitglieder | Lebensdauer | **heute immer `null`**; `ErasureExclusion` bis PRIV-E13 (`erasure_engine.py:1024–1030`) [v] | — | **neu aufgenommen (LEG-46)** |
| ⟂ | `task_comments.{created_by, comment_text (≤2000)}` | ATTR/TXT | ja/kann | Diskussion | 6(1)(b) | Mitglieder | keine → R-47 | Marker; Prüfung | Schwärzung | — |
| | `task_audit_entries.changed_by` | ATTR | immer `'system'` [v Ausschlusshinweis] | — | — | — | — | ausgeschlossen | — | — |
| | `workflow_templates.created_by` | TXT (Freitext, kein Schlüssel [v]) | kann | — | 6(1)(b) | Mitglieder | Lebensdauer | heute ausgeschlossen → **Prüffeld** (PRIV-212) | Schwärzung | — |

### 3.4 Pflanzenpflegeprotokolle und gesetzliche Aufzeichnungen (Verantwortlicher: Mandant)

| ⟂ | Entität.Feld | Kat | Personenbezogen? | Zweck | Rechtsgrundlage | Sichtbarkeit | Aufbewahrung | Löschung | Anonymisierung | Herkunft |
|---|--------------|-----|-------------|---------|-------------|------------|-----------|---------|---------------|---------|
| ⟂ | `harvest_batches.harvested_by_key` | ATTR `performed_by`, **Pflicht im gesetzlichen Profil** | ja | Ernteaufzeichnung | 6(1)(c) (R-16, falls LEG-03) sonst 6(1)(b) | P | ≥ 5 J ab `harvest_date` | **Ist: immer Tombstone** — `record_keeping` hat keinen Leser (Audit 2026-11-22, LEG-30); Soll: Tombstone (gesetzlich) / Marker (`record_keeping=none`, PRIV-400); Mandantenlöschung schreibt denselben instanzweiten Tombstone auch für lebende Konten (`tenant_erasure_engine.py:189–209`, LEG-47) | Pseudonym | aus der Abschluss-Engine `event.performed_by_user_key` |
| ⟂ | `harvest_batches.harvester` (≤ 200, Freitext) | TXT (eingetippter Name) | ja | Altfeld für Namen | — | Mitglieder (`HarvestBatchResponse` [v]) | — | **geleert** [v] | geleert | Zeilen vor #1669: `*_by_key = null`, Name bleibt → Alt-Prüfeintrag (PRIV-233) |
| | `harvest_batches.notes` | TXT | kann | Protokoll | 6(1)(c)/(b) | Mitglieder | R-16 | behalten (gesetzlich) / Prüfung (`none`) | Schwärzung nur, wenn nicht gesetzlich | — |
| ⟂ | `quality_assessments.{assessed_by_key, assessed_by, notes}` | wie oben | | | R-16 | | | wie Ernte | | |
| ⟂ | `treatment_applications.{applied_by_key, applied_by, notes, applied_at, dosage, product}` | ATTR/TXT | ja | Aufzeichnung nach PflSchG §11 (beruflich) | 6(1)(c) falls LEG-03 | P; Mitglieder | ≥ 3 J | Tombstone + Name geleert [v] — **LEG-04** | Pseudonym | → `care_events(pest_control)` per Backfill (Ausführende/r übernommen, PRIV-205) |
| ⟂ | `inspections.{inspected_by_key, inspector, notes}` | wie oben | ja | Überwachung nach PflSchG | R-18 | | ≥ 3 J | wie Behandlung | | MCP schreibt `inspector = "mcp:<key>"` [v] → PRIV-310 |
| | `watering_events.{performed_by (Freitext), notes}`, `watering_logs.{performed_by, notes}`, `tank_fill_events.{performed_by, notes}`, `maintenance_logs.{performed_by, notes}` | TXT (eingetippter Name) | ja (Name) | Betrieb | 6(1)(b) | Mitglieder; in der UI editierbar [v] | **keine [v] → R-46** | **ausgeschlossen [v] (Freitext, `erasure_engine.py:948–970`)** → **auf Schlüsselfeld + Label migrieren** (`08` §3.4); die v0111-Felder `performed_by_user_key` existieren (`watering_event.py:58`, `watering_log.py:125`, `tank.py:74, 145`), **kein Schreiber stempelt sie** (immer `null`, `ErasureExclusion` bis PRIV-E13) [v, Audit 2026-11-22] | nach Migration: Marker | → `care_events(watering/feeding)` ohne Ausführende/n [v] |
| | `feeding_events.{notes, material}` | TXT | kann | Betrieb | 6(1)(b) | Mitglieder | keine → R-46 | behalten | — | → `care_events(feeding)` |
| | `nutrient_plans.author` (Freitext, **kein Maximum [v]**, `nutrient_plan.py:198`) | TXT (eingetippter Name) | ja | Urheberschaft | 6(1)(b) | Mitglieder; **auf dem Nährstoffplan-PDF gedruckt [v]** | Lebensdauer | **in keiner Regel [v]** → Schlüsselfeld + Label (`08` §3.4) | Marker | Druckvorlage |
| | `nutrient_plans.author_user_key`, `author_label` (≤ 80) (`nutrient_plan.py:203–205`; v0111) | ATTR/TXT | ja, sobald gestempelt | Urheberschaft | 6(1)(b) | Mitglieder | Lebensdauer | **`author_user_key` heute immer `null`**, `ErasureExclusion` bis PRIV-E13 (`erasure_engine.py:1016–1022`) [v, Audit 2026-11-22] | — | **neu aufgenommen (LEG-46)** |
| ⟂ | `rooting_protocols.author_user_key` (`propagation.py:115`) — früher `author` = roher Kontoschlüssel der zuletzt ändernden Person, **kein** Freitext; seit #2976 Schlüsselfeld (Bestand v0114, `09` §5a) | ATTR `modified_by` | ja | Urheberschaft | 6(1)(b) | Mitglieder (Antwort zeigt Anzeigenamen) | Lebensdauer | Marker (`erasure_engine.py:150–161`) [v]; Art.-15-Quelle | Marker | eigene Zeile seit 1.2 (zuvor nur Nachtrag, LEG-46) |
| ⟂ | `plant_diary_entries.{created_by, analysis_requested_by, analysis_claimed_by}` | ATTR | ja | Pflanzenprotokoll | 6(1)(b)/(f) | C (t); alle Mitglieder lesen Einträge [v] | Lebensdauer | Marker [v] | Marker | — |
| ⟂ | `plant_diary_entries.{title (≤200), text (≤5000), tags, analysis.summary, analysis.findings}` | TXT | kann | Pflanzenprotokoll | 6(1)(b) | alle Mitglieder; `GET /diary?q=` Teilstringsuche [v] | Lebensdauer | behalten [v]; **Prüfung** | Schwärzung | KI-Analyse aus Text abgeleitet (Einwilligung `diary_ai_analysis`) |
| | `plant_diary_entries.photo_refs` | MED | kann | Protokoll | 6(1)(b) | Mitglieder | Lebensdauer | Speicherbereich `user_diary_attachments` (Bytes behalten, `created_by` Marker, EXIF erneut entfernt) | — | `attachments` |
| | `plant_instances.plant_name`, `planting_runs.{name, notes}`, `propagation.{name, notes, PhenotypeNote.note}`, `post_harvest.*notes`, `succession_plan.notes`, `aquaponik.*`, `care_profiles.notes`, Aktor-/Zeitplan-`notes`, `manual_overrides.reason` (≤500) | TXT | kann (gering) | Domäne | 6(1)(b) | Mitglieder | Lebensdauer | behalten; `manual_overrides.created_by` → Marker [v] | Prüfung nur bei Namenstoken-Treffer | — |

### 3.5 Medien und Anhänge

| ⟂ | Entität.Feld | Kat | Personenbezogen? | Zweck | Rechtsgrundlage | Sichtbarkeit | Aufbewahrung | Löschung | Anonymisierung | Herkunft |
|---|--------------|-----|-------------|---------|-------------|------------|-----------|---------|---------------|---------|
| ⟂ | `attachments.created_by` | ATTR `created_by` | ja | Eigentum | 6(1)(b) | C; **Löschen eigener Galeriefotos/Anhänge nur durch `lead`** (Audit 2026-11-22, LEG-39, `05` PRIV-321) | Lebensdauer des Elternobjekts | Marker (Speicherbereich) / `pest_reference` gelöscht / `user_personal` gelöscht — **Korrektur (Audit 2026-11-22, `DOCUMENTATION_GAP`, LEG-22):** der Scope `user_personal` ist leer (`data_access/storage/local_fs_adapter.py:582`), der Regeltext nennt Kategorien `profile`/`user_notes`, die im Enum nicht existieren (`erasure_engine.py:495–497`, `common/enums.py:1562–1588`); das „[v]“ belegt keine wirksame Löschung | Marker | geteilte Bytes (Deduplizierung je Beitragende/n seit #1770, Art.-19-Mitteilung AK-OS-09 **nicht implementiert**) |
| ⟂ | `attachments.original_filename` | TXT (identitätstragend) | oft | Echo des Uploads | 6(1)(b) | Mitglieder; Art.-15-Bündel | Lebensdauer | **heute behalten [v] → geleert (PRIV-211)** | geleert | v0062 leert es bei geteilten Datensätzen [v] |
| ⟂ | `attachments.caption` (≤ 500) | TXT | kann | Galerie | 6(1)(b) | Mitglieder | Lebensdauer | behalten; **Prüfung** | Schwärzung | — |
| | Anhang-Bytes (Fotos; EXIF beim Upload entfernt und bei Löschung erneut entfernt — **präzisiert (Audit 2026-11-22):** der Upload-Strip ist fail-open (`strict=False`, Originalbytes bei Dekodierfehler) und per `STORAGE_STRIP_EXIF=false` global abschaltbar (LEG-57); der Nachstrip bei Kontolöschung erreicht nur Mandanten mit aktueller Mitgliedschaft, nicht verlassene (LEG-55; Sachverhalt `01`/`03`); Speicherschlüssel `t/{tenant}/{category}/{yyyy}/{mm}/{ulid}` — kein Benutzer im Pfad [v, `attachment_service.py:358–364`]) | MED | kann (Gesichter, Orte) | Protokoll | 6(1)(b)/(f) | Mitglieder; Thumbnails | Lebensdauer des Elternobjekts | behalten für geteilte Kategorien; `user_personal`/Schädlingsreferenz gelöscht | — | Renditions |
| | `attachments.client_event_id/_digest` [v Welle 9] | — | pseudonym | Replay | 6(1)(b) | keine | mit der Zeile | mit der Zeile | — | — |
| | `pest_image_contributions.{contributed_by, promoted_by}`, pgvector `species_embeddings(source='user_contributed', contributed_by, tenant_key)` | ATTR/SENS | ja | Erkennungsindex (Einwilligung) | 6(1)(a) | Admin | bis Widerruf / Löschung | gelöscht / `promoted_by` Marker [v] | Marker | — |

### 3.6 Standort- und Sensordaten

| ⟂ | Entität.Feld | Kat | Personenbezogen? | Zweck | Rechtsgrundlage | Sichtbarkeit | Aufbewahrung | Löschung | Anonymisierung | Herkunft |
|---|--------------|-----|-------------|---------|-------------|------------|-----------|---------|---------------|---------|
| ⟂ | `sites.gps_coordinates` | LOC | **ja** — persönlicher Garten = Wohnadresse (REQ-025 §3.1.2) | Wetter, Frost, Klimazone | 6(1)(b) (PA-16, Vorschlag LEG-33); **Soll** DP-002: vor dem Verlassen auf 2 Dezimalstellen runden — **Ist: ungerundet** (Audit 2026-11-22, LEG-49; kein Adapter und kein Aufrufer rundet; Sachverhalt `06`, PRA-2.14) | Mitglieder; Art.-15-Bündel; **Mandantenarchiv (LEG-13, ungerundet)**; GeoJSON WON'T [v] | Lebensdauer des Standorts | mit persönlichem Mandanten; bleibt im geteilten Mandanten | — | Wetteranfragen an OpenWeatherMap, Open-Meteo, Bright Sky (DWD-Daten), NASA POWER (USA) — **mit voller Genauigkeit** bis PRA-2.14 |
| | `weather_source_configs.updated_by` (`weather.py:168`) | ATTR `modified_by` | ja | letzte Änderung der Wetterquelle je Site (REQ-046) | 6(1)(b) | Mitglieder | Lebensdauer | Marker (`erasure_engine.py:426`) [v] | Marker | **neu aufgenommen (LEG-46)** |
| | `sensor_readings` (TimescaleDB: `tenant_key`, `sensor_key`, Wert, `source`, `metadata` JSONB) — **keine Benutzerspalte [v]**; `metadata` ist ein freies Client-Dict [?] | SENS | kontextuell (CO₂/Bewegung/manuelle Übersteuerung → Anwesenheitsmuster; NFR-001 §6.7 DSFA) | Überwachung | 6(1)(b) | Mitglieder | 90 d roh → 2 J stündlich → 5 J täglich (festes SQL; R-14-Klassifizierung **nicht implementiert [v]**) | mit Mandant (`delete_by_tenant`) | — | Aggregate |
| | `manual_overrides.{created_by, reason}` | ATTR/TXT | ja | Aktor-Übersteuerung (Anwesenheitssignal) | 6(1)(b)/(f) | Mitglieder | keine | Marker [v]; Prüfung | Schwärzung | der im selben Vorgang geschriebene `control_events.triggered_by_user` fehlt in jeder Regel (§3.9, LEG-29) |

### 3.7 Benachrichtigungen

| ⟂ | Entität.Feld | Kat | Personenbezogen? | Zweck | Rechtsgrundlage | Sichtbarkeit | Aufbewahrung | Löschung | Anonymisierung | Herkunft |
|---|--------------|-----|-------------|---------|-------------|------------|-----------|---------|---------------|---------|
| ⟂ | `notifications.{user_key, title, body, data, read_at, acted_at}` | ATTR `recipient` / TXT | ja | Zustellung | 6(1)(b) | Empfänger/in | **keine [v] → R-48-Vorschlag** | gelöscht [v] | — | Texte tragen Aufgaben-/Pflanzennamen, keine Mitgliedsnamen [v Messung] |
| | `notification_preferences.pwa.subscriptions`, Apprise-URLs (Fernet) | AUTH | ja | Kanäle | 6(1)(b) (PA-15, Vorschlag LEG-33) | selbst; **Empfänger:** Push-Dienst des Browserherstellers (Payload verschlüsselt, `pwa_notification_channel.py:214–218`), Apprise-Ziele, SMTP-Dienst (§3.11) | Lebensdauer | gelöscht | — | — |

### 3.8 Daten auf dem Gerät (Verantwortlicher: Betreiber für Standardwerte; siehe `07`)

| ⟂ | Speicher.Schlüssel | Kat | Personenbezogen? | Zweck | Rechtsgrundlage (TDDDG §25 / DSGVO) | Aufbewahrung | Beim Logout geleert? [v] | Erforderlich |
|---|-----------|-----|-------------|---------|--------------------------------|-----------|------------------------|----------|
| ⟂ | IndexedDB `kp-plan-cache` (`{key, userKey, tenantKey, cachedAt, data}`; keine Namen, Notizen, Zuweisungen [v]) | DEV | ja (Schlüssel, Plan) | Offline-Lesen | §25(2) Nr. 2 unbedingt erforderlich — **Vorschlag, LEG-09**; 6(1)(b) | 15 min TTL; bereinigt bei Start/Lesen/Schreiben | alle Datenbanken außer der Queue gelöscht | behalten |
| ⟂ | IndexedDB `kp-write-queue` (`id`, `userKey`, `tenantKey`, `capturedAt`, `status`, `write` inkl. Notiztext und Fotobytes, `bedName`) | DEV/TXT/MED | ja | Offline-Schreibvorgänge | wie oben | 365 d ausstehend / 90 d nicht sendbar | nur die Zeilen der ausscheidenden Person, nach Bestätigung | verkürzen + Quarantäne (`07`) |
| ⟂ | Cache Storage `kp:{user_key}:{tenant_key}` — **Korrektur (Audit 2026-11-22, LEG-27):** nicht mehr leer; seit die drei Offline-Lesepfade (`/sites`, `/sites/{k}/plan`, `/locations/{k}/summary`) `private, no-cache` antworten, speichert der Service Worker die **vollständige JSON-Antwort** inkl. `plan.plan_updated_by_name` (Name eines Mitglieds), Beet-`notes`/`description` und `cover_photo_ref` (`sw.ts:193–207, 232–243`, `pwa/apiCache.ts:617–626`; keine `storedProjection`) | DEV/TXT/IDN | **ja** (Schlüssel; Namen und Freitexte anderer Mitglieder) | SW-Cache | wie oben | Auslieferung 15 min; **physisch unbefristet** bis Überlauf, Namespace-Wechsel, Sitzungsende oder Kill-Switch (LEG-36) | gelöscht | projizieren oder abschalten (PRA-0.07, Q-PO-08); physische Frist (PRA-2.16); Sachverhalt `07` |
| ⟂ | Cache Storage `kp-sw-state` (Client-ID → `kp:{user_key}:{tenant_key}`) | DEV/IDN | ja (Schlüssel) | SW-Zustand | wie oben | **physisch unbefristet** ohne lebende Clients (LEG-36) | gelöscht | beim Prune ohne lebende Clients leeren (PRA-2.16) |
| ⟂ | IndexedDB `kp-write-queue`, Store `notices` (`{userKey, count}` je Eigentümer nach Retention-Bereinigung; `queueDb.ts:647–651`) | DEV/IDN | ja (Schlüssel) | Hinweis „Einträge verworfen“ | wie oben | **unbefristet** bis zur Anmeldung desselben Eigentümers (`acknowledgePurged`) (Audit 2026-11-22, LEG-56) | nur bei bestätigtem Logout/Kontolöschung desselben Nutzers oder Kill-Switch | `createdAt` speichern, nach Gerätefrist löschen; beim Login eines anderen `user_key` mitlöschen (PRA-2.16) |
| | Cache Storage Precache, `kp-static-assets`, `kp-runtime-config` | — | nein | App-Shell | erforderlich | — | behalten | — |
| ⟂ | localStorage `kp_local_data_owner` (**ein `user_key`** [v]) | DEV/IDN | ja | Eigentümerprüfung lokaler Daten | erforderlich | — | **nein [v]** → leeren (PRIV-512) | |
| ⟂ | localStorage `kp-garden-field-mode` (`userKey`, `tenantSlug`, `siteKey`, Tab) | DEV/IDN | ja | Wiederaufnahme des Feldmodus | erforderlich | — | **nein [v]** → leeren | |
| ⟂ | sessionStorage `kp.emailChange.address` (**E-Mail**), `kp.stepUp.{token,resume,error}` | DEV/IDN/AUTH | ja | Abläufe | erforderlich | ablaufgebunden | **nein [v]** → leeren | |
| | localStorage `kp_active_tenant_slug` | DEV | Slug (kann aus einem Namen abgeleitet sein) | Routing | erforderlich | — | ja | — |
| | localStorage `kp.gardenPlanner.planting.lastUsed.{tenantSlug}` | DEV | Mandanten-Slug im Schlüssel | UX | erforderlich | — | nein | beim Logout leeren (Hygiene) |
| | localStorage `kamerplanter:consent:v1`, `kamerplanter:consent:pending-revoke:<konto-hash>`, `kamerplanter:consent:account-signal`, `plant_identification_consent` | CONS | nur Entscheidung (bzw. ausstehender Widerruf je Konto, Signal ohne Personenbezug) | Einwilligung | erforderlich | — | nein (muss erhalten bleiben) | behalten |
| | localStorage Theme/Sprache/Kiosk/Layout/Modulsichtbarkeit/Seitengrößen/ausgeblendete Tipps/Editor-Einstellungen | DEV | nein | UX | erforderlich | — | nein | behalten |
| | sessionStorage `kamerplanter.pendingInvitation` | AUTH | Token | Onboarding | erforderlich | Ablauf | ja | — |
| | Refresh-Cookie (HttpOnly [Spec; von der Analyse im Backend-Code nicht verifiziert]), CSRF-Cookie | AUTH | ja | Authentifizierung | erforderlich | **präzisiert (Audit 2026-11-22, LEG-37):** Sitzungs-Cookie; 30 d nur mit „Angemeldet bleiben“ (implementiert, `LoginPage.tsx:39, 85, 198–205`, `api/v1/auth/router.py:251–269`; Sachverhalt `07`) | widerrufen | — |

**Nicht vorhanden [v]**: `redux_state` in sessionStorage (Zeile in REQ-025 §10 ist veraltet), `i18next`-/
`theme`-Schlüssel (tatsächliche Schlüssel `kamerplanter-lang`, `kamerplanter-theme`), `device_id` (R-049b
nicht implementiert), jegliche API-Nutzlast in localStorage (G-W9 a hält).

**Nur verarbeitet, nie gespeichert [v] (#2898):** die Eigenposition des Feldmodus (REQ-053 GP-UX-026, `LOC`).
Nach dem Einschalten von „Meine Position“ liest die Karte die Geräteposition per `watchPosition` und hält sie
ausschließlich im Komponentenzustand (`features/gardenPlanner/field/useOwnPosition.ts`); weder die Position noch
die Wahl landen in einem der Speicher dieser Tabelle, in Redux, in einer Anfrage oder in einem Log. Der gemerkte
Kartenausschnitt (`kp-garden-field-mode`) folgt nur Zoom und Beet-Tipp, nie der Position. Abgesichert durch
`OwnPosition.test.tsx` (Storage, IndexedDB, Anfragen, Konsole, Store); die Fehlerverfolgung schwärzt Schlüssel
mit `latitude`/`longitude`/`gps`/`coords`/`geolocation` zusätzlich (`observability/errorTracking.ts`).
Daher keine Zeile in §3.8.

### 3.9 Aktorik (Verantwortlicher: Mandant) — neu in 1.2 (LEG-29, LEG-46)

| ⟂ | Entität.Feld | Kat | Personenbezogen? | Zweck | Rechtsgrundlage | Sichtbarkeit | Aufbewahrung | Löschung | Anonymisierung | Herkunft / Kopien |
|---|--------------|-----|-------------|---------|-------------|------------|-----------|---------|---------------|------------------|
| ⟂ | `control_events.triggered_by_user` (`domain/models/actuator.py:227`; geschrieben bei manuellen Aktorbefehlen, Overrides und Not-Aus, `actuator_service.py:158–170, 181, 274, 394, 718–741`) | ATTR `performed_by` / SENS | **ja** — wer schaltet wann Licht/Lüftung (Anwesenheits- und Arbeitszeitsignal; NFR-001 §6.7) | Steuerung, Fehleranalyse | 6(1)(b)/(f) (PA-10) | **alle Mitglieder, roher Kontoschlüssel** (`ControlEventResponse`, `api/v1/actuators/schemas.py:111–125`; Router `actuators/tenant_router.py:145, 167, 344–375, 513`) [v] | **keine [v]** (Vorschlag 90 d analog `mcp_audit_log`, Q-DSB-21) | **in keiner Regel der Kontolöschung, nicht im Art.-15-Export** (`grep control_events\|triggered_by_user` in `erasure_engine.py`, `data_export_engine.py` = 0); nur Mandantenlöschung (`tenant_erasure_engine.py:143`) [v] | — | R6 erkennt `_by_user` nicht (§1); Soll PRA-2.07: `triggered_by_user_key` mit Marker-Regel oder nur `source = manual` (Q-PO-15), Art.-15-Quelle, Frist, Darstellung als `PersonRef` (`05` PRIV-319) |
| | `control_events.{notes, error_message}`, `actuators/control_rules/control_schedules/phase_control_profiles.{name, notes}` | TXT | gering | Steuerung | 6(1)(b) | Mitglieder | Lebensdauer | mit Mandant | — | Freitextinventar `04` §3.4 |

### 3.10 Erkennung und Diagnose (Verantwortlicher: Betreiber für die Funktion; Einwilligungszwecke) — neu in 1.2 (LEG-46)

Das Foto selbst wird bei keiner dieser Anfragen gespeichert [VERIFIED_CODE]: `domain/models/identification.py:3–5`
(„The user photo is never persisted … `image_hash` is a truncated SHA-256 used for deduplication/audit, not the image“),
`pest_detection.py:34, 58`, `plant_diagnosis_request.py:4–5, 47–49` (`image_deleted_at` beim Anlegen gesetzt). Es geht
aber zur Verarbeitung an externe Dienste (Pl@ntNet, Kindwise; Rolle offen, Q-LAW-07; fremde Fotos LEG-40 → `01`/`03`).

| ⟂ | Entität.Feld | Kat | Personenbezogen? | Zweck | Rechtsgrundlage | Sichtbarkeit | Aufbewahrung | Löschung | Anonymisierung | Herkunft / Empfänger |
|---|--------------|-----|-------------|---------|-------------|------------|-----------|---------|---------------|------------------|
| ⟂ | `identification_requests.{user_key, tenant_key, image_hash, image_organ, results, selected_result_rank, plant_instance_key}` (`identification.py:39–58`) | IDN/SENS | ja | Pflanzenbestimmung (REQ-029) | 6(1)(a) Einwilligung `plant_identification` (PA-14, Vorschlag LEG-33) | selbst, Plattform-Admin [INFERRED] | bis Widerruf/Löschung | gelöscht (`erasure_engine.py:695–700`) [v] | — | Bild an Erkennungsdienst (Pl@ntNet), nicht gespeichert |
| ⟂ | `pest_detections.{user_key, image_hash, llm_explanation, …}` + Kanten `pest_detection_of/_flagged/_suggested_inspection` (`pest_detection.py:33–59`) | IDN/SENS/TXT | ja | Schädlingserkennung (REQ-044) | 6(1)(a) (PA-14) | selbst, Plattform-Admin [INFERRED] | bis Widerruf/Löschung | Dokument und Kanten gelöscht (`erasure_engine.py:705–727`) [v] | — | Bild an Kindwise (`kindwise_pest_adapter.py`), nicht gespeichert |
| ⟂ | `plant_diagnosis_requests.{user_key, image_hash, image_deleted_at, Klassenlabels}` (`plant_diagnosis_request.py:21–49`) | IDN/SENS | ja | Pflanzendiagnose | 6(1)(a) Einwilligung `plant_diagnosis` (PA-14) | selbst, Plattform-Admin [INFERRED] | bis Widerruf/Löschung | Dokument und Kanten gelöscht (`erasure_engine.py:774–809`) [v] | — | — |
| | `pest_image_contributions`, `species_embeddings(source='user_contributed')` | | | | | | | siehe §3.5 | | |

### 3.11 Betriebstelemetrie und externe Empfänger (Verantwortlicher: Betreiber) — neu in 1.2 (LEG-46)

Telemetrie trägt keine Klarnamen, aber stabile Pseudonyme; sie ist damit eine pseudonyme Aktivitätsspur
(Art. 4 Nr. 5; Überwachungspotenzial Ü7 in `05` §11). Die Frist liegt in der Log-Pipeline des Clusters, nicht im Repo
(LEG-44 → `06`; Q-OP-09).

| Datenfluss | Personenbezug | Evidenz [VERIFIED_CODE] | Empfänger | Frist | Löschverhalten |
|------------|---------------|-------------------------|-----------|-------|----------------|
| structlog-Logs (Route, Zeit, Request-ID, gekürzte IP) | pseudonymes Subjekt `sub_…`/`ten_…` (HMAC mit eigenem Log-Salt), nie roher Schlüssel oder E-Mail (157 Aufrufe `log_subject(`, Guard; AST-Scan der `logger.*`-Kwargs) | `common/log_privacy.py:1–34`; `erasure_engine.py:1258–1310` | Betreiber der Log-Pipeline | **nicht im Repo festgelegt** (Vorschlag ≤ 30 d, LEG-44) | keine Löschung je Person; Korrelation nur mit Log-Salt (Rotation erwägen, Q-OP-04) |
| GlitchTip-Ereignisse | `send_default_pii=False`, Scrubbing; `user`-Block (`sub_…`/`ten_…`) nur mit Einwilligung `error_tracking` | `observability/error_tracking.py:675, 685`; `observability/event_user.py:36–46` | GlitchTip-Betreiber | nicht im Repo festgelegt | — (LIA-4 offen, LEG-16 → `06`) |
| GlitchTip-Ereignisse aus dem Browser (#3025) | nur mit Einwilligung `browser_error_reports` nach UI-NFR-013 §5.4; `dataCollection` alles aus, `scrubEvent`/`scrubBreadcrumb`, kein `user`-Block; IP beim Empfang | `src/frontend/src/observability/errorTracking.ts`, `observability/consent.ts` | GlitchTip-Betreiber | nicht im Repo festgelegt | Einwilligung (beim Umsetzen festgelegt, #2517) |
| Prometheus-Metriken | keine Personenlabels | `observability/*.py` | Betreiber | Betrieb | — |
| Rate-Limit-Schlüssel je Konto | Kontoschlüssel im Valkey-Schlüssel (`user_rate_limit_key`) | `api/v1/care_events/tenant_router.py:55` | — (Valkey intern, ohne Authentifizierung, LEG-59 → `01`) | Fenster des Limiters | Ablauf |
| Celery-Nachrichten | Konto-/Mandantenschlüssel als Task-Argumente [INFERRED, Strang E] | Celery-Broker Valkey | — (intern) | bis Abarbeitung | — |
| Externe Empfänger | E-Mail (SMTP/Resend), Web-Push-Dienste, Apprise-Ziele, Wetter-APIs (**ungerundete** Koordinaten, LEG-49), OIDC-Provider, Home Assistant/MCP-Clients (Service-Accounts, Ü8), KI/LLM (Knowledge-Service, LEG-31), Pl@ntNet/Kindwise (§3.10), Medien-/Katalogdienste ohne Personenbezug (GBIF, Perenual, iNaturalist, iDigBio, Wikimedia), Backup-S3 | `data_access/external/*`, `src/knowledge-service/app/llm/*`, `helm/kamerplanter/values.yaml:593` (vollständige Liste in LEG-33) | wie genannt | je Dienst | **Register mit Rolle, Sitz, Drittlandgrundlage fehlt** → `06` (LEG-33, PRA-1.03) |

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
| gespeichertes Foto einer Erkennungs-/Diagnoseanfrage | nicht vorhanden; nur `image_hash` (gekürztes SHA-256) und `image_deleted_at` (`identification.py:3–5`, `pest_detection.py:58`, `plant_diagnosis_request.py:4–5`) [v, Audit 2026-11-22] |
| Freitextinventar aller Collections | steht in `04` §3.4 (Abdeckung durch Schwärzung, R-25, Leeren, Mandantenlöschung) |

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
| Offline-Puffer/-Cache | `kp-write-queue`, `kp-plan-cache`, SW-API-Cache `kp:{user}:{tenant}` | clientseitig; Opt-in (`07` §2.1); Projektion ohne Namen **nur im IndexedDB-Cache** — der SW-Cache kopiert die Rohantwort (Audit 2026-11-22, LEG-27) | TTL, Quarantäne, Übergang; SW-Cache ohne physische Frist (LEG-36) |
| Mandantenimport | `tenant_import_engine._rewrite_value` | `anon2_` → Marker, **`anon_` unverändert übernommen** (`tenant_import_engine.py:399–406`, LEG-54) | `04` PRIV-241 |
| Plan-Restore | `garden_plan_import_service.restore_snapshot` (`:420–441`) | materialisiert `garden_plan_audit.snapshot` wieder als Live-Zeilen (LEG-34) | `04` PRIV-240 |
| Materialisierte Sichten | TimescaleDB Continuous Aggregates (`sensor_hourly`, `sensor_daily`) | keine Kontoreferenz | `delete_by_tenant` |
| Audit-Snapshots | `garden_plan_audit.snapshot` (Import), `summary` | `derived_from` (neu) | Blatt-Schwärzung (PRIV-229), R-26 |
| Spiegel/Backups | `erasure_mirror`, Dumps | Tombstones / vollständige Kopien | R-45; Restore-Replay (`09` §6) |

---

## 6. Durch das Inventar gefundene Lücken (Faktenliste; Lösung in `04`–`09`, `12`)

Stand nach Audit 2026-11-22 (develop `007a4ea90`); erledigte Punkte bleiben mit Vermerk stehen.

1. Tombstones in `care_events.performed_by_user_key` über `account_of` erreichbar (#2770) — **behoben #2839**
   (Mapper + v0107, VERIFIED_CODE); `garden_plan_audit` erledigt (DEC-16, v0109); `task_completion_engine` kopiert
   weiterhin Rohschlüssel ohne `carry_account_reference` (offen, PRIV-205).
2. Freitext wird bei der Löschung nie geleert oder aufgelistet; Schwärzung nur für Pflegeereignisse, nur lead,
   keine UI-Aktion über einen Chip hinaus; keine Liste betroffener Zeilen (LEG-08 bestätigt; > 50 Felder, `04` §3.4).
3. `care_events.material`, Messwert-Strings außerhalb der Schwärzungsmenge (LEG-08 bestätigt).
4. `original_filename` wird seit v0109 geleert (PRIV-211 **erledigt**); `caption` überlebt die Löschung;
   `nutrient_plans.author` und die `performed_by`-Freitextfelder der Gieß-/Tank-Protokolle liegen außerhalb jeder Regel.
5. `garden_plan_audit.user_key` erhält seit v0109 den Marker (**erledigt**); Freitextkopien bleiben, und
   `snapshot` setzt sie per Restore zurück (LEG-34); ob die UI `null`-Akteure verwirft, ist nicht erneut geprüft.
6. Keine Aufbewahrung für `notifications`, `watering_events`/`feeding_events`/Tankprotokolle, Aufgaben und
   Kommentare, `care_confirmations`.
7. Das Ende einer Mitgliedschaft hat keine datenschutzrechtliche Wirkung außer dem Leeren von `tasks.assigned_to_user_key`
   und dem Löschen der Kalender-Feeds; kein `left_at`; der Name wird für immer aufgelöst (LEG-06 bestätigt, `05` §8).
8. Geschlossene Konten lösen ihren Anzeigenamen noch bis zu 90 Tage auf.
9. Jedes Mitglied sieht die E-Mail jedes Mitglieds.
10. Das MCP-Tagebuch-Tool gibt rohes `users._key` zurück; MCP-Inspektionen schreiben `inspector = "mcp:<key>"`.
11. Gesetzliche Regeln gelten für jeden Mandanten; `CanG §X` unspezifiziert.
12. Mehrere `localStorage`-/`sessionStorage`-Schlüssel mit einem `user_key` oder einer E-Mail überleben das
    Logout; REQ-025 §10 listet veraltete/nicht existierende Schlüssel und übersieht vorhandene.
13. Kein Verfahren für Löschung nach Wiederherstellung; Backups sind konfigurierbar, aber nichts wendet Löschungen
    erneut an (`erasure_mirror` nicht gebaut; LEG-11, LEG-43 → `09`).
14. Keine Datenschutz-Betriebsmetriken oder Listen-Endpunkt; „Gauge" ist ein Logfeld.
15. Marker-/Regex-Konstanten dupliziert — **erledigt** (eine Definition in `domain/models/privacy.py:17, 25`; Guard
    `tests/unit/guards/test_privacy_marker_and_tombstone_have_one_definition.py`; `04` PRIV-201).
16. `security_audit_log` hat keine Aktion für Löschung/Export/Einwilligung/Schwärzung.
17. **Neu (Audit 2026-11-22):** Aufgaben speichern und zeigen Leistungsdaten je Person an alle Mitglieder (LEG-28, §3.3).
18. **Neu:** `control_events.triggered_by_user` ohne Löschung, Auskunft, Frist; R6 blind für `_by_user` (LEG-29, §3.9).
19. **Neu:** Mandantenklassifizierung (`record_keeping`, `organization_kind`) gespeichert, ohne Setz- und Lesepfad
    (LEG-30; `05` §11) — damit wirken gesetzliche Fristen für jeden Mandanten und keine klassenabhängige Voreinstellung.
20. **Neu:** Inventarlücken `tenants.owner_user_key`, `calendar_feeds`, `user_favorites`, Erkennung/Diagnose,
    `weather_source_configs.updated_by`, `ai_tip_cache.dismissed_by`, Telemetrie, externe Empfänger (LEG-46; in 1.2
    aufgenommen, §3.0–§3.11; Register der Empfänger → `06`, LEG-33).
21. **Neu:** SW-API-Cache speichert Mitgliedernamen und Beet-Notizen (LEG-27) und hat wie `kp-sw-state` und der
    Store `notices` keine physische Frist (LEG-36, LEG-56) — `07`.
22. **Neu:** Koordinaten gehen ungerundet an Wetterdienste (LEG-49) — `06`.
