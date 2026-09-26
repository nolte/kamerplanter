# NFR-011: Vorratsdatenspeicherung & Aufbewahrungsfristen

```yaml
ID: NFR-011
Titel: Vorratsdatenspeicherung & Aufbewahrungsfristen
Kategorie: Datenschutz & Compliance
Unterkategorie: Retention Policy, Datensparsamkeit, DSGVO
Fokus: Beides (Zierpflanze & Nutzpflanze)
Technologie: Python, Celery, ArangoDB, TimescaleDB, Valkey
Status: Genehmigt
Priorität: Kritisch
Version: 1.10 (eigener, rotierbarer Log-Salt, #1812)
Datum: 2026-04-27
Tags: [dsgvo, retention, datensparsamkeit, loeschfristen, compliance, cross-cutting]
Abhängigkeiten: [REQ-023, REQ-024, REQ-025 v1.1, NFR-001]
Betroffene Module: [ALL]
Security-Review-Referenz: SEC-K-001, SEC-K-002, SEC-K-005
```

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.10 | 2026-09-26 | **#1812:** Die Log-Pseudonyme (`subject=`, `email_sha256=`) sind mit einem eigenen, rotierbaren `LOG_PSEUDONYM_SALT` verschlüsselt statt mit `ERASURE_TOMBSTONE_SALT` (L-1, L-2); API und Worker starten in Produktion nicht ohne ihn (L-5); neuer Absatz zur Rotation. Betreiberentscheidung vom 2026-09-26. |
| 1.9 | 2026-09-25 | **#1795/#1796:** §3.4 um L-6 bis L-8 erweitert: keine API-Schlüssel und Einmal-Tokens in einer Log-Senke (httpx/httpcore/urllib3 auf WARNING mit Query-Filter in API und Worker, Console-Mail-Adapter ohne Link außerhalb von `DEBUG`), redigierte Zugriffsprotokolle von uvicorn und nginx, redigierte Tracebacks in beiden Prozessen. L-3 nennt zusätzlich URL-Userinfo und Fragmente; der Offen-Hinweis in L-4 entfällt. Ein eigener, rotierbarer Log-Salt ist eine offene DSB-Entscheidung (#1812). |
| 1.8 | 2026-09-25 | **#1788 Persönlicher Mandant bei Kontolöschung:** Die Kontolöschung behielt den bei der Registrierung angelegten persönlichen Mandanten samt Standorten, Pflanzen, Tagebuch und Aufgaben; nur Eigentümer, Name und Kurzname wurden ersetzt. Jetzt läuft für jeden persönlichen Mandanten der Person, in dem sie das einzige aktive Mitglied (mit aktivem Konto) ist, vor dem ArangoDB-Plan das Mandanten-Löschinventar (#1769) mit `origin: account_erasure`; R-16 bis R-18 bleiben dort unter ihrem Tombstone-Hash. **Entscheidung für Mandanten mit weiteren aktiven Mitgliedern:** keine Spezifikation nennt einen Nachfolger (REQ-049 AK-19); der Mandant bleibt wie bisher erhalten, der Löschauftrag nennt den Grund (`personal_tenants[].outcome = retained_other_members`); offen in #1824. §2.3 Klarstellung, Abnahmekriterien AK-PT-01 bis AK-PT-03 in §6. REQ-025 §3.1.3 Regel 2 wird nachgezogen (#1826), gemeinsam mit den an REQ-025 verankerten Reach-Proben. |
| 1.7 | 2026-09-25 | **#1782/#1784:** §3.1 beschreibt die Einzel-Tasks, die es gibt, statt eines Master-Tasks `enforce_retention_policy` (Begründung in §3.1). §3.2: Fristvergleiche in AQL vergleichen Zeitpunkte (`DATE_TIMESTAMP`), nie ISO-Strings — ArangoDB ordnet Strings nach ICU-Kollation, gemessen `"…00.5Z" < "…00+00:00"` → `true`. §3.3: Prometheus-Metriken als nicht implementiert gekennzeichnet (#1800). §4: die tatsächlichen Settings mit Untergrenzen; R-04, R-12, R-14, R-15 und R-16..R-18 ohne lesenden Code als nicht implementiert gekennzeichnet (#1800). AK-04 bis AK-06, AK-10 und AK-11 angepasst. |
| 1.6 | 2026-09-25 | **#1781:** §3.4 Anwendungs- und Zugriffsprotokolle ergänzt (L-1 bis L-5): keine Kontoschlüssel, E-Mail-Adressen oder ungekürzten IP-Adressen an Log-Aufrufen der Anwendung (Zugriffsprotokolle und Tracebacks noch offen), gesalzener E-Mail-Digest, Salt-Pflicht auch für den Celery-Worker. Die Aufbewahrungsfrist der Log-Pipeline selbst ist als offene Betreiber-Frage markiert. |
| 1.5 | 2026-09-23 | **#1663:** Die ID R-19 war doppelt vergeben (Gießdienst-Rotation in §2.1, Promotion-Audit-Log in §2.3). Das Promotion-Audit-Log heißt jetzt **R-24** (R-23 ist im `spec/knowledge/COMPLIANCE-PLAN.md` bereits für RAG-Anfragen vorgesehen); R-19 bleibt die Gießdienst-Rotation, auf die sich `spec/e2e-testcases/TC-NFR-011.md` bezieht. Die Zeilen R-19, R-19a, R-20, R-21 und R-24 sind als nicht implementiert gekennzeichnet — ihre Collections existieren im Code nicht. `quality_assessments` (R-16) wird seit #1663 über das serverseitige `assessed_by_key` anonymisiert; `yield_metrics` (R-16) trägt kein Nutzerfeld. |
| 1.4 | 2026-04-27 | **ADR-003 (W-014 Sensor-Retention für Perennials):** R-14 differenziert nach `Location.data_classification` (REQ-002): `OUTDOOR_OPEN` Stufe 2 = 5y, Stufe 3 = 20y (Opt-in); `GREENHOUSE` Stufe 3 = 10y (Opt-in); `INDOOR_*` und `UNKNOWN` weiterhin 5y. Forward-only-Klassifizierungs-Wechsel. Vier neue Settings. R-19a für Saison-Aggregate-Anonymisierung bei User-Löschung. |
| 1.3 | 2026-04-27 | **ADR-002 (W-006 Promotion-Audit):** R-19 (seit v1.5: R-24) ergänzt — `promotion_audit_log`-Collection mit 5 Jahren Aufbewahrung. Begründung: Bei Sortenrechts-Streitigkeiten relevant; konsistent mit Erntedaten-Retention (R-16). |
| 1.2 | 2026-04-27 | **ADR-001 (W-009 Karenz-Detach):** R-17 präzisiert: Aufbewahrungsfrist umfasst auch geerbte `to_plant`-Edges (Karenz-Snapshot beim Detach). Fristberechnung anhand Original-`applied_at`, nicht anhand `inherited_at`. Hard-Delete nach 3 Jahren entfernt Original-Treatment + alle abhängigen Edges (direkt, run, geerbt) im selben Schritt. |
| 1.1 | 2026-04-27 | **W-002 Fix (Tombstone-Salt):** R-06 Maßnahme präzisiert (Pseudonymisierung sofort nach User-Hard-Delete + Hard-Delete des Audit-Eintrags nach 1 Jahr). Pflicht-Setting `ERASURE_TOMBSTONE_SALT` in §4 ergänzt — Backend startet ohne dieses Setting nicht (siehe REQ-025 §3.1). Compliance-Begründung: Art. 5(1)(e) Speicherbegrenzung. |
| 1.0 | 2026-02-27 | Erstversion — Retention-Matrix R-01 bis R-15, Celery-Master-Task, TimescaleDB-Downsampling, Konfigurations-Defaults. |

## 1. Business Case

