"""#1827 class guard — every sender of a notification channel prunes what the push service reports gone.

Until #1827 the Web-Push channel reported expired subscriptions (HTTP 404/410)
and nothing removed them: every notification dialled the dead endpoints again.
The pruning lives in ``NotificationEngine.prune_expired_subscriptions``; a new
place that sends through a channel and forgets to call it would bring the
defect back for its path. So the rule is about the *senders*:

**The rule.** In ``app/`` outside the channel implementations themselves
(``data_access/external/*_channel.py`` and the ``INotificationChannel`` default
``send_batch``), every function that awaits ``<x>.send(...)`` or
``<x>.send_batch(...)`` also calls ``prune_expired_subscriptions`` — or is
listed in :data:`_EXEMPT` with the reason its channel can report no expired
endpoint.

Spellings this does NOT see
---------------------------

* a send whose result is handed to another function that prunes (the engine's
  ``_send_to_channel`` prunes itself, so its callers are not listed);
* a channel reached through ``getattr`` or a call not written as ``.send(``;
* ``await`` on a variable holding the coroutine (``c = ch.send(n); await c``).
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests.support.execution_guards import find_project_root

_APP = find_project_root(Path(__file__)) / "app"
_SEND_METHODS = {"send", "send_batch"}
_PRUNE = "prune_expired_subscriptions"
#: The channels themselves: they produce results, they do not own stored subscriptions.
_CHANNEL_MODULES = ("data_access/external/", "domain/interfaces/notification_channel.py")
_EXEMPT: dict[tuple[str, str], str] = {
    ("domain/services/notification_service.py", "send_email_digest"): (
        "sends through the e-mail channel only (registry key 'email'), which has no push subscriptions"
    ),
}


def scan_source(source: str, rel: str) -> tuple[list[tuple[str, str]], set[tuple[str, str]]]:
    """``(senders without a prune, every sender)`` as ``(rel, function)`` pairs."""
    missing: list[tuple[str, str]] = []
    senders: set[tuple[str, str]] = set()
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        sends = prunes = False
        for inner in ast.walk(node):
            if isinstance(inner, ast.Await) and isinstance(inner.value, ast.Call):
                func = inner.value.func
                if isinstance(func, ast.Attribute) and func.attr in _SEND_METHODS:
                    sends = True
            if isinstance(inner, ast.Call):
                func = inner.func
                name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
                prunes = prunes or name == _PRUNE
        if sends:
            senders.add((rel, node.name))
            if not prunes:
                missing.append((rel, node.name))
    return missing, senders


def _scan_app() -> tuple[list[tuple[str, str]], set[tuple[str, str]]]:
    missing: list[tuple[str, str]] = []
    senders: set[tuple[str, str]] = set()
    for path in sorted(_APP.rglob("*.py")):
        rel = str(path.relative_to(_APP))
        if rel.startswith(_CHANNEL_MODULES):
            continue
        m, s = scan_source(path.read_text(encoding="utf-8"), rel)
        missing += m
        senders |= s
    return missing, senders


def test_every_channel_sender_prunes_expired_subscriptions() -> None:
    missing, _ = _scan_app()
    offenders = [f"{rel}::{fn}" for rel, fn in missing if (rel, fn) not in _EXEMPT]

    assert offenders == [], (
        "A function sends through a notification channel without pruning the subscriptions the push service "
        "reported gone (#1827). Call NotificationEngine.prune_expired_subscriptions(user_key, result), or list "
        "it in _EXEMPT with the reason its channel has no subscriptions.\n  " + "\n  ".join(offenders)
    )


def test_the_scan_sees_the_known_senders_and_every_exemption_is_live() -> None:
    _, senders = _scan_app()

    assert {
        ("domain/engines/notification_engine.py", "_send_to_channel"),
        ("domain/engines/notification_engine.py", "notify_batch"),
        ("domain/services/notification_service.py", "send_test"),
    } <= senders
    assert set(_EXEMPT) <= senders, "an _EXEMPT entry names no sender any more: remove it"


def test_the_detector_sees_a_sender_that_does_not_prune() -> None:
    source = """
async def a(ch, n, cfg):
    return await ch.send(n, cfg)

async def b(self, ch, n, cfg, user):
    result = await ch.send_batch(n, cfg)
    self._engine.prune_expired_subscriptions(user, result)
    return result

def c(ch):
    return ch.send_email("x")
"""
    missing, senders = scan_source(source, "probe.py")
    assert missing == [("probe.py", "a")]
    assert senders == {("probe.py", "a"), ("probe.py", "b")}
