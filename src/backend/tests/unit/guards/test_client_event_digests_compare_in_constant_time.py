"""REQ-053 wave 9 acceptance (#2757, review finding SEC-002) — a request digest is never compared with ``==``/``!=``.

A buffered write (WP 9.3) stores an HMAC digest of the request beside its ``client_event_id``; a replay is answered
from the stored object only when the digest of the new request is the stored one. ``same_digest``
(``app/domain/models/client_event.py``) compares the two in constant time (``hmac.compare_digest``). The review found
three call sites that compared with ``!=`` instead (``task_service`` for the batch completion, ``attachment_service``
twice for the upload replay) beside one that used the helper (``care_event_service``) - the same rule, opt-in at
each call site, drifted between siblings.

**Predicate** - every ``==`` / ``!=`` comparison in ``app/**`` with an operand whose name ends in ``digest`` (an
attribute such as ``client_event_digest``, ``completion_client_event_digest``, ``stamp.digest``, or a bare name
``digest``) is a finding. ``is None`` / ``is not None`` is a presence check, not a comparison of values, and stays
allowed. A call such as ``hashlib.sha256(...).hexdigest()`` is not a name and is not matched.
"""

from __future__ import annotations

import ast
from pathlib import Path

_APP = Path(__file__).resolve().parents[3] / "app"


def _name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Subscript):
        return _name(node.value)
    return None


def digest_equality_comparisons(source: str, path: str = "<probe>") -> list[str]:
    """``path:line: expression`` for every ``==`` / ``!=`` comparison with an operand named ``*digest``."""
    findings: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Compare):
            continue
        if not any(isinstance(op, (ast.Eq, ast.NotEq)) for op in node.ops):
            continue
        operands = [node.left, *node.comparators]
        if any((name := _name(operand)) is not None and name.endswith("digest") for operand in operands):
            findings.append(f"{path}:{node.lineno}: {ast.unparse(node)}")
    return findings


def test_no_digest_is_compared_with_equality_operators() -> None:
    findings: list[str] = []
    for path in sorted(_APP.rglob("*.py")):
        findings += digest_equality_comparisons(path.read_text(encoding="utf-8"), str(path.relative_to(_APP.parent)))
    assert findings == [], "compare request digests with same_digest() (hmac.compare_digest):\n" + "\n".join(findings)


def test_the_predicate_finds_both_operators_and_the_attribute_forms() -> None:
    probe = (
        "if stored.client_event_digest != stamp.digest:\n    pass\n"
        "ok = holder.completion_client_event_digest == stamps[key].digest\n"
        "same = digest == other\n"
    )
    assert len(digest_equality_comparisons(probe)) == 3


def test_presence_checks_and_hash_calls_are_not_findings() -> None:
    probe = (
        "if digest is not None and stored is None:\n    pass\n"
        "if same_digest(row.client_event_digest, stamp.digest):\n    pass\n"
        "if hashlib.sha256(data).hexdigest() == expected_sha:\n    pass\n"
    )
    assert digest_equality_comparisons(probe) == []