### 1.1 User Story

**Als** Datenschutzbeauftragter
**möchte ich** dass personenbezogene Daten automatisch nach definierten Fristen gelöscht oder anonymisiert werden
**um** die DSGVO-Grundsätze der Speicherbegrenzung (Art. 5 Abs. 1 lit. e) und Datenminimierung (Art. 5 Abs. 1 lit. c) einzuhalten.

**Als** Systemadministrator
**möchte ich** dass Löschfristen automatisch durch das System durchgesetzt werden
**um** manuellen Aufwand zu vermeiden und menschliche Fehler bei der Datenbereinigung auszuschließen.

**Als** Betreiber einer Anbauanlage
**möchte ich** dass gesetzlich vorgeschriebene Aufbewahrungsfristen (CanG, PflSchG) eingehalten werden
**um** bei behördlichen Kontrollen alle erforderlichen Nachweise vorlegen zu können.

### 1.2 Geschäftliche Motivation

Diese NFR ist ein **Cross-Cutting Concern** (querschnittliche Anforderung), der alle 24 funktionalen Anforderungen (REQ-001 bis REQ-024) sowie das zukünftige REQ-025 (Datenschutz & Betroffenenrechte) betrifft. Sie adressiert:

1. **DSGVO Art. 5 Abs. 1 lit. e (Speicherbegrenzung):** Personenbezogene Daten dürfen nur so lange gespeichert werden, wie es für den Verarbeitungszweck erforderlich ist.
2. **DSGVO Art. 17 (Recht auf Löschung):** Betroffene können Löschung verlangen; das System muss diese technisch umsetzen können.
3. **Gesetzliche Aufbewahrungspflichten:** CanG (Cannabis-Gesetz) und PflSchG (Pflanzenschutzgesetz) schreiben Mindestaufbewahrungsfristen für bestimmte Datenkategorien vor.
4. **Datensparsamkeit:** Sensor- und Verhaltensdaten, die Rückschlüsse auf Personen erlauben (SEC-K-005), müssen nach definierter Frist aggregiert oder gelöscht werden.

### 1.3 Hintergrund: IT-Security-Review-Findings

Diese NFR adressiert direkt die folgenden kritischen Befunde aus dem IT-Security-Review:

| Finding | Schweregrad | Adressiert durch |
|---------|-------------|-----------------|
| SEC-K-001 | Kritisch | Retention-Matrix (§2), Celery-Enforcement (§3) |
| SEC-K-002 | Kritisch | IP-Anonymisierung (§2.1 Zeile "IP-Adressen") |
| SEC-K-005 | Kritisch | Sensordaten-Downsampling (§2.2) |

---

## 2. Retention-Matrix

### 2.1 Personenbezogene Daten

