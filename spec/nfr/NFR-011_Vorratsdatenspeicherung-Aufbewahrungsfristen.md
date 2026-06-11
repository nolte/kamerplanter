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
Version: 1.4 (Sensor-Retention nach data_classification, ADR-003)
Datum: 2026-04-27
Tags: [dsgvo, retention, datensparsamkeit, loeschfristen, compliance, cross-cutting]
Abhängigkeiten: [REQ-023, REQ-024, REQ-025 v1.1, NFR-001]
Betroffene Module: [ALL]
Security-Review-Referenz: SEC-K-001, SEC-K-002, SEC-K-005
```

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.4 | 2026-04-27 | **ADR-003 (W-014 Sensor-Retention für Perennials):** R-14 differenziert nach `Location.data_classification` (REQ-002): `OUTDOOR_OPEN` Stufe 2 = 5y, Stufe 3 = 20y (Opt-in); `GREENHOUSE` Stufe 3 = 10y (Opt-in); `INDOOR_*` und `UNKNOWN` weiterhin 5y. Forward-only-Klassifizierungs-Wechsel. Vier neue Settings. R-19a für Saison-Aggregate-Anonymisierung bei User-Löschung. |
| 1.3 | 2026-04-27 | **ADR-002 (W-006 Promotion-Audit):** R-19 ergänzt — `promotion_audit_log`-Collection mit 5 Jahren Aufbewahrung. Begründung: Bei Sortenrechts-Streitigkeiten relevant; konsistent mit Erntedaten-Retention (R-16). |
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
| R-01 | Soft-Deleted User-Accounts | `users` (status: `deleted`) | 90 Tage nach Soft-Delete | Hard-Delete: Account-Daten endgültig entfernen, E-Mail-Hash für Duplikatprüfung behalten | Art. 17 DSGVO, Art. 5(1)(e) | REQ-023 §2, REQ-025 |
| R-02 | Unbestätigte Accounts | `users` (status: `unverified`) | 7 Tage nach Erstellung | Hard-Delete: Account und zugehörige Auth-Provider entfernen | Art. 5(1)(e), Zweckentfall | REQ-023 §3.5 |
| R-03 | IP-Adressen in Sessions | `refresh_tokens` (Feld: `ip_address`) | 7 Tage nach Speicherung | Anonymisierung: IPv4 letztes Oktett → `0`, IPv6 → `/48`-Präfix behalten | Art. 6(1)(f) berechtigtes Interesse, Art. 5(1)(c) Datenminimierung | REQ-023 §2 |
| R-04 | Consent Records | `consent_records` | 3 Jahre nach Widerruf | Hard-Delete | Art. 7(1) Nachweispflicht | REQ-025 |
| R-05 | Export-Dateien | Dateisystem (Export-Verzeichnis) | 72 Stunden nach Erstellung | Datei löschen, Status auf `expired` setzen | Art. 15/20 DSGVO, Zweckentfall | REQ-025 |
| R-06 | Erasure-Audit-Logs | `erasure_requests` | 1 Jahr nach Abschluss | **Pseudonymisierung sofort nach User-Hard-Delete (`user_key` → Tombstone-Hash via REQ-025 §3.1 Phase 2.5), anschließend Hard-Delete des Audit-Eintrags nach 1 Jahr** <!-- W-002 --> | Art. 5(2) Rechenschaftspflicht + Art. 5(1)(e) Speicherbegrenzung | REQ-025 |
| R-07 | E-Mail-Änderungsanfragen | `email_change_requests` | 24 Stunden nach Erstellung | Hard-Delete (abgelaufene Tokens) | Zweckentfall | REQ-025 |
| R-08 | Passwort-Reset-Tokens | `users` (Felder: `password_reset_token`, `password_reset_expires`) | 1 Stunde (besteht) | Token-Felder nullen | REQ-023 §1 | REQ-023 |
| R-09 | E-Mail-Verifikations-Tokens | `users` (Felder: `email_verification_token`, `email_verification_expires`) | 24 Stunden (besteht) | Token-Felder nullen | REQ-023 §1 | REQ-023 |
| R-10 | OAuth State | Redis | 5 Minuten (besteht, Redis TTL) | Automatische Bereinigung durch Redis | REQ-023 §3.2 | REQ-023 |
| R-11 | Abgelaufene Refresh Tokens | `refresh_tokens` | Sofort nach Ablauf | Hard-Delete (TTL-Index besteht) | Zweckentfall | REQ-023 §2 |
| R-12 | Einladungen (abgelaufen) | `invitations` | 30 Tage nach Ablauf | Hard-Delete | Zweckentfall | REQ-024 |
| R-13 | Processing Restrictions | `processing_restrictions` | Unbegrenzt (bis Aufhebung durch Betroffenen) | Nur auf expliziten Wunsch entfernen | Art. 18 DSGVO | REQ-025 |
| R-19 | Gießdienst-Rotation (DutyRotation) | `duty_rotations` | Unbegrenzt (bei User-Löschung: User-Referenz anonymisieren) | Anonymisierung: User-Referenz auf NULL, Dienst-Zeitraum bleibt | Art. 17 Abs. 3 (berechtigtes Interesse Tenant) | REQ-024 v1.2 |
| R-20 | Pinnwand-Beiträge (BulletinPost/Comment) | `bulletin_posts`, `bulletin_comments` | Bei User-Löschung: User-Referenz anonymisieren, Inhalt bleibt | Anonymisierung | Art. 17 Abs. 3 (berechtigtes Interesse Tenant) | REQ-024 v1.2 |
| R-21 | Einkaufslisten (SharedShoppingList) | `shared_shopping_lists` | Bei User-Löschung: User-Referenz anonymisieren | Anonymisierung | Art. 17 Abs. 3 (berechtigtes Interesse Tenant) | REQ-024 v1.2 |
| R-22 | Aufgaben-Bewertungen (Task difficulty/quality ratings) | `tasks` (Felder: `difficulty_rating`, `quality_rating`, `assigned_to`) | Bei User-Löschung: `assigned_to` auf NULL setzen, Bewertungen bleiben (aggregiert nutzbar) | Anonymisierung | Art. 17 Abs. 3 (Lern-System benötigt Aggregatdaten) | REQ-006 |
| R-19a <!-- ADR-003 --> | Saison-Aggregate (`seasonal_cycles.sensor_aggregates`) | `seasonal_cycles` (Feld `aggregate_computed_by`) | Aggregate bleiben unbegrenzt (keine personenbezogenen Daten); bei User-Löschung `aggregate_computed_by → NULL` | Anonymisierung | Art. 17 Abs. 3 (fachliche Trendanalyse über Pflanzenleben) | REQ-003 v2.x, REQ-025 |

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
| R-19 <!-- ADR-002 --> | Promotion-Audit-Log (Species/Cultivar tenant→global) | `promotion_audit_log` | 5 Jahre | Sortenrechts-Streitigkeiten, Art. 5(2) Rechenschaftspflicht | REQ-001 v4.1 |

**Wichtig:** Bei einer Löschanfrage (Art. 17 DSGVO) durch einen Betroffenen werden diese Daten **anonymisiert** (User-Referenz entfernt), aber nicht gelöscht, solange die gesetzliche Aufbewahrungsfrist läuft (Art. 17 Abs. 3 lit. b).

<!-- Quelle: ADR-001 / W-009 -->
**R-17 Klarstellung — geerbte Treatment-Edges (ADR-001):**

Beim Detach einer PlantInstance werden aktive Run-Level-Treatments als `to_plant`-Edges mit `inherited_from_run`-Property auf die Plant kopiert (Karenz-Snapshot). Diese geerbten Edges teilen die 3-Jahre-Aufbewahrungsfrist des Original-Treatments. Die Fristberechnung erfolgt anhand des Original-`applied_at`-Timestamps des `treatment_applications`-Dokuments — nicht anhand des `inherited_at`-Timestamps der Edge.

Konsequenz: Bei Hard-Delete des Original-Treatments nach 3 Jahren werden auch alle abhängigen Edges (`to_plant`, `to_run`, geerbte `to_plant`) im selben Schritt entfernt. Pflanzen, die historisch detached wurden, verlieren damit ihren Karenz-Snapshot — der ist nach 3 Jahren ohnehin nicht mehr karenzwirksam.
<!-- /Quelle: ADR-001 / W-009 -->

---

## 3. Technische Umsetzung: Celery-Enforcement

### 3.1 Master-Task

Der Master-Task `enforce_retention_policy` läuft täglich um 02:00 UTC und dispatcht Sub-Tasks für jede Datenkategorie:

```python
# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    "enforce-retention-policy": {
        "task": "app.tasks.retention.enforce_retention_policy",
        "schedule": crontab(hour=2, minute=0),  # Täglich 02:00 UTC
    },
}
```

```python
class RetentionMasterTask:
    """Orchestriert alle Retention-Sub-Tasks."""

    SUB_TASKS = [
        "hard_delete_soft_deleted_accounts",    # R-01: 90 Tage
        "hard_delete_unverified_accounts",      # R-02: 7 Tage (besteht)
        "anonymize_session_ips",                # R-03: 7 Tage
        "cleanup_expired_consents",             # R-04: 3 Jahre nach Widerruf
        "cleanup_expired_exports",              # R-05: 72 Stunden
        "cleanup_erasure_audits",               # R-06: 1 Jahr
        "cleanup_expired_email_changes",        # R-07: 24 Stunden
        "cleanup_expired_tokens",               # R-08/R-09/R-11
        "cleanup_expired_invitations",          # R-12: 30 Tage nach Ablauf
    ]

    def run(self):
        results = {}
        for task_name in self.SUB_TASKS:
            result = dispatch_sub_task(task_name)
            results[task_name] = result
        log_retention_run(results)
        return results
