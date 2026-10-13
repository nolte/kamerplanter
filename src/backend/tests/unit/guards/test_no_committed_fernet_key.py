"""#1838 — no real-format Fernet key is committed, outside an explicit allow-list.

GitGuardian reported the E2E stack's ``FERNET_KEY`` (``docker-compose.e2e.yml``,
four services) on 2026-09-24. It was a test fixture of a disposable stack, but a
syntactically real key in a public repository: every scanner flags it, and
nothing stops it from being copied into a real deployment. The stack now takes
a key generated per run (``scripts/e2e_fernet_key.py`` → ``E2E_FERNET_KEY``).

**The class, enumerated rather than listed:** every tracked file (``git ls-files``,
text only) is scanned for a *real-format* Fernet key — 43 base64 characters
(URL-safe or standard alphabet) plus ``=``, bounded on both sides, that decodes
to exactly 32 bytes. That is the shape ``Fernet.generate_key()`` produces and the
shape a secret scanner matches; a match anywhere fails unless the file and value
are on :data:`ALLOWED` with a reason. An allow-list entry that no longer matches
fails too, so the list cannot outlive what it excused.

**How tests spell such values** (the convention #1838 records for every
credential-shaped probe — see ``spec/style-guides/BACKEND.md`` §Tests): they are
*assembled at runtime* from innocuous parts, never written as a literal. The
self-test below does exactly that.
"""

from __future__ import annotations

import base64
import binascii
import re
import subprocess
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[5]

#: 43 base64 characters and one pad, not embedded in a longer base64 token. Both
#: alphabets: ``Fernet`` decodes with ``urlsafe_b64decode``, which also accepts the
#: standard ``+``/``/`` that ``openssl rand -base64 32`` emits. A preceding ``=``
#: is a boundary, not a token character (``FERNET_KEY=<key>``).
FERNET_SHAPE = re.compile(r"(?<![A-Za-z0-9_+/-])([A-Za-z0-9_+/-]{43}=)(?![A-Za-z0-9_+/=-])")

#: (tracked path, sha256 of the value) → why this real-format key may be committed.
#: Empty on purpose: generate the key instead (``scripts/e2e_fernet_key.py``).
ALLOWED: dict[tuple[str, str], str] = {}


def _is_fernet_key(candidate: str) -> bool:
    try:
        return len(base64.urlsafe_b64decode(candidate)) == 32
    except (binascii.Error, ValueError) as exc:  # `as` keeps ruff from the PEP 758 spelling
        del exc
        return False


def fernet_keys_in(text: str) -> list[str]:
    return [match for match in FERNET_SHAPE.findall(text) if _is_fernet_key(match)]


def _tracked_hits() -> dict[tuple[str, str], int]:
    import hashlib

    files = subprocess.run(["git", "ls-files", "-z"], cwd=_ROOT, capture_output=True, check=True).stdout.split(b"\0")
    hits: dict[tuple[str, str], int] = {}
    for raw in filter(None, files):
        path = _ROOT / raw.decode()
        if not path.is_file():
            continue
        data = path.read_bytes()
        # prose-permeable: a secret scan reads every byte of a file, comments included; this only skips binaries
        if b"\0" in data[:4096]:
            continue  # binary
        for key in fernet_keys_in(data.decode("utf-8", errors="replace")):
            site = (raw.decode(), hashlib.sha256(key.encode()).hexdigest())
            hits[site] = hits.get(site, 0) + 1
    return hits


def test_no_real_format_fernet_key_is_tracked():
    stray = sorted(site for site in _tracked_hits() if site not in ALLOWED)

    assert stray == [], (
        "real-format Fernet key committed (path, sha256 of value) — generate it per run "
        f"(scripts/e2e_fernet_key.py) or allow it in ALLOWED with a reason: {stray}"
    )


def test_every_allowed_entry_still_matches():
    hits = _tracked_hits()
    stale = [site for site in ALLOWED if site not in hits]

    assert stale == [], f"ALLOWED entries that no longer match a committed key: {stale}"


def test_the_scan_sees_a_generated_key():
    # Self-test, spelled by the convention it enforces: assembled at runtime, so
    # this file itself carries no key-shaped literal.
    key = base64.urlsafe_b64encode(bytes(range(32))).decode()
    assert fernet_keys_in(f"FERNET_KEY: {key}\n") == [key]
    assert fernet_keys_in(f'"{key}"') == [key]


def test_the_scan_ignores_longer_tokens_and_wrong_lengths():
    key = base64.urlsafe_b64encode(bytes(range(32))).decode()
    assert fernet_keys_in("x" + key) == []  # embedded in a longer token
    assert fernet_keys_in(base64.urlsafe_b64encode(bytes(range(31))).decode()) == []
    assert fernet_keys_in(base64.urlsafe_b64encode(bytes(range(64))).decode()) == []


def test_the_scan_sees_env_file_and_shell_spellings():
    # Security review of #1838, W-2: `=` before the key is the commonest spelling.
    key = base64.urlsafe_b64encode(bytes(range(32))).decode()
    for text in (f"FERNET_KEY={key}\n", f"export FERNET_KEY={key}", f"-e FERNET_KEY={key} ", f"--from-literal=k={key}"):
        assert fernet_keys_in(text) == [key], text


def test_the_scan_sees_a_standard_alphabet_key_fernet_also_accepts():
    # W-3: `openssl rand -base64 32` output carries `+`/`/`; Fernet accepts it.
    key = base64.b64encode(bytes([251, 255] * 16)).decode()
    assert "+" in key or "/" in key
    assert fernet_keys_in(f"FERNET_KEY: {key}") == [key]
