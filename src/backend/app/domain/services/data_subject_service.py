"""Data-subject-rights facade (REQ-025 GDPR Art. 15-21).

This is a thin coordinator that surfaces the GDPR data-subject rights as a
self-documenting API for the rest of the system. It delegates all real work
to ``PrivacyService`` so we have a single source of truth.

Why a separate class? It provides a discoverable, article-aware entry point
for callers that want to express intent in GDPR terms (``access``,
``rectify``, ``erase``, etc.) without having to know the privacy-service
method naming. It also keeps room for future auditing/policy hooks that
should fire on every right invocation without polluting the lower-level
service.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from app.common.types import UserKey
from app.domain.models.privacy import (
    DataExportRequest,
    EmailChangeRequest,
    ErasureRequest,
    ProcessingRestriction,
    RestrictionReason,
)
from app.domain.services.step_up_service import StepUpConfirmation

if TYPE_CHECKING:
    from app.domain.services.privacy_service import PrivacyService

logger = structlog.get_logger()


class DataSubjectService:
    """GDPR Art. 15-21 facade over ``PrivacyService``."""

    def __init__(self, privacy_service: PrivacyService) -> None:
        self._privacy = privacy_service

    # ── Art. 15: right of access ──────────────────────────────────

    def access(self, user_key: UserKey) -> DataExportRequest:
        """Art. 15: trigger a machine-readable copy of all personal data."""
        logger.info("data_subject_right_invoked", article="15", subject=self._privacy.log_subject(user_key))
        return self._privacy.request_data_export(user_key)

    # ── Art. 16: right to rectification ───────────────────────────

    def rectify_email(
        self,
        user_key: UserKey,
        new_email: str,
        *,
        password: str | None,
        step_up_code: str | None,
        step_up_token: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> EmailChangeRequest:
        """Art. 16: initiate an email-change with token verification, behind the step-up (#1841)."""
        logger.info("data_subject_right_invoked", article="16", subject=self._privacy.log_subject(user_key))
        return self._privacy.request_email_change(
            user_key,
            new_email,
            password=password,
            step_up_code=step_up_code,
            step_up_token=step_up_token,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )

    # ── Art. 17: right to erasure ─────────────────────────────────

    def erase(
        self,
        user_key: UserKey,
        *,
        confirmation: StepUpConfirmation,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> ErasureRequest:
        """Art. 17: request account erasure (soft + scheduled hard delete), behind the step-up (#1813)."""
        logger.info("data_subject_right_invoked", article="17", subject=self._privacy.log_subject(user_key))
        return self._privacy.request_erasure(
            user_key,
            confirmation=confirmation,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )

    # ── Art. 18: right to restriction ─────────────────────────────

    def restrict(
        self,
        user_key: UserKey,
        scope: str,
        reason: RestrictionReason,
        notes: str | None = None,
    ) -> ProcessingRestriction:
        """Art. 18: restrict processing for a specific scope."""
        logger.info("data_subject_right_invoked", article="18", subject=self._privacy.log_subject(user_key))
        return self._privacy.restrict_processing(user_key, scope, reason, notes)

    # ── Art. 20: right to portability ─────────────────────────────

    def portability(self, user_key: UserKey) -> DataExportRequest:
        """Art. 20: identical to Art. 15 (export covers both rights)."""
        logger.info("data_subject_right_invoked", article="20", subject=self._privacy.log_subject(user_key))
        return self._privacy.request_data_export(user_key)

    # ── Art. 21: right to object ──────────────────────────────────

    def object_to(
        self,
        user_key: UserKey,
        purpose: str,
        reason: str,
    ) -> ProcessingRestriction:
        """Art. 21: file an objection against legitimate-interest processing."""
        logger.info("data_subject_right_invoked", article="21", subject=self._privacy.log_subject(user_key))
        return self._privacy.object_to_processing(user_key, purpose, reason)
