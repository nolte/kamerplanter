# SPEC-08 — Änderungen an API und Datenmodell

```
Paket: spec/privacy · Version 1.1 · 2026-11-09 · gemessen gegen develop 24d1c2988; Nachtrag #2839 (develop 343afbb97)
Anforderungs-IDs: PRIV-600 … PRIV-649
Hängt ab von: 01 §3 (Komponenten), 03–07 (Verhalten); Style Guides BACKEND.md / FRONTEND.md;
NFR-016 (Migrationen), NFR-006 (Fehlerformat)
Änderung v1.1: `record_keeping`/`organization_kind` ohne Modell-Default (Anlagepfad setzt; W-03), Zustandsautomat
der Prüfeinträge, `erasure_mirror` statt Raw-Key-Ledger (DEC-26), Feature-Flags (§8a), Laufzeit-Provenienz (§2.4a).
```

Jede Änderung unten ist **additiv**, sofern nicht als *inkompatibel (breaking)* markiert; wo Kompatibilität
wenig kostet, bleibt sie für ein Release erhalten und die Deprecation ist benannt. Nichts hiervon wurde
implementiert; das bestehende Modell wurde zuerst validiert (`02` §4 listet Felder, die es nicht gibt).

---

## 1. Prinzipien

**PRIV-600** Neue Metadaten erweitern die bestehenden Pydantic-Modelle in
`src/backend/app/domain/models/privacy.py` (`AnonymizationRule`, `PseudonymizationRule`,
`ErasureStep`, `ErasureExclusion`, `DataSourceDefinition`); kein paralleles Registry-Modul. Die
bestehenden Felder (`collection`, `user_field`, `anonymized_value`, `replacement_strategy`,
`clear_fields`, `rename_fields`, `rename_when`, `reason`) bleiben unverändert.

**PRIV-601** Enum-Werte sind nur additiv; DE/EN-i18n im selben PR (Projektregel).

**PRIV-602** Neue Routen sind mandantenbezogen unter `/api/v1/t/{tenant_slug}/privacy/…` und
plattformbezogen unter `/api/v1/admin/platform/privacy/…`; jede neue Route kommt in die
Route-Walk-Isolationsmatrix, den Route-Consumer-Pin und den Bounded-List-Guard (REQ-053-
Leitplanken), und neue Service-Methoden, die per Schlüssel laden und schreiben, nehmen `*, tenant_key: str`.

**PRIV-603** Das Fehlerformat folgt NFR-006 (`error_code`-Strings siehe §7).

---

## 2. Registry (Domänenmodelle)

### 2.1 Zuordnung und Aufbewahrungsklasse bei den Inventareinträgen

```python
# domain/models/privacy.py — additive fields (defaults keep every existing entry valid)
class AttributionRole(StrEnum):
    PERFORMED_BY = "performed_by"; PERFORMED_FOR = "performed_for"; CREATED_BY = "created_by"
    CONFIRMED_BY = "confirmed_by"; MODIFIED_BY = "modified_by"; ASSIGNED_TO = "assigned_to"
    OWNER = "owner"; ACTOR = "actor"; RECIPIENT = "recipient"; SUBJECT_OF = "subject_of"

class RetentionClass(StrEnum):
    EPHEMERAL = "ephemeral"; SHARED_HISTORY = "shared_history"; STATUTORY = "statutory"; AUDIT = "audit"

class AnonymizationRule(BaseModel):
    ...  # existing fields unchanged
    attribution: AttributionRole                      # PRIV-001 — required (no default) → every rule names it
    retention_class: RetentionClass = RetentionClass.SHARED_HISTORY
    required_attribution: bool = False                # PRIV-004
    review_fields: list[str] = Field(default_factory=list)   # PRIV-212; free text listed for review

class PseudonymizationRule(BaseModel):
    ...
    attribution: AttributionRole
    retention_class: RetentionClass = RetentionClass.AUDIT
    review_fields: list[str] = Field(default_factory=list)

class ErasureStep(BaseModel):
    ...
    attribution: AttributionRole | None = None        # None for edge/user steps
    retention_class: RetentionClass = RetentionClass.EPHEMERAL

class ErasureExclusion(BaseModel):
    ...
    attribution: AttributionRole | None = None        # free-text "performed_by" fields: None + reason
```

**PRIV-604** `scripts/check_privacy_inventory.py` erhält **R7**: Jede `AnonymizationRule` und
`PseudonymizationRule` hat eine `attribution`; jedes kontoförmige Modellfeld, das eine
Regel erreicht, hat genau eine. Der Unit-Test `test_privacy_engines.py` erhält dieselbe Assertion.

### 2.2 Gemeinsame Konstanten (eine Definition)

