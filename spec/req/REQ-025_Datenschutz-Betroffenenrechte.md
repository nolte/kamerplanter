# Spezifikation: REQ-025 - Datenschutz & Betroffenenrechte (DSGVO)

```yaml
ID: REQ-025
Titel: Datenschutz & Betroffenenrechte (DSGVO)
Kategorie: Plattform & Datenschutz
Fokus: Beides
Technologie: Python, FastAPI, ArangoDB, Celery, React, TypeScript, MUI
Status: Entwurf
Version: 1.0
Abhängigkeit: REQ-023 v1.2 (Benutzerverwaltung), REQ-024 v1.1 (Mandantenverwaltung), NFR-011 (Retention Policy)
Security-Review-Referenz: SEC-K-001, SEC-K-003
```

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
    ]

    # Collections die vollständig gelöscht werden (Edges vor Nodes!)
    DELETE_ORDER: list[str] = [
        # Phase 1: Edges
        "requested_export", "has_consent", "has_restriction",
        "requested_erasure", "requested_email_change",
        "has_auth_provider", "has_session", "has_membership",
        # Phase 2: Nodes (Reihenfolge wichtig)
        "data_export_requests", "consent_records", "processing_restrictions",
        "email_change_requests", "auth_providers", "refresh_tokens",
        # Phase 3: User selbst (zuletzt)
        "users",
    ]

    def build_erasure_plan(self, user_key: str, user_data: dict) -> ErasurePlan:
        """Erstellt einen Löschplan für den gegebenen User."""
        plan = ErasurePlan(user_key=user_key)
        plan.anonymize = self.ANONYMIZE_COLLECTIONS
        plan.delete = self.DELETE_ORDER
        plan.soft_delete_immediate = True
        plan.hard_delete_after_days = 90  # NFR-011 R-01
        return plan
```

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
            # Phase 1: Edges löschen
            for edge_collection in plan.edge_deletions:
                await delete_user_edges(edge_collection, erasure.user_key)
            # Phase 2: Documents löschen
            for doc_collection in plan.doc_deletions:
                await delete_user_docs(doc_collection, erasure.user_key)
            # Phase 3: User löschen
            await hard_delete_user(erasure.user_key)

            await update_erasure(erasure.key, {
                "status": "completed",
                "completed_at": now,
                "deleted_collections": plan.delete,
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
  }
]
```

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
- Art. 35 Datenschutz-Folgenabschätzung (DSFA): Separates Bewertungsdokument
- Art. 28 Auftragsverarbeitungsverträge (AVV): Vertragliche, nicht technische Anforderung
- Cookie-/Consent-Banner für technisch notwendige Cookies (Refresh Token = funktional)
- DSGVO-Export pro Tenant (REQ-024 Out-of-Scope, zukünftige Erweiterung)

---

**Dokumenten-Ende**

**Version**: 1.0
**Status**: Entwurf
**Datum**: 2026-02-27
**Security-Review**: Adressiert SEC-K-001, SEC-K-003