```

### 3.2 Sub-Tasks (Beispiele)

**R-01: Hard-Delete Soft-Deleted Accounts (90 Tage):**

```python
async def hard_delete_soft_deleted_accounts():
    """Löscht Accounts die seit > 90 Tagen im Status 'deleted' sind."""
    cutoff = datetime.utcnow() - timedelta(days=90)

    # AQL: Finde alle soft-deleted Accounts älter als 90 Tage
    accounts = await aql("""
        FOR u IN users
          FILTER u.status == 'deleted'
          FILTER u.updated_at < @cutoff
          RETURN u._key
    """, cutoff=cutoff.isoformat())

    for user_key in accounts:
        # Löschreihenfolge: Edges vor Nodes
        await delete_edges_for_user(user_key)  # has_auth_provider, has_session, etc.
        await delete_collection_docs("auth_providers", user_key)
        await delete_collection_docs("refresh_tokens", user_key)
        await delete_collection_docs("consent_records", user_key)
        await delete_user(user_key)
        log.info("retention.hard_delete_account", user_key=user_key)

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
          FILTER rt.issued_at < @cutoff
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
          FILTER e.completed_at < @cutoff
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

**Prometheus-Metriken:**

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

---

## 4. Konfigurierbarkeit

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
| AK-04 | Celery-Master-Task läuft täglich um 02:00 UTC und dispatcht alle Sub-Tasks | Integration |
| AK-05 | Jeder Retention-Lauf wird strukturiert geloggt (structlog) mit Ergebniszählen pro Kategorie | Integration |
| AK-06 | Prometheus-Metriken (`retention_records_processed_total`) werden pro Kategorie inkrementiert | Integration |
| AK-07 | TimescaleDB Continuous Aggregates erzeugen Stunden-/Tagesmittel für Sensordaten | Integration |
| AK-08 | TimescaleDB Retention Policies löschen Rohdaten nach 90 Tagen, Stundendaten nach 2 Jahren, Tagesdaten nach 5 Jahren | Integration |
| AK-09 | Erntedaten und Behandlungsanwendungen werden bei Löschanfrage anonymisiert (User-Referenz entfernt), aber nicht gelöscht | Integration |
| AK-10 | Konfigurierbare Fristen können per Umgebungsvariable überschrieben werden, unterschreiten aber nicht die gesetzlichen Mindestfristen | Unit |
| AK-11 | Unbestätigte Accounts werden nach 7 Tagen gelöscht (bestehender Task, jetzt in Master-Task integriert) | Integration |
<!-- Quelle: Widerspruchsanalyse W-002 -->
| AK-12 | **Pflicht-Setting `ERASURE_TOMBSTONE_SALT`:** Backend startet nicht, wenn die Umgebungsvariable `RETENTION_ERASURE_TOMBSTONE_SALT` nicht gesetzt oder kürzer als 32 Zeichen ist (Pydantic `Field(..., min_length=32)`). Fehlermeldung verweist auf NFR-011 §4. | Integration |
| AK-13 | **R-06 Phase-Reihenfolge:** Im Erasure-Lauf (REQ-025 §3.5) wird die Pseudonymisierung der `erasure_requests`-Collection AUSGEFÜHRT, bevor der User selbst hard-deleted wird. Der Hard-Delete des Audit-Eintrags selbst erfolgt erst nach Ablauf von `ERASURE_AUDIT_RETENTION_YEARS` (Default 1 Jahr). | Integration |
<!-- /Quelle: Widerspruchsanalyse W-002 -->

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
| Celery Beat | Scheduling des Master-Tasks (täglich 02:00 UTC) |
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

**Version**: 1.4
**Status**: Genehmigt
**Datum**: 2026-02-27
**Security-Review**: Adressiert SEC-K-001, SEC-K-002, SEC-K-005
**Review**: Genehmigt
**Genehmigung**: Genehmigt (2026-06-11)