```python
# domain/models/privacy.py
ANONYMIZED_MARKER = "_anonymized"
TOMBSTONE_REGEX = r"^anon_[0-9a-f]{16}$|^anon2_[0-9a-f]{16}$"   # beide Generationen (PRIV-238, W-08); in 09 unter demselben Namen
TOMBSTONE_PATTERN = re.compile(TOMBSTONE_REGEX)
REDACTED = "[redacted]"

def is_tombstone(value: str | None) -> bool: ...
def carry_account_reference(value: str | None, *, target: Literal["marker", "tombstone"]) -> str | None:
    """PRIV-205: a current key passes; marker/tombstone → marker (marker target) or None (tombstone target);
    any other string (a label) → None."""
```

Aufrufstellen, die umzuhängen sind [verifiziert]: `erasure_engine.py` (definiert heute), `models/care_event.py`
(`ANONYMIZED_MARKER`, `REDACTED`), `data_access/arango/attachment_repository.py`,
`domain/engines/tenant_export_engine.py` (`ANONYMIZED_ACCOUNT`, `_TOMBSTONE`),
`data_access/arango/tenant_erasure_executor.py` (`_TOMBSTONE_REGEX`),
`domain/engines/care_event_backfill_mapper.py` (`account_of` → nutzt `carry_account_reference`; seit #2839
ruft es bereits `ErasureEngine.is_tombstone` → Marker), `domain/engines/task_completion_engine.py`
(`harvested_by_key = event.performed_by_user_key`). Der Test
`test_garden_plan_retention.py` (pinnt drei Kopien als gleich) wird zu einem Guard, der prüft, dass die Namen
importiert und nicht neu definiert werden (AST-Scan auf ein zweites Literal `"_anonymized"` in `app/`, **ohne**
`app/migrations/versions/` — eingefrorene Migrationen wie v0107 kopieren die Konstanten absichtlich, NFR-016 M-7).

### 2.3 PersonRef und der Resolver

```python
# domain/models/person_ref.py (new)
class PersonRefState(StrEnum):
    MEMBER = "member"; FORMER_MEMBER = "former_member"; ERASED = "erased"
    THIRD_PARTY = "third_party"; SYSTEM = "system"; SERVICE_ACCOUNT = "service_account"

class PersonRef(BaseModel):
    state: PersonRefState
    display_name: str | None = None      # only for MEMBER (and SERVICE_ACCOUNT label); never a key
    is_self: bool = False
```

```python
# domain/services/identity_reference_service.py (new; pure resolution, repositories injected)
class IdentityReferenceService:
    def resolve_display(self, keys_or_labels: Iterable[tuple[str | None, str | None]], *,
                        tenant_key: str, viewer: TenantContext, visibility: AttributionVisibility) -> dict[str, PersonRef]:
        """One batched lookup (users.display_name, users.is_active, users.account_type, active membership
        in tenant_key, last MEMBERSHIP_LEFT/REMOVED instant from security_audit_log) → PersonRef per key.
        Rules: PRIV-006/007/008, PRIV-104 (closed → erased), PRIV-112 (former member after N days),
        PRIV-300 (leads_and_self), tombstone/marker/missing → ERASED, label without key → THIRD_PARTY,
        None/None → SYSTEM, account_type=service → SERVICE_ACCOUNT."""
```

**PRIV-605** `display_performer()` in `models/care_event.py` wird durch einen dünnen Adapter ersetzt,
der das Service-Ergebnis aufruft; sein Schlüsselwort `anonymised=` (von Druckvorlagen genutzt) bildet auf die
i18n von `PersonRefState.ERASED` ab.

### 2.4 Lineage-Registry

```python
# domain/models/privacy.py
class PropagationRule(StrEnum):
    CARRY_ACCOUNT_REFERENCE = "carry_account_reference"   # account fields copied between rows
    REVIEW_SUGGESTION = "review_suggestion"               # content copies → batch suggestion in the review UI
    NONE = "none"                                          # live resolution, nothing stored

class DerivedField(BaseModel):
    source: str          # "collection.field"
    derived: str         # "collection.field"
    via: str             # "backfill_mapper" | "task_completion_engine" | "place_template" | "plan_audit_summary" | "import_snapshot" | "supersede"
    propagation: PropagationRule
    reason: str

DERIVED_FIELDS: tuple[DerivedField, ...] = (...)   # content of 02 §5
```

**PRIV-606** Guard **R8** (`scripts/check_privacy_inventory.py`): Jede Codestelle, die
ein kontoförmiges Feld aus dem Feld eines anderen Dokuments zuweist (AST: Attribut → Attribut-
Zuweisung innerhalb `domain/engines/*` und `domain/services/*`), ist in `DERIVED_FIELDS`
oder in einem expliziten Ausschluss mit Begründung aufgeführt.

### 2.4a Laufzeit-Provenienz (ergänzt die statische Registry; `02` §5a)

Eine AST-Prüfung erfasst keine Event-Handler, Celery-Jobs, Exporte, Benachrichtigungen, Offline-Puffer oder
Audit-Snapshots vollständig. Deshalb:

**PRIV-609** [PROPOSED] Jede **persistierte** abgeleitete Zeile MUSS ihre Herkunft tragen: `source_ref {collection,
key}` (bei `care_events` vorhanden [VERIFIED_CODE]) bzw. `derived_from: list[{collection, key, field}]` bei Kopien
von Inhalten (`locations.template_key` existiert; `garden_plan_audit` erhält `derived_from` für `summary`/`snapshot`).
Der Beat `privacy.consistency` (Vollform) prüft stichprobenartig, dass jedes `(source.collection → derived.collection)`-
Paar, das in Daten vorkommt, in `DERIVED_FIELDS` registriert ist; ein unregistriertes Paar ist ein Befund.

**PRIV-610** [PROPOSED] **Nicht persistierte** oder **flüchtige** Ableitungen werden in `DERIVED_FIELDS` mit
`propagation` und einer **Lebensdauerregel** geführt statt mit Laufzeitmarker: Art.-15-Bundle (R-05 72 h),
Pflegeereignis-CSV (Download, gehört dem Empfänger; Audit PRIV-308), Mandantenarchiv (R-05), Benachrichtigungen
(R-48; Texte tragen keine Mitgliedsnamen [VERIFIED_CODE]), Offline-Puffer/-Cache (`07`: TTL, Quarantäne,
Übergang), Audit-Snapshots (`garden_plan_audit.snapshot`, R-26, Blatt-Schwärzung PRIV-229), TimescaleDB-Continuous-
Aggregates (keine Kontoreferenz [VERIFIED_CODE]). Jede Zeile der Lineage-Tabelle `02` §5/§5a nennt Quelle, Ableitung,
Löschverhalten.

### 2.5 Schwärzbare Felder

```python
REDACTABLE_FIELDS: frozenset[tuple[str, str]]  # derived: union of review_fields over all rules + garden_plan_audit.summary/snapshot leaves
```

### 2.6 Tombstone-Allowlist

```python
def tombstone_allowed_fields() -> frozenset[tuple[str, str]]:
    """Derived from ANONYMIZE_COLLECTIONS (strategy tombstone_hash) ∪ PSEUDONYMIZE_AUDIT_COLLECTIONS. No second list."""
```

---

## 3. Änderungen am Domänenmodell

### 3.1 Pflegeereignisse (additiv)

| Feld / Änderung | Typ | Zweck | Kompat. |
|-----------------|-----|-------|---------|
| `CareEventView.performed_by_kind`, `performed_for_kind`, `created_by_kind`, `voided_by_kind`, `redacted_by_kind` | `PersonRefState` | PRIV-007 Darstellung nach Art | additiv; der String `performed_by` bleibt für ein Release (deprecated: weiterhin `"anonymisiert"` für gelöschte, bis zur Entfernung, danach `null`) |
| `CareEventResponse.performed_by_kind` usw. | gleich | API | additiv |
| `FREE_TEXT_FIELDS` += `material`; Messwert-Strings werden vom Schwärzungs-/Aufbewahrungs-Patch behandelt | — | PRIV-213 | Verhaltensänderung für Schwärzung/R-25 (Spec-Änderungsvorschlag) |
| Korrekturrecht: `created_by is None and performed_by_user_key == user` | — | PRIV-215 | additiv |
| `check_performed_by_filter`: Tombstone-förmige Werte ablehnen (422) | — | PRIV-207 | additiv |

### 3.2 Mandanten (additive Einstellungen)

```python
class AttributionVisibility(StrEnum): ALL_MEMBERS = "all_members"; LEADS_AND_SELF = "leads_and_self"
class RecordKeeping(StrEnum): LEGACY = "legacy"; NONE = "none"; PFLSCHG_PROFESSIONAL = "pflschg_professional"; KCANG_ASSOCIATION = "kcang_association"; BOTH = "both"
class OrganizationKind(StrEnum): ASSOCIATION = "association"; COMMERCIAL = "commercial"; COMMUNITY = "community"; OTHER = "other"; UNKNOWN_LEGACY = "unknown_legacy"

class TenantSettings(BaseModel):
    ...  # existing ai_* fields
    attribution_visibility: AttributionVisibility | None = None   # None → Default nach Klasse (DA-04), PRIV-300
    record_keeping: RecordKeeping | None = None                   # None = "undeclared" (PRIV-409); v0109 stempelt Bestand auf LEGACY
    organization_kind: OrganizationKind | None = None             # Pflichtangabe bei Anlage eines organization-Mandanten (PRIV-409)
    shared_device_mode: bool = False                              # PRIV-524
```

