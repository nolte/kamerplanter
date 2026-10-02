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

**What needs no step-up (operator decision D6, corrected after security review SEC-001).**
An allow-list, so a field added later defaults to needing one: only ``display_name`` and
``icon_url``, which change how a provider is shown, not whom a sign-in resolves to.
Everything else — issuer and endpoints, client id and secret, provider type, scopes,
discovery, the default tenant new federated accounts join, and switching a provider on
*or off* — and every creation and deletion needs it. Switching off was free in the first
draft; but ``FederatedReauthPolicy`` reads only enabled configurations, so disabling a
provider moves every account whose only re-authenticating link it was from the fresh
sign-in to the mailed code — a step-up downgrade reachable without a step-up (and with
a leaked admin key). A field sent with the value it already has is no change.

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
from app.domain.interfaces.auth_provider_repository import IAuthProviderRepository
from app.domain.interfaces.oidc_config_repository import IOidcConfigRepository
from app.domain.models.oidc_config import OidcProviderConfig
from app.domain.models.user import User
from app.domain.services.step_up_service import StepUpVerifier
from app.domain.services.step_up_targets import oidc_provider_target

logger = structlog.get_logger()

#: Fields whose change never needs the step-up: they change how a provider is shown,
#: not whom a sign-in resolves to. Not ``enabled`` — in either direction (SEC-001).
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
        return True
    return False


#: The fields whose change makes the stored discovery document belong to another issuer.
_DISCOVERY_BOUND_FIELDS = frozenset({"issuer_url", "provider_type"})


def _repoints_discovery(current: OidcProviderConfig, changes: dict[str, Any]) -> bool:
    """Whether *changes* move the provider to another issuer or type (#1969)."""
    return any(field in changes and changes[field] != getattr(current, field) for field in _DISCOVERY_BOUND_FIELDS)


#: The explicitly configured endpoints; each one belongs to the issuer it was typed for.
_EXPLICIT_ENDPOINT_FIELDS = ("authorization_url", "token_url", "userinfo_url", "jwks_url")


def _endpoints_of_the_old_issuer(current: OidcProviderConfig, data: dict[str, Any]) -> list[str]:
    """The explicit endpoints a repoint of the issuer leaves behind: set, and not replaced by this request (#1987).

    "Repoint" is a change of the issuer a token's ``iss`` is checked against — compared the way
    the login compares it, so adding a trailing ``/`` or dropping a scheme-less spelling is not
    one. A field the request sends is the operator's answer for the new issuer and stays (it was
    validated as https at the boundary); a field it does not send is cleared.
    """
    new_issuer = data.get("issuer_url")
    if new_issuer is None or OAuthEngine.same_issuer(current.issuer_url, new_issuer):
        return []
    return [name for name in _EXPLICIT_ENDPOINT_FIELDS if getattr(current, name) and name not in data]


