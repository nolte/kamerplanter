"""Creating, repointing and deleting OIDC provider configurations — behind the step-up (#1883).

The configurations are installation-wide identity federation. A provider under an
attacker's control can assert ``email=<victim>`` with ``email_verified=true``, and the
OAuth auto-link (``OAuthEngine.should_auto_link``) links that sign-in to the victim's
verified account; a second generic provider that claims the victim's ``sub`` signs in
as the victim (#1869). Until #1883 the routes wrote the repository directly behind
``require_platform_admin`` alone, which a hijacked admin session — or an admin's leaked
``kp_`` API key — passes. Every change that can steer a sign-in now passes the admin's
own step-up (:class:`~app.domain.services.step_up_service.StepUpVerifier`, act
``oidc_provider_change``, bound to the configuration — #1884), the same class as a
credential change (operator decision D5): the password, a fresh re-authentication or
the mailed code; an API-key request is 403, 429 when locked.

**What needs no step-up (operator decision D6).** An allow-list, so a field added later
defaults to needing one: ``display_name``, ``icon_url`` and switching a provider *off*
(``enabled`` true → false) change nothing about who a sign-in resolves to. Everything
else — issuer and endpoints, client id and secret, provider type, scopes, discovery,
the default tenant new federated accounts join, switching a provider *on* — and every
creation and deletion needs it. A field sent with the value it already has is no change.

**Known edge (D5).** An admin whose only sign-in is a link to the very provider being
repaired, while that provider cannot sign anyone in, can neither re-authenticate there
nor receive the mailed code (an account with a re-authenticating link is refused the
code). A local password, or the operator, is the way out.
"""

from __future__ import annotations

from typing import Any

import structlog

from app.common.exceptions import DuplicateError, NotFoundError
from app.common.log_privacy import log_subject
from app.domain.engines.encryption_engine import EncryptionEngine
from app.domain.engines.oauth_engine import OAuthEngine
from app.domain.interfaces.oidc_config_repository import IOidcConfigRepository
from app.domain.models.oidc_config import OidcProviderConfig
from app.domain.models.user import User
from app.domain.services.step_up_service import StepUpVerifier
from app.domain.services.step_up_targets import oidc_provider_target

logger = structlog.get_logger()

#: Fields whose change never needs the step-up: they change how a provider is shown,
#: not whom a sign-in resolves to. ``enabled`` is judged separately — off is free, on is not.
_PRESENTATION_FIELDS = frozenset({"display_name", "icon_url"})

#: Written encrypted; its stored value cannot be compared with the one sent, so sending it is a change.
_SECRET_FIELD = "client_secret"


def update_requires_step_up(current: OidcProviderConfig, data: dict[str, Any]) -> bool:
    """Whether applying *data* to *current* changes anything a sign-in depends on (D6)."""
    for field, value in data.items():
        if field == _SECRET_FIELD:
            return True
        if getattr(current, field) == value:
            continue
        if field in _PRESENTATION_FIELDS:
            continue
        if field == "enabled" and value is False:
            continue
        return True
    return False