**Defaults (löst W-03):** Das Modell trägt für `record_keeping` und `attribution_visibility` **keinen** festen
Default. Der **Anlagepfad** setzt sie: persönliche Mandanten `record_keeping = none`, `attribution_visibility =
all_members`; Organisationsmandanten verlangen `organization_kind` und `record_keeping` als Pflichtangabe
(Formularschritt, 422 ohne Angabe) und erhalten `attribution_visibility` nach Klasse (`commercial` →
`leads_and_self`, sonst `all_members`). **Bestandsmandanten** werden durch v0109 auf `record_keeping = legacy`,
`organization_kind = unknown_legacy`, `attribution_visibility = all_members` gestempelt. Ein `None` zur Laufzeit
(nur Bestand vor v0109 oder manuell gelöscht) wird wie `legacy`/`all_members` gelesen **und** als `undeclared`
gezählt (PRIV-409). `extra="allow"` hält gespeicherte Dokumente gültig. Jeder Default hat einen Test (TA-630). `PATCH /tenants/{slug}` akzeptiert sie für `lead ∧ management`; Änderungen werden
auditiert (`TENANT_PRIVACY_SETTING_CHANGED`, alter/neuer Wert in der bestehenden `reason`-freien
Form → `setting_key`, `old_value`, `new_value` zu `SecurityAuditEntry` als optionale
Strings hinzufügen, kein Freitext).

### 3.3 Nutzer (kein neues persistiertes Feld)

Der geschlossene Zustand wird abgeleitet (`is_active=false` ∧ Löschanfrage existiert) — PRIV-104 braucht
`is_active` nur im Anzeige-Join.

### 3.4 Freitext-Durchführer-Felder → schlüsselbasiert (Migration, `09` §5)

| Modell | Heute [v] | Ziel |
|--------|-----------|------|
| `watering_events.performed_by`, `watering_logs.performed_by`, `tank_fill_events.performed_by`, `maintenance_logs.performed_by` | Freitext, von der Löschung ausgenommen | `performed_by_user_key: str \| None` (serverseitig gestempelt, nicht im Request-Schema) + `performed_by_label: str \| None` (≤ 80, nur Dritte); das alte Feld wird bei der Migration zum Label; UI-Dialog ersetzt durch „Ich war es / jemand anderes (Label)" |
| `nutrient_plans.author`, `propagation.*.author` | Freitext, unbegrenzt | `author_user_key` + `author_label` (≤ 80); Druckvorlage rendert über `PersonRef` |
| `inspections.inspector` über MCP `"mcp:<key>"` | Pseudo-Schlüssel im Freitext | `inspected_by_key = service account key`; `inspector = ""` |
| `workflow_templates.created_by` | Freitext | `created_by_user_key` + Prüffeld |

Alle neuen `*_user_key`-Felder kommen im selben PR in `ANONYMIZE_COLLECTIONS` (Marker, `attribution=performed_by`
/ `created_by`) und `USER_DATA_MANIFEST` (R2-Reziprozität).

### 3.5 Anhänge

`original_filename` bleibt ein Feld; die Löschung leert es (`clear_fields` an der Anhang-
Regel, PRIV-211). Keine Schemaänderung.

### 3.6 Gartenplan-Audit

Die Regel `PlanAuditRecord.user_key` wechselt zum Marker (DEC-16). API `PlanAuditEntry.changed_by:
PersonRef` hinzugefügt; `changed_by_name` deprecated (für ein Release erhalten, `null` für Nicht-Mitglieder).

### 3.7 Neue Collections

```python
# collections.py (additive)
PRIVACY_REVIEW_ITEMS = "privacy_review_items"      # tenant-scoped → TenantErasureEngine.INVENTORY _delete
ERASURE_MIRROR = "erasure_mirror"                  # platform → NOT_TENANT_SCOPED (reason: tombstone list for restore replay; no raw keys) — DEC-26
MIGRATION_REPORTS = "migration_reports"            # platform → NOT_TENANT_SCOPED (operator proof; no personal data)
```

```python
class PrivacyReviewItem(BaseModel):
    key: str | None = Field(alias="_key")        # sha256(erasure_key|collection|row_key)[:32] — deterministic, idempotent
    tenant_key: str
    erasure_key: str                              # erasure_requests key (its user_key is the tombstone)
    source_kind: Literal["account_erasure", "attribution_removal", "legacy_unkeyed_name", "record_keeping_change"]
    collection: str
    row_key: str
    fields: list[str]                             # review fields present on the row at creation
    match_kinds: list[Literal["authored", "performed", "modified", "name_token", "lineage"]]
    status: Literal["REVIEW_REQUIRED", "REDACTION_PENDING", "REDACTED",
                    "RETAINED_WITH_LEGAL_BASIS", "VOID", "FAILED"] = "REVIEW_REQUIRED"   # 04 §5.1a; DISCOVERY_PENDING
                                                  # ist ein Zustand des Löschauftrags (review_discovery_cursor), kein Item-Zustand
    due_at: datetime                              # created_at + PRIVACY_REVIEW_SLA_DAYS
    overdue_since: datetime | None = None
    decision: Literal["redact", "keep"] | None = None
    redacted_fields: list[str] = Field(default_factory=list)
    reason_code: Literal["no_personal_reference", "agronomic_record", "third_party_consent", "statutory", "other"] | None = None
    legal_basis_ref: str | None = None            # PA-nn (06 §2) oder LEG-nn; Pflicht bei decision == keep (PRIV-225)
    reason_text: str | None = Field(default=None, max_length=500)
    decided_by: str | None = None                 # account ref, attribution=actor → marker at erasure
    decided_at: datetime | None = None
    failure_count: int = 0
    last_error_code: str | None = None
    created_at: datetime
    # never: text, token, subject key, display name
```

