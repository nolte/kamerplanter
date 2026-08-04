# Spezifikation: REQ-025 - Datenschutz & Betroffenenrechte (DSGVO)

```yaml
ID: REQ-025
Titel: Datenschutz & Betroffenenrechte (DSGVO)
Kategorie: Plattform & Datenschutz
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, Celery, React, TypeScript, MUI
Status: Entwurf
Version: 1.5 (REQ-050: diary_ai_analysis-Consent + Präzisierung des KI-Assistent-Zwecks)
Abhängigkeit: REQ-023 v1.10 (Benutzerverwaltung), REQ-024 v1.6 (Mandantenverwaltung), NFR-011 v1.1 (Retention Policy), NFR-013 v1.3 (Object Storage), REQ-029-A v1.1 (DINOv2-Referenz-Index), REQ-034 v1.1 (Pflanzenfoto-Galerie), REQ-050 v1.0 (KI-Analyse von Tagebuch-Einträgen)
Security-Review-Referenz: SEC-K-001, SEC-K-003
```

### Changelog

| Version | Datum | Änderungen |
|---------|-------|-----------|
| 1.5 | 2026-08-04 | **REQ-050 KI-Analyse von Tagebuch-Einträgen:** Neuer Consent-Purpose `diary_ai_analysis` (Art. 6(1)(a), opt-in **je Eintrag**, nie automatisch). Gleichzeitig **Widerspruch aufgelöst:** Der Zwecktext von `ai_tenant_data_access` sagte pauschal, Tagebuch-Freitexte würden „NIE" übertragen. Diese Zusage gilt für den **serverseitigen** Assistenten (REQ-031) und ist entsprechend präzisiert; sie darf nicht als Verbot der ausdrücklich vom Nutzer ausgelösten Freigabe nach REQ-050 gelesen werden. Beide Wege sind getrennt und einzeln einwilligungspflichtig. |
| 1.4 | 2026-06-19 | **REQ-034 Pflanzenfoto-Galerie (Security-Review SR-001/SR-003):** Neuer Consent-Purpose `reference_contribution` in `ConsentEngine.PURPOSES` (opt-in Foto-Beitrag zum DINOv2-Index, Art. 6(1)(a), global pro Nutzer). `user_diary_attachments`-Cleanup-Regel um `category 'plant'` erweitert. Neue Erasure-**Phase 0.5** `_reference_index_cleanup` (pgvector): entfernt vom Nutzer beigesteuerte `user_contributed`-Embeddings via Provenienz `contributed_by`/`tenant_key` VOR der ArangoDB-Löschung. Neues Abnahmekriterium AK-OS-05. |
| 1.3 | 2026-04-27 | **ADR-002 (W-006 Tenant-Species im Export):** `SpeciesReferenceResolver` + `species_ref`-Wrapper-Struktur ergänzt. Tenant-eigene Species werden inline als Snapshot exportiert (DSGVO Art. 20 Datenübertragbarkeit). Globale Species bleiben als Referenz mit `scope='global'`. Neue `DataSourceDefinition`s für `tenant_species_config` und `tenant_cultivar_config`. |
| 1.2 | 2026-04-27 | **W-007 Fix (Object-Storage-Cleanup Phase 0):** Erasure-Pipeline um Phase 0 erweitert, die VOR allen ArangoDB-Operationen den Object Storage bereinigt. Zwei Scopes: `user_personal` (Hard-Delete von Profilfoto/persönlichen Notiz-Fotos) und `user_diary_attachments` (Anonymisierung der `created_by`-Metadaten + EXIF-Strip-Pass für Tenant-Datensätze mit `STORAGE_KEEP_EXIF=true`). Erasure-Reihenfolge: Phase 0 → Phase 1 (Edges) → Phase 2 (Documents) → Phase 2.5 (Audit-Pseudonymisierung) → Phase 3 (User). Drei neue Abnahmekriterien (AK-OS-01 bis AK-OS-03). |
| 1.1 | 2026-04-27 | **W-002 Fix (Audit-Pseudonymisierung):** Phase 2.5 (Audit-Log-Pseudonymisierung) im `ErasureEngine` ergänzt. Generischer Mechanismus über `PSEUDONYMIZE_AUDIT_COLLECTIONS`-Liste — aktuell ein Eintrag (`erasure_requests.user_key`). Tombstone-Hash via SHA-256 + 64 Bit Truncation + Per-Instanz-Salt (`ERASURE_TOMBSTONE_SALT`, NFR-011 §4 Pflicht-Setting). Zwei neue Abnahmekriterien (AK-PD-01, AK-PD-02). |
| 1.0 | 2026-02-27 | Erstversion — DSGVO Art. 15–21 Betroffenenrechte, ErasureEngine, ConsentEngine, Celery-Tasks, Privacy-API. |

## 1. Business Case

**User Story (Auskunft — Art. 15):** "Als registrierter Nutzer möchte ich alle über mich gespeicherten personenbezogenen Daten in einem maschinenlesbaren Format herunterladen können — damit ich weiß, welche Informationen das System über mich hat, und mein Auskunftsrecht nach DSGVO Art. 15 wahrnehmen kann."

**User Story (Berichtigung — Art. 16):** "Als Nutzer möchte ich meine E-Mail-Adresse ändern können — damit meine Kontaktdaten aktuell sind und ich mein Recht auf Berichtigung nach DSGVO Art. 16 ausüben kann."

**User Story (Löschung — Art. 17):** "Als Nutzer, der das System nicht mehr nutzen möchte, möchte ich die Löschung meines Accounts und aller zugehörigen personenbezogenen Daten beantragen können — damit mein Recht auf Löschung nach DSGVO Art. 17 umgesetzt wird. Ich verstehe, dass gesetzlich geschützte Daten (Erntedokumentation, IPM-Behandlungsnachweise) anonymisiert statt gelöscht werden (Art. 17 Abs. 3 lit. b)."

**User Story (Einschränkung — Art. 18):** "Als Nutzer möchte ich die Verarbeitung meiner Daten für bestimmte Zwecke einschränken können — beispielsweise wenn ich die Richtigkeit meiner Daten bestreite oder die Verarbeitung für unrechtmäßig halte."

**User Story (Datenportabilität — Art. 20):** "Als Nutzer möchte ich meine Daten in einem strukturierten, maschinenlesbaren Format exportieren können — damit ich sie in ein anderes System übertragen kann."

**User Story (Widerspruch — Art. 21):** "Als Nutzer möchte ich der Verarbeitung meiner Daten zu bestimmten Zwecken widersprechen können — insbesondere wenn die Verarbeitung auf berechtigtem Interesse (Art. 6(1)(f)) basiert."

**User Story (Einwilligung):** "Als Nutzer möchte ich jederzeit nachvollziehen können, welche Einwilligungen ich erteilt habe, und diese einzeln widerrufen können — damit ich die Kontrolle über meine Daten behalte."

**Beschreibung:**
Kamerplanter verarbeitet personenbezogene Daten (E-Mail, Name, IP-Adressen, Nutzungsverhalten, indirekt Sensordaten). Die DSGVO verpflichtet den Verantwortlichen, Betroffenenrechte (Art. 15–21) technisch und organisatorisch umzusetzen. Diese REQ spezifiziert die vollständige technische Implementierung aller Betroffenenrechte als Self-Service-Funktionalität.

**Kernkonzepte:**

- **Datenexport (Art. 15/20):** Asynchrone Zusammenstellung aller User-Daten als JSON-Download
- **E-Mail-Änderung (Art. 16):** Zweistufig mit Token-Verifikation der neuen Adresse
- **Kontolöschung (Art. 17):** Soft-Delete → 90-Tage-Retention (NFR-011 R-01) → Hard-Delete. Gesetzlich geschützte Daten werden anonymisiert statt gelöscht (Art. 17 Abs. 3 lit. b)
- **Verarbeitungseinschränkung (Art. 18):** Zweckbezogene Sperren, die bei Datenverarbeitung geprüft werden
- **Widerspruch (Art. 21):** Zweckbezogener Opt-out, technisch identisch mit Einschränkung für Verarbeitungen auf Basis von Art. 6(1)(f)
- **Consent-Tracking:** Nachweisbare Einwilligungen pro Verarbeitungszweck mit Zeitstempel

### 1.1 Szenarien

**Szenario 1: Datenexport — Nutzer fordert Auskunft an**
```
1. Nutzer navigiert zu /settings/privacy
2. Klickt "Meine Daten exportieren"
3. System erstellt Export-Auftrag (status: pending)
4. Celery-Task sammelt alle Daten des Nutzers aus allen Collections
5. JSON-Datei wird erstellt und zum Download bereitgestellt
6. Nutzer erhält Benachrichtigung (E-Mail oder In-App)
7. Download-Link ist 72 Stunden gültig (NFR-011 R-05)
```

**Szenario 2: E-Mail-Änderung — Nutzer korrigiert Kontaktdaten**
```
1. Nutzer navigiert zu /settings/privacy
2. Gibt neue E-Mail-Adresse ein
3. System prüft: Adresse nicht bereits vergeben
4. Verifikations-E-Mail wird an die NEUE Adresse gesendet
5. Nutzer klickt Verifikations-Link
6. E-Mail wird aktualisiert, alte E-Mail erhält Info-Mail
7. Alle bestehenden Sessions werden invalidiert (Neuanmeldung erforderlich)
```

**Szenario 3: Account-Löschung — Nutzer verlässt das System**
```
1. Nutzer navigiert zu /settings/privacy → Tab "Account löschen"
2. Bestätigt mit Passwort (oder OAuth Re-Auth)
3. System erstellt Löschauftrag (status: scheduled)
4. Sofort: Soft-Delete (status: deleted), alle Sessions invalidiert
5. Erntedaten/Behandlungen: User-Referenz anonymisiert, Daten bleiben (CanG/PflSchG)
6. Nach 90 Tagen (NFR-011 R-01): Hard-Delete aller verbleibenden Daten
7. Erasure-Audit-Log wird für 1 Jahr aufbewahrt (NFR-011 R-06)
```

