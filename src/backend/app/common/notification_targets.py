"""Shape rules for the Home Assistant destinations a user may put in a preference.

``channels.home_assistant.config`` is user-editable and has no schema. Three of its
keys name *what the operator's Home Assistant is asked to call*:

* ``notify_service`` — a service of the ``notify`` domain (``notify.<slug>``; the
  bare ``<slug>`` is accepted too and means the same),
* ``tts_entity_id`` — a ``tts`` or ``media_player`` entity (``<domain>.<object_id>``),
* ``tts_service`` — a service slug of the ``tts`` domain.

The Home Assistant connection itself is platform-wide (``HA_URL`` / ``HA_TOKEN`` in
the operator's settings, one client for every tenant), so these values are the only
thing a user steers. A value outside the shape is refused on save (422, value-free)
and dropped again at send time. The shape closes URL-path injection into
``/api/services/{domain}/{service}`` and calls to any domain other than
``notify`` / ``tts``; it does not decide *which* ``notify.*`` service of the
operator's instance a user may address (REQ-030 §3.2).
"""

from __future__ import annotations

import re

import structlog

from app.common.exceptions import ValidationError

logger = structlog.get_logger(__name__)

#: ASCII slug: lowercase letters, digits, underscore. ``re.ASCII`` + ``fullmatch`` —
#: no ``$`` newline slack, no Unicode digits or letters.
_SLUG = r"[a-z0-9_]{1,64}"
_NOTIFY_SERVICE = re.compile(rf"(?:notify\.)?({_SLUG})", re.ASCII)
_SERVICE_SLUG = re.compile(_SLUG, re.ASCII)
_TTS_ENTITY = re.compile(rf"(?:tts|media_player)\.{_SLUG}", re.ASCII)

HA_DEFAULT_NOTIFY_SERVICE = "notify"
HA_DEFAULT_TTS_SERVICE = "speak"
HA_DESTINATION_KEYS = ("notify_service", "tts_entity_id", "tts_service")


def ha_notify_service_slug(value: object) -> str | None:
    """The ``notify`` service slug ``value`` names, or ``None`` if it is not allowed."""
    if not isinstance(value, str):
        return None
    match = _NOTIFY_SERVICE.fullmatch(value)
    return match.group(1) if match else None


def ha_tts_service_slug(value: object) -> str | None:
    """The ``tts`` service slug ``value`` names, or ``None`` if it is not allowed."""
    return value if isinstance(value, str) and _SERVICE_SLUG.fullmatch(value) else None


def ha_tts_entity_id(value: object) -> str | None:
    """``value`` when it is an allowed ``tts.*`` / ``media_player.*`` entity id, else ``None``."""
    return value if isinstance(value, str) and _TTS_ENTITY.fullmatch(value) else None


_CHECKS = {
    "notify_service": ha_notify_service_slug,
    "tts_entity_id": ha_tts_entity_id,
    "tts_service": ha_tts_service_slug,
}
_REASONS = {
    "notify_service": "Must be a Home Assistant notify service such as notify.mobile_app_<device>.",
    "tts_entity_id": "Must be a tts.* or media_player.* entity id.",
    "tts_service": "Must be a lowercase service name of the tts domain.",
}


def validate_ha_channel_config(config: object) -> None:
    """Refuse a Home Assistant channel config whose destination keys leave their shape.

    An absent key, ``None`` and the empty string (the settings UI sends ``""`` for
    a cleared field) mean "unset" and are accepted; a stored ``""`` is never sent.

    Raises:
        ValidationError: a value-free message naming the offending key.
    """
    if not isinstance(config, dict):
        return
    for key in HA_DESTINATION_KEYS:
        value = config.get(key)
        if value is None or value == "":
            continue
        if _CHECKS[key](value) is None:
            logger.warning("ha_destination_rejected", key=key)
            raise ValidationError(
                "A Home Assistant destination is not allowed.",
                details=[
                    {
                        "field": f"channels.home_assistant.config.{key}",
                        "reason": _REASONS[key],
                        "code": "HA_DESTINATION_NOT_ALLOWED",
                    }
                ],
            )