class OidcProviderAdminService:
    """The write side of ``/admin/oidc-providers`` (#1883)."""

    def __init__(
        self,
        oidc_config_repo: IOidcConfigRepository,
        encryption_engine: EncryptionEngine,
        oauth_engine: OAuthEngine,
        step_up_verifier: StepUpVerifier,
    ) -> None:
        self._oidc_config_repo = oidc_config_repo
        self._encryption = encryption_engine
        self._oauth = oauth_engine
        self._step_up_verifier = step_up_verifier

    def create_provider(
        self,
        data: dict[str, Any],
        *,
        requester: User,
        current_password: str | None,
        step_up_code: str | None,
        step_up_token: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> OidcProviderConfig:
        """Store a new configuration after the step-up (target ``new:<slug>``).

        The checks that read no secret run first — a taken slug (409), scopes a
        GitHub provider cannot sign in with (422, #1477) — so a request refused
        anyway spends no mailed code and no attempt.
        """
        fields = dict(data)
        if self._oidc_config_repo.get_by_slug(fields["slug"]) is not None:
            raise DuplicateError("OidcProviderConfig", "slug", fields["slug"])
        client_secret = fields.pop(_SECRET_FIELD)
        config = OidcProviderConfig(**fields, client_secret_encrypted=self._encryption.encrypt(client_secret))
        self._oauth.require_supported_scopes(config)
        self._verify(
            requester,
            target=oidc_provider_target(None, slug=config.slug),
            current_password=current_password,
            step_up_code=step_up_code,
            step_up_token=step_up_token,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )
        created = self._oidc_config_repo.create(config)
        logger.info("oidc_provider.created", provider=created.slug, requested_by=log_subject(requester.key))
        return created

    def update_provider(
        self,
        key: str,
        data: dict[str, Any],
        *,
        requester: User,
        current_password: str | None,
        step_up_code: str | None,
        step_up_token: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> OidcProviderConfig:
        """Apply a partial update; the step-up when it touches more than presentation (D6).

        The scope check (#1477) runs on the MERGED result, before the step-up: a
        request may switch ``provider_type`` to ``github`` without touching
        ``scopes``, and only the state that would be stored answers whether sign-in
        can read the address list.
        """
        config = self._oidc_config_repo.get_by_key(key)
        if config is None:
            raise NotFoundError("OidcProviderConfig", key)
        needs_step_up = update_requires_step_up(config, data)
        changes = {
            ("client_secret_encrypted" if field == _SECRET_FIELD else field): (
                self._encryption.encrypt(value) if field == _SECRET_FIELD else value
            )
            for field, value in data.items()
        }
        # The merged state, validated as a whole: what the scope check (#1477)
        # judges and what the written fields are taken from.
        merged = OidcProviderConfig.model_validate({**config.model_dump(by_alias=True), **changes})
        self._oauth.require_supported_scopes(merged)
        if needs_step_up:
            self._verify(
                requester,
                target=oidc_provider_target(key),
                current_password=current_password,
                step_up_code=step_up_code,
                step_up_token=step_up_token,
                authenticated_with_api_key=authenticated_with_api_key,
                client_ip=client_ip,
            )
        # Only the changed fields (security review SEC-003): a full write of the
        # snapshot read above would revert whatever another admin changed while
        # this request was being confirmed.
        updated = self._oidc_config_repo.update_fields(key, merged.model_dump(mode="json", include=set(changes)))
        logger.info(
            "oidc_provider.updated",
            provider=updated.slug,
            fields=sorted(data),
            step_up=needs_step_up,
            requested_by=log_subject(requester.key),
        )
        return updated

    def delete_provider(
        self,
        key: str,
        *,
        requester: User,
        current_password: str | None,
        step_up_code: str | None,
        step_up_token: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> None:
        """Delete a configuration after the step-up — the accounts linked to it lose that sign-in."""
        config = self._oidc_config_repo.get_by_key(key)
        if config is None:
            raise NotFoundError("OidcProviderConfig", key)
        self._verify(
            requester,
            target=oidc_provider_target(key),
            current_password=current_password,
            step_up_code=step_up_code,
            step_up_token=step_up_token,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )
        self._oidc_config_repo.delete(key)
        logger.info("oidc_provider.deleted", provider=config.slug, requested_by=log_subject(requester.key))

    def _verify(
        self,
        requester: User,
        *,
        target: str,
        current_password: str | None,
        step_up_code: str | None,
        step_up_token: str | None,
        authenticated_with_api_key: bool,
        client_ip: str | None,
    ) -> None:
        self._step_up_verifier.verify(
            requester,
            action="oidc_provider_change",
            target=target,
            echo_ok=None,
            password=current_password,
            code=step_up_code,
            reauth_token=step_up_token,
            authenticated_with_api_key=authenticated_with_api_key,
            client_ip=client_ip,
        )