**Szenario 4: Einwilligungsverwaltung**
```
1. Nutzer navigiert zu /settings/privacy → Tab "Einwilligungen"
2. Sieht Liste aller Verarbeitungszwecke:
   - "Grundfunktionen" (erforderlich, nicht widerrufbar)
   - "Fehler-Tracking (Sentry)" (optional)
   - "HaveIBeenPwned Passwort-Check" (optional)
   - "Externe Stammdatenanreicherung" (optional)
3. Kann optionale Einwilligungen einzeln widerrufen
4. System speichert Widerruf mit Zeitstempel
```

---

## 2. ArangoDB-Modellierung

### Nodes:

- **`:DataExportRequest`** — Export-Auftrag (Art. 15/20)
  - Collection: `data_export_requests`
  - Properties:
    - `user_key: str` (Referenz auf `users`)
    - `status: Literal['pending', 'processing', 'completed', 'expired', 'failed']`
    - `file_path: Optional[str]` (Pfad zur generierten JSON-Datei)
    - `file_size_bytes: Optional[int]`
    - `requested_at: datetime`
    - `processing_started_at: Optional[datetime]`
    - `completed_at: Optional[datetime]`
    - `expires_at: Optional[datetime]` (72h nach Fertigstellung, NFR-011 R-05)
    - `error_message: Optional[str]` (bei Status `failed`)
    - `download_count: int` (Default: 0)

- **`:ConsentRecord`** — Einwilligung pro Verarbeitungszweck
  - Collection: `consent_records`
  - Properties:
    - `user_key: str` (Referenz auf `users`)
    - `purpose: str` (z.B. `sentry_tracking`, `hibp_check`, `external_enrichment`)
    - `granted: bool` (true = erteilt, false = widerrufen)
    - `granted_at: Optional[datetime]`
    - `revoked_at: Optional[datetime]`
    - `ip_address: Optional[str]` (IP bei Einwilligungserteilung, anonymisiert nach 7d)
    - `user_agent: Optional[str]` (Browser bei Einwilligung)
    - `consent_version: str` (Version der Datenschutzerklärung, z.B. "1.0")

- **`:ProcessingRestriction`** — Verarbeitungseinschränkung (Art. 18)
  - Collection: `processing_restrictions`
  - Properties:
    - `user_key: str` (Referenz auf `users`)
    - `scope: str` (z.B. `all`, `sensor_data`, `analytics`, `enrichment`)
    - `reason: Literal['accuracy_contested', 'unlawful_processing', 'purpose_expired', 'objection_pending']`
    - `created_at: datetime`
    - `lifted_at: Optional[datetime]`
    - `notes: Optional[str]`

- **`:ErasureRequest`** — Löschauftrag (Art. 17)
  - Collection: `erasure_requests`
  - Properties:
    - `user_key: str` (Referenz auf `users`)
    - `status: Literal['scheduled', 'in_progress', 'completed', 'partially_completed']`
    - `requested_at: datetime`
    - `soft_deleted_at: Optional[datetime]`
    - `hard_delete_scheduled_at: Optional[datetime]` (90 Tage nach Soft-Delete)
    - `completed_at: Optional[datetime]`
    - `anonymized_collections: list[str]` (Collections in denen User-Referenz anonymisiert wurde)
    - `deleted_collections: list[str]` (Collections die vollständig gelöscht wurden)
    - `retained_reason: Optional[str]` (z.B. "CanG §X: Erntedaten 5 Jahre")

- **`:EmailChangeRequest`** — E-Mail-Änderungsauftrag (Art. 16)
  - Collection: `email_change_requests`
  - Properties:
    - `user_key: str` (Referenz auf `users`)
    - `new_email: str` (gewünschte neue E-Mail)
    - `verification_token_hash: str` (SHA-256 Hash des Tokens)
    - `status: Literal['pending', 'confirmed', 'expired']`
    - `requested_at: datetime`
    - `expires_at: datetime` (24h nach Erstellung)
    - `confirmed_at: Optional[datetime]`

### Edges:

```
requested_export:      users → data_export_requests    (1:N, User hat Export-Aufträge)
has_consent:           users → consent_records          (1:N, User hat Einwilligungen)
has_restriction:       users → processing_restrictions  (1:N, User hat Verarbeitungssperren)
requested_erasure:     users → erasure_requests         (1:N, User hat Löschaufträge)
requested_email_change: users → email_change_requests   (1:N, User hat E-Mail-Änderungen)
```

### Indizes:

```
data_export_requests:
  - PERSISTENT INDEX on [user_key]
  - PERSISTENT INDEX on [status]
  - PERSISTENT INDEX on [expires_at]

consent_records:
  - PERSISTENT INDEX on [user_key, purpose] UNIQUE  (eine Einwilligung pro Zweck)
  - PERSISTENT INDEX on [user_key]

processing_restrictions:
  - PERSISTENT INDEX on [user_key]
  - PERSISTENT INDEX on [user_key, scope] UNIQUE  (eine Sperre pro Scope)

erasure_requests:
  - PERSISTENT INDEX on [user_key]
  - PERSISTENT INDEX on [status]
  - PERSISTENT INDEX on [hard_delete_scheduled_at]

email_change_requests:
  - PERSISTENT INDEX on [user_key]
  - PERSISTENT INDEX on [verification_token_hash] UNIQUE
  - TTL INDEX on [expires_at] expireAfter: 0  (automatische Bereinigung)
```

---

## 3. Backend-Architektur

### 3.1 Engine-Schicht

**`DataExportEngine`** — Daten-Zusammenstellung (pure Logik, kein I/O):

```python
class DataExportEngine:
    """Definiert das Manifest aller User-bezogenen Daten-Collections."""

    # Manifest: Welche Collections enthalten User-bezogene Daten?
    USER_DATA_MANIFEST: list[DataSourceDefinition] = [
        DataSourceDefinition(
            collection="users",
            filter_field="_key",
            label="Profildaten",
            fields=["email", "display_name", "avatar_url", "locale",
                    "timezone", "status", "email_verified", "created_at"],
        ),
        DataSourceDefinition(
            collection="auth_providers",
            edge_collection="has_auth_provider",
            label="Verknüpfte Authentifizierungs-Provider",
            fields=["provider", "provider_email", "linked_at", "last_used_at"],
        ),
        DataSourceDefinition(
            collection="refresh_tokens",
            edge_collection="has_session",
            label="Aktive Sessions",
            fields=["device_info", "ip_address", "issued_at", "expires_at"],
        ),
        DataSourceDefinition(
            collection="memberships",
            edge_collection="has_membership",
            label="Tenant-Mitgliedschaften",
            fields=["role", "joined_at"],
        ),
        DataSourceDefinition(
            collection="consent_records",
            edge_collection="has_consent",
            label="Einwilligungen",
            fields=["purpose", "granted", "granted_at", "revoked_at"],
        ),
        # Tenant-scoped Daten (über created_by / assigned_to)
        DataSourceDefinition(
            collection="tasks",
            filter_field="assigned_to",
            label="Zugewiesene Aufgaben",
            fields=["title", "status", "due_date", "completed_at"],
        ),
        DataSourceDefinition(
            collection="harvest_batches",
            filter_field="harvester",
            label="Erntedaten",
            fields=["name", "status", "started_at", "completed_at"],
        ),
        DataSourceDefinition(
            collection="inspections",
            filter_field="inspector",
            label="Inspektionsprotokolle",
            fields=["type", "date", "findings"],
        ),
        # <!-- Quelle: ADR-002 / W-006 -->
        # Tenant-eigene Stammdaten und Overlays (Schicht 2 + 3) — DSGVO Art. 20
        DataSourceDefinition(
            collection="tenant_species_config",
            filter_field="tenant_key",            # Alle Overlays des Tenants
            label="Tenant-Anpassungen an Species",
            fields=["species_key", "notes", "hidden", "custom_fields"],
        ),
        DataSourceDefinition(
            collection="tenant_cultivar_config",
            filter_field="tenant_key",
            label="Tenant-Anpassungen an Cultivars",
            fields=["cultivar_key", "notes", "hidden", "custom_fields"],
        ),
        # <!-- /Quelle: ADR-002 / W-006 -->
    ]

    def build_export_manifest(self, user_key: str) -> list[DataSourceDefinition]:
        """Gibt das vollständige Manifest für einen User zurück."""
        return self.USER_DATA_MANIFEST

    def validate_export_request(self, user_key: str, existing_exports: list) -> list[str]:
        """Prüft ob Export möglich ist. Gibt Fehlerliste zurück."""
        errors = []
        # Max. 1 aktiver Export pro User
        active = [e for e in existing_exports if e.status in ('pending', 'processing')]
        if active:
            errors.append("Ein Export-Auftrag ist bereits aktiv.")
        return errors
```

**`ErasureEngine`** — Orchestrierte Löschreihenfolge (pure Logik):