```python
class ErasureMirrorEntry(BaseModel):              # DEC-26 — ersetzt ErasureReplayLedgerEntry (v1.0)
    key: str | None = Field(alias="_key")         # = erasure_key bzw. "ter_<tenant_key>"
    kind: Literal["account", "tenant"]
    tombstone: str | None = None                  # account: instanzweiter Tombstone (`anon_`, = erasure_requests.user_key); NIE der Rohschlüssel
    tenant_tombstones: list[str] = Field(default_factory=list)  # account: mandantengebundene `anon2_`-Werte (PRIV-238), für den Residue-Scan nach Restore
    tenant_key: str | None = None                 # tenant
    completed_at: datetime
    plan_fingerprint: str
    chain_hmac: str                               # HMAC-Kette über die Einträge (Integrität des Spiegel-Objekts)
    expires_at: datetime                          # wie R-06 / R-06a
```

Am `ErasureRequest` kommen hinzu (additiv): `review_discovery_cursor: str | None`,
`review_discovery_completed_at: datetime | None`, `review_name_tokens_enc: str | None` (Fernet; gelöscht bei
Abschluss der Entdeckung), `followups_open: int`, `followups_overdue: int`, `post_commit_pending: bool`;
`ErasureStatus` erhält den additiven Wert `"erasure_completed"` (`04` §5.1a).

Indizes (Migration `vNNNN`): `privacy_review_items(tenant_key, status, due_at)`, `(tenant_key, collection,
row_key)`, `(erasure_key, status)`; `erasure_mirror(expires_at)`, `(kind, tombstone)`. Art.-15-Manifest:
`privacy_review_items` → `EXCLUDED_FROM_DISCLOSURE` (kein Text, kein Schlüssel des Subjekts); `erasure_mirror`
→ `EXCLUDED_FROM_DISCLOSURE` (nur Pseudonyme; die Existenz des Eintrags zeigt der Admin-Löschstatus). Guard R2
akzeptiert Ausschlüsse mit Begründung [VERIFIED_CODE].

### 3.8 Security-Audit (additive Enum-Werte und optionale Felder)

```python
class SecurityAuditAction(StrEnum):
    ...  # existing
    ERASURE_REQUESTED = "erasure_requested"; ERASURE_COMPLETED = "erasure_completed"
    EXPORT_REQUESTED = "export_requested"; CONSENT_CHANGED = "consent_changed"
    REDACTION_APPLIED = "redaction_applied"; REVIEW_DECIDED = "review_decided"
    ATTRIBUTION_REMOVED = "attribution_removed"; ATTRIBUTION_EXPORTED = "attribution_exported"
    ATTRIBUTION_FILTER_USED = "attribution_filter_used"            # PRIV-405, counts only
    TENANT_PRIVACY_SETTING_CHANGED = "tenant_privacy_setting_changed"
    TENANT_RECORD_KEEPING_CHANGED = "tenant_record_keeping_changed"

class SecurityAuditEntry(BaseModel):
    ...
    setting_key: str | None = None; old_value: str | None = None; new_value: str | None = None  # enum values only
    row_count: int | None = None                                                                # exports
```

`target_user_key` von Löschzeilen ist von Anfang an der Tombstone (PRIV-219).

---

## 4. API-Änderungen

### 4.1 Mandantenbezogene Privacy-Routen (neu; `api/v1/privacy/tenant_router.py`)