| # | Datenkategorie | Collection(s) | Frist | Aktion nach Frist | Rechtsgrundlage | Referenz |
|---|---------------|---------------|-------|-------------------|----------------|----------|
| R-01 | Soft-Deleted User-Accounts | `users` (status: `deleted`) | 90 Tage nach Soft-Delete | Hard-Delete: Account-Daten endgültig entfernen, E-Mail-Hash für Duplikatprüfung behalten. **Der Soft-Delete selbst entfernt bereits `password_hash` und `avatar_url`** — die Frist darf kein Authentifizierungsgeheimnis überdauern (REQ-025 Szenario 3, #1525) | Art. 17 DSGVO, Art. 5(1)(e) | REQ-023 §2, REQ-025 |
| R-02 | Unbestätigte Accounts | `users` (status: `unverified`) | 7 Tage nach Erstellung | Hard-Delete: Account und zugehörige Auth-Provider entfernen | Art. 5(1)(e), Zweckentfall | REQ-023 §3.5 |
| R-03 | IP-Adressen in Sessions | `refresh_tokens` (Feld: `ip_address`) | 7 Tage nach Speicherung | Anonymisierung: IPv4 letztes Oktett → `0`, IPv6 → `/48`-Präfix behalten | Art. 6(1)(f) berechtigtes Interesse, Art. 5(1)(c) Datenminimierung | REQ-023 §2 |
| R-04 | Consent Records | `consent_records` | 3 Jahre nach Widerruf | Hard-Delete | Art. 7(1) Nachweispflicht | REQ-025 **Nicht implementiert** (Stand #1782): Kein Task löscht `consent_records`; die IP-Adresse eines Consent Records wird ebenfalls nicht anonymisiert (#1800). |
| R-05 | Export-Dateien | Dateisystem (Export-Verzeichnis) | 72 Stunden nach Erstellung | Datei löschen, Status auf `expired` setzen | Art. 15/20 DSGVO, Zweckentfall | REQ-025 |
| R-06 | Erasure-Audit-Logs | `erasure_requests` | 1 Jahr nach Abschluss | **Pseudonymisierung sofort nach User-Hard-Delete (`user_key` → Tombstone-Hash via REQ-025 §3.1 Phase 2.5), anschließend Hard-Delete des Audit-Eintrags nach 1 Jahr** <!-- W-002 --> | Art. 5(2) Rechenschaftspflicht + Art. 5(1)(e) Speicherbegrenzung | REQ-025 |
| R-07 | E-Mail-Änderungsanfragen | `email_change_requests` | 24 Stunden nach Erstellung | Hard-Delete (abgelaufene Tokens) | Zweckentfall | REQ-025 **Teilweise implementiert** (Stand #1782): Nach Ablauf der Frist setzt `retention.expire_email_change_requests` den Status auf `expired`; ein Hard-Delete findet nicht statt (#1800). |
| R-08 | Passwort-Reset-Tokens | `users` (Felder: `password_reset_token`, `password_reset_expires`) | 1 Stunde (besteht) | Token-Felder nullen | REQ-023 §1 | REQ-023 |
| R-09 | E-Mail-Verifikations-Tokens | `users` (Felder: `email_verification_token`, `email_verification_expires`) | 24 Stunden (besteht) | Token-Felder nullen | REQ-023 §1 | REQ-023 |
| R-10 | OAuth State | Redis | 5 Minuten (besteht, Redis TTL) | Automatische Bereinigung durch Redis | REQ-023 §3.2 | REQ-023 |
| R-11 | Abgelaufene Refresh Tokens | `refresh_tokens` | Sofort nach Ablauf | Hard-Delete (TTL-Index besteht) | Zweckentfall | REQ-023 §2 |
| R-12 | Einladungen (abgelaufen) | `invitations` | 30 Tage nach Ablauf | Hard-Delete | Zweckentfall | REQ-024 **Teilweise implementiert** (Stand #1782): `cleanup_expired_invitations` setzt abgelaufene Einladungen auf `expired`; die 30-Tage-Löschung existiert nicht (#1800). |
| R-13 | Processing Restrictions | `processing_restrictions` | Unbegrenzt (bis Aufhebung durch Betroffenen) | Nur auf expliziten Wunsch entfernen | Art. 18 DSGVO | REQ-025 |
| R-19 | Gießdienst-Rotation (DutyRotation) | `duty_rotations` | Unbegrenzt (bei User-Löschung: User-Referenz anonymisieren) | Anonymisierung: User-Referenz auf NULL, Dienst-Zeitraum bleibt | Art. 17 Abs. 3 (berechtigtes Interesse Tenant) | REQ-024 v1.2 **Nicht implementiert** (Stand #1663): Die Collection `duty_rotations` existiert im Code nicht; es gibt keine Regel im Löschinventar (`ErasureEngine`). |
| R-20 | Pinnwand-Beiträge (BulletinPost/Comment) | `bulletin_posts`, `bulletin_comments` | Bei User-Löschung: User-Referenz anonymisieren, Inhalt bleibt | Anonymisierung | Art. 17 Abs. 3 (berechtigtes Interesse Tenant) | REQ-024 v1.2 **Nicht implementiert** (Stand #1663): Die Collections `bulletin_posts`/`bulletin_comments` existieren im Code nicht; es gibt keine Regel im Löschinventar (`ErasureEngine`). |
| R-21 | Einkaufslisten (SharedShoppingList) | `shared_shopping_lists` | Bei User-Löschung: User-Referenz anonymisieren | Anonymisierung | Art. 17 Abs. 3 (berechtigtes Interesse Tenant) | REQ-024 v1.2 **Nicht implementiert** (Stand #1663): Die Collection `shared_shopping_lists` existiert im Code nicht; es gibt keine Regel im Löschinventar (`ErasureEngine`). |
| R-22 | Aufgaben-Bewertungen (Task difficulty/quality ratings) | `tasks` (Felder: `difficulty_rating`, `quality_rating`, `assigned_to_user_key`) | Bei User-Löschung: `assigned_to_user_key` durch den Marker `_anonymized` ersetzen (`ErasureEngine.ANONYMIZE_COLLECTIONS`), Bewertungen bleiben (aggregiert nutzbar) | Anonymisierung | Art. 17 Abs. 3 (Lern-System benötigt Aggregatdaten) | REQ-006 |
| R-19a <!-- ADR-003 --> | Saison-Aggregate (`seasonal_cycles.sensor_aggregates`) | `seasonal_cycles` (Feld `aggregate_computed_by`) | Aggregate bleiben unbegrenzt (keine personenbezogenen Daten); bei User-Löschung `aggregate_computed_by → NULL` | Anonymisierung | Art. 17 Abs. 3 (fachliche Trendanalyse über Pflanzenleben) | REQ-003 v2.x, REQ-025 **Nicht implementiert** (Stand #1663): Die Collection `seasonal_cycles` existiert im Code nicht; es gibt keine Regel im Löschinventar (`ErasureEngine`). |

### 2.2 Sensordaten (Indirekt personenbezogen — SEC-K-005)

Sensordaten können Rückschlüsse auf Anwesenheit und Verhalten von Personen erlauben (CO2-Kurven, Bewegungssensoren, manuelle Overrides). Sie unterliegen daher einer gestuften Retention-Policy mit zunehmender Aggregierung:

| # | Datenkategorie | Speichersystem | Stufe 1 (Rohdaten) | Stufe 2 (Stündlich) | Stufe 3 (Täglich) | Rechtsgrundlage |
|---|---------------|---------------|-------------------|--------------------|--------------------|----------------|
| R-14 | Sensordaten (Temperatur, RH, CO2, Licht, Bodenfeuchtigkeit) <!-- ADR-003 differenziert nach Location.data_classification (REQ-002), siehe Tabelle unten --> | TimescaleDB | 90 Tage volle Auflösung | 90d–2 Jahre (Default) bzw. 90d–5 Jahre (`OUTDOOR_OPEN`): Stundenmittelwerte | **Differenziert nach Klassifizierung (siehe Untertabelle)** | Art. 6(1)(b) Vertragserfüllung |
| R-15 | Aktor-Logs (manuelle Overrides) | TimescaleDB | 90 Tage | 90d–1 Jahr: aggregiert (Override-Anzahl/Tag) | Danach löschen | Art. 6(1)(f) berechtigtes Interesse |

<!-- Quelle: ADR-003 / W-014 -->
**R-14 Differenzierung nach `Location.data_classification` (ADR-003):**

Sensor-Retention auf Stufe 2 + 3 wird nach DSGVO-Risikogruppe der Location (REQ-002) differenziert. Die Klassifizierung steuert, wie lange aggregierte Daten aufbewahrt werden dürfen, ohne gegen Art. 5(1)(e) Speicherbegrenzung zu verstoßen.

| `data_classification` | Stufe 1 (Roh) | Stufe 2 (Stunde) | Stufe 3 (Tag) | Saison-Aggregate (REQ-003) |
|----------------------|---------------|------------------|---------------|----------------------------|
| `INDOOR_PRIVATE` (Default für `UNKNOWN`) | 90d | 2y | 5y | ∞ (anonymisiert bei User-Löschung, R-19a) |
| `INDOOR_PUBLIC` | 90d | 2y | 5y | ∞ (anonymisiert bei User-Löschung, R-19a) |
| `GREENHOUSE` | 90d | 2y | **10y (opt-in)** | ∞ (anonymisiert bei User-Löschung, R-19a) |
| `OUTDOOR_OPEN` | 90d | **5y** | **20y (opt-in)** | ∞ |

**Verlängerte Retention bei `GREENHOUSE` und `OUTDOOR_OPEN`:** Tenant-Admin muss explizit zustimmen (Opt-in), damit die längeren Stufen aktiviert werden. Default für alle Klassifizierungen ist die DSGVO-konservative 5-Jahres-Grenze auf Stufe 3. Begründung der Werte: Bei `OUTDOOR_OPEN` (Garten, Hochbeet) besteht kein Personenbezug — Stundenmittelwerte enthalten keine Anwesenheits-Indikatoren. Eine längere Aufbewahrung ist daher DSGVO-rechtlich unkritisch und fachlich für mehrjährige Analysen wertvoll (Apfelbäume, Beerensträucher).

**Forward-only-Klassifizierungs-Wechsel (Workshop-Frage 5):** Bei Wechsel der `data_classification` einer Location (z.B. `INDOOR_PRIVATE` → `OUTDOOR_OPEN`) gelten die neuen Retention-Fristen NUR für Sensor-Werte, die NACH dem Wechsel erfasst wurden. Bestehende Daten behalten ihre ursprüngliche Schutzklasse — verhindert nachträgliche Schutz-Senkung durch Klassifizierungs-Manipulation.

**Klassifizierungs-Default `UNKNOWN` (Workshop-Frage 2):** Locations ohne explizite Klassifizierung werden wie `INDOOR_PRIVATE` behandelt — DSGVO-konservativ, Anwender muss bewusst auf `OUTDOOR_OPEN` wechseln (UI-Warnung).
<!-- /Quelle: ADR-003 / W-014 -->

<!-- Quelle: Widerspruchsanalyse W-009 — Klimatische Extremwerte dauerhaft archivieren -->
**Ausnahme: Klimatische Extremwert-Events:**

Sensordaten-Rohdaten werden nach 90 Tagen aggregiert (R-14). Für die Pflanzenpflege-Analyse bei mehrjährigen Pflanzen (Perennials, Obstbäume) archiviert das System jedoch **klimatische Extremereignisse** (Frost, Hitzewelle, Sturm) als eigenständige Event-Dokumente in ArangoDB dauerhaft. Diese Events enthalten keinen Personenbezug und unterliegen daher nicht der DSGVO-Löschpflicht:

- `ClimateEvent`-Dokument in ArangoDB (nicht TimescaleDB): `type` (frost/heat/storm), `location_key`, `start_at`, `end_at`, `min_temp`/`max_temp`, `severity`
- Automatische Erkennung durch Schwellwert-Prüfung im Sensor-Ingestion-Task
- Konfigurierbar: `SENSOR_RAW_RETENTION_DAYS` (Standard 90), erhöhbar für Perennial-Anlagen

**TimescaleDB Continuous Aggregates:**

```sql
-- Stundenmittel (Stufe 2): automatisch nach 90 Tagen
CREATE MATERIALIZED VIEW sensor_hourly
  WITH (timescaledb.continuous) AS
  SELECT
    time_bucket('1 hour', timestamp) AS bucket,
    location_key,
    sensor_type,
    AVG(value) AS avg_value,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    COUNT(*) AS sample_count
  FROM sensor_readings
  GROUP BY bucket, location_key, sensor_type;

-- Tagesmittel (Stufe 3): automatisch nach 2 Jahren
CREATE MATERIALIZED VIEW sensor_daily
  WITH (timescaledb.continuous) AS
  SELECT
    time_bucket('1 day', bucket) AS bucket,
    location_key,
    sensor_type,
    AVG(avg_value) AS avg_value,
    MIN(min_value) AS min_value,
    MAX(max_value) AS max_value,
    SUM(sample_count) AS sample_count
  FROM sensor_hourly
  GROUP BY time_bucket('1 day', bucket), location_key, sensor_type;

-- Retention-Policies
SELECT add_retention_policy('sensor_readings', INTERVAL '90 days');
SELECT add_retention_policy('sensor_hourly', INTERVAL '2 years');
SELECT add_retention_policy('sensor_daily', INTERVAL '5 years');
```

### 2.3 Fachliche Aufbewahrungspflichten

Diese Daten unterliegen gesetzlichen Mindestaufbewahrungsfristen und dürfen **nicht** vor Ablauf gelöscht werden:

| # | Datenkategorie | Collection(s) | Mindestfrist | Rechtsgrundlage | Referenz |
|---|---------------|---------------|-------------|----------------|----------|
| R-16 | Erntedaten (HarvestBatch, QualityAssessment, YieldMetric) | `harvest_batches`, `quality_assessments`, `yield_metrics` | 5 Jahre | Art. 6(1)(c) gesetzl. Pflicht, CanG (Cannabis-Gesetz) | REQ-007 |
| R-17 | Behandlungsanwendungen (TreatmentApplication) | `treatment_applications` + `to_plant`/`to_run`-Edges (inkl. geerbter `inherited_from_run`-Edges, ADR-001) | 3 Jahre | Art. 6(1)(c) gesetzl. Pflicht, PflSchG §11 | REQ-010 |
| R-18 | Inspektionsprotokolle | `inspections` | 3 Jahre | PflSchG §11 | REQ-010 |
| R-24 <!-- ADR-002; bis v1.4 doppelt als R-19 vergeben --> | Promotion-Audit-Log (Species/Cultivar tenant→global) | `promotion_audit_log` | 5 Jahre | Sortenrechts-Streitigkeiten, Art. 5(2) Rechenschaftspflicht. **Nicht implementiert** (Stand #1663): Die Collection `promotion_audit_log` existiert im Code nicht. | REQ-001 v4.1 |

**Wichtig:** Bei einer Löschanfrage (Art. 17 DSGVO) durch einen Betroffenen werden diese Daten **anonymisiert** (User-Referenz entfernt), aber nicht gelöscht, solange die gesetzliche Aufbewahrungsfrist läuft (Art. 17 Abs. 3 lit. b).

**Der persönliche Mandant der Person (#1788):** Die Aufbewahrungspflicht hält die Datensätze fest, nicht den Mandanten, in dem sie liegen. War die Person das einzige aktive Mitglied ihres persönlichen Mandanten, löscht die Kontolöschung den Mandanten über das Mandanten-Löschinventar (AK-PT-01 bis AK-PT-03 in §6); die Datensätze dieser Tabelle bleiben dabei unter dem Tombstone-Hash der Person erhalten, alles andere im Mandanten (Standorte, Pflanzen, Tagebuch, Aufgaben …) hat keinen Aufbewahrungsgrund und geht. Ein persönlicher Mandant mit weiteren aktiven Mitgliedern bleibt erhalten (#1824).

<!-- Quelle: ADR-001 / W-009 -->
**R-17 Klarstellung — geerbte Treatment-Edges (ADR-001):**

Beim Detach einer PlantInstance werden aktive Run-Level-Treatments als `to_plant`-Edges mit `inherited_from_run`-Property auf die Plant kopiert (Karenz-Snapshot). Diese geerbten Edges teilen die 3-Jahre-Aufbewahrungsfrist des Original-Treatments. Die Fristberechnung erfolgt anhand des Original-`applied_at`-Timestamps des `treatment_applications`-Dokuments — nicht anhand des `inherited_at`-Timestamps der Edge.

Konsequenz: Bei Hard-Delete des Original-Treatments nach 3 Jahren werden auch alle abhängigen Edges (`to_plant`, `to_run`, geerbte `to_plant`) im selben Schritt entfernt. Pflanzen, die historisch detached wurden, verlieren damit ihren Karenz-Snapshot — der ist nach 3 Jahren ohnehin nicht mehr karenzwirksam.
<!-- /Quelle: ADR-001 / W-009 -->

---

## 3. Technische Umsetzung: Celery-Enforcement

### 3.1 Einzel-Tasks je Regel

Jede Regel läuft als eigener Celery-Beat-Task mit einem Takt, der zu ihrer Frist passt. Einen Master-Task, der alle Regeln in einem Lauf orchestriert, gibt es nicht (Entscheidung #1782, v1.7):

| Regel | Celery-Task | Takt (UTC) | Frist aus |
|-------|-------------|------------|-----------|
| R-01 | `retention.execute_scheduled_erasures` | täglich 04:00 | `RETENTION_SOFT_DELETE_RETENTION_DAYS` (beim Antrag in `hard_delete_scheduled_at` festgeschrieben) |
| R-02 | `app.tasks.auth_tasks.cleanup_unverified_accounts` | täglich | `RETENTION_UNVERIFIED_ACCOUNT_DAYS` |
| R-03 | `app.tasks.auth_tasks.anonymize_old_ips` | täglich | `RETENTION_IP_ANONYMIZATION_DAYS` |
| R-05 | `retention.expire_data_exports` | stündlich, Minute 20 | `RETENTION_EXPORT_FILE_RETENTION_HOURS` (bei Fertigstellung in `expires_at` festgeschrieben) |
| R-06 | `retention.purge_expired_erasure_records` | täglich 04:30 | `RETENTION_ERASURE_AUDIT_RETENTION_YEARS` |
| R-07 | `retention.expire_email_change_requests` | stündlich, Minute 15 | `RETENTION_EMAIL_CHANGE_RETENTION_HOURS` (beim Antrag in `expires_at` festgeschrieben) |
| R-11 | `app.tasks.auth_tasks.cleanup_expired_tokens` | stündlich | Ablaufzeitpunkt des Tokens |
| R-12 | `app.tasks.tenant_tasks.cleanup_expired_invitations` | täglich | Ablaufzeitpunkt der Einladung (Status `expired`; die 30-Tage-Löschung fehlt, #1800) |

Jede Frist wird aus genau einem Setting über `RetentionService` gelesen (§4); kein Task trägt eine eigene Zahl.

**Warum kein Master-Task:** Nichts in dieser NFR verlangt einen Orchestrator als solchen. Was er leisten sollte — jede Regel wird regelmäßig durchgesetzt (AK-04), jeder Lauf protokolliert seine Zahlen (AK-05), ein Fehler in einer Regel hält keine andere auf — leisten die Einzel-Tasks bereits. Ein einheitlicher Tagestakt wäre für die stundengenauen Fristen sogar falsch: Ein Lauf um 02:00 UTC würde R-07 (24 h) um bis zu 24 Stunden überziehen und R-05 (72 h) ebenso, also länger speichern als deklariert. Die Beschreibung folgt deshalb dem Code, nicht umgekehrt.

### 3.2 Sub-Tasks (Beispiele)

**Fristvergleiche vergleichen Zeitpunkte, nie Strings (#1784).** ArangoDB ordnet Strings mit `<`/`>` nach ICU-Kollation, und gespeicherte Zeitstempel haben je nach Schreibweg verschiedene Formen (`…00Z`, `…00.500000Z`, `…00+00:00`, `…00.000Z`). Gemessen auf ArangoDB 3.12.8: `"2025-09-25T04:30:00.5Z" < "2025-09-25T04:30:00+00:00"` → `true` — ein Datensatz eine halbe Sekunde *nach* dem Stichtag galt als älter. Jeder Fristvergleich in AQL MUSS deshalb beide Seiten mit `DATE_TIMESTAMP(...)` vergleichen; `null < Zahl` ist in AQL wahr, deshalb entscheidet jeder `<`/`<=`-Selektor ausdrücklich, was mit einem Datensatz ohne lesbaren Zeitstempel geschieht, und zwar nach der Richtung der Aktion: Eine **zerstörende** Aktion nach Alter (Löschen, Erasure) schließt ihn aus (`DATE_TIMESTAMP(x) != null`), denn sein Alter ist nicht belegt. Eine **minimierende** Aktion (IP-Anonymisierung R-03) schließt ihn ein, denn Anonymisieren schadet niemandem, das Behalten der vollen Adresse schon. Die Ablauf-Selektoren (`expires_at`) für Sessions, Einladungen, E-Mail-Änderungen, MCP-Idempotenz und Aktor-Overrides behandeln einen fehlenden Ablaufzeitpunkt als abgelaufen; Export und KI-Gespräch tun das noch nicht (#1806). Durchgesetzt von `src/backend/tests/unit/guards/test_aql_timestamp_comparisons_are_instants.py`. `DATE_TIMESTAMP` löst auf Millisekunden auf; bei einem strikten `<` gegen den Stichtag kann das einen Datensatz nur jünger, nie älter erscheinen lassen.

Die folgenden Beispiele zeigen die Form; die tatsächlichen Selektoren liegen in den Repositories unter `src/backend/app/data_access/arango/`.

**R-01: Hard-Delete Soft-Deleted Accounts (90 Tage):**

```python
async def hard_delete_soft_deleted_accounts():
    """Löscht Accounts die seit > 90 Tagen im Status 'deleted' sind."""
    cutoff = datetime.utcnow() - timedelta(days=90)

    # AQL: Finde alle soft-deleted Accounts älter als 90 Tage
    accounts = await aql("""
        FOR u IN users
          FILTER u.status == 'deleted'
          FILTER DATE_TIMESTAMP(u.updated_at) != null
          FILTER DATE_TIMESTAMP(u.updated_at) < DATE_TIMESTAMP(@cutoff)
          RETURN u._key
    """, cutoff=cutoff.isoformat())

    for user_key in accounts:
        # Löschreihenfolge: Edges vor Nodes
        await delete_edges_for_user(user_key)  # has_auth_provider, has_session, etc.
        await delete_collection_docs("auth_providers", user_key)
        await delete_collection_docs("refresh_tokens", user_key)
        await delete_collection_docs("consent_records", user_key)
        await delete_user(user_key)
        log.info("retention.hard_delete_account", subject=log_subject(user_key))  # §3.4 L-1

    return {"deleted_count": len(accounts)}
```

**R-03: IP-Anonymisierung (7 Tage):**

```python
async def anonymize_session_ips():
    """Anonymisiert IP-Adressen in Sessions älter als 7 Tage."""
    cutoff = datetime.utcnow() - timedelta(days=7)

    # AQL: Anonymisiere IPs in nicht-anonymisierten Sessions
    result = await aql("""
        FOR rt IN refresh_tokens
          FILTER rt.ip_address != null
          FILTER rt.ip_anonymized_at == null
          FILTER DATE_TIMESTAMP(rt.issued_at) != null
          FILTER DATE_TIMESTAMP(rt.issued_at) < DATE_TIMESTAMP(@cutoff)
          UPDATE rt WITH {
            ip_address: REGEX_REPLACE(rt.ip_address, '\\.[0-9]+$', '.0'),
            ip_anonymized_at: DATE_ISO8601(DATE_NOW())
          } IN refresh_tokens
          RETURN 1
    """, cutoff=cutoff.isoformat())

    return {"anonymized_count": len(result)}
```

**R-05: Export-Dateien bereinigen (72 Stunden):**

```python
async def cleanup_expired_exports():
    """Löscht Export-Dateien die älter als 72 Stunden sind."""
    cutoff = datetime.utcnow() - timedelta(hours=72)

    exports = await aql("""
        FOR e IN data_export_requests
          FILTER e.status == 'completed'
          FILTER DATE_TIMESTAMP(e.completed_at) != null
          FILTER DATE_TIMESTAMP(e.completed_at) < DATE_TIMESTAMP(@cutoff)
          RETURN { _key: e._key, file_path: e.file_path }
    """, cutoff=cutoff.isoformat())

    for export in exports:
        if export["file_path"]:
            await delete_file(export["file_path"])
        await update_export_status(export["_key"], "expired")

    return {"expired_count": len(exports)}
```

### 3.3 Logging & Monitoring

Jeder Retention-Lauf wird strukturiert geloggt:

```python
log.info(
    "retention.run_completed",
    task="enforce_retention_policy",
    results={
        "hard_delete_soft_deleted_accounts": {"deleted_count": 3},
        "anonymize_session_ips": {"anonymized_count": 47},
        "cleanup_expired_exports": {"expired_count": 1},
        # ...
    },
    duration_ms=1234,
)
```

Tatsächlich protokolliert jeder Einzel-Task (§3.1) seine eigene Ergebniszeile, z.B. `retention.execute_scheduled_erasures.completed`, `anonymize_old_ips`, `retention.purge_expired_erasure_records` mit Zählern; eine gemeinsame Zeile `retention.run_completed` gibt es nicht.

**Prometheus-Metriken:** **Nicht implementiert** (Stand #1782): Das Backend hat keine Metrik-Pipeline; die folgenden Metriken sind Zielbild (#1800).

```python
retention_records_processed = Counter(
    'retention_records_processed_total',
    'Records processed by retention policy',
    ['category', 'action']  # action: delete, anonymize, expire
)

retention_run_duration = Histogram(
    'retention_run_duration_seconds',
    'Duration of retention policy enforcement run'
)

retention_run_errors = Counter(
    'retention_run_errors_total',
    'Errors during retention policy enforcement',
    ['category']
)
```

### 3.4 Anwendungs- und Zugriffsprotokolle (Log-Pipeline) <!-- #1781 -->

Die Retention-Matrix (§2) regelt Datenbank-Collections und Dateien. Protokollzeilen
fallen nicht darunter: Was die Anwendung auf `stdout` schreibt, liegt so lange vor, wie
die Log-Pipeline des Betreibers es aufbewahrt (Container-Runtime, Node-Rotation, ein
Log-Aggregator wie Loki). Eine Kennung, die dort landet, überdauert deshalb das Konto,
seine Löschung und den Löschnachweis (R-06). Die Anwendung stellt darum sicher, dass
ihre Protokolle keine direkte Kennung einer betroffenen Person enthalten:

| ID | Anforderung | Durchsetzung |
|----|-------------|--------------|
| L-1 | Keine Protokollzeile nennt den Kontoschlüssel. An seiner Stelle steht `subject=` — ein HMAC-SHA256 über den Schlüssel mit `LOG_PSEUDONYM_SALT` und dem Zweck-Label `log-subject` (`sub_…`, zweckgetrennt vom Tombstone-Hash). | Guard `test_privacy_logs_carry_no_plaintext_subject.py`, Selektor: die gesamten Bäume `src/backend/app/` und `src/backend/scripts/` |
| L-2 | Keine Protokollzeile nennt eine E-Mail-Adresse. An ihrer Stelle steht ein **gesalzener** Digest (`email_sha256=`, HMAC mit demselben Salt, Zweck-Label `log-email`) — ein ungesalzener SHA-256 wäre per Wörterbuch umkehrbar. | derselbe Guard |
| L-3 | Fehlertexte (`error=`) laufen durch eine Bereinigung: Kontoschlüssel → Referenz, Export-Bundle-Pfade maskiert, E-Mail-Adressen → Digest, Query-Strings und Fragmente aus URLs entfernt, Userinfo (`scheme://user:pw@`) maskiert. Die Bereinigung läuft in linearer Zeit auf einem längenbegrenzten Text. | derselbe Guard (`str(exc)` und `<name>.message` am Log-Aufruf werden abgelehnt) |
| L-4 | IP-Adressen erscheinen in Anwendungsprotokollen höchstens in der R-03-Kürzung (IPv4 letztes Oktett `0`, IPv6 `/48`, Feld `ip_prefix=`). Eine Protokollzeile hält damit nie mehr, als die Datenbank nach sieben Tagen behält. Das gilt seit #1796 auch für die Zugriffsprotokolle (L-7). | Guard (IP-Schlüsselwörter an Log-Aufrufen) |
| L-5 | API **und** Celery-Worker starten in Produktion (`DEBUG=false`) nicht ohne gültigen `ERASURE_TOMBSTONE_SALT` und nicht ohne gültigen `LOG_PSEUDONYM_SALT` (je mindestens 32 Zeichen) — ohne den Log-Salt fiele jede Referenz und jeder E-Mail-Digest auf eine Konstante zurück. | `app/main.py::insecure_default_secrets`, `app/tasks/__init__.py` (`celeryd_init`) |
| L-6 | Keine Log-Senke erhält einen API-Schlüssel, ein Passwort oder ein Einmal-Token. Die Logger `httpx`, `httpcore` und `urllib3` stehen in API **und** Worker auf `WARNING`; ein Filter entfernt Query-String und Userinfo aus ihren Zeilen, auch wenn jemand die Stufe senkt (Pfadsegmente bleiben dann stehen — Zugangsdaten im URL-Pfad deckt der Filter nicht ab). Der Console-Mail-Adapter schreibt den Bestätigungs- oder Passwort-Reset-Link nur mit `DEBUG=true` und nie den Anzeigenamen; ohne SMTP warnt die API beim Start. | Laufzeit-Guard `test_logs_carry_no_secrets_runtime.py` (echtes httpx, beide Prozesse), statischer Guard `test_logs_carry_no_secrets.py` (Secret-Namen und von ihnen abgeleitete Werte an Log-Aufrufen) |
| L-7 | Zugriffsprotokolle nennen weder volle Client-Adresse noch `X-Forwarded-For`, User-Agent, Referrer oder Query-String. uvicorn schreibt die Adresse in der R-03-Kürzung und vom Pfad nur die festen Segmente der Routen (`/api/v1/t/{}/plants/{}`), sodass Tenant-Slug, Kontoschlüssel und Download-Token nicht erscheinen — außer ein Wert gleicht zufällig einem festen Routen-Segment. Dasselbe gilt für das Zugriffsprotokoll des knowledge-service (Query-String maskiert). nginx schreibt ein eigenes Format (`kp_redacted`) mit gekürzter Adresse; SPA-Pfade wie `/password-reset/<token>` erscheinen als `/<spa-route>`. Das nginx-Fehlerprotokoll steht auf `crit`, weil sein Format nicht redigierbar ist; die wenigen Meldungen ab `crit` tragen weiterhin Client-Adresse und Anfragezeile. | Laufzeit-Guard (echte `uvicorn.access`-Records), `nginx -t` und Live-Probe |
| L-8 | Tracebacks laufen durch dieselbe Bereinigung wie L-3: Die Meldung einer Domänen-Ausnahme erscheint nur als Klasse und Fehlercode, jede andere nur bereinigt. **Grenze:** Die Bereinigung kennt dort den Kontoschlüssel nicht — ein Schlüssel oder Name im Text einer Standard- oder Drittanbieter-Ausnahme (`KeyError('<key>')`, ArangoDB-Konfliktmeldungen, Pydantic `input_value=`) wird nicht maskiert, nur E-Mail-Adressen, URL-Bestandteile und Export-Bundle-Pfade. Das gilt für structlog-Zeilen und für die Tracebacks von uvicorn und Celery. | Tests über den structlog-Renderer und den Handler-Filter in API und Worker |

**Log-Salt und Rotation (#1812).** `LOG_PSEUDONYM_SALT` verschlüsselt ausschließlich die
Log-Pseudonyme (`log-subject`, `log-email`) — auch dort, wo eine solche Referenz in einem
Datensatz landet (`requested_by_subject` in Lösch- und Mandanten-Löschnachweisen, die
um die Kontokennung bereinigten `error_message`-Texte von Löschanträgen). Ohne gültigen
Log-Salt verweigert die Löschung deshalb auch mit `DEBUG=true` jeden Lauf, bevor sie etwas
ändert — der Nachweis trüge sonst die Konstante `anon_unavailable`. Der
Tombstone-Hash, der Anfrage-Schlüssel und der Slug-Digest bleiben bei
`ERASURE_TOMBSTONE_SALT`, der nie wechseln darf. Den Log-Salt darf der Betreiber
wechseln (neuer Wert in API **und** Worker, Neustart beider): Protokollzeilen und
`requested_by_subject`-Werte von vor dem Wechsel korrelieren danach nicht mehr mit
späteren, und wer nur den neuen Salt kennt, kann alte Referenzen nicht mehr einer
Kontokennung zuordnen — auch nicht, *welches* Admin-Konto eine gespeicherte Löschung
ausgelöst hat. Soll diese Zuordnung für die R-06-Aufbewahrung (ein Jahr) nachprüfbar
bleiben, bewahrt der Betreiber den ausgemusterten Salt so lange gesichert auf; sonst
erlischt sie mit der Rotation. Weiter bricht nichts — keine Abfrage hängt vom Log-Salt ab.
Referenzen, die vor #1812 geschrieben wurden, sind mit dem Tombstone-Salt gebildet und
bleiben mit ihm nachrechenbar. Der Wert sollte sich vom Tombstone-Salt unterscheiden; die
Anwendung prüft das nicht.

**Aufbewahrung der Log-Pipeline — Betreiberpflicht, offen.** Auch pseudonyme Referenzen
sind personenbezogene Daten (Erwägungsgrund 26 DSGVO), solange der Salt existiert. Die
Aufbewahrungsdauer der Log-Pipeline MUSS deshalb begrenzt und dokumentiert sein. Sie ist
eine Infrastruktur-Entscheidung des Betreibers (Kubernetes-Log-Rotation, Loki-Retention,
Docker-`json-file`-Rotation) und wird von der Anwendung weder gesetzt noch geprüft; das
Helm-Chart dieses Repositorys betreibt keinen Log-Aggregator.

!!! question "Offene Frage (Betreiber / Datenschutzbeauftragte:r) — #1781"
    Welche Höchstfrist gilt für die Log-Pipeline? Vorschlag zur Entscheidung: **30 Tage**
    für Anwendungs- und Zugriffsprotokolle (Fehleranalyse und Sicherheitsvorfälle), mit
    einer Rotation, die ältere Zeilen löscht statt archiviert. Bis zur Entscheidung gilt
    die Frist als nicht festgelegt; sie ist im Verzeichnis der Verarbeitungstätigkeiten
    (Art. 30 DSGVO) nachzutragen.

---

## 4. Konfigurierbarkeit

**Umsetzungsstand (#1782, v1.7).** Die Settings-Klasse `Settings` hat kein Präfix; die Umgebungsvariablen heißen trotzdem wie unten (`RETENTION_…`). Jede Frist wird über `RetentionService` gelesen, und der Konstruktor prüft dieselben Untergrenzen noch einmal:

| Setting (Umgebungsvariable) | Regel | Default | Untergrenze | Auch akzeptiert (alter Name) |
|-----------------------------|-------|---------|-------------|------------------------------|
| `RETENTION_SOFT_DELETE_RETENTION_DAYS` | R-01 | 90 | 1 | `PRIVACY_HARD_DELETE_AFTER_DAYS` |
| `RETENTION_UNVERIFIED_ACCOUNT_DAYS` | R-02 | 7 | 1 | — |
| `RETENTION_IP_ANONYMIZATION_DAYS` | R-03 | 7 | 1 | — |
| `RETENTION_EXPORT_FILE_RETENTION_HOURS` | R-05 | 72 | 1 | `PRIVACY_EXPORT_RETENTION_HOURS` |
| `RETENTION_ERASURE_AUDIT_RETENTION_YEARS` | R-06 | 1 | 1 (die Frist selbst) | — |
| `RETENTION_EMAIL_CHANGE_RETENTION_HOURS` | R-07 | 24 | 1 | `PRIVACY_EMAIL_CHANGE_TTL_HOURS` |

Sind beide Namen gesetzt, gilt der `RETENTION_…`-Name. **Nicht implementiert** (kein Code liest sie, #1800): `CONSENT_RETENTION_YEARS` (R-04, kein Lösch-Task), `INVITATION_RETENTION_DAYS` (R-12, keine Löschung), `SENSOR_*` (R-14; die Intervalle stehen als Literale in `src/backend/app/data_access/timescale/migrations/003_retention_policies.sql`: 90 Tage, 2 Jahre, 5 Jahre; die ADR-003-Stufen je Klassifizierung sind nicht modelliert), `ACTOR_LOG_*` (R-15, es gibt keinen Aktor-Log-Speicher) und `HARVEST_DATA_MIN_…`/`TREATMENT_MIN_…`/`INSPECTION_MIN_…` (R-16..R-18: nichts löscht diese Daten automatisch, eine Untergrenze hätte nichts zu begrenzen). `ERASURE_TOMBSTONE_SALT` heißt im Code `ERASURE_TOMBSTONE_SALT` (ohne Präfix).

Zielbild (unverändert):

Alle Fristen sind als Konfigurationsparameter definiert und können über Umgebungsvariablen überschrieben werden:

```python
class RetentionSettings(BaseSettings):
    """Konfigurierbare Retention-Fristen."""

    # Personenbezogene Daten
    SOFT_DELETE_RETENTION_DAYS: int = 90          # R-01
    UNVERIFIED_ACCOUNT_DAYS: int = 7              # R-02
    IP_ANONYMIZATION_DAYS: int = 7                # R-03
    CONSENT_RETENTION_YEARS: int = 3              # R-04
    EXPORT_FILE_RETENTION_HOURS: int = 72         # R-05
    ERASURE_AUDIT_RETENTION_YEARS: int = 1        # R-06
    EMAIL_CHANGE_RETENTION_HOURS: int = 24        # R-07
    INVITATION_RETENTION_DAYS: int = 30           # R-12

    # Sensordaten (TimescaleDB)
    SENSOR_RAW_RETENTION_DAYS: int = 90           # R-14 Stufe 1 (alle Klassifizierungen)
    SENSOR_HOURLY_RETENTION_YEARS: int = 2        # R-14 Stufe 2 Default (INDOOR_*, GREENHOUSE)
    SENSOR_DAILY_RETENTION_YEARS: int = 5         # R-14 Stufe 3 Default (alle, ohne Opt-in)
    # <!-- Quelle: ADR-003 / W-014 -->
    SENSOR_HOURLY_RETENTION_OUTDOOR_YEARS: int = 5    # R-14 Stufe 2 für OUTDOOR_OPEN
    SENSOR_DAILY_RETENTION_GREENHOUSE_YEARS: int = 10 # R-14 Stufe 3 für GREENHOUSE (Opt-in)
    SENSOR_DAILY_RETENTION_OUTDOOR_YEARS: int = 20    # R-14 Stufe 3 für OUTDOOR_OPEN (Opt-in)
    SENSOR_EXTENDED_RETENTION_REQUIRES_OPTIN: bool = True  # Tenant-Admin muss aktiv zustimmen
    # <!-- /Quelle: ADR-003 / W-014 -->
    ACTOR_LOG_RAW_RETENTION_DAYS: int = 90        # R-15 Stufe 1
    ACTOR_LOG_AGGREGATED_RETENTION_YEARS: int = 1 # R-15 Stufe 2

    # Gesetzliche Mindestfristen (NICHT konfigurierbar unterschreitbar)
    HARVEST_DATA_MIN_RETENTION_YEARS: int = 5     # R-16, CanG
    TREATMENT_MIN_RETENTION_YEARS: int = 3        # R-17, PflSchG
    INSPECTION_MIN_RETENTION_YEARS: int = 3       # R-18, PflSchG

    # <!-- Quelle: Widerspruchsanalyse W-002 -->
    # Audit-Log-Pseudonymisierung (R-06): Pflicht-Setting ohne Default.
    # Backend startet nicht, wenn ERASURE_TOMBSTONE_SALT nicht aus dem Helm
    # Secret bereitgestellt wird — analog zur W-001-Hard-Crash-Strategie.
    # Mindestens 32 Zeichen (256 Bit Entropie). Wechsel des Salts macht
    # alle bestehenden Tombstones nicht mehr deterministisch zuordenbar
    # (was im Compliance-Sinne unkritisch ist — Pseudonymisierung soll
    # gerade nicht reversibel sein), neue Erasures nutzen den neuen Salt.
    # Wechsel daher nur bei Sicherheitsvorfall vornehmen.
    ERASURE_TOMBSTONE_SALT: str = Field(
        ...,                                       # Pflicht — kein Default
        min_length=32,
        description=(
            "Per-Instanz-Salt für SHA-256-Tombstone-Hashes in "
            "PSEUDONYMIZE_AUDIT_COLLECTIONS (REQ-025 §3.1). MUSS aus "
            "einem Secret-Store (Helm Sealed Secret) kommen. Mindestens "
            "32 Zeichen (256 Bit Entropie)."
        ),
    )
    # <!-- /Quelle: Widerspruchsanalyse W-002 -->

    model_config = SettingsConfigDict(env_prefix="RETENTION_")
```

**Wichtig:** Die gesetzlichen Mindestfristen (R-16 bis R-18) sind als untere Schranke implementiert. Die konfigurierbaren Fristen dürfen diese nicht unterschreiten; eine Validierung in der `RetentionSettings`-Klasse stellt dies sicher.

<!-- Quelle: Widerspruchsanalyse W-002 -->
**Pflicht-Setting `ERASURE_TOMBSTONE_SALT` (W-002):**

| Aspekt | Verhalten |
|--------|-----------|
| **Quelle** | Helm Sealed Secret (`RETENTION_ERASURE_TOMBSTONE_SALT`), per Pod als Env-Var |
| **Bereitstellung** | Während Initial-Deployment vom Operator generiert (z.B. `openssl rand -base64 48`) |
| **Pflicht** | `Field(...)` ohne Default — Backend startet ohne dieses Setting nicht (Hard-Crash, analog REQ-027 W-001-Strategie) |
| **Mindestlänge** | 32 Zeichen (Pydantic-Validation `min_length=32`) — sonst Startup-Crash |
| **Rotation** | Nur bei Sicherheitsvorfall. Salt-Wechsel = neue Tombstones sind nicht mehr deterministisch mit alten verknüpfbar (Pseudonymisierung bleibt gültig, lediglich nicht mehr identisch zu früheren Hashes desselben Users — das ist gewollt). |
| **Backup** | Salt MUSS in Disaster-Recovery-Backup enthalten sein, sonst sind bestehende Tombstones nach Restore nicht mehr deterministisch erzeugbar. |
| **Zugriff** | Nur Backend-Pods. Keine Frontend-Exposition, kein Logging. |
<!-- /Quelle: Widerspruchsanalyse W-002 -->

---

## 5. Interaktion mit DSGVO-Löschanfragen (REQ-025)

Wenn ein Betroffener eine Löschanfrage stellt (Art. 17 DSGVO, REQ-025), interagiert das System wie folgt mit den Retention-Fristen:

1. **Sofort löschbar:** Consent Records (nach Widerruf), Processing Restrictions, Export-Dateien
2. **Soft-Delete + Retention:** User-Account → `status: deleted`, Hard-Delete nach 90 Tagen (R-01)
3. **Anonymisierung statt Löschung:** Erntedaten (R-16), Behandlungsanwendungen (R-17) und Inspektionsprotokolle (R-18) werden **anonymisiert** (User-Referenz entfernt), aber beibehalten, wenn die gesetzliche Aufbewahrungsfrist noch läuft (Art. 17 Abs. 3 lit. b DSGVO)
4. **Shared Data:** Daten, die mehrere Betroffene betreffen (z.B. Tenant-Ressourcen), werden nicht gelöscht, sondern der User-Bezug wird entfernt

---

## 6. Abnahmekriterien

| # | Kriterium | Prüfmethode |
|---|-----------|-------------|
| AK-01 | Soft-Deleted Accounts werden nach 90 Tagen endgültig gelöscht (inkl. Edges und verknüpfte Collections) | Integration |
| AK-02 | IP-Adressen in `refresh_tokens` werden nach 7 Tagen anonymisiert (IPv4: letztes Oktett → 0) | Integration |
| AK-03 | Export-Dateien werden nach 72 Stunden vom Dateisystem entfernt | Integration |
| AK-04 | Jede Regel aus §3.1 hat einen Celery-Beat-Eintrag mit dem dort genannten Takt (seit v1.7 statt eines Master-Tasks) | Unit |
| AK-05 | Jeder Retention-Task protokolliert seinen Lauf strukturiert (structlog) mit Ergebniszählen | Integration |
| AK-06 | Prometheus-Metriken (`retention_records_processed_total`) werden pro Kategorie inkrementiert — **nicht implementiert** (#1800) | Integration |
| AK-07 | TimescaleDB Continuous Aggregates erzeugen Stunden-/Tagesmittel für Sensordaten | Integration |
| AK-08 | TimescaleDB Retention Policies löschen Rohdaten nach 90 Tagen, Stundendaten nach 2 Jahren, Tagesdaten nach 5 Jahren | Integration |
| AK-09 | Erntedaten und Behandlungsanwendungen werden bei Löschanfrage anonymisiert (User-Referenz entfernt), aber nicht gelöscht | Integration |
| AK-10 | Konfigurierbare Fristen können per Umgebungsvariable überschrieben werden, unterschreiten aber nicht ihre Untergrenze (§4); jede Frist wird aus genau einem Setting gelesen | Unit |
| AK-11 | Unbestätigte Accounts werden nach `RETENTION_UNVERIFIED_ACCOUNT_DAYS` (Default 7) Tagen gelöscht | Integration |
<!-- Quelle: Widerspruchsanalyse W-002 -->
| AK-12 | **Pflicht-Setting `ERASURE_TOMBSTONE_SALT`:** Backend startet nicht, wenn die Umgebungsvariable `RETENTION_ERASURE_TOMBSTONE_SALT` nicht gesetzt oder kürzer als 32 Zeichen ist (Pydantic `Field(..., min_length=32)`). Fehlermeldung verweist auf NFR-011 §4. | Integration |
| AK-13 | **R-06 Phase-Reihenfolge:** Im Erasure-Lauf (REQ-025 §3.5) wird die Pseudonymisierung der `erasure_requests`-Collection AUSGEFÜHRT, bevor der User selbst hard-deleted wird. Der Hard-Delete des Audit-Eintrags selbst erfolgt erst nach Ablauf von `ERASURE_AUDIT_RETENTION_YEARS` (Default 1 Jahr). | Integration |
<!-- /Quelle: Widerspruchsanalyse W-002 -->
<!-- Quelle: #1788 -->
| AK-PT-01 | **Persönlicher Mandant geht mit dem Konto:** Nach Abschluss einer Kontolöschung (Selbstbedienung, Plattform-Admin, Bereinigung unverifizierter Konten) ist von jedem persönlichen Mandanten, dessen einziges aktives Mitglied die Person war, keine Zeile mehr übrig außer den Aufbewahrungsdaten nach NFR-011 R-16 bis R-18 (Kontoschlüssel = Tombstone-Hash, Freitextnamen leer); ein `tenant_erasure_records`-Eintrag mit `origin: account_erasure` steht auf `completed`. | Integration + Reach (T2) |
| AK-PT-02 | **Nachweis im Löschauftrag:** Der Löschauftrag nennt je persönlichem Mandanten das Ergebnis (`erased` mit Schlüssel des Mandanten-Löschnachweises, `retained_other_members` mit Grund, `absent`) und ist erst `completed`, wenn jeder dieser Mandanten gelöscht oder begründet erhalten ist. Scheitert die Mandantenlöschung, bleibt der Auftrag offen und der ArangoDB-Plan läuft nicht; die Wiederholung erreicht den Mandanten über die im Auftrag gespeicherten Schlüssel, auch wenn er nicht mehr über den Eigentümer auffindbar ist. | Unit + Integration |
| AK-PT-03 | **Geteilter persönlicher Mandant bleibt:** Hat ein persönlicher Mandant der Person ein weiteres aktives Mitglied, bleibt er samt Daten erhalten; nur Eigentümer, Name und Kurzname werden ersetzt (REQ-025 §3.1.3 Regel 2). Kann das Deployment keinen Mandanten löschen, verweigert die Kontolöschung vor jeder Änderung (REQ-025 AK-IE-02). | Unit + Integration |
<!-- /Quelle: #1788 -->

---

## 7. Abhängigkeiten

### Abhängig von (bestehend):

| REQ/NFR | Bezug |
|---------|-------|
| REQ-023 | User-Datenmodell, RefreshToken-Collection, Celery-Tasks |
| REQ-024 | Membership- und Invitation-Collections |
| NFR-001 | Architektur-Layer (Tasks in Business Logic Layer) |

### Wird benötigt von:

| REQ/NFR | Bezug |
|---------|-------|
| REQ-025 | Datenschutz & Betroffenenrechte — referenziert Löschfristen aus dieser NFR |
| REQ-005 | Sensordaten-Retention (TimescaleDB Downsampling) |
| REQ-018 | Aktor-Log-Retention |

### Neue Infrastruktur-Abhängigkeiten:

| Komponente | Zweck |
|------------|-------|
| Celery Beat | Scheduling der Retention-Einzel-Tasks (§3.1) |
| TimescaleDB Continuous Aggregates | Automatische Sensordaten-Aggregierung |
| Prometheus | Monitoring der Retention-Läufe |

---

## 8. Scope-Abgrenzung

**In Scope:**
- Automatische Durchsetzung aller Retention-Fristen via Celery
- IP-Anonymisierung nach 7 Tagen
- Sensordaten-Downsampling in TimescaleDB (3-stufig)
- Konfigurierbare Fristen mit gesetzlichen Mindestschranken
- Monitoring und strukturiertes Logging

**Nicht in Scope:**
- Manuelle Löschanfragen durch Betroffene → REQ-025
- Consent-Management → REQ-025
- Verzeichnis von Verarbeitungstätigkeiten (Art. 30 DSGVO) → separates Organisationsdokument
- Datenschutz-Folgenabschätzung (Art. 35 DSGVO) → separates Bewertungsdokument

---

**Dokumenten-Ende**

**Version**: 1.7
**Status**: Genehmigt
**Datum**: 2026-02-27
**Security-Review**: Adressiert SEC-K-001, SEC-K-002, SEC-K-005
**Review**: Genehmigt
**Genehmigung**: Genehmigt (2026-06-11)