```python
class ErasureEngine:
    """Definiert die Löschreihenfolge und Anonymisierungsregeln."""

    # Collections die bei Löschung anonymisiert werden (gesetzl. Aufbewahrungspflicht)
    ANONYMIZE_COLLECTIONS: list[AnonymizationRule] = [
        AnonymizationRule(
            collection="harvest_batches",
            user_field="harvester",
            anonymized_value="[gelöscht]",
            reason="CanG: 5 Jahre Aufbewahrungspflicht",
            min_retention=NFR011.HARVEST_DATA_MIN_RETENTION_YEARS,
        ),
        AnonymizationRule(
            collection="treatment_applications",
            user_field="applicator",
            anonymized_value="[gelöscht]",
            reason="PflSchG §11: 3 Jahre Aufbewahrungspflicht",
            min_retention=NFR011.TREATMENT_MIN_RETENTION_YEARS,
        ),
        AnonymizationRule(
            collection="inspections",
            user_field="inspector",
            anonymized_value="[gelöscht]",
            reason="PflSchG §11: 3 Jahre Aufbewahrungspflicht",
            min_retention=NFR011.INSPECTION_MIN_RETENTION_YEARS,
        ),
        # REQ-050: Tagebuch-Einträge. Anders als die drei Regeln darüber gibt es
        # hier KEINE gesetzliche Aufbewahrungspflicht — der Grund ist ein anderer:
        # Der Eintrag gehört zum Pflanzen-Datensatz eines womöglich geteilten
        # Mandanten und würde beim Hard-Delete die Historie fremder Mitglieder
        # zerreissen. Dieselbe Abwägung wie bei den Foto-Anhängen (Scope
        # `user_diary_attachments`, siehe unten) — dort wird der Anhang
        # anonymisiert statt gelöscht, das Eintragsdokument selbst blieb bis
        # REQ-050 versehentlich ungeregelt.
        AnonymizationRule(
            collection="plant_diary_entries",
            user_field="created_by",
            anonymized_value="_anonymized",
            reason="REQ-050: geteilter Mandanten-Datensatz, keine gesetzliche Frist",
            min_retention=None,
        ),
        AnonymizationRule(
            collection="plant_diary_entries",
            user_field="analysis_requested_by",
            anonymized_value="_anonymized",
            reason="REQ-050: wer die KI-Analyse angefordert hat",
            min_retention=None,
        ),
        AnonymizationRule(
            collection="plant_diary_entries",
            user_field="analysis_claimed_by",
            anonymized_value="_anonymized",
            reason="REQ-050: Kennung des ausführenden Agenten",
            min_retention=None,
        ),
    ]

    # Collections die vollständig gelöscht werden (Edges vor Nodes!)
    DELETE_ORDER: list[str] = [
        # Phase 0: Object-Storage-Cleanup (W-007, siehe unten) — MUSS vor
        # Phase 1 laufen, weil danach die attachments-Metadaten weg sind
        # und der created_by-Filter nicht mehr funktioniert.
        "_storage_cleanup",
        # Phase 0.5: Referenz-Index-Cleanup (REQ-034 §5 / SR-003) — MUSS
        # ebenfalls vor Phase 1 laufen. Entfernt vom Nutzer beigesteuerte
        # DINOv2-Embeddings (source='user_contributed') aus dem pgvector-
        # Referenz-Index (REQ-029-A species_embeddings) anhand der Provenienz-
        # Felder contributed_by/tenant_key. Der Index liegt NICHT in ArangoDB,
        # daher ein eigener Cleanup-Pfad (siehe REFERENCE_INDEX_CLEANUP_RULES).
        "_reference_index_cleanup",
        # Phase 1: Edges
        "requested_export", "has_consent", "has_restriction",
        "requested_erasure", "requested_email_change",
        "has_auth_provider", "has_session", "has_membership",
        # Phase 2: Nodes (Reihenfolge wichtig)
        "data_export_requests", "consent_records", "processing_restrictions",
        "email_change_requests", "auth_providers", "refresh_tokens",
        # Phase 2.5: Audit-Log-Pseudonymisierung (W-002, siehe unten)
        # Diese Collections werden NICHT gelöscht — der user_key wird durch
        # einen Tombstone-Hash ersetzt, bevor Phase 3 ausgeführt wird.
        "_pseudonymize_audit_collections",
        # Phase 3: User selbst (zuletzt)
        "users",
    ]

    # <!-- Quelle: Widerspruchsanalyse W-007 -->
    # Object-Storage-Cleanup: zwei Scopes, generisch erweiterbar.
    # Phase 0 läuft vor allen ArangoDB-Operationen — sie braucht den Lookup
    # auf attachments.created_by == user_key, der nach Phase 1 nicht mehr
    # zuverlässig funktioniert.
    STORAGE_CLEANUP_RULES: list[StorageCleanupRule] = [
        StorageCleanupRule(
            scope="user_personal",
            description=(
                "Hard-Delete: alle Anhaenge mit created_by == user_key UND "
                "category in {'profile', 'user_notes'}. Beispiele: "
                "Profilfoto, eigene Notiz-Fotos ohne Bezug zu "
                "aufbewahrungspflichtigen Datensaetzen."
            ),
            action="hard_delete",
            ref="NFR-013 §6.2 Punkt 2",
        ),
        StorageCleanupRule(
            scope="user_diary_attachments",
            description=(
                "Anonymisierung: alle Anhaenge mit created_by == user_key UND "
                "category in {'diary', 'inspection', 'treatment', 'harvest', 'plant'}. "
                "('plant' = Pflanzenfoto-Galerie, REQ-034 §5 — gehört zum "
                "Pflanzen-Datensatz der Instanz.) "
                "Datei bleibt erhalten (gehört zum Tenant-Datensatz, evtl. "
                "Aufbewahrungspflicht via NFR-011 R-16/R-17/R-18). "
                "ArangoDB-Metadatum created_by wird auf '_anonymized' gesetzt. "
                "Wenn Tenant STORAGE_KEEP_EXIF_<category>=true gesetzt hat, "
                "werden zusätzlich EXIF-Daten aus der Datei selbst entfernt "
                "(strip_exif_for_user, NFR-013 §4.2)."
            ),
            action="anonymize_metadata_and_strip_exif",
            ref="NFR-013 §6.2 Punkt 3+4, §6.4",
        ),
    ]
    # <!-- /Quelle: Widerspruchsanalyse W-007 -->

    # <!-- Quelle: Widerspruchsanalyse W-002 -->
    # Audit-Log-Pseudonymisierung: Generische Liste — aktuell ein Eintrag,
    # leicht erweiterbar für künftige Audit-Collections (z.B. consent_change_audit).
    # Hintergrund: NFR-011 R-06 verlangt 1 Jahr Aufbewahrung des Erasure-
    # Audit-Logs (Art. 5(2) Rechenschaftspflicht). Ohne Pseudonymisierung
    # bleibt user_key 1 Jahr personenbezogen → Verstoß gegen Art. 5(1)(e)
    # Speicherbegrenzung. Tombstone-Hash entkoppelt den Eintrag vom User.
    PSEUDONYMIZE_AUDIT_COLLECTIONS: list[PseudonymizationRule] = [
        PseudonymizationRule(
            collection="erasure_requests",
            user_field="user_key",
            replacement_strategy="tombstone_hash",
            reason=(
                "Erasure-Audit-Logs werden 1 Jahr aufbewahrt (NFR-011 R-06, "
                "Art. 5(2) Rechenschaftspflicht). Nach Hard-Delete des Users "
                "darf der user_key nicht mehr als personenbezogener "
                "Identifikator gespeichert sein (Art. 5(1)(e))."
            ),
        ),
    ]
    # <!-- /Quelle: Widerspruchsanalyse W-002 -->

    def build_erasure_plan(self, user_key: str, user_data: dict) -> ErasurePlan:
        """Erstellt einen Löschplan für den gegebenen User."""
        plan = ErasurePlan(user_key=user_key)
        plan.storage_cleanup = self.STORAGE_CLEANUP_RULES                # W-007
        plan.anonymize = self.ANONYMIZE_COLLECTIONS
        plan.pseudonymize_audit = self.PSEUDONYMIZE_AUDIT_COLLECTIONS    # W-002
        plan.delete = self.DELETE_ORDER
        plan.soft_delete_immediate = True
        plan.hard_delete_after_days = 90  # NFR-011 R-01
        return plan


# <!-- Quelle: Widerspruchsanalyse W-007 -->
@dataclass
class StorageCleanupRule:
    """Regel für die Object-Storage-Bereinigung in Phase 0 des Erasure-Tasks."""
    scope: Literal["user_personal", "user_diary_attachments"]
    description: str
    action: Literal["hard_delete", "anonymize_metadata_and_strip_exif"]
    ref: str  # Referenz auf NFR-013-Sektion
# <!-- /Quelle: Widerspruchsanalyse W-007 -->


# <!-- Quelle: REQ-034 Security-Review SR-003 -->
# Referenz-Index-Cleanup (Phase 0.5): Der DINOv2-Referenz-Index
# (REQ-029-A species_embeddings) liegt physisch in pgvector, NICHT in
# ArangoDB. Die generische Erasure-Pipeline (Phasen 1–3) erfasst ihn daher
# nicht. Vom Nutzer beigesteuerte Embeddings (source='user_contributed')
# tragen seit REQ-029-A §5.1 die Provenienz-Felder contributed_by / tenant_key /
# contributed_at und werden über diese Regel entfernt. Kuratiert übernommene
# Referenzen (source != 'user_contributed') bleiben unberührt — sie sind
# nicht personenbezogen.
REFERENCE_INDEX_CLEANUP_RULES: list[ReferenceIndexCleanupRule] = [
    ReferenceIndexCleanupRule(
        store="pgvector",
        collection="species_embeddings",
        filter="source == 'user_contributed' AND contributed_by == user_key",
        action="hard_delete",
        ref="REQ-029-A §5.1, REQ-034 §5",
    ),
]
# Bei Tenant-Löschung (REQ-024) greift dieselbe Regel mit Filter
# `source == 'user_contributed' AND tenant_key == X`.


@dataclass
class ReferenceIndexCleanupRule:
    """Regel für die pgvector-Referenz-Index-Bereinigung (Phase 0.5)."""
    store: Literal["pgvector"]
    collection: str
    filter: str
    action: Literal["hard_delete"]
    ref: str
# <!-- /Quelle: REQ-034 Security-Review SR-003 -->
```

<!-- Quelle: Widerspruchsanalyse W-002 -->
**Audit-Log-Pseudonymisierung (W-002):**

Die `PSEUDONYMIZE_AUDIT_COLLECTIONS`-Liste ist bewusst generisch ausgelegt: jede Collection, die einen User-Verweis länger als den User selbst aufbewahren muss (Compliance-Ausnahme), wird hier eingetragen. Die Pseudonymisierung läuft als **Phase 2.5** zwischen den Document-Löschungen (Phase 2) und der User-Löschung (Phase 3) — siehe Celery-Task in §3.5.