| Methode & Pfad | Gate | Body / Query | Antwort | Spec |
|----------------|------|--------------|---------|------|
| `GET /t/{slug}/privacy/review` | `privacy.review` (lead ∨ management) | `status=review_required\|redaction_pending\|redacted\|retained_with_legal_basis\|void\|failed` (Mehrfachauswahl, Default `review_required`; Zustandsnamen aus `04` §5.1a in Kleinschreibung), `collection`, cursor, `limit ≤ 200` | `{items: PrivacyReviewItemResponse[], next_cursor, counts: {review_required, overdue}}`; jedes Item trägt eine **aufgelöste Zeilenvorschau**, geholt über den normalen Leseweg (`detail_url`, aktuelle `fields`-Werte) — die Vorschau wird berechnet, nie gespeichert | PRIV-224 |
| `POST /t/{slug}/privacy/review/{item_key}/decide` | `privacy.review` | `{decision: redact\|keep, fields?: [], reason_code, reason_text?}` | Item | PRIV-225 |
| `POST /t/{slug}/privacy/redactions` | `privacy.review` | `{collection, key, fields[], reason_code, reason_text?, review_item_key?}` | `{redacted_fields, audit_key}`; 422 `redaction.field_not_redactable`; idempotent 200 | PRIV-228 |
| `GET /t/{slug}/privacy/review/suggestions?item={key}` | `privacy.review` | — | Lineage-Batch (Standorte aus einer Vorlage, Audit-Zusammenfassungen) | PRIV-230 |
| `GET /t/{slug}/privacy/summary` | `privacy.review` | — | `{open_review_items, overdue, last_erasure_at, settings: {attribution_visibility, record_keeping, shared_device_mode}}` | — |
| `POST /t/{slug}/privacy/attribution-removal` | Mitglied (selbst) | `{confirm: true}` + Step-up | 202; mandantenbezogener Marker-Lauf + Prüf-Items | PRIV-116 (P2) |
| `POST /care-events/{key}/redact` (bestehend) | lead → lead ∨ management | Body unverändert | delegiert an die generische Schwärzung | PRIV-228/231 |

### 4.2 Plattform-Routen (neu; `api/v1/admin/platform/router.py`)

| Methode & Pfad | Antwort |
|----------------|---------|
| `GET /admin/platform/privacy/operations?kind=account_erasure\|tenant_erasure\|export\|migration&status=…` | Liste von Operations-Zustandsdokumenten (Schlüssel, Status, attempt_count, next_attempt_at, Rest-Zähler, `review_items_created`, `mirror_present_until`); **keine Mandantennamen außer dem Schlüssel, kein Zeileninhalt** |
| `GET /admin/platform/privacy/consistency` | letzter `privacy.consistency`-Lauf: Tombstones außerhalb der Allowlist pro Collection, Marker in Tombstone-Feldern, offene Prüf-Items pro Mandant (Zähler), überfällig |

### 4.3 Geänderte Antworten (additiv)

| Antwort | Änderung |
|---------|----------|
| `CareEventResponse` | `+ performed_by_kind, performed_for_kind, created_by_kind, voided_by_kind, redacted_by_kind` (`PersonRefState`); die Strings `performed_by`/`performed_for` sind für den gelöschten Fall deprecated |
| `PlanAuditEntry` | `+ changed_by: PersonRef`; `changed_by_name` deprecated |
| `MemberInfoResponse` | `email` nur für `management`/Plattform-Admin vorhanden (*inkompatibel (breaking) für viewer/grower-Clients, die es lesen*; Frontend `TenantSettingsPage` im selben PR angepasst) |
| Ernte-/IPM-Antworten | `+ harvested_by: PersonRef`, `applied_by_ref: PersonRef`, `inspected_by: PersonRef`; Freitext-Namensfelder unverändert |
| Antworten zu Tagebuch, Aufgabenkommentar, Gartenobjekt, Beetvorlage, Anhang | `+ created_by: PersonRef` (heute: nichts oder roher Schlüssel im MCP) |
| MCP-Tools `diary.*`, `ipm.*` | `created_by`/`inspector` → `PersonRef`-Form; rohe Schlüssel entfernt (*inkompatibel (breaking) für MCP-Clients*; REQ-033-Versionssprung) |
| `GET /care-events?format=csv` | Spalten unverändert; Werte rendern `R` für Nicht-Leads (PRIV-307); `+ Cache-Control: no-store` existiert |
| `GET /tenants/{slug}` | `+ settings.attribution_visibility, record_keeping, shared_device_mode` |
| Auth-Refresh | `401 {error_code: "account.closed"}` für ein geschlossenes Konto (PRIV-520) |
| Mandanten-Schreibpfade | `403 {error_code: "membership.ended"}`, wenn das Token des Aufrufers gültig ist und eine `MEMBERSHIP_LEFT/REMOVED`-Audit-Zeile für `(user, tenant)` existiert (PRIV-520) |

### 4.4 Frontend

| Bereich | Änderung |
|---------|----------|
| i18n | `enums.personRef.{member, former_member, erased, third_party, system, service_account}` DE/EN; Abhängigkeit vom Literal `anonymisiert` entfällt |
| `HistoryList`, Beet-Verlauf, CSV-Button | Rendern nach `*_kind`; CSV-Button zeigt „Namen enthalten" nur für Leads |
| Mandanten-Einstellungsseite | drei neue Einstellungen mit Erklärungen (PRIV-301, PRIV-401, PRIV-524) |
| Privacy-Admin-Seite (neu, `pages/tenants/PrivacyReviewPage.tsx`) | Prüfwarteschlange, Entscheiden, Batch-Vorschläge, Zusammenfassung; Lazy-Chunk (Bundle-Budget) |
| Konto-Seite | Geräte-Abschnitt (PRIV-530); Dialogtext zum Verlassen des Mandanten (PRIV-115); Aktion zur Zuordnungsentfernung (P2) |
| Offline-Schicht | Zustand `quarantined`, Einstellungen aus `runtime-config.js`, PRIV-512-Schlüsselbereinigung, abgewartete Logout-Bereinigung, `KP_CLEAR_DONE`-Handshake, Shared-Device-Modus |

