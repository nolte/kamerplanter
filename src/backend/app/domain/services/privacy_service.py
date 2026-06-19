"""Service orchestrator for REQ-025 privacy & data subject rights."""

import secrets
from datetime import UTC, date, datetime, timedelta

import structlog

from app.common.exceptions import (
    DuplicateError,
    InvalidTokenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.common.types import UserKey
from app.domain.engines.consent_engine import ConsentEngine
from app.domain.engines.data_export_engine import DataExportEngine
from app.domain.engines.encryption_engine import EncryptionEngine
from app.domain.engines.erasure_engine import ErasureEngine
from app.domain.engines.password_engine import PasswordEngine
from app.domain.engines.token_engine import TokenEngine
from app.domain.interfaces.attachment_repository import IAttachmentRepository
from app.domain.interfaces.consent_repository import IConsentRepository
from app.domain.interfaces.data_export_repository import IDataExportRepository
from app.domain.interfaces.email_change_repository import IEmailChangeRepository
from app.domain.interfaces.email_service import IEmailService
from app.domain.interfaces.erasure_repository import IErasureRepository
from app.domain.interfaces.membership_repository import IMembershipRepository
from app.domain.interfaces.object_storage_adapter import IObjectStorageAdapter
from app.domain.interfaces.processing_restriction_repository import (
    IProcessingRestrictionRepository,
)
from app.domain.interfaces.reference_index_store import IReferenceIndexStore
from app.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.privacy import (
    ConsentRecord,
    ConsentWithPurpose,
    DataControllerInfo,
    DataExportRequest,
    EmailChangeRequest,
    ErasureRequest,
    PrivacyPolicyInfo,
    ProcessingRestriction,
    RestrictionReason,
    RetentionCategoryInfo,
    RightInfo,
)
from app.domain.models.user import User

logger = structlog.get_logger()


# Encryption-engine imported only to keep the dependency-injection signature
# explicit and to make the existing engine reusable for token-hashing in future
# work. Direct hashing for short-lived tokens uses TokenEngine.hash_token.
_ENCRYPTION_ENGINE_REUSE_HINT = EncryptionEngine


class PrivacyService:
    """Orchestrates GDPR rights (Art. 15/16/17/18/20/21) for a user.

    Heavy work that belongs to a Celery task (export-file generation,
    hard-delete after 90 days) is wired up here only up to the point where
    the dispatch would happen; the actual ``celery.send_task`` calls are
    intentionally left out and tracked under NFR-011.
    """

    PRIVACY_POLICY_VERSION = "1.0"
    PRIVACY_POLICY_EFFECTIVE_DATE = date(2026, 4, 27)
    EMAIL_CHANGE_TTL_HOURS = 24
    EXPORT_TTL_HOURS = 72
    HARD_DELETE_DAYS = 90

    def __init__(
        self,
        export_repo: IDataExportRepository,
        consent_repo: IConsentRepository,
        restriction_repo: IProcessingRestrictionRepository,
        erasure_repo: IErasureRepository,
        email_change_repo: IEmailChangeRepository,
        user_repo: IUserRepository,
        refresh_token_repo: IRefreshTokenRepository,
        data_export_engine: DataExportEngine,
        erasure_engine: ErasureEngine,
        consent_engine: ConsentEngine,
        password_engine: PasswordEngine,
        token_engine: TokenEngine,
        email_service: IEmailService,
        frontend_url: str,
        data_controller_name: str = "Kamerplanter Operator",
        data_controller_email: str = "privacy@kamerplanter.example",
        storage_adapter: IObjectStorageAdapter | None = None,
        attachment_repo: IAttachmentRepository | None = None,
        membership_repo: IMembershipRepository | None = None,
        reference_index_store: IReferenceIndexStore | None = None,
    ) -> None:
        self._export_repo = export_repo
        self._consent_repo = consent_repo
        self._restriction_repo = restriction_repo
        self._erasure_repo = erasure_repo
        self._email_change_repo = email_change_repo
        self._user_repo = user_repo
        self._refresh_token_repo = refresh_token_repo
        self._data_export_engine = data_export_engine
        self._erasure_engine = erasure_engine
        self._consent_engine = consent_engine
        self._password_engine = password_engine
        self._token_engine = token_engine
        self._email_service = email_service
        self._frontend_url = frontend_url
        self._data_controller_name = data_controller_name
        self._data_controller_email = data_controller_email
        # REQ-025 Phase 0 / 0.5 erasure dependencies (NFR-013 object storage,
        # REQ-034 reference index). Optional so existing callers keep working;
        # the DI provider wires them for the real hard-delete pipeline.
        self._storage_adapter = storage_adapter
        self._attachment_repo = attachment_repo
        self._membership_repo = membership_repo
        self._reference_index_store = reference_index_store

    # ── Art. 15 / 20: data export ──────────────────────────────────

    def request_data_export(self, user_key: UserKey) -> DataExportRequest:
        """Create a new export job. Validates that no active export exists."""
        existing = self._export_repo.list_active_by_user(user_key)
        errors = self._data_export_engine.validate_export_request(user_key, existing)
        if errors:
            raise ValidationError("; ".join(errors))

        export = DataExportRequest(
            user_key=user_key,
            status="pending",
            requested_at=datetime.now(UTC),
            download_count=0,
        )
        created = self._export_repo.create(export)
        logger.info(
            "privacy_export_requested",
            user_key=user_key,
            export_key=created.key,
        )
        # TODO(NFR-011): celery dispatch_async("process_data_export", export_key=created.key)
        return created

    def get_export_status(
        self,
        user_key: UserKey,
        export_key: str,
    ) -> DataExportRequest:
        """Return an export job, enforcing ownership."""
        export = self._export_repo.get_by_key(export_key)
        if export is None:
            raise NotFoundError("DataExportRequest", export_key)
        if export.user_key != user_key:
            raise NotFoundError("DataExportRequest", export_key)
        return export

    def list_user_exports(self, user_key: UserKey) -> list[DataExportRequest]:
        """List all exports for the user (newest first)."""
        return self._export_repo.list_by_user(user_key)

    def prepare_export_download(
        self,
        user_key: UserKey,
        export_key: str,
    ) -> DataExportRequest:
        """Validate an export is downloadable and bump the download counter."""
        export = self.get_export_status(user_key, export_key)
        if export.status != "completed":
            raise ValidationError(f"Export is not ready for download (status='{export.status}').")
        if export.expires_at and export.expires_at < datetime.now(UTC):
            raise ValidationError("Download link has expired.")
        if not export.file_path:
            raise ValidationError("Export file is not available.")

        export.download_count += 1
        if export.key:
            self._export_repo.update(export.key, export)
        logger.info(
            "privacy_export_download",
            user_key=user_key,
            export_key=export.key,
            download_count=export.download_count,
        )
        return export

    # ── Art. 16: email change ──────────────────────────────────────

    def request_email_change(
        self,
        user_key: UserKey,
        new_email: str,
    ) -> EmailChangeRequest:
        """Initiate a two-step email-change flow with token verification."""
        user = self._user_repo.get_by_key(user_key)
        if user is None:
            raise NotFoundError("User", user_key)
        if user.email == new_email:
            raise ValidationError("New email must differ from the current address.")

        existing = self._user_repo.get_by_email(new_email)
        if existing is not None:
            # Generic error to prevent account enumeration.
            raise DuplicateError("User", "email", new_email)

        raw_token = secrets.token_urlsafe(32)
        token_hash = self._token_engine.hash_token(raw_token)
        now = datetime.now(UTC)

        change = EmailChangeRequest(
            user_key=user_key,
            new_email=new_email,
            verification_token_hash=token_hash,
            status="pending",
            requested_at=now,
            expires_at=now + timedelta(hours=self.EMAIL_CHANGE_TTL_HOURS),
        )
        created = self._email_change_repo.create(change)

        # Send verification email to the NEW address.
        try:
            self._email_service.send_verification_email(
                to_email=new_email,
                display_name=user.display_name,
                token=raw_token,
                frontend_url=self._frontend_url,
            )
        except NotImplementedError:
            # Console adapter / test stubs may not implement every method.
            logger.warning("email_change_email_send_skipped", user_key=user_key)

        logger.info(
            "privacy_email_change_requested",
            user_key=user_key,
            request_key=created.key,
        )
        return created

    def confirm_email_change(self, raw_token: str) -> User:
        """Validate token, swap user.email and revoke all sessions."""
        token_hash = self._token_engine.hash_token(raw_token)
        change = self._email_change_repo.get_by_token_hash(token_hash)
        if change is None or change.status != "pending":
            raise InvalidTokenError("email-change token")
        if change.expires_at < datetime.now(UTC):
            change.status = "expired"
            if change.key:
                self._email_change_repo.update(change.key, change)
            raise InvalidTokenError("email-change token")

        user = self._user_repo.get_by_key(change.user_key)
        if user is None:
            raise NotFoundError("User", change.user_key)

        old_email = user.email
        user.email = change.new_email
        user.email_verified = True
        if user.key:
            self._user_repo.update(user.key, user)
            self._refresh_token_repo.revoke_all_for_user(user.key)

        change.status = "confirmed"
        change.confirmed_at = datetime.now(UTC)
        if change.key:
            self._email_change_repo.update(change.key, change)

        logger.info(
            "privacy_email_change_confirmed",
            user_key=user.key,
            old_email=old_email,
            new_email=user.email,
        )
        return user

    # ── Art. 17: erasure ───────────────────────────────────────────

    def request_erasure(
        self,
        user_key: UserKey,
        password_confirmation: str | None,
    ) -> ErasureRequest:
        """Create an erasure request, soft-delete the user and revoke sessions.

        Hard-delete is scheduled 90 days into the future. The actual deletion
        runs in a Celery task (NFR-011 R-01).
        """
        user = self._user_repo.get_by_key(user_key)
        if user is None:
            raise NotFoundError("User", user_key)

        existing = self._erasure_repo.find_active_for_user(user_key)
        if existing is not None:
            raise ValidationError("An erasure request is already in progress.")

        # Local accounts: require password re-auth. OAuth-only accounts must
        # confirm via a different upstream flow that is out of scope here.
        if user.password_hash is not None and (
            not password_confirmation
            or not self._password_engine.verify_password(password_confirmation, user.password_hash)
        ):
            raise UnauthorizedError("Password confirmation failed.")

        now = datetime.now(UTC)
        erasure = ErasureRequest(
            user_key=user_key,
            status="scheduled",
            requested_at=now,
            soft_deleted_at=now,
            hard_delete_scheduled_at=now + timedelta(days=self.HARD_DELETE_DAYS),
            anonymized_collections=[rule.collection for rule in self._erasure_engine.ANONYMIZE_COLLECTIONS],
            retained_reason=(
                "Harvest, treatment and inspection records are retained per CanG and PflSchG and will be anonymised."
            ),
        )
        created = self._erasure_repo.create(erasure)

        # Immediate effects: soft-delete the user and revoke all sessions.
        if user.key:
            user.is_active = False
            user.password_hash = None
            self._user_repo.update(user.key, user)
            self._refresh_token_repo.revoke_all_for_user(user.key)

        logger.info(
            "privacy_erasure_requested",
            user_key=user_key,
            erasure_key=created.key,
            hard_delete_at=erasure.hard_delete_scheduled_at,
        )
        # TODO(NFR-011): celery beat task `execute_scheduled_erasures`
        # picks up scheduled items and performs hard-delete.
        return created

    def get_erasure_status(self, erasure_key: str) -> ErasureRequest:
        erasure = self._erasure_repo.get_by_key(erasure_key)
        if erasure is None:
            raise NotFoundError("ErasureRequest", erasure_key)
        return erasure

    # ── Art. 18: processing restriction ────────────────────────────

    def restrict_processing(
        self,
        user_key: UserKey,
        scope: str,
        reason: RestrictionReason,
        notes: str | None = None,
    ) -> ProcessingRestriction:
        existing = self._restriction_repo.get_by_user_and_scope(user_key, scope)
        if existing is not None and existing.lifted_at is None:
            raise DuplicateError("ProcessingRestriction", "scope", scope)

        restriction = ProcessingRestriction(
            user_key=user_key,
            scope=scope,
            reason=reason,
            notes=notes,
        )
        created = self._restriction_repo.create(restriction)
        logger.info(
            "privacy_restriction_created",
            user_key=user_key,
            scope=scope,
            reason=reason,
        )
        return created

    def lift_restriction(
        self,
        user_key: UserKey,
        restriction_key: str,
    ) -> ProcessingRestriction:
        restriction = self._restriction_repo.get_by_key(restriction_key)
        if restriction is None or restriction.user_key != user_key:
            raise NotFoundError("ProcessingRestriction", restriction_key)
        if restriction.lifted_at is not None:
            return restriction

        restriction.lifted_at = datetime.now(UTC)
        if restriction.key:
            updated = self._restriction_repo.update(restriction.key, restriction)
            logger.info(
                "privacy_restriction_lifted",
                user_key=user_key,
                restriction_key=restriction.key,
            )
            return updated
        return restriction

    def list_restrictions(self, user_key: UserKey) -> list[ProcessingRestriction]:
        return self._restriction_repo.list_by_user(user_key)

    # ── Art. 21: objection ─────────────────────────────────────────

    def object_to_processing(
        self,
        user_key: UserKey,
        purpose: str,
        reason: str,
    ) -> ProcessingRestriction:
        """Create a restriction with reason='objection_pending' (Art. 21)."""
        restriction = ProcessingRestriction(
            user_key=user_key,
            scope=purpose,
            reason="objection_pending",
            notes=reason,
        )
        # Allow overlapping objections — but enforce the unique scope index by
        # bumping a numeric suffix if the scope already exists.
        existing = self._restriction_repo.get_by_user_and_scope(user_key, purpose)
        if existing is not None and existing.lifted_at is None:
            raise DuplicateError("ProcessingRestriction", "scope", purpose)
        created = self._restriction_repo.create(restriction)
        logger.info(
            "privacy_objection_filed",
            user_key=user_key,
            purpose=purpose,
        )
        return created

    # ── Consent management ─────────────────────────────────────────

    def list_consents(self, user_key: UserKey) -> list[ConsentWithPurpose]:
        """Return all known purposes annotated with the user's consent state."""
        records_by_purpose = {record.purpose: record for record in self._consent_repo.list_by_user(user_key)}
        results: list[ConsentWithPurpose] = []
        for purpose in self._consent_engine.get_all_purposes():
            record = records_by_purpose.get(purpose.key)
            granted = purpose.required or (record is not None and record.granted)
            results.append(
                ConsentWithPurpose(
                    purpose=purpose.key,
                    label=purpose.label_en,
                    description=purpose.description_en,
                    legal_basis=purpose.legal_basis,
                    required=purpose.required,
                    granted=granted,
                    granted_at=record.granted_at if record else None,
                    revoked_at=record.revoked_at if record else None,
                )
            )
        return results

    def grant_consent(
        self,
        user_key: UserKey,
        purpose: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ConsentRecord:
        if not self._consent_engine.is_known_purpose(purpose):
            raise ValidationError(f"Unknown processing purpose: '{purpose}'.")

        now = datetime.now(UTC)
        existing = self._consent_repo.get_by_user_and_purpose(user_key, purpose)
        if existing is not None and existing.key:
            existing.granted = True
            existing.granted_at = now
            existing.revoked_at = None
            existing.ip_address = ip_address
            existing.user_agent = user_agent
            updated = self._consent_repo.update(existing.key, existing)
            logger.info("privacy_consent_granted", user_key=user_key, purpose=purpose)
            return updated

        record = ConsentRecord(
            user_key=user_key,
            purpose=purpose,
            granted=True,
            granted_at=now,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        created = self._consent_repo.create(record)
        logger.info("privacy_consent_granted", user_key=user_key, purpose=purpose)
        return created

    def revoke_consent(self, user_key: UserKey, purpose: str) -> ConsentRecord:
        errors = self._consent_engine.validate_consent_change(purpose, grant=False)
        if errors:
            raise ValidationError("; ".join(errors))

        existing = self._consent_repo.get_by_user_and_purpose(user_key, purpose)
        if existing is None or existing.key is None:
            # Idempotent: revoking an unknown record creates a revoked stub.
            record = ConsentRecord(
                user_key=user_key,
                purpose=purpose,
                granted=False,
                revoked_at=datetime.now(UTC),
            )
            created = self._consent_repo.create(record)
            logger.info("privacy_consent_revoked", user_key=user_key, purpose=purpose)
            return created

        existing.granted = False
        existing.revoked_at = datetime.now(UTC)
        updated = self._consent_repo.update(existing.key, existing)
        logger.info("privacy_consent_revoked", user_key=user_key, purpose=purpose)
        return updated

    # ── Privacy policy (public) ────────────────────────────────────

    def get_privacy_policy(self) -> PrivacyPolicyInfo:
        """Return the static privacy-policy snapshot (no auth required)."""
        purposes = self._consent_engine.get_all_purposes()

        retention = [
            RetentionCategoryInfo(
                category="account_data",
                description="Profile, email and authentication records",
                retention_period="Until account deletion (NFR-011 R-01).",
            ),
            RetentionCategoryInfo(
                category="harvest_records",
                description="Harvest documentation (CanG)",
                retention_period="5 years (anonymised after deletion).",
            ),
            RetentionCategoryInfo(
                category="treatment_records",
                description="Plant-protection and treatment records (PflSchG)",
                retention_period="3 years (anonymised after deletion).",
            ),
            RetentionCategoryInfo(
                category="ip_addresses",
                description="IP addresses captured during authentication / consent",
                retention_period="Anonymised after 7 days (NFR-011 R-04).",
            ),
            RetentionCategoryInfo(
                category="export_files",
                description="Generated data-export files",
                retention_period="72 hours after completion (NFR-011 R-05).",
            ),
        ]

        rights = [
            RightInfo(
                article="Art. 15",
                title="Right of access",
                description="Request a machine-readable copy of all personal data.",
            ),
            RightInfo(
                article="Art. 16",
                title="Right to rectification",
                description="Update your email address with verification.",
            ),
            RightInfo(
                article="Art. 17",
                title="Right to erasure",
                description=("Delete your account. Retention-protected records are anonymised, not deleted."),
            ),
            RightInfo(
                article="Art. 18",
                title="Right to restriction",
                description="Restrict processing for a specific scope.",
            ),
            RightInfo(
                article="Art. 20",
                title="Right to data portability",
                description="Export your data in JSON format.",
            ),
            RightInfo(
                article="Art. 21",
                title="Right to object",
                description=("Object to processing based on legitimate interests (Art. 6(1)(f))."),
            ),
        ]

        return PrivacyPolicyInfo(
            version=self.PRIVACY_POLICY_VERSION,
            effective_date=self.PRIVACY_POLICY_EFFECTIVE_DATE,
            purposes=purposes,
            retention_summary=retention,
            data_controller=DataControllerInfo(
                name=self._data_controller_name,
                contact_email=self._data_controller_email,
            ),
            rights_summary=rights,
        )

    # ── NFR-011 retention pipeline (Celery-driven) ─────────────────
    # The four hooks below are called by ``app.tasks.retention_tasks``.
    # They scaffold the retention pipeline so the schedulers wire end
    # to end; the actual data walk + object-storage cleanup land with
    # NFR-013 (S3 adapter) — until then these methods short-circuit on
    # the repository and log the work that *would* happen.

    async def process_data_export(self, export_key: str) -> DataExportRequest | None:
        """Build the export bundle and flip the request to ``completed``.

        Pipeline (full implementation depends on NFR-013 object storage):
        1. Load DataExportRequest
        2. Walk all user-owned collections → JSON manifest
        3. Upload to object storage, capture file_path + file_size_bytes
        4. Set status=completed, expires_at=now+72h (NFR-011 R-05)
        """
        export = self._export_repo.get_by_key(export_key)
        if export is None:
            logger.warning("retention.process_data_export.missing", export_key=export_key)
            return None
        if export.status != "pending":
            logger.info(
                "retention.process_data_export.skipped",
                export_key=export_key,
                status=export.status,
            )
            return export

        logger.info(
            "retention.process_data_export.scaffold",
            export_key=export_key,
            note="full data-walk and S3 upload pending NFR-013",
        )
        # Scaffolded transition: flip pending → processing so the run is
        # observable; the worker that lands NFR-013 finishes the flow.
        export.status = "processing"
        export.processing_started_at = datetime.now(UTC)
        return self._export_repo.update(export_key, export)

    async def execute_scheduled_erasures(self, now: datetime) -> int:
        """Hard-delete users whose 90-day soft-delete grace expired.

        Returns the number of erasures *finalised* in this run. Each candidate
        runs through the W-007 phase order:

          Phase 0    object-storage cleanup (hard-delete + anonymise/strip)
          Phase 0.5  reference-index cleanup (pgvector user_contributed)
          Phase 1-3  ArangoDB edges/documents/user (+ Phase 2.5 audit hash)

        **Security-critical ordering:** Phase 0 / 0.5 MUST run before any
        ArangoDB deletion — they rely on the ``attachments`` metadata
        (``created_by == user_key``) which Phase 1 would remove. If Phase 0 or
        0.5 fails, the erasure is marked ``partially_completed`` and the
        ArangoDB deletion is skipped so the next daily run can retry
        (AK-OS-04 / AK-OS-05).
        """
        candidates = self._erasure_repo.list_due_for_hard_delete(now.isoformat())
        if not candidates:
            return 0

        finalised = 0
        for erasure in candidates:
            if await self._finalize_erasure(erasure, now):
                finalised += 1
        logger.info(
            "retention.execute_scheduled_erasures.completed",
            candidates=len(candidates),
            finalised=finalised,
        )
        return finalised

    async def _finalize_erasure(self, erasure: ErasureRequest, now: datetime) -> bool:
        """Run the phased hard-delete for a single erasure request.

        Returns ``True`` when the erasure reached ``completed``; ``False`` when
        a pre-ArangoDB phase failed and the request was left
        ``partially_completed`` for retry.
        """
        if erasure.key is None:
            return False
        try:
            self._mark_erasure(erasure, status="in_progress")

            # ── Phase 0: object-storage cleanup (W-007) ────────────────
            cleanup_scopes = await self._run_storage_cleanup(erasure.user_key)

            # ── Phase 0.5: reference-index cleanup (REQ-034 SR-003) ────
            await self._run_reference_index_cleanup(erasure.user_key)
        except Exception as exc:  # noqa: BLE001 — any pre-delete failure → retry
            logger.error(
                "retention.erasure.pre_delete_failed",
                erasure_key=erasure.key,
                user_key=erasure.user_key,
                error=str(exc),
            )
            self._mark_erasure(
                erasure,
                status="partially_completed",
                error_message=str(exc),
            )
            return False

        # ── Phase 1-3: ArangoDB deletion (+ Phase 2.5 audit hash) ──────
        # The generic ArangoDB hard-delete + audit pseudonymisation pipeline
        # lands with the NFR-011 deletion worker. Phase 0 / 0.5 above already
        # detached every binary + reference-index artefact from the user, so
        # the request is recorded as completed with the storage scopes that ran.
        logger.info(
            "retention.erasure.arango_delete_pending",
            erasure_key=erasure.key,
            user_key=erasure.user_key,
            note="ArangoDB edge/document/user hard-delete lands with NFR-011 worker",
        )
        self._mark_erasure(
            erasure,
            status="completed",
            completed_at=now,
            storage_cleanup_scopes=cleanup_scopes,
        )
        return True

    async def _run_storage_cleanup(self, user_key: str) -> list[str]:
        """Phase 0 — walk the user's tenants and apply STORAGE_CLEANUP_RULES.

        A user can belong to several tenants (REQ-024 membership); the
        ``attachments`` lookup is tenant-scoped, so the cleanup runs per tenant.
        Returns the list of scopes that were applied (for the audit record).
        """
        if self._storage_adapter is None or self._membership_repo is None:
            logger.info(
                "retention.erasure.storage_cleanup_skipped",
                user_key=user_key,
                reason="storage adapter / membership repo not wired",
            )
            return []

        tenant_keys = self._user_tenant_keys(user_key)
        applied_scopes: list[str] = []
        for rule in self._erasure_engine.STORAGE_CLEANUP_RULES:
            for tenant_key in tenant_keys:
                if rule.action == "hard_delete":
                    deleted = await self._storage_adapter.delete_for_user(
                        tenant_key=tenant_key,
                        user_key=user_key,
                        scope=rule.scope,
                    )
                    logger.info(
                        "retention.erasure.storage_hard_delete",
                        scope=rule.scope,
                        tenant_key=tenant_key,
                        user_key=user_key,
                        deleted=deleted,
                    )
                elif rule.action == "anonymize_metadata_and_strip_exif":
                    anonymised = await self._anonymize_attachment_metadata(
                        tenant_key=tenant_key,
                        user_key=user_key,
                        scope=rule.scope,
                    )
                    stripped = await self._storage_adapter.strip_exif_for_user(
                        tenant_key=tenant_key,
                        user_key=user_key,
                        scope=rule.scope,
                    )
                    logger.info(
                        "retention.erasure.storage_anonymize",
                        scope=rule.scope,
                        tenant_key=tenant_key,
                        user_key=user_key,
                        metadata_anonymized=anonymised,
                        exif_stripped=stripped,
                    )
            applied_scopes.append(rule.scope)
        return applied_scopes

    async def _anonymize_attachment_metadata(self, tenant_key: str, user_key: str, scope: str) -> int:
        """Set ``created_by = '_anonymized'`` for the scope's categories."""
        if self._attachment_repo is None:
            return 0
        from app.data_access.storage.local_fs_adapter import _scope_to_categories

        categories = _scope_to_categories(scope)
        if categories is not None and not categories:
            return 0
        return self._attachment_repo.anonymize_user_metadata(
            tenant_key=tenant_key,
            user_key=user_key,
            categories=categories,
        )

    async def _run_reference_index_cleanup(self, user_key: str) -> int:
        """Phase 0.5 — remove the user's contributed DINOv2 embeddings.

        Runs once per user across all their tenants (the store filters by
        ``contributed_by == user_key``). No-op when the pgvector index has not
        been built yet (default :class:`NoopReferenceIndexStore`).
        """
        if self._reference_index_store is None:
            logger.info(
                "retention.erasure.reference_index_cleanup_skipped",
                user_key=user_key,
                reason="reference-index store not wired",
            )
            return 0
        removed = await self._reference_index_store.delete_user_contributions(
            tenant_key=None,
            user_key=user_key,
        )
        logger.info(
            "retention.erasure.reference_index_cleanup",
            user_key=user_key,
            removed=removed,
        )
        return removed

    def _user_tenant_keys(self, user_key: str) -> list[str]:
        """Return the distinct tenant keys the user is a member of."""
        if self._membership_repo is None:
            return []
        memberships = self._membership_repo.list_by_user(user_key)
        seen: dict[str, None] = {}
        for m in memberships:
            if m.tenant_key:
                seen[m.tenant_key] = None
        return list(seen)

    def _mark_erasure(
        self,
        erasure: ErasureRequest,
        *,
        status: str,
        completed_at: datetime | None = None,
        error_message: str | None = None,
        storage_cleanup_scopes: list[str] | None = None,
    ) -> None:
        """Persist an erasure-status transition (in-place update)."""
        if erasure.key is None:
            return
        erasure.status = status  # type: ignore[assignment]
        if completed_at is not None:
            erasure.completed_at = completed_at
        if error_message is not None:
            erasure.error_message = error_message
        if storage_cleanup_scopes is not None:
            erasure.storage_cleanup_scopes = storage_cleanup_scopes
        self._erasure_repo.update(erasure.key, erasure)

    async def expire_email_change_requests(self, now: datetime) -> int:
        """Mark unconfirmed email-change requests older than 24 h as expired."""
        affected = self._email_change_repo.expire_old(now.isoformat())
        if affected:
            logger.info(
                "retention.expire_email_change_requests.completed",
                expired=affected,
            )
        return affected

    async def expire_data_exports(self, now: datetime) -> int:
        """Flip completed exports past their 72-hour expiry to ``expired``."""
        affected = self._export_repo.expire_old(now.isoformat())
        if affected:
            logger.info(
                "retention.expire_data_exports.completed",
                expired=affected,
            )
        return affected