```python
from dataclasses import dataclass
from typing import Literal
import hashlib

@dataclass
class PseudonymizationRule:
    """Regel zur Pseudonymisierung eines User-Verweises in einer Audit-Collection."""
    collection: str                                    # z.B. "erasure_requests"
    user_field: str                                    # z.B. "user_key"
    replacement_strategy: Literal["tombstone_hash"]    # erweiterbar für andere Strategien
    reason: str                                         # Compliance-Begründung


def compute_tombstone_hash(user_key: str, salt: str) -> str:
    """Erzeugt einen nicht umkehrbaren Tombstone-Hash für gelöschte User.

    Format:    'anon_' + hex(sha256(user_key + salt))[:16]
    Länge:     21 Zeichen (5 Präfix + 16 Hex = 64 Bit Identitätsraum)
    Properties:
      - Deterministisch: gleicher (user_key, salt) → gleicher Hash
      - Einweg: aus dem Hash ist user_key nicht rekonstruierbar (SHA-256)
      - Salt-isoliert: ohne Kenntnis des per-Instanz-Salts ist keine
        Brute-Force-Reidentifikation gegen den User-Key-Raum möglich

    64 Bit reichen für Kamerplanter-Skalen (max. ~100k User über 10 Jahre,
    Geburtstagsparadox-Kollision ~2^32 Tombstones nicht erreichbar). Salt
    MUSS pro Instanz einzigartig in einem Secret abgelegt sein
    (NFR-011 §4 ERASURE_TOMBSTONE_SALT, Pflicht-Setting).

    Raises:
        ValueError: Wenn salt leer ist oder kürzer als 32 Zeichen
            (Mindestentropie für sichere Pseudonymisierung).
    """
    if not salt or len(salt) < 32:
        raise ValueError(
            "ERASURE_TOMBSTONE_SALT muss mindestens 32 Zeichen lang sein "
            "(siehe NFR-011 §4)."
        )
    h = hashlib.sha256((user_key + salt).encode("utf-8")).hexdigest()
    return f"anon_{h[:16]}"
```
<!-- /Quelle: Widerspruchsanalyse W-002 -->

**`ConsentEngine`** — Einwilligungsmanagement (pure Logik):

```python
class ConsentEngine:
    """Verwaltet Einwilligungen pro Verarbeitungszweck."""

    # Definierte Verarbeitungszwecke
    PURPOSES: list[ConsentPurpose] = [
        ConsentPurpose(
            key="core_functionality",
            label_de="Grundfunktionen",
            label_en="Core Functionality",
            description_de="Verarbeitung für den Betrieb des Systems (Pflanzenverwaltung, Phasensteuerung, etc.)",
            legal_basis="Art. 6(1)(b) Vertragserfüllung",
            required=True,  # Nicht widerrufbar
        ),
        ConsentPurpose(
            key="error_tracking",
            label_de="Fehler-Tracking (Sentry)",
            label_en="Error Tracking (Sentry)",
            description_de="Automatische Erfassung von Fehlern zur Verbesserung der Software-Qualität",
            legal_basis="Art. 6(1)(a) Einwilligung",
            required=False,
        ),
        ConsentPurpose(
            key="hibp_check",
            label_de="Passwort-Sicherheitscheck (HaveIBeenPwned)",
            label_en="Password Security Check (HaveIBeenPwned)",
            description_de="Prüfung ob Passwort in bekannten Datenlecks vorkommt (k-Anonymity, SHA-1-Prefix)",
            legal_basis="Art. 6(1)(a) Einwilligung",
            required=False,
        ),
        ConsentPurpose(
            key="external_enrichment",
            label_de="Externe Stammdatenanreicherung",
            label_en="External Master Data Enrichment",
            description_de="Abfrage botanischer Daten bei GBIF, Perenual und anderen externen Diensten",
            legal_basis="Art. 6(1)(a) Einwilligung",
            required=False,
        ),
        # REQ-034 §4.4 — opt-in Foto-Beitrag zum DINOv2-Referenz-Index (REQ-029-A).
        # Granularität: global pro Nutzer (die UNIQUE(user_key, purpose)-Constraint
        # auf consent_records erlaubt genau einen Datensatz pro Zweck → O-04 in
        # REQ-034 ist damit auf "global pro Nutzer" entschieden).
        ConsentPurpose(
            key="reference_contribution",
            label_de="Beitrag eigener Fotos zur Pflanzenerkennung",
            label_en="Contribution of own photos to plant recognition",
            description_de=(
                "Aus deinen Galerie-Fotos einer korrekt bestimmten Pflanze wird "
                "ein Embedding-Vektor berechnet und — nach Admin-Prüfung — als "
                "zusätzliche Referenz für die self-hosted Bilderkennung genutzt. "
                "Es wird ausschließlich der Vektor gespeichert, das Originalbild "
                "verlässt die Instanz nicht und geht an keinen Dritten. Jederzeit "
                "widerrufbar; bei Widerruf/Kontolöschung werden beigesteuerte "
                "Vektoren entfernt."
            ),
            legal_basis="Art. 6(1)(a) Einwilligung",
            required=False,
        ),
    ]

    def get_all_purposes(self) -> list[ConsentPurpose]:
        """Gibt alle definierten Verarbeitungszwecke zurück."""
        return self.PURPOSES

    def is_processing_allowed(self, purpose_key: str, consent: Optional[ConsentRecord]) -> bool:
        """Prüft ob Verarbeitung für den gegebenen Zweck erlaubt ist."""
        purpose = self._find_purpose(purpose_key)
        if purpose.required:
            return True  # Erforderliche Zwecke immer erlaubt
        if consent is None:
            return False  # Kein Consent-Record → nicht erlaubt
        return consent.granted

    def validate_consent_change(self, purpose_key: str, grant: bool) -> list[str]:
        """Validiert ob Einwilligungsänderung zulässig ist."""
        errors = []
        purpose = self._find_purpose(purpose_key)
        if purpose.required and not grant:
            errors.append(f"Einwilligung für '{purpose.label_de}' ist erforderlich und kann nicht widerrufen werden.")
        return errors
```

<!-- Quelle: ADR-002 / W-006 -->
**`SpeciesReferenceResolver`** — Wandelt `species_key`-Referenzen in `species_ref`-Wrapper um (DSGVO Art. 20 Datenübertragbarkeit).

Hintergrund: Plant-Daten enthalten `species_key`-Referenzen. Bei `origin='system'`/`'enrichment'` ist das eine globale Referenz, beim Empfänger auflösbar. Bei `origin='tenant'` ist die Referenz nur im Quell-Tenant gültig. Damit der Export self-contained ist, wird tenant-eigene Species **inline als Snapshot** eingebettet.

```python
class SpeciesReferenceResolver:
    """ADR-002: Wandelt species_key in self-contained species_ref-Wrapper um."""

    async def resolve(self, species_key: str) -> dict:
        """Liefert ein species_ref-Objekt für DSGVO-Export.

        Returns:
          {
            "scope": "global" | "tenant",
            "key": "<species_key>",
            "snapshot": <embedded_data> | None  // nur bei scope='tenant'
          }
        """
        species = await self.species_repo.get(species_key)
        if species.origin != "tenant":
            # Globale Species: nur Referenz, Empfänger kann auflösen
            return {"scope": "global", "key": species_key, "snapshot": None}

        # Tenant-eigene Species: Inline-Snapshot
        snapshot = self._build_snapshot(species)
        return {"scope": "tenant", "key": species_key, "snapshot": snapshot}

    def _build_snapshot(self, species) -> dict:
        """Kompakter, self-contained Snapshot der tenant-eigenen Species."""
        return {
            "scientific_name": species.scientific_name,
            "common_names": species.common_names,
            "family": species.family,
            "genus": species.genus,
            "origin": species.origin,
            "parent_species_key": species.parent_species_key,  # KI-Kontext-Hint
            "growth_phases": species.growth_phases,
            "care_profile": species.care_profile,
            "created_at": species.created_at.isoformat(),
            "_export_note": (
                "Diese Spezies wurde im Quell-Tenant erstellt und ist nicht "
                "in der globalen Stammdaten-Datenbank verfügbar. Inline-Snapshot "
                "für Datenübertragbarkeit (DSGVO Art. 20)."
            ),
        }
```

Aufruf-Pattern im Export-Builder:

```python
# Export-Wrapper für plant_instances:
plant_data = {
    "_key": plant.key,
    "name": plant.name,
    "species_ref": await species_resolver.resolve(plant.species_key),  # statt species_key
    "cultivar_ref": await cultivar_resolver.resolve(plant.cultivar_key) if plant.cultivar_key else None,
    # ... weitere Felder
}
```

Dasselbe Pattern gilt für Cultivar-Referenzen. Der Resolver kann mehrere `species_key`/`cultivar_key`-Auflösungen batch-cachen, um N+1-Queries zu vermeiden.
<!-- /Quelle: ADR-002 / W-006 -->

### 3.2 Service-Schicht

**`PrivacyService`** — Orchestriert alle Datenschutz-Operationen:

```python
class PrivacyService:
    def __init__(
        self,
        export_repo, consent_repo, restriction_repo, erasure_repo,
        email_change_repo, user_repo,
        data_export_engine, erasure_engine, consent_engine,
        token_engine, email_service,
    ): ...

    # --- Art. 15/20: Datenexport ---
    async def request_data_export(self, user_key: str) -> DataExportRequest: ...
        # 1. Validiert: kein aktiver Export vorhanden (DataExportEngine)
        # 2. Erstellt DataExportRequest (status: pending)
        # 3. Dispatcht Celery-Task process_data_export
        # 4. Gibt Request-Objekt zurück

    async def get_export_status(self, user_key: str, export_key: str) -> DataExportRequest: ...
        # Prüft Eigentümerschaft (user_key muss übereinstimmen)

    async def download_export(self, user_key: str, export_key: str) -> ExportFileResponse: ...
        # 1. Prüft Eigentümerschaft und Status (completed)
        # 2. Prüft Ablaufdatum (72h, NFR-011 R-05)
        # 3. Inkrementiert download_count
        # 4. Gibt Dateipfad zurück

    # --- Art. 16: E-Mail-Änderung ---
    async def request_email_change(self, user_key: str, new_email: str) -> None: ...
        # 1. Prüft: neue E-Mail nicht bereits vergeben
        # 2. Generiert Verifikations-Token (secrets.token_urlsafe(32))
        # 3. Speichert EmailChangeRequest mit Token-Hash
        # 4. Sendet Verifikations-E-Mail an NEUE Adresse

    async def confirm_email_change(self, token: str) -> User: ...
        # 1. Findet Request per Token-Hash
        # 2. Prüft Ablaufdatum (24h)
        # 3. Aktualisiert User.email
        # 4. Setzt email_verified: true (neue Adresse wurde ja verifiziert)
        # 5. Invalidiert alle Refresh Tokens (Neuanmeldung)
        # 6. Sendet Info-E-Mail an ALTE Adresse
        # 7. Setzt Request status: confirmed

    # --- Art. 17: Kontolöschung ---
    async def request_erasure(self, user_key: str, password_confirmation: str) -> ErasureRequest: ...
        # 1. Verifiziert Passwort (oder OAuth re-auth)
        # 2. Erstellt ErasurePlan (ErasureEngine)
        # 3. Sofort: Soft-Delete (User.status → deleted)
        # 4. Sofort: Alle Refresh Tokens invalidieren
        # 5. Sofort: Anonymisierung gesetzlich geschützter Daten
        # 6. Erstellt ErasureRequest (status: scheduled, hard_delete in 90 Tagen)
        # 7. Tenant-Mitgliedschaften entfernen (REQ-024)

    async def get_erasure_status(self, erasure_key: str) -> ErasureRequest: ...

    # --- Art. 18: Verarbeitungseinschränkung ---
    async def restrict_processing(self, user_key: str, scope: str, reason: str) -> ProcessingRestriction: ...
        # Erstellt ProcessingRestriction für den gegebenen Scope

    async def lift_restriction(self, user_key: str, restriction_key: str) -> None: ...
        # Setzt lifted_at, entfernt Sperre

    # --- Art. 21: Widerspruch ---
    async def object_to_processing(self, user_key: str, purpose: str, reason: str) -> ProcessingRestriction: ...
        # Erstellt Restriction mit reason: objection_pending
        # Für Verarbeitungen auf Basis Art. 6(1)(f) berechtigtes Interesse

    # --- Consent-Management ---
    async def get_consents(self, user_key: str) -> list[ConsentWithPurpose]: ...
        # Gibt alle Zwecke mit aktuellem Consent-Status zurück

    async def grant_consent(self, user_key: str, purpose: str) -> ConsentRecord: ...
        # Erteilt Einwilligung (upsert: granted=true, granted_at=now)

    async def revoke_consent(self, user_key: str, purpose: str) -> ConsentRecord: ...
        # 1. Validiert: nicht erforderlich (ConsentEngine)
        # 2. Setzt granted=false, revoked_at=now

    # --- Datenschutzrichtlinie ---
    async def get_privacy_policy(self) -> PrivacyPolicyInfo: ...
        # Gibt aktuelle Version der Datenschutzrichtlinie zurück
        # Öffentlich zugänglich (kein Auth erforderlich)
```

### 3.3 API-Schicht

**Router: `/api/v1/privacy`** — Datenschutz & Betroffenenrechte:

| Methode | Pfad | Beschreibung | Auth | Art. |
|---------|------|-------------|------|------|
| POST | `/privacy/export` | Datenexport beantragen | Ja | 15/20 |
| GET | `/privacy/export/{key}` | Export-Status abfragen | Ja | 15/20 |
| GET | `/privacy/export/{key}/download` | Export-Datei herunterladen | Ja | 15/20 |
| POST | `/privacy/email-change` | E-Mail-Änderung beantragen | Ja | 16 |
| POST | `/privacy/email-change/confirm` | E-Mail-Änderung bestätigen | Nein (Token) | 16 |
| POST | `/privacy/erasure` | Kontolöschung beantragen | Ja | 17 |
| GET | `/privacy/erasure/{key}` | Löschstatus abfragen | Ja | 17 |
| POST | `/privacy/restrict` | Verarbeitungseinschränkung setzen | Ja | 18 |
| DELETE | `/privacy/restrict/{key}` | Verarbeitungseinschränkung aufheben | Ja | 18 |
| POST | `/privacy/object` | Widerspruch einlegen | Ja | 21 |
| GET | `/privacy/consents` | Einwilligungen auflisten | Ja | 7 |
| POST | `/privacy/consents` | Einwilligung erteilen | Ja | 7 |
| DELETE | `/privacy/consents/{purpose}` | Einwilligung widerrufen | Ja | 7 |
| GET | `/privacy/policy` | Datenschutzrichtlinie abrufen | Nein | 13/14 |

**Gesamtanzahl API-Endpunkte:** 14

### 3.4 Request/Response-Schemas

```python
# --- Export (Art. 15/20) ---
class DataExportResponse(BaseModel):
    key: str
    status: Literal['pending', 'processing', 'completed', 'expired', 'failed']
    requested_at: datetime
    completed_at: Optional[datetime]
    expires_at: Optional[datetime]
    file_size_bytes: Optional[int]
    download_count: int

# --- E-Mail-Änderung (Art. 16) ---
class EmailChangeRequest(BaseModel):
    new_email: EmailStr

class EmailChangeConfirmRequest(BaseModel):
    token: str

# --- Löschung (Art. 17) ---
class ErasureCreateRequest(BaseModel):
    password: Optional[str] = None  # Für lokale Accounts
    # Für OAuth-only Accounts: Re-Auth über separaten Flow

class ErasureResponse(BaseModel):
    key: str
    status: Literal['scheduled', 'in_progress', 'completed', 'partially_completed']
    requested_at: datetime
    soft_deleted_at: Optional[datetime]
    hard_delete_scheduled_at: Optional[datetime]
    completed_at: Optional[datetime]
    anonymized_collections: list[str]
    retained_reason: Optional[str]

# --- Einschränkung (Art. 18) ---
class RestrictionCreateRequest(BaseModel):
    scope: str  # z.B. 'all', 'sensor_data', 'analytics'
    reason: Literal['accuracy_contested', 'unlawful_processing', 'purpose_expired', 'objection_pending']

class RestrictionResponse(BaseModel):
    key: str
    scope: str
    reason: str
    created_at: datetime
    lifted_at: Optional[datetime]

# --- Widerspruch (Art. 21) ---
class ObjectionRequest(BaseModel):
    purpose: str
    reason: str  # Freitext-Begründung

# --- Consent ---
class ConsentGrantRequest(BaseModel):
    purpose: str

class ConsentResponse(BaseModel):
    purpose: str
    label: str  # Lokalisiert (DE/EN)
    description: str  # Lokalisiert
    legal_basis: str
    required: bool
    granted: bool
    granted_at: Optional[datetime]
    revoked_at: Optional[datetime]

# --- Policy ---
class PrivacyPolicyResponse(BaseModel):
    version: str
    effective_date: date
    purposes: list[ConsentPurposeInfo]
    retention_summary: list[RetentionCategoryInfo]
    data_controller: DataControllerInfo
    rights_summary: list[RightInfo]
```

### 3.5 Celery-Tasks

| Task | Schedule | Beschreibung |
|------|----------|-------------|
| `process_data_export` | On-Demand (dispatcht bei Export-Request) | Sammelt alle User-Daten, erstellt JSON-Datei |
| `execute_scheduled_erasures` | Täglich 04:00 UTC | Führt Hard-Deletes für fällige Löschaufträge aus |

```python
async def process_data_export(export_key: str):
    """Celery-Task: Sammelt alle User-Daten und erstellt Export-Datei."""
    export = await get_export(export_key)
    await update_export_status(export_key, "processing")

    try:
        manifest = data_export_engine.build_export_manifest(export.user_key)
        export_data = {}

        for source in manifest:
            data = await fetch_user_data(source, export.user_key)
            export_data[source.label] = data

        # JSON-Datei schreiben
        file_path = f"/exports/{export_key}.json"
        await write_json(file_path, export_data)
        file_size = await get_file_size(file_path)

        await update_export(export_key, {
            "status": "completed",
            "file_path": file_path,
            "file_size_bytes": file_size,
            "completed_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=72),
        })
    except Exception as e:
        await update_export(export_key, {
            "status": "failed",
            "error_message": str(e),
        })
```

```python
async def execute_scheduled_erasures():
    """Celery-Task: Führt Hard-Deletes für fällige Löschaufträge aus."""
    now = datetime.utcnow()
    pending = await get_due_erasures(now)

    for erasure in pending:
        await update_erasure_status(erasure.key, "in_progress")
        try:
            plan = erasure_engine.build_erasure_plan(erasure.user_key, {})
            # <!-- Quelle: Widerspruchsanalyse W-007 -->
            # Phase 0: Object-Storage-Cleanup (W-007)
            # MUSS vor Phase 1 laufen — nutzt attachments-Metadaten in
            # ArangoDB als Lookup-Quelle (created_by == user_key).
            storage_adapter = get_storage_adapter()
            for rule in plan.storage_cleanup:
                if rule.action == "hard_delete":
                    deleted_count = await storage_adapter.delete_for_user(
                        tenant_key=erasure.tenant_key,
                        user_key=erasure.user_key,
                        scope=rule.scope,
                    )
                    logger.info(
                        "storage_cleanup_hard_delete",
                        scope=rule.scope,
                        user_key=erasure.user_key,
                        tenant_key=erasure.tenant_key,
                        deleted=deleted_count,
                    )
                elif rule.action == "anonymize_metadata_and_strip_exif":
                    # 1. ArangoDB-Metadaten anonymisieren (created_by → '_anonymized')
                    anon_count = await attachment_repo.anonymize_user_metadata(
                        tenant_key=erasure.tenant_key,
                        user_key=erasure.user_key,
                        scope=rule.scope,
                    )
                    # 2. EXIF-Strip-Pass für Tenant-Datensätze mit
                    #    STORAGE_KEEP_EXIF_<category>=true (NFR-013 §6.4).
                    #    Adapter überspringt Dateien ohne EXIF-Daten oder
                    #    Tenant-Settings ohne Keep-EXIF.
                    stripped = await storage_adapter.strip_exif_for_user(
                        tenant_key=erasure.tenant_key,
                        user_key=erasure.user_key,
                        scope=rule.scope,
                    )
                    logger.info(
                        "storage_cleanup_anonymize",
                        scope=rule.scope,
                        user_key=erasure.user_key,
                        tenant_key=erasure.tenant_key,
                        metadata_anonymized=anon_count,
                        exif_stripped=stripped,
                    )
            # <!-- /Quelle: Widerspruchsanalyse W-007 -->
            # <!-- Quelle: REQ-034 Security-Review SR-003 -->
            # Phase 0.5: Referenz-Index-Cleanup (pgvector, REQ-034 §5)
            # MUSS ebenfalls vor Phase 1 laufen. Der DINOv2-Referenz-Index
            # liegt außerhalb von ArangoDB; ohne diesen Pfad blieben vom
            # Nutzer beigesteuerte Embeddings (source='user_contributed')
            # nach der Löschung dauerhaft im Index (Verstoß gegen Art. 17).
            reference_index = get_reference_index_store()  # pgvector
            for rule in erasure_engine.REFERENCE_INDEX_CLEANUP_RULES:
                removed = await reference_index.delete_user_contributions(
                    tenant_key=erasure.tenant_key,
                    user_key=erasure.user_key,
                )
                logger.info(
                    "reference_index_cleanup",
                    store=rule.store,
                    collection=rule.collection,
                    user_key=erasure.user_key,
                    tenant_key=erasure.tenant_key,
                    removed=removed,
                )
            # <!-- /Quelle: REQ-034 Security-Review SR-003 -->
            # Phase 1: Edges löschen
            for edge_collection in plan.edge_deletions:
                await delete_user_edges(edge_collection, erasure.user_key)
            # Phase 2: Documents löschen
            for doc_collection in plan.doc_deletions:
                await delete_user_docs(doc_collection, erasure.user_key)
            # <!-- Quelle: Widerspruchsanalyse W-002 -->
            # Phase 2.5: Audit-Log-Pseudonymisierung (W-002)
            # user_key in Aufbewahrungspflichtigen Audit-Logs durch Tombstone
            # ersetzen, BEVOR Phase 3 den User selbst löscht.
            tombstone = compute_tombstone_hash(
                erasure.user_key, settings.erasure_tombstone_salt
            )
            for rule in plan.pseudonymize_audit:
                affected = await replace_user_field(
                    collection=rule.collection,
                    old_user_key=erasure.user_key,
                    new_value=tombstone,
                    field=rule.user_field,
                )
                logger.info(
                    "audit_log_pseudonymized",
                    collection=rule.collection,
                    field=rule.user_field,
                    affected_rows=affected,
                    tombstone=tombstone,  # Hash ist nicht personenbezogen
                )
            # <!-- /Quelle: Widerspruchsanalyse W-002 -->
            # Phase 3: User löschen
            await hard_delete_user(erasure.user_key)

            await update_erasure(erasure.key, {
                "status": "completed",
                "completed_at": now,
                "deleted_collections": plan.delete,
                "pseudonymized_collections": [r.collection for r in plan.pseudonymize_audit],  # W-002
                "storage_cleanup_scopes": [r.scope for r in plan.storage_cleanup],  # W-007
            })
        except Exception as e:
            await update_erasure(erasure.key, {
                "status": "partially_completed",
                "error_message": str(e),
            })
```