---

## 5. Observability

**PRIV-607** Prometheus-Metriken (`app/observability/privacy_metrics.py`, neu):
`privacy_operations_open{kind,status}` (Gauge, von jedem Beat gesetzt), `privacy_review_items_open{tenant_kind}`,
`privacy_review_items_overdue`, `privacy_consistency_findings{kind}`,
`privacy_erasure_duration_seconds` (Histogramm), `privacy_erasure_mirror_entries`. Kein Mandanten-
Schlüssel als Label (Kardinalität und Datenschutz); `tenant_kind ∈ {personal, organization}`.

**PRIV-608** Structlog-Ereignisse behalten die Pseudonyme `sub_…`/`ten_…` (Guards existieren); neue Ereignisse:
`privacy.review_items_created`, `privacy.redaction_applied` (nur Kategorie),
`privacy.consistency.completed`, `privacy.mirror_purged`.

---

## 6. Hintergrundjobs (additive Beats; jeder in `TENANT_AGNOSTIC_BEATS` oder `TENANT_WRITING_BEATS` mit Begründung)

| Task | Zeitplan (UTC) | Tut | Mandanten-Gate |
|------|----------------|-----|----------------|
| `privacy.consistency` | täglich 05:20 | **Minimalform (E04):** PRIV-206-Scans (Tombstones außerhalb der Allowlist, Marker in Tombstone-Feldern) als Zähler + Metrik; **Vollform (E15):** zusätzlich offene/überfällige Prüfungen, `undeclared`-Mandanten, Registry-Abdeckung der Laufzeit-Provenienz (`02` §5a) | agnostisch (nur lesende Zähler) |
| `privacy.purge_erasure_mirror` (R-45) | 05:25 | löscht `expires_at < now`; schreibt das Spiegel-Objekt gefiltert neu (HMAC-Kette) | agnostisch |
| `privacy.sync_erasure_mirror` | vor jedem Backup-Dump (CronJob-Reihenfolge) | Spiegel-Objekt im Bucket aktualisieren | agnostisch |
| `privacy.purge_review_items` (R-43) | 05:30 | löscht entschiedene Items älter als 3 J. | agnostisch |
| `privacy.post_commit_followups` | 04:05 (nach Löschungen) | wiederholt Prüf-Item-Entdeckung / Spiegel-Eintrag für Löschungen, die mit `post_commit_pending` markiert sind | agnostisch |
| `retention.purge_notifications` (R-48, Vorschlag) | 05:35 | 90 d nach `read_at`, 180 d ungelesen | schreibender Beat → `ActiveTenants` nicht nötig (löscht) |

Zeilen der NFR-011-§3.1-Tabelle werden im selben PR ergänzt (Guard `test_nfr011_task_table_matches_the_beat`).

---

## 7. Fehlercodes (NFR-006)

| Code | HTTP | Wo |
|------|------|----|
| `care_event.filter_target_unavailable` | 422 | Filter nach Marker / Tombstone / unterdrücktem ehemaligem Mitglied |
| `redaction.field_not_redactable` | 422 | generische Schwärzung |
| `redaction.row_not_found` | 404 | generische Schwärzung (gleicher Body wie fremder Mandant) |
| `privacy_review.already_decided` | 409 | zweimal entscheiden mit abweichender Entscheidung |
| `account.closed` | 401 | Refresh / Schreibzugriffe von einem geschlossenen Konto |
| `membership.ended` | 403 | Mandanten-Schreibzugriff nach Ende der Mitgliedschaft (gültiges Token) |
| `tenant.record_keeping_downgrade_blocked` | 422 | `record_keeping` gesetzlich → none, solange ein gesetzlicher Purge-Job läuft |
| `tenant.classification_required` | 422 | Anlage eines Organisationsmandanten ohne `organization_kind`/`record_keeping` (PRIV-409) |
| `privacy_review.legal_basis_required` | 422 | `keep` ohne `legal_basis_ref` (PRIV-225) |
| `privacy.feature_disabled` | 409 | datenvernichtende Aktion hinter einem nicht gesetzten Flag (§8a) |

---

## 8. Einstellungen (Umgebung / `runtime-config.js`)

