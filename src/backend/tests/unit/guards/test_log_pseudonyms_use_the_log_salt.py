"""#1812 class guard — every log pseudonym is keyed with ``LOG_PSEUDONYM_SALT``.

Until #1812 the ``sub_…`` subject references and the ``email_sha256`` digests on
log lines were keyed with ``ERASURE_TOMBSTONE_SALT``, which can never rotate (the
erasure tombstones are keyed with it). Services held that salt and called
``ErasureEngine.log_subject(key, self._tombstone_salt)`` themselves — eleven
sites in four services, each one a place where the log salt could be forgotten.

**The rule.** Outside ``app/common/log_privacy.py`` (which reads
``settings.log_pseudonym_salt`` at call time) and the engine itself, no code in ``app/`` calls
``ErasureEngine.log_subject`` or ``ErasureEngine.redact_subject``; it uses
``app.common.log_privacy.log_subject`` / ``redact_subject`` / ``loggable_error``.
And the two keyed log digests read the log salt: ``log_privacy.log_subject`` and
``decoys.email_digest`` name ``log_pseudonym_salt`` and not the tombstone salt.

Spellings this does NOT see
---------------------------

* a log pseudonym computed with ``hmac`` directly under another purpose label;
* ``ErasureEngine`` imported under another name, or the static method reached
  through an instance whose name is not ``ErasureEngine`` / ``*erasure_engine``.
"""

from __future__ import annotations

import ast
import inspect
from pathlib import Path

from app.common import decoys, log_privacy
from tests.support.execution_guards import find_project_root

_APP = find_project_root(Path(__file__)) / "app"
#: The caller that reads the log salt, and the engine that implements the HMAC
#: (its ``redact_subject`` hands the salt it was given on to ``log_subject``).
_EXEMPT = {"common/log_privacy.py", "domain/engines/erasure_engine.py"}
_KEYED = {"log_subject", "redact_subject"}


def scan_source(source: str, rel: str) -> list[str]:
    findings = []
    for node in ast.walk(ast.parse(source)):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in _KEYED):
            continue
        receiver = node.func.value
        name = receiver.id if isinstance(receiver, ast.Name) else getattr(receiver, "attr", "")
        if name == "ErasureEngine" or name.endswith("erasure_engine"):
            findings.append(f"{rel}:{node.lineno}: {ast.unparse(node.func)}(...) — use app.common.log_privacy")
    return findings


def test_no_log_pseudonym_is_keyed_outside_log_privacy() -> None:
    findings = []
    for path in sorted(_APP.rglob("*.py")):
        rel = str(path.relative_to(_APP))
        if rel not in _EXEMPT:
            findings += scan_source(path.read_text(encoding="utf-8"), rel)

    assert findings == [], (
        "A log pseudonym is keyed with a salt the caller holds — the tombstone salt, until #1812. Route it through "
        "app.common.log_privacy (log_subject, redact_subject, loggable_error), which reads LOG_PSEUDONYM_SALT.\n  "
        + "\n  ".join(findings)
    )


def test_the_two_keyed_log_digests_read_the_log_salt() -> None:
    for function in (log_privacy.log_subject, log_privacy.redact_subject, decoys.email_digest):
        source = inspect.getsource(function)
        assert "settings.log_pseudonym_salt" in source, function.__qualname__
        assert "erasure_tombstone_salt" not in source, function.__qualname__


def test_the_detector_sees_both_receivers_and_nothing_else() -> None:
    source = """
def f(self, k, t):
    a = ErasureEngine.log_subject(k, self._tombstone_salt)
    b = self._erasure_engine.redact_subject(t, k, salt)
    c = log_subject(k)
    d = ErasureEngine.compute_tombstone_hash(k, self._tombstone_salt)
"""
    assert len(scan_source(source, "probe.py")) == 2