### 3.6 Middleware: Consent-Prüfung

Für Features die eine Einwilligung erfordern, wird eine Dependency bereitgestellt:

```python
def require_consent(purpose: str):
    """FastAPI Dependency Factory: Prüft ob Einwilligung für den Zweck erteilt wurde."""
    async def check_consent(
        current_user: User = Depends(get_current_user),
        consent_repo: ConsentRepository = Depends(get_consent_repo),
        consent_engine: ConsentEngine = Depends(get_consent_engine),
    ) -> None:
        consent = await consent_repo.get_by_user_and_purpose(
            current_user.key, purpose
        )
        if not consent_engine.is_processing_allowed(purpose, consent):
            raise HTTPException(
                status_code=403,
                detail=f"Einwilligung für '{purpose}' nicht erteilt."
            )
    return check_consent

# Verwendung in Endpunkten:
@router.post("/enrichment/trigger")
async def trigger_enrichment(
    _consent: None = Depends(require_consent("external_enrichment")),
    ...
): ...
```

### 3.7 Middleware: Restriction-Prüfung

```python
def check_processing_restriction(scope: str):
    """FastAPI Dependency: Prüft ob Verarbeitungseinschränkung für den Scope aktiv ist."""
    async def check(
        current_user: User = Depends(get_current_user),
        restriction_repo: RestrictionRepository = Depends(get_restriction_repo),
    ) -> None:
        restrictions = await restriction_repo.get_active_by_user(current_user.key)
        for r in restrictions:
            if r.scope in ("all", scope) and r.lifted_at is None:
                raise HTTPException(
                    status_code=423,  # Locked
                    detail=f"Verarbeitung eingeschränkt: {r.reason}"
                )
    return check
```

---

## 4. Frontend

### 4.1 Neue Seiten

| Seite | Route | Beschreibung |
|-------|-------|-------------|
| `PrivacySettingsPage` | `/settings/privacy` | Datenschutz-Einstellungen mit 4 Tabs |

### 4.2 Komponenten

**`PrivacySettingsPage`** — 4 Tabs:

**Tab "Einwilligungen":**
- Liste aller Verarbeitungszwecke (aus `GET /privacy/consents`)
- Jeder Zweck zeigt: Label, Beschreibung, Rechtsgrundlage, Status (erteilt/widerrufen)
- Erforderliche Zwecke: Toggle deaktiviert, Hinweistext "Erforderlich für den Betrieb"
- Optionale Zwecke: Toggle zum Erteilen/Widerrufen
- Zeitstempel der letzten Änderung

**Tab "Datenexport":**
- Button "Meine Daten exportieren" (disabled wenn bereits ein Export läuft)
- Liste vergangener Exporte mit Status (pending/processing/completed/expired)
- Download-Link für abgeschlossene Exporte (mit Dateigröße)
- Info-Text: "Download ist 72 Stunden verfügbar"

**Tab "Account löschen":**
- Warnhinweis: "Diese Aktion ist nach 90 Tagen unwiderruflich"
- **Transparente Aufschlüsselung:** Welche Daten vollständig gelöscht werden (Profil, Sessions, Einwilligungen, Aufgaben) und welche nur anonymisiert werden (Erntedokumentation, IPM-Behandlungsnachweise — gesetzliche Aufbewahrungspflicht nach CanG/PflSchG). <!-- Quelle: Widerspruchsanalyse W-001 -->
- Passwort-Bestätigung (oder OAuth Re-Auth Button)
- Bestätigungs-Dialog mit Checkbox "Ich verstehe, dass mein Account gelöscht wird und gesetzlich geschützte Daten anonymisiert aufbewahrt bleiben"

**Tab "Verarbeitungseinschränkung":**
- Info-Text: Erklärung Art. 18 DSGVO
- Formular: Scope auswählen, Grund auswählen
- Liste aktiver Einschränkungen mit "Aufheben"-Button
- Widerspruchs-Formular (Art. 21): Zweck + Freitext-Begründung

### 4.3 i18n-Keys

```
pages.privacy.title: "Datenschutz-Einstellungen"
pages.privacy.tabs.consents: "Einwilligungen"
pages.privacy.tabs.export: "Datenexport"
pages.privacy.tabs.delete: "Account löschen"
pages.privacy.tabs.restrictions: "Verarbeitungseinschränkung"
pages.privacy.export.button: "Meine Daten exportieren"
pages.privacy.export.pending: "Export wird vorbereitet..."
pages.privacy.export.download: "Herunterladen"
pages.privacy.export.expires: "Verfügbar bis {{date}}"
pages.privacy.delete.warning: "Diese Aktion ist nach 90 Tagen unwiderruflich."
pages.privacy.delete.confirm: "Ich verstehe, dass mein Account gelöscht wird"
pages.privacy.delete.button: "Account endgültig löschen"
pages.privacy.consent.required: "Erforderlich für den Betrieb"
pages.privacy.consent.granted: "Erteilt am {{date}}"
pages.privacy.consent.revoked: "Widerrufen am {{date}}"
pages.privacy.restriction.info: "Sie können die Verarbeitung Ihrer Daten für bestimmte Zwecke einschränken."
pages.privacy.objection.title: "Widerspruch"
```

---

## 5. Seed-Daten

### Standard-Consent-Purposes (Vorkonfiguriert):

```json
[
  {
    "key": "core_functionality",
    "label_de": "Grundfunktionen",
    "label_en": "Core Functionality",
    "required": true,
    "legal_basis": "Art. 6(1)(b)"
  },
  {
    "key": "error_tracking",
    "label_de": "Fehler-Tracking (Sentry)",
    "label_en": "Error Tracking (Sentry)",
    "required": false,
    "legal_basis": "Art. 6(1)(a)"
  },
  {
    "key": "hibp_check",
    "label_de": "Passwort-Sicherheitscheck",
    "label_en": "Password Security Check",
    "required": false,
    "legal_basis": "Art. 6(1)(a)"
  },
  {
    "key": "external_enrichment",
    "label_de": "Externe Stammdatenanreicherung",
    "label_en": "External Data Enrichment",
    "required": false,
    "legal_basis": "Art. 6(1)(a)"
  },
  {
    "key": "ai_tenant_data_access",
    "label_de": "KI-Assistent darf meine Pflanzendaten als Kontext nutzen",
    "label_en": "AI assistant may use my plant data as context",
    "required": false,
    "legal_basis": "Art. 6(1)(a)",
    "description_de": "Erlaubt dem serverseitigen KI-Assistenten (REQ-031), bei Tipp-Karten, 'Warum?'-Erklärungen, Chat und Diagnose-Sessions auf Stammwerte deiner Pflanzen (Art, Phase, Substrat, EC, pH, VPD, IPM-Status) zuzugreifen, um personalisierte Empfehlungen zu generieren. Ohne diese Einwilligung sind nur allgemeine Wissensfragen (Glossar, REQ-035) verfügbar. Auf diesem Weg werden personenbezogene Daten (Name, E-Mail, Tagebuch-Freitexte) NIE übertragen. Wenn du einzelne Tagebuch-Einträge samt Fotos ausdrücklich zur Analyse freigeben möchtest, ist das ein getrennter Weg mit eigener Einwilligung (siehe 'diary_ai_analysis').",
    "description_en": "Allows the server-side AI assistant (REQ-031) to access stem values of your plants (species, phase, substrate, EC, pH, VPD, IPM status) when generating tip cards, 'Why?' explanations, chat answers and diagnosis sessions. Without this consent only general knowledge questions (Glossary, REQ-035) are available. On this path, personal data (name, email, diary free text) is NEVER transmitted. Releasing individual diary entries including photos for analysis is a separate path with its own consent (see 'diary_ai_analysis')."
  },
  {
    "key": "diary_ai_analysis",
    "label_de": "Einzelne Tagebuch-Einträge dürfen von meinem KI-Agenten analysiert werden",
    "label_en": "Individual diary entries may be analysed by my AI agent",
    "required": false,
    "legal_basis": "Art. 6(1)(a)",
    "description_de": "Erlaubt dir, einzelne Tagebuch-Einträge samt Freitext und Fotos zur Analyse freizugeben (REQ-050). Die Analyse führt ein KI-Agent aus, den DU betreibst und der die Daten über deinen eigenen API-Schlüssel abruft — Kamerplanter selbst ruft dabei kein Sprachmodell auf. Es wird nie automatisch etwas analysiert: Jeden einzelnen Eintrag musst du selbst markieren. Übertragen werden verkleinerte Bildfassungen ohne Aufnahmeort und Gerätekennung. Ein Widerruf verhindert neue Markierungen und lässt vorhandene Ergebnisse unberührt.",
    "description_en": "Allows you to release individual diary entries, including free text and photos, for analysis (REQ-050). The analysis is performed by an AI agent that YOU operate and that fetches the data via your own API key — Kamerplanter itself never calls a language model. Nothing is ever analysed automatically: you have to mark every single entry yourself. Only downscaled image renditions without capture location or device identifier are transmitted. Withdrawing consent prevents new markings and leaves existing results untouched."
  },
  {
    "key": "ai_cloud_processing",
    "label_de": "KI-Anfragen dürfen über Cloud-Provider verarbeitet werden",
    "label_en": "AI requests may be processed via cloud providers",
    "required": false,
    "legal_basis": "Art. 6(1)(a) + Art. 49 (Drittland)",
    "description_de": "Erlaubt die Verarbeitung deiner KI-Anfragen über Cloud-Provider (OpenAI, Anthropic, OpenAI-kompatible Anbieter). Dabei werden anonymisierte Pflanzdaten und deine Frage an den Cloud-Anbieter (typischerweise USA) übermittelt. Lokale Provider (Ollama im eigenen Cluster) erfordern diesen Consent NICHT.",
    "description_en": "Allows your AI requests to be processed via cloud providers (OpenAI, Anthropic, OpenAI-compatible). Anonymized plant data and your question are transmitted to the cloud provider (typically USA). Local providers (Ollama in own cluster) do NOT require this consent."
  }
]
```

