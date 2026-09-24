"""Service orchestrator for REQ-025 privacy & data subject rights."""

from __future__ import annotations

import asyncio
import json
import secrets
from collections.abc import AsyncIterator, Callable
from datetime import UTC, date, datetime, timedelta
from typing import TYPE_CHECKING

import structlog

from app.common.decoys import decoy_document_key, email_digest
from app.common.exceptions import (
    DuplicateError,
    FeatureNotConfiguredError,
    InvalidTokenError,
    KamerplanterError,
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
from app.domain.interfaces.erasure_executor import IErasureExecutor
from app.domain.interfaces.erasure_repository import IErasureRepository
from app.domain.interfaces.ipm_repository import IIpmRepository
from app.domain.interfaces.membership_repository import IMembershipRepository
from app.domain.interfaces.object_storage_adapter import IObjectStorageAdapter
from app.domain.interfaces.personal_data_repository import IPersonalDataRepository
from app.domain.interfaces.pest_image_repository import IPestImageRepository
from app.domain.interfaces.processing_restriction_repository import (
    IProcessingRestrictionRepository,
)
from app.domain.interfaces.reference_index_store import IReferenceIndexStore
from app.domain.interfaces.refresh_token_repository import IRefreshTokenRepository
from app.domain.interfaces.user_repository import IUserRepository
from app.domain.models.privacy import (
    AccountErasureReport,
    ConsentRecord,
    ConsentWithPurpose,
    DataControllerInfo,
    DataExportRequest,
    DataSourceDefinition,
    EmailChangeRequest,
    ErasureRequest,
    PrivacyPolicyInfo,
    ProcessingRestriction,
    RestrictionReason,
    RetentionCategoryInfo,
    RightInfo,
)
from app.domain.models.user import User, is_tombstone_email

if TYPE_CHECKING:
    from app.data_access.external.pest_inference_client import PestDetectionInferenceClient

logger = structlog.get_logger()


def _persistable(fields: dict[str, object]) -> dict[str, object]:
    """Serialise a named-field write the way the full-model path serialises.

    ``update_fields`` hands its dict to the driver untouched — that is its
    documented caller obligation — while ``_to_doc`` runs a full model through
    pydantic. A raw ``datetime`` therefore reaches python-arango and raises
    ``Object of type datetime is not JSON serializable``; and a value that
    serialised *differently* would be worse, because the same field would then
    round-trip as one type when written narrowly and another when written whole.
    """
    return {key: (value.isoformat() if isinstance(value, datetime) else value) for key, value in fields.items()}


async def _single_chunk(payload: bytes) -> AsyncIterator[bytes]:
    """Adapt a fully-built bundle to the adapter's streaming ``put_object``."""
    yield payload


class ExportBundleUnavailableError(RuntimeError):
    """No Art. 15 bundle could be produced for a request.

    Carried as the ``error_message`` of the ``failed`` record so the requester
    sees a reason rather than a request that never moves.
    """


# Encryption-engine imported only to keep the dependency-injection signature
# explicit and to make the existing engine reusable for token-hashing in future
# work. Direct hashing for short-lived tokens uses TokenEngine.hash_token.
_ENCRYPTION_ENGINE_REUSE_HINT = EncryptionEngine


class PrivacyService:
    """Orchestrates GDPR rights (Art. 15/16/17/18/20/21) for a user.

    Heavy work runs in Celery (``app.tasks.retention_tasks``): export
    processing is dispatched by :meth:`request_data_export`, hard-delete
    after the 90-day grace period runs via the daily
    ``retention.execute_scheduled_erasures`` beat task (NFR-011).
    """

    PRIVACY_POLICY_VERSION = "1.0"
    PRIVACY_POLICY_EFFECTIVE_DATE = date(2026, 4, 27)
    EMAIL_CHANGE_TTL_HOURS = 24
    #: NFR-011 R-05 — how long a built Art. 15 bundle stays downloadable.
    EXPORT_TTL_HOURS = 72
    HARD_DELETE_DAYS = 90
    # SEC-001 staleness guard: an ``in_progress`` erasure is only re-picked when
    # its last update is older than this window. The erasure beat task runs
    # daily, so 6 h is well beyond a single healthy run yet short enough to
    # recover a crashed worker on the next day's run.
    ERASURE_STALE_AFTER_HOURS = 6
    # #1666 — retry lifecycle of a failing scheduled erasure. The n-th failed
    # attempt defers the next one by ``2 ** (n - 1)`` days, capped: a transient
    # outage is retried the next night, a persistent failure stops repeating the
    # full erasure nightly. ``ERASURE_RETRY_SLACK`` absorbs the beat's own
    # jitter so a one-day backoff does not miss the next 04:00 run by seconds.
    ERASURE_RETRY_MAX_DELAY_DAYS = 7
    ERASURE_RETRY_SLACK = timedelta(hours=1)
    #: The failed attempt that is logged at error a second time (escalation).
    #: Between the first failure and this one the failures log at info.
    ERASURE_ESCALATE_AFTER_ATTEMPTS = 5

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
        pest_image_repo: IPestImageRepository | None = None,
        ipm_repo: IIpmRepository | None = None,
        pest_inference_client: PestDetectionInferenceClient | None = None,
        personal_data_repo: IPersonalDataRepository | None = None,
        erasure_executor: IErasureExecutor | None = None,
        tombstone_salt: str = "",
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
        # REQ-010 — pest-image link documents are an ArangoDB collection outside
        # the object-storage sweep; their bytes are hard-deleted by the
        # ``user_pest_reference_images`` storage rule, this repo drops the docs.
        self._pest_image_repo = pest_image_repo
        # SEC-001 — a promoted contribution also has a DINOv2 embedding in the
        # recognition index (``source="user_contributed"``). It must be retracted
        # before the link documents are dropped (the label is resolved from the
        # contribution's pest while it still exists). Both optional so non-erasure
        # callers stay unaffected; the retract is a no-op when either is unwired.
        self._ipm_repo = ipm_repo
        self._pest_inference_client = pest_inference_client
        # REQ-025 Art. 15 — the read side of the declared export manifest.
        # Optional so non-export callers (and the many tests that construct a
        # PrivacyService for one unrelated method) stay unaffected; when it is
        # absent an export run fails *visibly* rather than silently delivering
        # nothing, which is the whole point of #1645.
        self._personal_data_repo = personal_data_repo
        # REQ-025 Art. 17 — the write side of the declared erasure plan (#1664)
        # and the NFR-011 §4 salt its tombstone hashes are built from. Optional
        # for the same reason as above; :meth:`erase_account` refuses to start
        # without either, before it touches anything.
        self._erasure_executor = erasure_executor
        self._tombstone_salt = tombstone_salt

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
        if created.key:
            self._dispatch_export_processing(created.key)
        return created

    def _dispatch_export_processing(self, export_key: str) -> None:
        """Enqueue the export worker (NFR-011).

        Lazy import avoids a hard import cycle (tasks import dependencies
        which import services) and keeps Celery optional at
        service-construction time. A broker outage must not fail the API
        request — the record stays ``pending`` and is re-dispatched by the
        hourly ``retention.redispatch_stale_pending_exports`` beat task.
        """
        try:
            from app.tasks.retention_tasks import process_data_export

            process_data_export.delay(export_key)
            logger.info("privacy_export_dispatch", export_key=export_key)
        except Exception as exc:  # noqa: BLE001 — broker outage is survivable
            logger.error(
                "privacy_export_dispatch_failed",
                export_key=export_key,
                error=str(exc),
            )

    def get_export_status(
        self,
        user_key: UserKey,
        export_key: str,
    ) -> DataExportRequest:
        """Return an export job, enforcing ownership."""
        export = self._export_repo.get_or_raise(export_key)
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
            # #1645 — a bare status name tells the requester nothing. When the
            # run recorded why it failed, the refusal carries that reason.
            detail = f" {export.error_message}" if export.error_message else ""
            raise ValidationError(f"Export is not ready for download (status='{export.status}').{detail}")
        if export.expires_at and export.expires_at < datetime.now(UTC):
            raise ValidationError("Download link has expired.")
        if not export.file_path:
            raise ValidationError("Export file is not available.")

        # An atomic increment, not a full-model write-back: if
        # ``expire_data_exports`` ran between the read above and this write, a
        # write-back would resurrect ``completed`` and a ``file_path`` whose
        # object was just deleted (#1662 SCR-005).
        if export.key:
            export = self._export_repo.increment_download_count(export.key)
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
        user = self._user_repo.get_or_raise(user_key)
        if user.email == new_email:
            raise ValidationError("New email must differ from the current address.")
        # Same reserved domain as on the registration path (#1525 SCR-014): moving an
        # account into it would occupy the address a future soft-delete needs, and
        # `users.email` is uniquely indexed.
        if is_tombstone_email(new_email):
            raise ValidationError("This email domain is reserved and cannot be used.")

        if self._user_repo.get_by_email(new_email) is not None:
            return self._suppress_taken_email_change(user_key, user, new_email)

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

    def _suppress_taken_email_change(
        self,
        user_key: UserKey,
        user: User,
        new_email: str,
    ) -> EmailChangeRequest:
        """Answer an email change to an address someone else already owns.

        This branch used to ``raise DuplicateError("User", "email", new_email)``
        under a comment reading "Generic error to prevent account enumeration".
        It is not generic: the global handler renders it as **409** with
        ``User with email='<address>' already exists.`` plus a ``details[].reason``
        repeating the address — an explicit statement that the address is
        registered, to any authenticated caller, for any address they care to
        type in. The comment promising the opposite is what let it survive, the
        same way it did for registration in #901.

        The honest answer is the one REQ-025 §Art. 16 describes: accept the
        request as pending, exactly as for a free address, and tell the address
        that was targeted. So:

        * **Nothing is written.** A persisted request would be confirmable, and
          confirming it would move this account onto an address another account
          already holds — a duplicate-identity bug behind an enumeration fix.
          The returned object is synthesised and never reaches the repository,
          so ``confirm_email_change`` answers the same
          ``InvalidTokenError("email-change token")`` a genuine request whose
          token was never received would answer.
        * **No verification mail goes to the new address.** It belongs to
          somebody else; sending them a token they could act on would be worse
          than the disclosure. They get told what was attempted instead.
        * The token is still generated and hashed, so the branch does the same
          work — the response is only indistinguishable if the clock agrees.

        What the caller can still learn: nothing from this endpoint. They learn
        the address is taken only if they *also* control it and read the notice,
        which they could have established by logging in.
        """
        now = datetime.now(UTC)

        # Generated and discarded — see the docstring. Not doing this work would
        # leave a measurable gap between the two branches.
        self._token_engine.hash_token(secrets.token_urlsafe(32))

        self._notify_email_change_target(new_email, user.display_name)

        logger.info(
            "privacy_email_change_suppressed",
            user_key=user_key,
            new_email_sha256=email_digest(new_email),
        )
        return EmailChangeRequest(
            _key=decoy_document_key(),
            user_key=user_key,
            new_email=new_email,
            # No token exists, because no request exists. The field is never
            # returned to the caller (``EmailChangeResponse`` has no such field).
            verification_token_hash="",
            status="pending",
            requested_at=now,
            expires_at=now + timedelta(hours=self.EMAIL_CHANGE_TTL_HOURS),
        )

    def _notify_email_change_target(self, target_email: str, requester_display_name: str) -> None:
        """Tell an address that another account tried to move onto it.

        The requester's display name is *not* included: they are unauthenticated
        as far as the recipient is concerned, and echoing an attacker-chosen
        string into a third party's inbox turns this notice into a message
        channel.
        """
        body = (
            "<h2>Someone tried to use your email address</h2>"
            "<p>An account on Kamerplanter requested to change its email address "
            "to this one. Because the address is already registered here, the "
            "change was not carried out and nothing about your account has "
            "changed.</p>"
            "<p>If that was you, sign in with this address instead. If it was "
            "not, you do not need to do anything — but consider changing your "
            "password if you reused it elsewhere.</p>"
        )
        try:
            self._email_service.send_notification_email(
                to_email=target_email,
                subject="Kamerplanter — someone tried to use your email address",
                html_body=body,
            )
        except NotImplementedError:
            # Console adapter / test stubs may not implement every method.
            # Only NotImplementedError is swallowed, exactly as on the genuine
            # path below: if a real send failure produced a 500 there and a 201
            # here, the mail outage itself would become the oracle.
            logger.warning("email_change_target_notice_skipped")

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

        user = self._user_repo.get_or_raise(change.user_key)

        old_email = user.email
        # Narrow write (#1525 SCR-003): the token lookup and validation sit between
        # the read and the write, and a full-model write-back would remove whatever a
        # parallel request set in between now that the repository is full-replace.
        if user.key:
            user = self._user_repo.update_fields(user.key, {"email": change.new_email, "email_verified": True})
            self._refresh_token_repo.revoke_all_for_user(user.key)
        else:  # pragma: no cover - a user read through get_or_raise always carries a key
            user.email = change.new_email
            user.email_verified = True

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
        user = self._user_repo.get_or_raise(user_key)

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
            # De-duplicated: since REQ-050 one collection can carry several
            # anonymisation rules (plant_diary_entries has three user
            # references) and the confirmation lists categories, not rules.
            anonymized_collections=self._erasure_engine.anonymized_collection_names(),
            # REQ-025 AK-08a — the other half of the confirmation, off the same
            # inventory the erasure executes. It was declared on the model and
            # never filled, so the confirmation named no deleted category.
            deleted_collections=self._erasure_engine.deleted_collection_names(),
            retained_reason=(
                "Harvest records (including quality assessments), treatment and inspection records are "
                "retained per CanG and PflSchG and will be anonymised. "
                "Diary entries stay with the plant record of their tenant; their author and AI-analysis "
                "references are anonymised (REQ-050 section 7.4)."
            ),
        )
        created = self._erasure_repo.create(erasure)

        # Immediate effects: soft-delete the user and revoke all sessions.
        #
        # A *narrow* write (#1525 SCR-003). The full-model form read the user at the
        # top of this method, verified a bcrypt hash and created the erasure record
        # before writing — hundreds of milliseconds during which a parallel
        # `request_password_reset` could set `password_reset_token`. Since
        # `ArangoUserRepository` became full-replace, writing the stale model back
        # would not just lose that value, it would **remove** the attribute.
        # `update_fields` re-reads the stored user inside the call.
        if user.key:
            self._user_repo.update_fields(user.key, {"is_active": False, "password_hash": None})
            self._refresh_token_repo.revoke_all_for_user(user.key)

        logger.info(
            "privacy_erasure_requested",
            user_key=user_key,
            erasure_key=created.key,
            hard_delete_at=erasure.hard_delete_scheduled_at,
        )
        # Hard-delete is performed by the daily beat task
        # ``retention.execute_scheduled_erasures`` (app/tasks/__init__.py).
        return created

    def get_erasure_status(self, user_key: UserKey, erasure_key: str) -> ErasureRequest:
        """Return an erasure request, enforcing ownership.

        #1662 SCR-010 — this took only the key, so any authenticated user could
        read another subject's Art. 17 record (status, timestamps,
        ``retained_reason``, the deleted-collection lists) by enumerating keys.
        Foreign ownership reads as *not found*, word for word like the export
        route, so the response is not an existence oracle either.
        """
        erasure = self._erasure_repo.get_or_raise(erasure_key)
        if erasure.user_key != user_key:
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
    # This comment used to say that all four merely "log the work that
    # *would* happen". That stopped being true for one of them and kept
    # being true for another — the ambiguity #1645 is about. Precisely:
    #
    # * ``process_data_export`` **runs**: it walks the declared Art. 15
    #   manifest, stores the bundle and serves it (#1645).
    # * ``execute_scheduled_erasures`` **runs**: each due request goes
    #   through :meth:`erase_account`, the entry the platform-admin delete
    #   shares, and is recorded ``completed`` only when every declared step
    #   was reached (#1645).
    # * ``expire_email_change_requests`` and ``expire_data_exports`` run.

    async def process_data_export(
        self,
        export_key: str,
        *,
        final_attempt: bool = True,
        is_retry: bool = False,
    ) -> DataExportRequest | None:
        """Build the export bundle and flip the request to a **terminal** state.

        Pipeline:
        1. Load the DataExportRequest and take the declared manifest into scope
        2. Flip ``pending`` → ``processing`` so the run is observable
        3. Build the bundle and record ``file_path`` / ``file_size_bytes``
        4. ``completed`` with ``expires_at = now + 72h`` (NFR-011 R-05)

        **#1645 — a run always ends somewhere.** The previous version stopped
        after step 2 and returned, so an Art. 15 request stayed ``processing``
        for ever: it neither delivered data nor reported a failure, and nothing
        on the record or in the API told the requester that the statutory right
        had not been served. Any failure of step 3/4 now ends the request as
        ``failed`` with an ``error_message`` the requester reads over
        ``GET /privacy/export/{key}``.

        **#1666 — which failures end it, and when.** A failure that another
        attempt would repeat identically — :class:`ExportBundleUnavailableError`
        or any domain error (:class:`KamerplanterError`) — ends the request as
        ``failed`` at once. Anything else is treated as infrastructure (object
        storage, database, network) and, unless this is the ``final_attempt``,
        is re-raised with the request left ``processing`` so the calling
        Celery task's declared retry policy applies. Only the final attempt
        writes ``failed``. A caller without a retry policy keeps the default
        ``final_attempt=True``: it must not leave a request open that nothing
        will pick up again.

        Args:
            final_attempt: No retry follows this call; any failure is terminal.
            is_retry: This call is a retry of an attempt that left the request
                ``processing``; that state is accepted instead of skipped.
        """
        export = self._export_repo.get_by_key(export_key)
        if export is None:
            logger.warning("retention.process_data_export.missing", export_key=export_key)
            return None
        resumable = ("pending", "processing") if is_retry else ("pending",)
        if export.status not in resumable:
            logger.info(
                "retention.process_data_export.skipped",
                export_key=export_key,
                status=export.status,
            )
            return export

        # The Art. 15 scope comes from the declared manifest, read here rather
        # than restated (#1622). Recording it on the request is what makes the
        # disclosure auditable: the record says which sources the run took into
        # scope, and the answer is the manifest itself, not a second list.
        manifest = self._data_export_engine.build_export_manifest(export.user_key)
        export.manifest_collections = [source.collection for source in manifest]

        # Narrow writes throughout this method (#1506 / #1525). A full-model
        # write-back is wrong here twice over: `ArangoDataExportRepository` is in
        # **merge** mode, so a field set to ``None`` never reaches the payload and
        # the stored value survives a clear that meant to happen; and the walk plus
        # the storage upload below sit between the read and the write, which is
        # exactly the window in which a full model goes stale.
        export.status = "processing"
        export.processing_started_at = datetime.now(UTC)
        export = self._export_repo.update_fields(
            export_key,
            _persistable(
                {
                    "status": export.status,
                    "processing_started_at": export.processing_started_at,
                    "manifest_collections": export.manifest_collections,
                }
            ),
        )

        object_key = self._data_export_engine.bundle_object_key(export.user_key, export_key)
        try:
            return await self._build_export_bundle(export, manifest, object_key)
        except (ExportBundleUnavailableError, KamerplanterError) as exc:
            # Deterministic: a retry would fail the same way.
            return await self._fail_export(export, exc, object_key=object_key)
        except Exception as exc:  # noqa: BLE001 — terminal only on the last attempt
            if final_attempt:
                return await self._fail_export(export, exc, object_key=object_key)
            logger.warning(
                "retention.process_data_export.retrying",
                export_key=export.key,
                error_type=type(exc).__name__,
                error=str(exc),
            )
            raise

    async def _build_export_bundle(
        self,
        export: DataExportRequest,
        manifest: list[DataSourceDefinition],
        object_key: str,
    ) -> DataExportRequest:
        """Produce the Art. 15 bundle and complete the request.

        Raises whatever goes wrong; :meth:`process_data_export` turns that into
        a recorded ``failed`` state. Returning normally is the *claim* that a
        downloadable bundle exists, so this method must not return without
        setting ``file_path`` and ``file_size_bytes``.
        """
        if export.key is None:  # pragma: no cover - persisted records always carry a key
            raise ExportBundleUnavailableError("The export request has no key; nothing can be stored against it.")
        if self._personal_data_repo is None or self._storage_adapter is None:
            raise ExportBundleUnavailableError(
                "This deployment cannot build Art. 15 export bundles: the personal-data "
                "reader or the object storage is not configured. No data has been "
                "delivered; please contact the operator."
            )

        # The subject's own tenants bound every tenant-scoped source (#1662
        # SCR-001): the user-reference fields on those documents are written by
        # whoever edits them, so without this a writer in any tenant could name
        # a foreign key and plant rows into that subject's disclosure.
        tenant_keys = self._user_tenant_keys(export.user_key)
        sections: list[tuple[DataSourceDefinition, list[dict[str, object]]]] = []
        for source in manifest:
            if source.disclosure_gap is not None:
                # Never queried: the bundle carries the reason instead of an
                # empty list that would read as "no data here".
                sections.append((source, []))
                continue
            sections.append((source, self._personal_data_repo.collect_for_user(source, export.user_key, tenant_keys)))

        # Anti-vacuity, in production rather than only in a test: an export that
        # found *nothing at all* is what a broken walk looks like from the
        # outside, and it is indistinguishable from an empty account. The user
        # document is the one source that must always answer, so a bundle
        # without it is a failure, not a delivery.
        profile_rows = sum(len(rows) for source, rows in sections if source.filter_field == "_key")
        if profile_rows == 0:
            raise ExportBundleUnavailableError(
                f"The export walk found no profile record for user '{export.user_key}'; "
                "refusing to deliver a bundle that would read as an empty account."
            )

        now = datetime.now(UTC)
        bundle = self._data_export_engine.build_bundle(
            export.user_key,
            now,
            sections,
            controller_name=self._data_controller_name,
            controller_email=self._data_controller_email,
        )
        payload = json.dumps(bundle, ensure_ascii=False, indent=2, default=str).encode("utf-8")

        await self._storage_adapter.put_object(
            object_key,
            _single_chunk(payload),
            "application/json",
            metadata={"user_key": export.user_key, "export_key": export.key},
        )

        completion = {
            "file_path": object_key,
            "file_size_bytes": len(payload),
            "status": "completed",
            "completed_at": now,
            "expires_at": now + timedelta(hours=self.EXPORT_TTL_HOURS),
            # A retry after a failed run must not complete while still carrying
            # the old reason. ``update_fields`` writes ``keep_none=True``, so
            # this clear actually lands; through ``update`` it would not.
            "error_message": None,
        }
        for field, value in completion.items():
            setattr(export, field, value)
        logger.info(
            # Distinct from the task-level ``.completed`` in ``retention_tasks``:
            # this one is the claim that bytes exist, and it carries their size.
            "retention.process_data_export.delivered",
            export_key=export.key,
            user_key=export.user_key,
            sources=len(sections),
            records=sum(len(rows) for _source, rows in sections),
            file_size_bytes=export.file_size_bytes,
        )
        return self._export_repo.update_fields(export.key, _persistable(completion))

    async def open_export_bundle(
        self, user_key: UserKey, export_key: str
    ) -> tuple[DataExportRequest, AsyncIterator[bytes]]:
        """Return the export record **and its bytes** for download (Art. 15).

        The endpoint used to answer with metadata only, so even a ``completed``
        export delivered no data (#1645). Ownership, status and expiry are
        enforced by :meth:`prepare_export_download`, which also counts the
        download; this adds the one thing that was missing — the content.
        """
        export = self.prepare_export_download(user_key, export_key)
        if self._storage_adapter is None or not export.file_path:  # pragma: no cover - guarded above
            raise ValidationError("Export file is not available.")
        stream = await self._storage_adapter.get_object(export.file_path)
        return export, stream

    async def _fail_export(
        self,
        export: DataExportRequest,
        exc: BaseException,
        *,
        object_key: str | None = None,
    ) -> DataExportRequest:
        """End an export run visibly: ``failed`` plus a reason on the record.

        ``completed_at`` is deliberately left unset — it is the timestamp of a
        delivered disclosure, and writing one here would reintroduce exactly the
        kind of false claim #1645 is about.

        **What the requester sees (#1662 SCR-008).** Only the text of an
        :class:`ExportBundleUnavailableError` is written to the record — that
        class exists to be read by the data subject. Anything else is an
        internal failure whose message may carry an AQL query, a path or a
        hostname; it goes to the log under a reference the requester is given,
        and nothing more.

        **What is left behind (#1662 SCR-006).** If the run failed after the
        bundle was stored — the completion write, say — a full copy of the
        account would otherwise sit orphaned in object storage with no record
        pointing at it. The object is removed best-effort.
        """
        if isinstance(exc, ExportBundleUnavailableError):
            reason = str(exc)
        else:
            reference = secrets.token_hex(6)
            reason = (
                f"The export failed for an internal reason (reference {reference}). "
                "No data has been delivered; please contact the operator with this reference."
            )
            logger.error(
                "retention.process_data_export.internal_error",
                export_key=export.key,
                user_key=export.user_key,
                reference=reference,
                error=str(exc),
                error_type=type(exc).__name__,
            )
        export.status = "failed"
        export.error_message = reason
        logger.error(
            "retention.process_data_export.failed",
            export_key=export.key,
            user_key=export.user_key,
            reason=reason,
        )
        if object_key and self._storage_adapter is not None:
            try:
                await self._storage_adapter.delete_object(object_key)
            except Exception as cleanup_exc:  # noqa: BLE001 — the failure is already being recorded
                logger.error(
                    "retention.process_data_export.orphan_cleanup_failed",
                    export_key=export.key,
                    object_key=object_key,
                    error=str(cleanup_exc),
                )
        if export.key is None:  # pragma: no cover - persisted records always carry a key
            return export
        return self._export_repo.update_fields(
            export.key,
            {"status": "failed", "error_message": reason},
        )

    async def execute_scheduled_erasures(self, now: datetime) -> int:
        """Hard-delete users whose 90-day soft-delete grace expired.

        Returns the number of erasures *finalised* in this run. Each candidate
        runs :meth:`erase_account`, which keeps the W-007 phase order:

          Phase 0    object-storage cleanup (hard-delete + anonymise/strip)
          Phase 0.5  reference-index cleanup (pgvector user_contributed)
          Phase 1-3  ArangoDB edges/documents/user (+ Phase 2.5 audit hash)

        **Security-critical ordering:** Phase 0 / 0.5 MUST run before any
        ArangoDB deletion — they rely on the ``attachments`` metadata
        (``created_by == user_key``) which Phase 1 would remove. If Phase 0 or
        0.5 fails, the erasure is marked ``partially_completed`` and the
        ArangoDB deletion is skipped so a later run can retry
        (AK-OS-04 / AK-OS-05). The same holds for a failed ArangoDB run: its
        transaction aborts and the request stays ``partially_completed``.

        **Retry lifecycle (#1666):** a failed attempt is counted on the request
        and defers the next one by 1, 2, 4, then 7 days (capped); a deferred
        request is still selected and skipped with an info line. A missing
        executor or tombstone salt is a configuration error, checked once per
        run: one error line, no request touched, no attempt spent.

        **Retry selection (SEC-001):** candidates include not only ``scheduled``
        requests but also ``partially_completed`` (transient failure) and
        **stale** ``in_progress`` requests (worker crashed mid-run). A fresh
        ``in_progress`` request — one updated within ``ERASURE_STALE_AFTER_HOURS``
        — is skipped so a run still executing is never processed twice.
        """
        stale_before = now - timedelta(hours=self.ERASURE_STALE_AFTER_HOURS)
        candidates = self._erasure_repo.list_due_for_hard_delete(now.isoformat(), stale_before.isoformat())
        if not candidates:
            return 0

        configuration_error = self._erasure_configuration_error()
        if configuration_error is not None:
            return self._hold_erasures_for_configuration(candidates, now, configuration_error)

        finalised = 0
        deferred = 0
        for erasure in candidates:
            if self._erasure_deferred(erasure, now):
                deferred += 1
                continue
            if await self._finalize_erasure(erasure, now):
                finalised += 1
        logger.info(
            "retention.execute_scheduled_erasures.completed",
            candidates=len(candidates),
            finalised=finalised,
            deferred=deferred,
            # The gauge of open, failing Art. 17 duties (#1666): what an operator
            # watches instead of a nightly error line per request.
            open_failing=sum(1 for e in candidates if e.status != "completed" and e.attempt_count > 0),
        )
        return finalised

    def _erasure_configuration_error(self) -> str | None:
        """Why this deployment cannot erase anything, or ``None`` when it can.

        #1666 — a missing executor or tombstone salt is not a property of one
        request and not transient: every candidate fails identically until the
        operator changes the configuration. It is therefore checked once per
        run, before any request is touched, instead of surfacing as one error
        line and one spent retry per request.
        """
        if self._erasure_executor is None:
            return "No erasure executor is wired on this deployment."
        try:
            self._erasure_engine.compute_tombstone_hash("configuration-probe", self._tombstone_salt)
        except ValueError:
            return "Set ERASURE_TOMBSTONE_SALT to a secret of at least 32 characters."
        return None

    def _hold_erasures_for_configuration(self, candidates: list[ErasureRequest], now: datetime, reason: str) -> int:
        """Keep every due request open, untouched, while the deployment cannot erase.

        One error line per run — loud, because a statutory duty is blocked and
        only the operator can unblock it, but one line and not one per request.
        No attempt is spent and no backoff is set: the requests carry no failure
        of their own, so the first run after the fix executes all of them.
        A request whose ArangoDB plan already committed needs neither executor
        nor salt and is still closed.
        """
        finalised = 0
        held = 0
        for erasure in candidates:
            if erasure.key is None:
                continue
            if self._erasure_engine.is_tombstone(erasure.user_key):
                finalised += int(self._record_committed_erasure(erasure, now))
                continue
            held += 1
            self._mark_erasure(
                erasure,
                status="partially_completed",
                error_message=(
                    f"Erasure is not configured on this deployment: {reason} "
                    "It runs on the first daily run after the configuration is fixed."
                ),
            )
        logger.error(
            "retention.execute_scheduled_erasures.not_configured",
            reason=reason,
            held=held,
            finalised=finalised,
        )
        return finalised

    def _erasure_deferred(self, erasure: ErasureRequest, now: datetime) -> bool:
        """True while a failed request waits out its backoff (#1666).

        The request stays selected by ``list_due_for_hard_delete``; only this
        run leaves it alone, and says so below error level.
        """
        if erasure.next_attempt_at is None or erasure.next_attempt_at <= now + self.ERASURE_RETRY_SLACK:
            return False
        logger.info(
            "retention.erasure.deferred",
            erasure_key=erasure.key,
            attempt_count=erasure.attempt_count,
            next_attempt_at=erasure.next_attempt_at.isoformat(),
        )
        return True

    async def _finalize_erasure(self, erasure: ErasureRequest, now: datetime) -> bool:
        """Run the account erasure for one due request and record what it did.

        The ArangoDB work is :meth:`erase_account` — the same entry the
        platform-admin delete runs, so the self-service Art. 17 path executes
        no step of its own and skips none (#1645). Until #1645 this ran only
        the object-storage and reference-index phases and recorded the request
        ``partially_completed`` because nothing in ArangoDB had been touched.

        ``completed`` is written only when the returned report accounts for
        every step of the declared inventory. Any exception, or a report that
        leaves a declared step unaccounted for, records ``partially_completed``
        with the reason and a backoff (:meth:`_record_failed_attempt`);
        ``list_due_for_hard_delete`` keeps selecting that state.

        #1666 — a retry does not repeat the storage work that already finished:
        once export cleanup, Phase 0 and Phase 0.5 have run for this request,
        ``pre_arango_completed_at`` is recorded and the next attempt runs only
        the ArangoDB plan. Skipping them is safe because the subject is
        soft-deleted — nothing new is created under their key — and the ArangoDB
        plan that would remove the attachment index they rely on runs in one
        transaction, so a failed plan left it intact.

        Returns ``True`` when the request reached ``completed``.
        """
        if erasure.key is None:
            return False
        if self._erasure_engine.is_tombstone(erasure.user_key):
            return self._record_committed_erasure(erasure, now)

        def _checkpoint(scopes: list[str]) -> None:
            self._mark_erasure(
                erasure,
                status="in_progress",
                storage_cleanup_scopes=scopes,
                pre_arango_completed_at=now,
            )

        try:
            self._mark_erasure(erasure, status="in_progress", last_attempt_at=now)
            report = await self.erase_account(
                erasure.user_key,
                pre_arango_completed=erasure.pre_arango_completed_at is not None,
                recorded_storage_scopes=erasure.storage_cleanup_scopes,
                on_pre_arango_complete=_checkpoint,
            )
        except Exception as exc:  # noqa: BLE001 — any failure leaves the duty open for a later run
            self._record_failed_attempt(
                erasure,
                now,
                event="retention.erasure.failed",
                reason=f"Erasure did not finish: {exc}",
                error=str(exc),
            )
            return False

        unreached = report.unreached(self._erasure_engine.delete_order())
        if unreached:
            self._record_failed_attempt(
                erasure,
                now,
                event="retention.erasure.steps_unreached",
                reason=f"Erasure ran but did not account for the declared steps {', '.join(unreached)}.",
                storage_cleanup_scopes=report.storage_cleanup_scopes,
                unreached=unreached,
            )
            return False

        # The request is addressed by its document key only. Its ``user_key``
        # is the tombstone hash by now (``_pseudonymize_audit_collections``
        # rewrote it inside the run) and ``_mark_erasure`` never writes that
        # field, so the plaintext key does not return with the status.
        self._mark_erasure(
            erasure,
            status="completed",
            completed_at=now,
            storage_cleanup_scopes=report.storage_cleanup_scopes,
        )
        return True

    def _record_failed_attempt(
        self,
        erasure: ErasureRequest,
        now: datetime,
        *,
        event: str,
        reason: str,
        storage_cleanup_scopes: list[str] | None = None,
        **log_fields: object,
    ) -> None:
        """Count a failed attempt, set its backoff, and log at the right level (#1666).

        Error level is reserved for the two moments an operator must act on:
        the **first** failure of a request and the attempt that reaches
        :attr:`ERASURE_ESCALATE_AFTER_ATTEMPTS`. Every failure in between is the
        same news again and logs at info — the open duty stays visible through
        the record and the run's ``open_failing`` gauge, not through a nightly
        error line the operator learns to ignore (NFR-018 §1).
        """
        attempt = erasure.attempt_count + 1
        delay_days = min(2 ** (attempt - 1), self.ERASURE_RETRY_MAX_DELAY_DAYS)
        # recurrence-owner-ok: a retry backoff after a failed erasure attempt, not
        # a cadence — it ends when the erasure succeeds, so there is no rule to advance.
        next_attempt_at = now + timedelta(days=delay_days)
        escalated = attempt == self.ERASURE_ESCALATE_AFTER_ATTEMPTS
        log = logger.error if attempt == 1 or escalated else logger.info
        log(
            event,
            erasure_key=erasure.key,
            user_key=erasure.user_key,
            attempt=attempt,
            escalated=escalated,
            next_attempt_at=next_attempt_at.isoformat(),
            **log_fields,
        )
        self._mark_erasure(
            erasure,
            status="partially_completed",
            error_message=f"{reason} Attempt {attempt}; the next one is due after {next_attempt_at.date()}.",
            storage_cleanup_scopes=storage_cleanup_scopes,
            attempt_count=attempt,
            next_attempt_at=next_attempt_at,
        )

    def _record_committed_erasure(self, erasure: ErasureRequest, now: datetime) -> bool:
        """Close a request whose ArangoDB plan already committed.

        The tombstone hash reaches ``erasure_requests.user_key`` only inside the
        erasure transaction, and that transaction also removes the user
        document; the object-storage phases run before it. A due request that
        carries the hash therefore belongs to a run whose final status write
        was lost (the worker died after the commit, or the write failed), and
        everything the plan declares has been done. Re-running
        :meth:`erase_account` with the hash as the user key would reach none of
        the subject's rows and rewrite the audit rows to a hash of the hash.
        """
        logger.info(
            "retention.erasure.already_committed",
            erasure_key=erasure.key,
            previous_status=erasure.status,
        )
        self._mark_erasure(erasure, status="completed", completed_at=now)
        return True

    async def erase_account(
        self,
        user_key: UserKey,
        *,
        pre_arango_completed: bool = False,
        recorded_storage_scopes: list[str] | None = None,
        on_pre_arango_complete: Callable[[list[str]], None] | None = None,
    ) -> AccountErasureReport:
        """Erase one account: every declared phase, then the ArangoDB plan (#1664).

        The single entry both account-deletion paths share: the platform-admin
        ``DELETE /admin/platform/users/{key}`` (#1664) and the scheduled
        self-service Art. 17 path, :meth:`_finalize_erasure` (#1645).

        Order, and why:

        1. **Refuse before touching anything** when the executor or the NFR-011
           §4 tombstone salt is missing — a half-run erasure is worse than none.
        2. **Export bundles** (object storage): the ``data_export_requests``
           documents are the only pointer to a stored Art. 15 bundle, and step 4
           removes them.
        3. **Phase 0 / 0.5 / pest images** (:meth:`_run_pre_arango_phases`):
           they resolve the user's tenants through the memberships step 4 removes.
        4. **The ArangoDB plan** via :class:`IErasureExecutor`, in one
           transaction: edges and documents removed, retained rows anonymised,
           audit rows pseudonymised, the user document last.

        Every phase is idempotent, so a crash anywhere is repaired by running
        this again; nothing a first run missed is skipped by the second.

        Args:
            pre_arango_completed: Steps 2 and 3 already finished for this
                subject on an earlier attempt of the same request (#1666); they
                are skipped and ``recorded_storage_scopes`` stands in for their
                result. Only the scheduled path sets this, from its own marker.
            recorded_storage_scopes: The scopes recorded when steps 2 and 3
                finished; reported unchanged when they are skipped.
            on_pre_arango_complete: Called with the applied scopes as soon as
                steps 2 and 3 finished, before the ArangoDB plan — the scheduled
                path records its marker here, so a failing plan does not make
                the next attempt repeat the storage work.

        Returns:
            Per-phase and per-step counts. Logged without the rows' content.

        Raises:
            FeatureNotConfiguredError: ``ERASURE_TOMBSTONE_SALT`` is missing or
                shorter than NFR-011 §4 requires (HTTP 503).
            ValueError: ``user_key`` is empty or blank (#1664) — raised before
                any phase runs.
        """
        if self._erasure_executor is None:  # pragma: no cover - guarded by wiring
            raise RuntimeError(
                "PrivacyService.erase_account requires an erasure_executor; "
                "construct the service with one (see app.common.dependencies)."
            )
        if not user_key or not user_key.strip():
            # #1664 — the plan's filters are ``doc[@field] == @user_key``; a blank
            # key matches every unattributed row and erases other users' data.
            msg = "erase_account needs a user key; refusing to erase with an empty one"
            raise ValueError(msg)
        try:
            tombstone = self._erasure_engine.compute_tombstone_hash(user_key, self._tombstone_salt)
        except ValueError as exc:
            raise FeatureNotConfiguredError(
                "account_erasure",
                "Set ERASURE_TOMBSTONE_SALT to a secret of at least 32 characters.",
            ) from exc
        plan = self._erasure_engine.build_erasure_plan(user_key)

        report = AccountErasureReport()
        if pre_arango_completed:
            logger.info("retention.erasure.pre_arango_phases_skipped", user_key=user_key)
            report.storage_cleanup_scopes = list(recorded_storage_scopes or [])
            pest_removed = 0
        else:
            report.export_files_removed = await self._run_export_file_cleanup(user_key)
            scopes, reference_removed, pest_removed = await self._run_pre_arango_phases(user_key)
            report.storage_cleanup_scopes = scopes
            report.reference_index_removed = reference_removed
            if on_pre_arango_complete is not None:
                on_pre_arango_complete(scopes)
        # The pest-image cleanup removes the rows of the step attributed to it;
        # the executor's own pass over that step is the safety net.
        for step in plan.steps:
            if step.executor == "pest_image_cleanup":
                report.delegated_removed[step.collection] = pest_removed
        report.arango = await asyncio.to_thread(self._erasure_executor.run_erasure_plan, plan, tombstone=tombstone)

        logger.info(
            "erasure.account_erased",
            user_key=user_key,
            export_files_removed=report.export_files_removed,
            storage_cleanup_scopes=report.storage_cleanup_scopes,
            reference_index_removed=report.reference_index_removed,
            delegated_removed=report.delegated_removed,
            arango_steps={step.collection: step.affected for step in report.arango.steps},
        )
        return report

    async def _run_export_file_cleanup(self, user_key: str) -> int:
        """Delete the stored Art. 15 bundles of *user_key* before their records go.

        ``data_export_requests.file_path`` is the only pointer to a bundle in
        object storage. The ArangoDB plan removes those documents, so a bundle
        not deleted here first would sit in storage for good — a complete
        disclosure of the erased user's data that nothing can find again
        (NFR-011 R-05 is precisely "delete the file"). A failed delete raises
        and stops the erasure before the pointer is lost; a re-run retries it.
        """
        if self._storage_adapter is None:
            logger.info(
                "retention.erasure.export_file_cleanup_skipped",
                user_key=user_key,
                reason="storage adapter not wired",
            )
            return 0
        removed = 0
        for export in self._export_repo.list_by_user(user_key):
            if export.file_path:
                await self._storage_adapter.delete_object(export.file_path)
                removed += 1
        return removed

    async def _run_pre_arango_phases(self, user_key: str) -> tuple[list[str], int, int]:
        """Phase 0, Phase 0.5 and the pest-image documents, with their counts.

        Returns ``(storage scopes applied, reference vectors removed, pest-image
        contributions removed)``.
        """
        scopes = await self._run_storage_cleanup(user_key)
        reference_removed = await self._run_reference_index_cleanup(user_key)
        pest_removed = self._run_pest_image_document_cleanup(user_key)
        return scopes, reference_removed, pest_removed

    def _run_pest_image_document_cleanup(self, user_key: str) -> int:
        """REQ-010 — drop the user's ``pest_image_contributions`` link documents.

        The attachment *bytes* are hard-deleted by the
        ``user_pest_reference_images`` storage-cleanup rule; this removes the
        accompanying link documents (no legal retention basis — a *promoted*
        contribution is deleted too). No-op when the repo is not wired.

        SEC-001: a *promoted* contribution also has a DINOv2 embedding in the
        recognition index. Its provenance label is resolved from the
        contribution's pest, so the retract must run **before** the link
        documents are dropped (afterwards ``pest_key`` is gone). Best-effort —
        an inference-service error never aborts the erasure.
        """
        if self._pest_image_repo is None:
            return 0
        contributions = self._pest_image_repo.list_for_user(user_key)
        self._retract_promoted_pest_image_embeddings(contributions, erasure_scope="user")
        removed = 0
        for c in contributions:
            if c.key is not None and self._pest_image_repo.delete(c.key, c.tenant_key):
                removed += 1
        logger.info(
            "retention.erasure.pest_image_documents_cleanup",
            user_key=user_key,
            removed=removed,
        )
        return removed

    def _retract_promoted_pest_image_embeddings(self, contributions, erasure_scope: str) -> None:  # type: ignore[no-untyped-def]
        """SEC-001 — retract promoted contributions' recognition-index embeddings.

        No-op when the inference client or IPM repo are not wired (the retract
        cannot resolve a label without the pest record). Best-effort.
        """
        if self._pest_inference_client is None or self._ipm_repo is None:
            return
        from app.domain.services.pest_image_recognition_cleanup import (
            retract_promoted_contributions,
        )

        retract_promoted_contributions(
            list(contributions),
            inference_client=self._pest_inference_client,
            ipm_repo=self._ipm_repo,
            erasure_scope=erasure_scope,
        )

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

        tenant_keys = self._erasure_tenant_keys(user_key)
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
                    # Strip first: both halves select the photos by
                    # ``created_by == user_key``, and the anonymisation rewrites
                    # exactly that field. Run the other way round, the strip
                    # finds nothing and every photo keeps its GPS EXIF (#1645).
                    # A crash between the two leaves ``created_by`` intact, so
                    # a re-run repeats both.
                    stripped = await self._storage_adapter.strip_exif_for_user(
                        tenant_key=tenant_key,
                        user_key=user_key,
                        scope=rule.scope,
                    )
                    anonymised = await self._anonymize_attachment_metadata(
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

    def _erasure_tenant_keys(self, user_key: str) -> list[str]:
        """The tenants whose object storage may hold the user's files.

        The user's member tenants, plus every tenant holding one of their pest
        reference contributions (#1664). A contribution outlives its author's
        membership: a user who left a tenant still owns the pest images they
        uploaded there, and the ``user_pest_reference_images`` rule, walking
        member tenants only, never reached those bytes — while the pest-image
        cleanup removed the link documents that pointed at them.

        Deliberately **not** :meth:`_user_tenant_keys`: the Art. 15 export is
        restricted to member tenants (#1662 SCR-001), erasure must reach
        further.
        """
        keys = self._user_tenant_keys(user_key)
        if self._pest_image_repo is not None:
            for contribution in self._pest_image_repo.list_for_user(user_key):
                if contribution.tenant_key and contribution.tenant_key not in keys:
                    keys.append(contribution.tenant_key)
        return keys

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
        attempt_count: int | None = None,
        last_attempt_at: datetime | None = None,
        next_attempt_at: datetime | None = None,
        pre_arango_completed_at: datetime | None = None,
    ) -> None:
        """Persist an erasure-status transition as a named-field write.

        #1662 SCR-003 — this was a full-model ``update``, and the repository
        merges: a field set to ``None`` never reached the payload. Combined with
        ``if error_message is not None`` the reason could never be cleared, so
        the first record to reach ``completed`` would have kept saying
        "ArangoDB erasure did not run" — the #1645 untruth with the sign
        flipped. The transition to ``completed`` now names ``error_message:
        None`` explicitly, and ``update_fields`` (``keep_none=True``) lands it.
        """
        if erasure.key is None:
            return
        fields: dict[str, object] = {"status": status}
        if completed_at is not None:
            fields["completed_at"] = completed_at
        if error_message is not None:
            fields["error_message"] = error_message
        if storage_cleanup_scopes is not None:
            fields["storage_cleanup_scopes"] = storage_cleanup_scopes
        retry_fields = {
            "attempt_count": attempt_count,
            "last_attempt_at": last_attempt_at,
            "next_attempt_at": next_attempt_at,
            "pre_arango_completed_at": pre_arango_completed_at,
        }
        fields.update({name: value for name, value in retry_fields.items() if value is not None})
        if status == "completed":
            fields["error_message"] = None
            fields["next_attempt_at"] = None
        for field, value in fields.items():
            setattr(erasure, field, value)
        self._erasure_repo.update_fields(erasure.key, _persistable(fields))

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
        """Expire exports past their 72-hour window **and delete their files**.

        NFR-011 R-05 is "delete the file, set the status to expired" — both
        halves. Flipping the status alone would leave a full Art. 15 disclosure
        of a user's personal data sitting in object storage for ever, which is
        the storage-limitation breach the rule exists to prevent.
        """
        expired = self._export_repo.expire_old(now.isoformat())
        for export in expired:
            if not export.file_path:
                continue
            try:
                if self._storage_adapter is not None:
                    await self._storage_adapter.delete_object(export.file_path)
            except Exception as exc:  # noqa: BLE001 — one bad object must not stall the rest
                logger.error(
                    "retention.expire_data_exports.object_delete_failed",
                    export_key=export.key,
                    object_key=export.file_path,
                    error=str(exc),
                )
                continue
            # ``update_fields`` (``keep_none=True``), not ``update``: this
            # repository merges, so a ``None`` on a full model never reaches the
            # payload and the record would keep pointing at an object that has
            # just been deleted.
            if export.key:
                self._export_repo.update_fields(
                    export.key,
                    {"file_path": None, "file_size_bytes": None},
                )
            export.file_path = None
            export.file_size_bytes = None
        if expired:
            logger.info(
                "retention.expire_data_exports.completed",
                expired=len(expired),
            )
        return len(expired)
