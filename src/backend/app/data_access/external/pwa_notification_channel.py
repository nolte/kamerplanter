"""Web Push (PWA / browser) notification channel adapter.

Delivers notifications to browser / PWA clients via the Web Push protocol
using VAPID authentication. The ``pywebpush`` library (which bundles
py-vapid and http-ece for payload encryption) performs the encrypted POST
to each subscription's push endpoint.

Channel config expects:
  {
    "subscriptions": [
      {"endpoint": "https://...", "p256dh": "<base64url>", "auth": "<base64url>"},
      ...
    ]
  }

Each subscription corresponds to one browser/device registered via the
PushManager. Endpoints that the push service reports as gone (HTTP 404/410)
are collected in the result so callers can prune them from storage.

``pywebpush`` is imported lazily to keep it an optional runtime dependency
and to allow the channel to be mocked in tests.
"""

from __future__ import annotations

import asyncio
import json
from functools import partial

import structlog

from app.common.url_safety import is_safe_push_endpoint
from app.domain.interfaces.notification_channel import INotificationChannel
from app.domain.models.notification import ChannelResult, Notification

logger = structlog.get_logger(__name__)

# HTTP status codes the push service returns for a subscription that no
# longer exists and must be removed by the application.
_EXPIRED_STATUS_CODES: frozenset[int] = frozenset({404, 410})


class PwaNotificationChannel(INotificationChannel):
    """Delivers notifications to browser / PWA clients via Web Push (VAPID)."""

    def __init__(self, vapid_private_key: str, vapid_contact_email: str) -> None:
        """Initialise the channel.

        Args:
            vapid_private_key: VAPID private key (PEM or base64url) used to
                sign the push requests.
            vapid_contact_email: Contact email embedded in the VAPID ``sub``
                claim (``mailto:`` URI), required by push services.
        """
        self._vapid_private_key = vapid_private_key
        self._vapid_contact_email = vapid_contact_email

    @property
    def channel_key(self) -> str:
        return "pwa"

    @property
    def supports_actions(self) -> bool:
        return True

    @property
    def supports_batching(self) -> bool:
        return True

    async def send(
        self,
        notification: Notification,
        channel_config: dict,
    ) -> ChannelResult:
        """Push a notification to every registered subscription.

        Expired subscriptions (HTTP 404/410) are collected and reported in
        the result's ``error`` field as ``expired:<endpoint>;...`` so callers
        can prune them. A single ``WebPushException`` never aborts the batch;
        delivery is attempted for every subscription.

        Args:
            notification: The notification to deliver.
            channel_config: Per-channel config containing ``subscriptions``.

        Returns:
            A ChannelResult whose ``success`` is True if at least one
            subscription was delivered.
        """
        subscriptions = channel_config.get("subscriptions", [])
        if not subscriptions:
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error="No Web Push subscriptions configured in channel_config",
            )

        if not self._vapid_private_key:
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error="VAPID private key is not configured",
            )

        try:
            webpush, web_push_exception = _import_pywebpush()
        except ImportError:
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error="pywebpush package is not installed",
            )

        payload = self._build_payload(notification)
        vapid_claims = {"sub": f"mailto:{self._vapid_contact_email}"}

        delivered = 0
        errors: list[str] = []
        expired_endpoints: list[str] = []

        loop = asyncio.get_running_loop()
        for subscription in subscriptions:
            endpoint = subscription.get("endpoint", "")
            # SEC-001 — defence in depth: stored subscriptions may predate the
            # subscribe-time SSRF validation. Never dial an unsafe endpoint.
            if not is_safe_push_endpoint(endpoint):
                errors.append(f"{endpoint}: rejected (unsafe endpoint)")
                logger.warning("pwa_endpoint_skipped_unsafe", endpoint=endpoint)
                continue
            subscription_info = {
                "endpoint": endpoint,
                "keys": {
                    "p256dh": subscription.get("p256dh", ""),
                    "auth": subscription.get("auth", ""),
                },
            }
            try:
                await loop.run_in_executor(
                    None,
                    partial(
                        webpush,
                        subscription_info=subscription_info,
                        data=payload,
                        vapid_private_key=self._vapid_private_key,
                        vapid_claims=dict(vapid_claims),
                    ),
                )
                delivered += 1
                logger.debug(
                    "pwa_notification_sent",
                    notification_key=notification.key,
                    endpoint=endpoint,
                )
            except web_push_exception as exc:
                status_code = _extract_status_code(exc)
                if status_code in _EXPIRED_STATUS_CODES:
                    expired_endpoints.append(endpoint)
                    logger.info(
                        "pwa_subscription_expired",
                        endpoint=endpoint,
                        status_code=status_code,
                    )
                else:
                    errors.append(f"{endpoint}: {exc}")
                    logger.warning(
                        "pwa_notification_failed",
                        endpoint=endpoint,
                        status_code=status_code,
                        error=str(exc),
                    )
            except Exception as exc:  # noqa: BLE001 — never abort the batch
                errors.append(f"{endpoint}: {exc}")
                logger.error(
                    "pwa_notification_error",
                    endpoint=endpoint,
                    error=str(exc),
                    exc_info=True,
                )

        return self._build_result(delivered, errors, expired_endpoints)

    async def health_check(self) -> bool:
        """Return True only if a VAPID private key is configured."""
        return bool(self._vapid_private_key)

    # ── Internal helpers ─────────────────────────────────────────────

    @staticmethod
    def _build_payload(notification: Notification) -> str:
        """Serialise a notification into the JSON push payload."""
        payload = {
            "title": notification.title,
            "body": notification.body,
            "data": notification.data,
            "actions": [{"action_id": a.action_id, "title": a.title, "uri": a.uri} for a in notification.actions],
            "tag": notification.group_key,
            "urgency": notification.urgency.value,
        }
        if notification.image_url:
            payload["image_url"] = notification.image_url
        return json.dumps(payload)

    def _build_result(
        self,
        delivered: int,
        errors: list[str],
        expired_endpoints: list[str],
    ) -> ChannelResult:
        """Assemble the ChannelResult, encoding expired endpoints for callers."""
        success = delivered > 0
        detail_parts: list[str] = []
        if expired_endpoints:
            detail_parts.append("expired:" + ",".join(expired_endpoints))
        if errors:
            detail_parts.append("; ".join(errors))
        error = " | ".join(detail_parts) if detail_parts else None
        return ChannelResult(
            channel_key=self.channel_key,
            success=success,
            error=error,
        )


# ── Module-level helpers ─────────────────────────────────────────────


def _import_pywebpush():  # noqa: ANN202 — third-party objects are untyped
    """Lazy import of pywebpush to keep it an optional dependency.

    Returns:
        A tuple ``(webpush, WebPushException)``.
    """
    from pywebpush import WebPushException, webpush  # noqa: PLC0415

    return webpush, WebPushException


def _extract_status_code(exc: Exception) -> int | None:
    """Extract the HTTP status code from a WebPushException, if present."""
    response = getattr(exc, "response", None)
    return getattr(response, "status_code", None)