<!-- Quelle: REQ-031 v2.0 -->

**Hinweis zur Abgrenzung `ai_tenant_data_access` ↔ `diary_ai_analysis`:** Das sind zwei getrennte Wege mit gegenläufigen Eigenschaften, und sie dürfen nicht miteinander verrechnet werden. `ai_tenant_data_access` betrifft den **serverseitigen** Assistenten: Kamerplanter ruft das Modell, überträgt Stammwerte und niemals Freitext. `diary_ai_analysis` betrifft den **vom Nutzer betriebenen** Agenten (REQ-050): Kamerplanter ruft kein Modell, sondern gibt einen einzelnen, ausdrücklich markierten Eintrag samt Freitext und Bildfassungen über die MCP-Schnittstelle heraus. Keiner der beiden Consents impliziert den anderen. `ai_cloud_processing` gilt für `diary_ai_analysis` **nicht** — die Wahl des Modells und des Anbieters liegt dort vollständig beim Nutzer und außerhalb der Verantwortung der Instanz.

**Hinweis zur Verkettung:** `ai_cloud_processing` ist eine Zusatz-Einwilligung. Wenn ein Tenant-Admin einen Cloud-Provider als Default konfiguriert hat, brauchen Endpoints, die Tenant-Daten mit Cloud-Verarbeitung kombinieren, beide Einwilligungen (`ai_tenant_data_access` UND `ai_cloud_processing`). Light-Modus-Endpoints (`/api/v1/public/ai/*` aus REQ-031 v2.0 §5.3 und das Glossar aus REQ-035) brauchen weder den einen noch den anderen Consent, da sie keine personenbezogenen Daten verarbeiten.

---

## 6. Abnahmekriterien

### Funktionale Kriterien:

| # | Kriterium | Art. | Prüfmethode |
|---|-----------|------|-------------|
| AK-01 | Datenexport enthält alle im Manifest definierten User-Daten als JSON | 15/20 | Integration |
| AK-02 | Export-Datei ist nach 72 Stunden nicht mehr downloadbar (Status: expired) | 15/20 | Integration |
| AK-03 | Max. 1 aktiver Export-Auftrag pro User | 15/20 | Unit |
| AK-04 | E-Mail-Änderung erfordert Verifikation der neuen Adresse (Token, 24h gültig) | 16 | Integration |
| AK-05 | Nach E-Mail-Änderung werden alle Sessions invalidiert | 16 | Integration |
| AK-06 | Info-E-Mail wird an die alte Adresse gesendet | 16 | Integration |
| AK-07 | Kontolöschung setzt User sofort auf status: deleted (Soft-Delete) | 17 | Integration |
| AK-08 | Erntedaten und Behandlungsanwendungen werden anonymisiert, nicht gelöscht | 17 | Integration |
| AK-08a | Löschbestätigung unterscheidet zwischen `fully_deleted_categories` und `anonymized_categories` und zeigt beide Listen transparent an | 17 | E2E |
| AK-09 | Hard-Delete erfolgt 90 Tage nach Soft-Delete (NFR-011 R-01) | 17 | Integration |
| AK-10 | Erasure-Audit-Log wird für 1 Jahr aufbewahrt | 17 | Integration |
| AK-11 | Verarbeitungseinschränkung blockiert betroffene Endpunkte (423 Locked) | 18 | Integration |
| AK-12 | Widerspruch erstellt Restriction mit reason: objection_pending | 21 | Integration |
| AK-13 | Erforderliche Einwilligungen können nicht widerrufen werden | 7 | Unit |
| AK-14 | Consent-Prüfung blockiert Feature-Endpunkte ohne Einwilligung (403) | 7 | Integration |
| AK-15 | Datenschutzrichtlinie ist ohne Authentifizierung abrufbar | 13/14 | Integration |
| AK-16 | Celery-Task process_data_export erstellt korrekte JSON-Datei | 15/20 | Integration |
| AK-17 | Celery-Task execute_scheduled_erasures löscht fällige Accounts endgültig | 17 | Integration |
<!-- Quelle: Widerspruchsanalyse W-002 -->
| AK-PD-01 | **Audit-Pseudonymisierung:** Nach Abschluss eines Erasure-Requests MUSS in jeder Collection aus `PSEUDONYMIZE_AUDIT_COLLECTIONS` (aktuell: `erasure_requests`) der `user_key`-Wert durch einen Tombstone-Hash im Format `anon_<16hex>` ersetzt sein. Der Original-`user_key` darf nicht mehr in der Collection auffindbar sein. | 5(1)(e) | Integration |
| AK-PD-02 | **Tombstone-Determinismus & Salt-Schutz:** `compute_tombstone_hash(user_key, salt)` erzeugt für gleiche Eingaben denselben Hash; ohne Kenntnis von `ERASURE_TOMBSTONE_SALT` ist eine Reidentifikation aus dem Hash nicht möglich. Bei `salt=""` oder `len(salt) < 32` MUSS `ValueError` geworfen werden. | 5(1)(e) | Unit |
<!-- /Quelle: Widerspruchsanalyse W-002 -->
<!-- Quelle: Widerspruchsanalyse W-007 -->
| AK-OS-01 | **Storage-Cleanup `user_personal`:** Nach Abschluss eines Erasure-Requests sind alle Anhaenge mit `created_by == user_key` UND `category in {profile, user_notes}` aus dem Object Storage HART GELÖSCHT (`storage_adapter.delete_for_user(scope='user_personal')`). Anschließendes `head_object(key)` MUSS HTTP 404 liefern. | 17 | E2E |
| AK-OS-02 | **Storage-Anonymisierung `user_diary_attachments`:** Nach Abschluss eines Erasure-Requests haben alle Anhaenge mit `created_by == user_key` UND `category in {diary, inspection, treatment, harvest}` das ArangoDB-Metadatum `created_by = '_anonymized'`. Die S3-Datei selbst bleibt erhalten und behält ihren ursprünglichen Pfad (`t/{tenant}/{entity_type}/{entity_key}/{filename}`). | 17 | Integration |
| AK-OS-03 | **EXIF-Strip-Pass:** Wenn der Tenant für eine Kategorie `STORAGE_KEEP_EXIF_<category>=true` gesetzt hat, MUSS bei der Erasure ein `storage_adapter.strip_exif_for_user()`-Aufruf alle EXIF-Daten (GPS, Kamera-Seriennummer, Aufnahmezeit) aus den verbleibenden Diary-Fotos des Users entfernen. Bilder ohne EXIF und Tenants ohne Keep-EXIF werden nicht modifiziert. | 17, NFR-013 §6.4 | Integration |
| AK-OS-04 | **Phase-Reihenfolge:** Im Celery-Task `execute_scheduled_erasures` läuft Phase 0 (Storage-Cleanup) VOR Phase 1 (Edges). Wenn Phase 0 fehlschlägt, MUSS der Erasure-Status auf `partially_completed` gesetzt werden — kein Phase-1-Aufruf. | — | Unit |
<!-- /Quelle: Widerspruchsanalyse W-007 -->
<!-- Quelle: REQ-034 Security-Review SR-003 -->
| AK-OS-05 | **Referenz-Index-Cleanup (Phase 0.5):** Nach Abschluss eines Erasure-Requests sind alle DINOv2-Embeddings im pgvector-`species_embeddings`-Index mit `source == 'user_contributed'` UND `contributed_by == user_key` gelöscht. Bei Tenant-Löschung gilt derselbe Filter mit `tenant_key == X`. Phase 0.5 läuft VOR Phase 1; Fehlschlag ⇒ `partially_completed` (kein ArangoDB-Delete). Kuratiert übernommene Referenzen (`source != 'user_contributed'`) bleiben unberührt. | REQ-029-A §5.1, REQ-034 §5 | Integration |
<!-- /Quelle: REQ-034 Security-Review SR-003 -->
<!-- Quelle: REQ-050 §7.4 -->
| AK-DA-01 | **Tagebuch-Anonymisierung:** Nach Abschluss eines Erasure-Requests sind in `plant_diary_entries` die Felder `created_by`, `analysis_requested_by` und `analysis_claimed_by` mit dem Wert `user_key` auf `_anonymized` gesetzt. Das Eintragsdokument selbst — Freitext, Tags, Messwerte, `photo_refs` und ein vorhandenes `analysis`-Ergebnis — bleibt vollstaendig erhalten. Dies schliesst die Luecke, dass bislang nur die **Anhaenge** (AK-OS-02), nicht aber das Eintragsdokument geregelt waren. | 17 | Integration |
| AK-DA-02 | **Auskunft umfasst Tagebuch:** Der Datenexport nach Art. 15/20 enthaelt die Tagebuch-Eintraege des Nutzers samt vorhandener KI-Analyse-Ergebnisse (REQ-050). | 15/20 | Integration |
| AK-DA-03 | **Einwilligung `diary_ai_analysis`:** Ohne erteilte Einwilligung lehnt das Markieren eines Tagebuch-Eintrags zur KI-Analyse ab; ein Widerruf verhindert neue Markierungen und laesst bestehende Ergebnisse unberuehrt. Im Light-Modus (REQ-027) entfaellt die Pruefung, weil dort kein Consent erteilt werden kann (REQ-050 §7.5). | 6(1)(a) | Integration |
<!-- /Quelle: REQ-050 §7.4 -->