| Einstellung | Standard | Untergrenze / Obergrenze | Spec |
|-------------|----------|--------------------------|------|
| `RETENTION_FORMER_MEMBER_NAME_DAYS` | 90 | 0 / 365 | PRIV-112 |
| `PRIVACY_OPERATION_ESCALATE_AFTER_ATTEMPTS` | 3 | 1 / 10 | PRIV-109 |
| `PRIVACY_OPERATION_STALE_ALERT_DAYS` | 14 | 1 / 60 | PRIV-110 |
| `PRIVACY_REVIEW_ITEMS_ESCALATE_AT` (nur Eskalation, kein Ausschluss) | 5000 | 100 / 50000 | PRIV-223 |
| `PRIVACY_REVIEW_DISCOVERY_PAGE_SIZE` | 500 | 50 / 2000 | PRIV-223 |
| `PRIVACY_REVIEW_DISCOVERY_MAX_DAYS` | 2 | 1 / 7 | PRIV-223 |
| `PRIVACY_REVIEW_SLA_DAYS` | 30 | 7 / 30 | PRIV-226 (Obergrenze 30: Art. 12 Abs. 3 als Orientierung, L-19) |
| `PRIVACY_REVIEW_ITEM_RETENTION_YEARS` | 3 | 1 / 3 | R-43 |
| `BACKUP_RETENTION_DAYS` | 30 (helm `backup.retentionDays`) | 1 / 35 | `09` §6 |
| `OFFLINE_MODE_DEFAULT` | off | — | PRIV-531 |
| `OFFLINE_QUEUE_PENDING_MAX_DAYS` (runtime-config) | 90 | 7 / 365 | PRIV-511 |
| `OFFLINE_QUEUE_UNSENDABLE_MAX_DAYS` | 30 | 1 / 90 | PRIV-511 |
| `OFFLINE_DEAD_SESSION_GRACE_DAYS` | 14 | 0 / 30 | PRIV-511 |
| `OFFLINE_SHARED_DEVICE_MODE` | false | — | PRIV-524 |
| `SHARED_DEVICE_IDLE_MINUTES` | 15 | 1 / 120 | PRIV-524 |
| `PLAN_CACHE_MAX_BYTES` | 20 MB | — | PRIV-505 |
| `QUEUE_PHOTO_MAX_BYTES` | 100 MB | — | PRIV-509 |

### 8a. Feature-Flags für gegatete Verarbeitungen (Produktionsgates, `06` §10)

| Flag | Default | Gate | Wirkung bei aus |
|------|---------|------|-----------------|
| `PRIVACY_RECORD_KEEPING_RECLASSIFY` | false | LEG-03, LEG-17 | Reklassifizierung (`09` §4) und PRIV-411 werden gespeichert, aber nicht ausgeführt; Zustand `reclassification_pending`; Metrik |
| `PRIVACY_REVIEW_AUTO_REDACT_ON_SLA` | false | LEG-08 | SLA-Ablauf eskaliert nur (PRIV-239) |
| `PRIVACY_BACKFILL_COPIES_PERFORMER` | true (Bestand) | LEG-07 | `false`: Backfill/Konsistenz schreiben `performed_by_user_key = null` für Quellen aus Pflichtaufzeichnungen (DA-02) |
| `privacy.mirror.enabled` (Helm) | false | Voraussetzung für `backup.enabled` | Backup-CronJob wird nicht gerendert, solange der Spiegel nicht aktiviert ist (PRIV-707, TA-718) |

Flags sind **keine** Rechtsentscheidung; sie sind der technische Durchsetzungspunkt der im Decision-Log
registrierten Entscheidung (Spalte „Durchsetzungspunkt“). Jedes Flag ist in `docs/de/reference/environment-variables.md`
mit dem zugehörigen LEG dokumentiert.

Alle Einstellungen der §8-Tabelle werden zu `RETENTION_CEILINGS` / `test_retention_ceilings.py` und
`docs/de/reference/environment-variables.md` (DE/EN) hinzugefügt.

---

## 9. Kompatibilitätsübersicht

| Änderung | Kompat. |
|----------|---------|
| neue Felder an Inventarmodellen | intern |
| `*_kind`-Felder an Antworten | additiv |
| `performed_by`-String für gelöschte → bleibt `"anonymisiert"` für ein Release, danach `null` | Deprecation-Hinweis in OpenAPI |
| `MemberInfoResponse.email` eingeschränkt | **inkompatibel (breaking)** für Nicht-management-Clients (Frontend im selben PR aktualisiert; in den Release Notes dokumentiert) |
| rohe MCP-Schlüssel entfernt | **inkompatibel (breaking)** (REQ-033-Tool-Version) |
| CSV-Werte `R` für Nicht-Leads | Verhaltensänderung für viewer/grower; dokumentiert |
| `material` wird mit dem Set geschwärzt | Verhaltensänderung (mehr Schwärzung), Spec-Änderungsvorschlag |
| `garden_plan_audit` Tombstone → Marker | Datenmigration `09` §3 |
| Freitext-Durchführer → schlüsselbasiert | Migration `09` §5; Request-Schemas akzeptieren das alte Feld für ein Release als `performed_by_label` |