class OidcProviderAdminService:
    """The write side of ``/admin/oidc-providers`` (#1883)."""

    def __init__(
        self,
        oidc_config_repo: IOidcConfigRepository,
        encryption_engine: EncryptionEngine,
        oauth_engine: OAuthEngine,
        step_up_verifier: StepUpVerifier,
        auth_provider_repo: IAuthProviderRepository,
    ) -> None:
        self._auth_provider_repo = auth_provider_repo
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
        # A new configuration starts with no links (#1935). Links are matched by
        # (slug, sub); any still bound to this slug were left by a configuration
        # deleted before deletion removed them, and would be inherited — possibly
        # by a different IdP. Nothing legitimate can be bound to a slug that has no
        # configuration, so this removes only orphans.
        #
        # **Created first, switched off; purged; then switched on (#1987).** The
        # ``get_by_slug`` check above is not atomic: two creations of one slug can both
        # pass it, and with the purge first the loser deleted the winner's links before
        # its own ``create`` failed on the unique index. The ``create`` is the one
        # operation the index serialises, so it goes first — the loser fails there and
        # touches no link — and it is created disabled, so nobody can sign in at the
        # slug while its orphans still exist. A failed purge takes the new row with it.
        wanted_enabled = config.enabled
        created = self._oidc_config_repo.create(config.model_copy(update={"enabled": False}))
        try:
            purged = self._auth_provider_repo.delete_by_config_slug(created.slug)
            if wanted_enabled:
                created = self._oidc_config_repo.update_fields(created.key or "", {"enabled": True})
        except Exception:
            if created.key:
                self._oidc_config_repo.delete(created.key)
            raise
        logger.info(
            "oidc_provider.created",
            provider=created.slug,
            orphan_links_deleted=purged,
            requested_by=log_subject(requester.key),
        )
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
        # Only what actually changes is written (/code-review of #1910): a value sent
        # equal to the one read needs no step-up, so writing it would let a free
        # request put back a value a step-up'd change replaced in between.
        changes = {
            ("client_secret_encrypted" if field == _SECRET_FIELD else field): (
                self._encryption.encrypt(value) if field == _SECRET_FIELD else value
            )
            for field, value in data.items()
            if field == _SECRET_FIELD or getattr(config, field) != value
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
        stale_endpoints = _endpoints_of_the_old_issuer(config, data)
        if stale_endpoints:
            # Explicit endpoints are the OLD provider's: sign-in prefers them to anything
            # discovered, so left in place a repointed provider would still send the code and
            # the client secret to the issuer it was moved away from — or fetch its keys from
            # there (#1987). Cleared in the same write as the repoint; the request may name
            # new ones, which it did if they appear in ``data``.
            changes = {**changes, **dict.fromkeys(stale_endpoints)}
            merged = merged.model_copy(update=dict.fromkeys(stale_endpoints))
        if changes and _repoints_discovery(config, changes):
            # The stored discovery document is the OLD issuer's (or provider type's):
            # sign-in prefers its endpoints to the configured ones. Cleared in the
            # same write as the change, so no sign-in can see the new issuer with
            # the old document (#1969). The next refresh (or ``POST /{key}/test``)
            # fetches the new one.
            changes = {**changes, "discovery_document": None, "discovery_refreshed_at": None}
            merged = merged.model_copy(update={"discovery_document": None, "discovery_refreshed_at": None})
        updated = (
            self._oidc_config_repo.update_fields(key, merged.model_dump(mode="json", include=set(changes)))
            if changes
            else config
        )
        if "issuer_url" in changes and changes["issuer_url"] != config.issuer_url:
            # A link that recorded no issuer matches any issuer, and the first
            # sign-in from the new IdP would claim it (security review SEC-001, the
            # #1935 class on the update path). After the write, so a failed update
            # takes no link with it. Links with an issuer refuse the new IdP on
            # their own and stay.
            self._auth_provider_repo.delete_by_config_slug(config.slug, only_without_issuer=True)
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
        # The configuration first, then its links, and creation sweeps again (#1935):
        # a failure between the two leaves orphans that the next creation under the
        # slug removes, whereas links first would let a sign-in in that window write
        # a fresh one against a configuration about to go.
        self._oidc_config_repo.delete(key)
        # Deleted, not unbound. A link is useless without its configuration — nobody
        # can sign in through it, and a re-created slug must not match it — and no
        # "unbound" state exists that is safe: a link with no slug is the legacy,
        # ambiguous kind (never matched, but it collides on the (type, slug, sub)
        # unique key when two deleted configurations held the same ``sub``), and a
        # tombstone slug would be an unreviewed vocabulary. Deleting also drops the
        # link's encrypted provider tokens. The accounts keep every other way in.
        links_deleted = self._auth_provider_repo.delete_by_config_slug(config.slug)
        logger.info(
            "oidc_provider.deleted",
            provider=config.slug,
            links_deleted=links_deleted,
            requested_by=log_subject(requester.key),
        )

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