### Frontend-Kriterien:

| # | Kriterium | Prüfmethode |
|---|-----------|-------------|
| FK-01 | PrivacySettingsPage zeigt alle 4 Tabs korrekt an | E2E |
| FK-02 | Einwilligungs-Toggles für optionale Zwecke funktionieren | E2E |
| FK-03 | Erforderliche Einwilligungen sind als nicht-änderbar dargestellt | E2E |
| FK-04 | Export-Button ist deaktiviert während ein Export läuft | E2E |
| FK-05 | Lösch-Dialog erfordert Passwort-Bestätigung und Checkbox | E2E |

---

## 7. Abhängigkeiten

### Abhängig von (bestehend):

| REQ/NFR | Bezug |
|---------|-------|
| REQ-023 v1.2 | User-Modell, AuthService, TokenEngine, E-Mail-Verifikation |
| REQ-024 v1.1 | Tenant-Mitgliedschaften (werden bei Löschung entfernt) |
| NFR-011 | Retention-Fristen (R-01, R-04, R-05, R-06, R-07, R-16, R-17, R-18) |
| NFR-006 | API-Fehlerbehandlung (403, 423, 422 Fehlercodes) |

### Wird benötigt von:

| REQ | Bezug |
|-----|-------|
| REQ-011 | Consent-Prüfung für externe Stammdatenanreicherung |
| REQ-007 | Anonymisierung von Harvester-Referenzen bei Löschung |
| REQ-010 | Anonymisierung von Inspector-Referenzen bei Löschung |
| REQ-006 | Anonymisierung von Task-assigned_to bei Löschung |

### Neue Collections im Named Graph `kamerplanter_graph`:

| Typ | Collection | Zweck |
|-----|-----------|-------|
| Document | `data_export_requests` | Art. 15/20 Export-Aufträge |
| Document | `consent_records` | Einwilligungen pro Zweck |
| Document | `processing_restrictions` | Art. 18 Verarbeitungssperren |
| Document | `erasure_requests` | Art. 17 Löschaufträge |
| Document | `email_change_requests` | Art. 16 E-Mail-Änderungen |
| Edge | `requested_export` | users → data_export_requests |
| Edge | `has_consent` | users → consent_records |
| Edge | `has_restriction` | users → processing_restrictions |
| Edge | `requested_erasure` | users → erasure_requests |
| Edge | `requested_email_change` | users → email_change_requests |

---

## 8. Scope-Abgrenzung

**In Scope:**
- Art. 15 Auskunftsrecht (Datenexport als JSON)
- Art. 16 Berichtigungsrecht (E-Mail-Änderung mit Re-Verifikation)
- Art. 17 Recht auf Löschung (Soft-Delete + Hard-Delete nach Retention-Frist)
- Art. 18 Recht auf Einschränkung (zweckbezogene Verarbeitungssperren)
- Art. 20 Datenportabilität (maschinenlesbarer JSON-Export)
- Art. 21 Widerspruchsrecht (zweckbezogener Opt-out)
- Consent-Tracking (nachweisbare Einwilligungen)
- Privacy-Settings-Seite (Frontend)

**Nicht in Scope (bewusst ausgeklammert):**
- Art. 13/14 Informationspflichten: Datenschutzerklärung als statisches Dokument, nicht als Feature
- Art. 30 Verzeichnis von Verarbeitungstätigkeiten: Organisationsdokument, nicht Software-Feature
- Art. 35 Datenschutz-Folgenabschätzung (DSFA): Separates Bewertungsdokument (siehe NFR-001 §6.7)
- Art. 28 Auftragsverarbeitungsverträge (AVV): Vertragliche, nicht technische Anforderung
- DSGVO-Export pro Tenant (REQ-024 Out-of-Scope, zukünftige Erweiterung)

---

## 9. Datenschutz-Bewertung externer Dienste

<!-- Quelle: IT-Security-Review SEC-H-008 -->

Kamerplanter kommuniziert mit mehreren externen Diensten. Für jeden Dienst MUSS eine Datenschutz-Bewertung dokumentiert werden, die die übertragenen Daten, Rechtsgrundlage und Schutzmaßnahmen beschreibt.

| Dienst | Übertragene Daten | Rechtsgrundlage | Schutzmaßnahmen | Consent-pflichtig |
|--------|-------------------|-----------------|-----------------|-------------------|
| **GBIF** (REQ-011) | Artname (Suchanfrage) | Art. 6(1)(a) Einwilligung | Keine PII übertragen; `external_enrichment`-Consent | Ja |
| **Perenual** (REQ-011) | Artname (Suchanfrage) | Art. 6(1)(a) Einwilligung | Keine PII übertragen; `external_enrichment`-Consent | Ja |
| **HaveIBeenPwned** (REQ-023) | SHA-1-Prefix (5 Zeichen) des Passwort-Hashs | Art. 6(1)(a) Einwilligung | k-Anonymity — kein Rückschluss auf Passwort möglich; `hibp_check`-Consent | Ja |
| **Sentry** (NFR-001 §8.3) | IP (anon.), User-Agent, Stack-Traces, URLs | Art. 6(1)(a) Einwilligung | PII-Scrubbing, EU-Hosting oder AVV; `error_tracking`-Consent | Ja |
| **DWD / OpenWeatherMap / Open-Meteo** (REQ-005) | GPS-Koordinaten des Standorts (Site.latitude/longitude) | Art. 6(1)(b) Vertragserfüllung | Koordinaten auf 2 Dezimalstellen gerundet (~1 km Genauigkeit); kein Personenbezug | Nein |
| **InvenTree** (REQ-016) | Produktreferenzen, Bestandsänderungen | Art. 6(1)(b) Vertragserfüllung | Self-Hosted; kein externer Dienst im Regelfall | Nein |
| **OAuth-Provider** (REQ-023) | E-Mail, Name (vom Provider empfangen) | Art. 6(1)(b) Vertragserfüllung | Nur bei explizitem Nutzer-Login; Daten vom Provider kontrolliert | Nein (funktional) |

**Anforderungen:**

| # | Regel | Stufe |
|---|-------|-------|
| DP-001 | Externe API-Aufrufe DÜRFEN NUR nach Prüfung der Consent-Pflicht erfolgen. Consent-pflichtige Dienste MÜSSEN die `require_consent()`-Dependency verwenden. | MUSS |
| DP-002 | GPS-Koordinaten MÜSSEN vor Übertragung an Wetter-APIs auf maximal 2 Dezimalstellen gerundet werden. | MUSS |
| DP-003 | Bei Nutzung von Sentry SaaS MUSS ein AVV nach Art. 28 DSGVO vorliegen (siehe NFR-001 §8.3 SE-004). | MUSS |

---

## 10. TTDSG-Konformität (Cookie-/Speicher-Einwilligung)

<!-- Quelle: IT-Security-Review SEC-M-007 -->

Das Telemediengesetz (TTDSG) §25 unterscheidet zwischen technisch notwendigen und nicht-notwendigen Zugriffen auf die Endeinrichtung des Nutzers (Cookies, localStorage, sessionStorage).

**Klassifikation der Speicherzugriffe in Kamerplanter:**

| Speicherzugriff | Zweck | TTDSG-Kategorie | Einwilligung nötig |
|----------------|-------|-----------------|-------------------|
| `refresh_token` (HttpOnly Cookie) | Authentifizierung | Technisch notwendig (§25 Abs. 2 Nr. 2) | Nein |
| `csrf_token` (Cookie) | CSRF-Schutz | Technisch notwendig | Nein |
| `i18next` (localStorage) | Spracheinstellung | Technisch notwendig | Nein |
| `theme` (localStorage) | Dark/Light-Mode | Technisch notwendig | Nein |
| `redux_state` (sessionStorage) | App-State | Technisch notwendig | Nein |
| Sentry SDK (localStorage, Cookies) | Fehler-Tracking | **Nicht notwendig** | **Ja** (`error_tracking`-Consent) |

**Anforderungen:**

| # | Regel | Stufe |
|---|-------|-------|
| TT-001 | Technisch notwendige Cookies/Storage-Zugriffe DÜRFEN OHNE Einwilligung gesetzt werden. | Info |
| TT-002 | Sentry und alle zukünftigen Tracking-/Analyse-Dienste DÜRFEN Cookies/Storage ERST NACH expliziter Einwilligung nutzen (ConsentEngine `error_tracking`). | MUSS |
| TT-003 | Ein Cookie-/Einwilligungs-Banner ist NICHT erforderlich, solange ausschließlich technisch notwendige Speicherzugriffe erfolgen. Bei Aktivierung von Sentry oder Analytics MUSS ein Einwilligungs-Dialog implementiert werden (UI-NFR-013). | BEDINGT |

---

**Dokumenten-Ende**

**Version**: 1.1
**Status**: Entwurf
**Datum**: 2026-03-18
**Security-Review**: Adressiert SEC-K-001, SEC-K-003, SEC-H-008, SEC-M-005, SEC-M-007
