"""#1860 — no API-key-, JWT- or URL-password-shaped literal is committed, outside a reasoned allow-list.

``spec/style-guides/BACKEND.md`` §16.3 (#1838) records the convention: a test
value that looks like a real secret is **assembled at runtime**, never
committed as a literal — a secret scanner (GitGuardian scans every PR commit)
reports it, and nothing stops it from being copied into a real configuration.
Until #1860 only the Fernet shape was enforced (``test_no_committed_fernet_key.py``);
the GitGuardian findings on PR #1837 were exactly the other shapes. This guard
enforces three more, over every tracked text file (``git ls-files``):

* **``kp_`` API key** — ``kp_`` + at least 32 URL-safe characters (the service
  mints ``kp_`` + ``secrets.token_urlsafe(32)``, 43 characters);
* **JWT** — ``eyJ…`` ``.`` ``eyJ…`` ``.`` signature, the base64url header and
  payload every JWT starts with;
* **URL userinfo password** — ``scheme://user:<password>@``.

**Evident placeholders pass** (§16.3 allows them): a value with a template
marker (``${…}``, ``{…}``, ``[…]``, ``<…>``), or one whose Shannon entropy is
below :data:`PLACEHOLDER_ENTROPY` bits per character — ``kp_live_xxxx…``,
``kp_demo0000…``, ``user:pass@``, ``pw-1795``. Everything else fails unless its
``(path, sha256 of the value)`` is in :data:`ALLOWED` with a reason; an entry
that no longer matches fails too.

Spellings this does NOT see
---------------------------

* a ``password = "…"`` / ``password: …`` literal outside a URL — measured on
  develop: 64 quoted literals, almost all human-readable test passwords
  (``sicheres-passwort-2024``); not in this guard's scope (#1860 names the three
  shapes above);
* a high-entropy value split across two literals joined at run time (that is
  the convention, not an evasion) or read from an environment file that is not
  tracked;
* an API key of another provider (``sk-…``, ``AKIA…``), which GitGuardian knows
  and this guard does not.
"""

from __future__ import annotations

import collections
import hashlib
import math
import re
import subprocess
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[5]

#: The shapes, each with the group that holds the secret part.
SHAPES: dict[str, re.Pattern[str]] = {
    "kp_api_key": re.compile(r"(?<![A-Za-z0-9_-])kp_([A-Za-z0-9_-]{32,})(?![A-Za-z0-9_-])"),
    "jwt": re.compile(r"(?<![A-Za-z0-9_-])(eyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,})"),
    "url_password": re.compile(r"[A-Za-z][A-Za-z0-9+.-]{1,20}://[^\s:/@'\"`<>]+:([^\s@/'\"`<>]+)@"),
}

#: Bits per character below which a value is an evident placeholder. A minted
#: key (``token_urlsafe``) carries ~5.3, a hex example ~3.9, ``xxxx…`` ~1.0.
PLACEHOLDER_ENTROPY = 3.0
_TEMPLATE = re.compile(r"\$\{|[{}\[\]<>]")

#: (tracked path, sha256 of the value) → why this shaped literal may be committed.
ALLOWED: dict[tuple[str, str], str] = {
    (
        "spec/req/REQ-023_Benutzerverwaltung-Authentifizierung.md",
        "d57829edd394cabfff7842d7084f3b2f7b0290e790892c78f5c32e5b844b3f5c",
    ): "a Prometheus metric name (kp_auth_token_family_invalidated_total), not a key",
    (
        "spec/dev-tooling/INTEGRATION-DB-ISOLATION.md",
        "5e10d4f1ac2ab2fa827c29bf4db7ac154953a2da291dfc2d4eca4de0d34618de",
    ): "an integration-test database name (kp_it_<run>__<epoch>_<hex>) quoted from a log line, not a key",
}


def entropy(value: str) -> float:
    counts = collections.Counter(value)
    return -sum(n / len(value) * math.log2(n / len(value)) for n in counts.values())


def is_placeholder(value: str) -> bool:
    return bool(_TEMPLATE.search(value)) or entropy(value) < PLACEHOLDER_ENTROPY


def shaped_literals_in(text: str) -> list[tuple[str, str]]:
    """``(shape, value)`` for every credential-shaped value in *text* that is not an evident placeholder."""
    found = []
    for shape, pattern in SHAPES.items():
        for match in pattern.finditer(text):
            value = match.group(1)
            if not is_placeholder(value):
                found.append((shape, value))
    return found


def _tracked_hits() -> dict[tuple[str, str], str]:
    files = subprocess.run(["git", "ls-files", "-z"], cwd=_ROOT, capture_output=True, check=True).stdout.split(b"\0")
    hits: dict[tuple[str, str], str] = {}
    for raw in filter(None, files):
        path = _ROOT / raw.decode()
        if not path.is_file():
            continue
        data = path.read_bytes()
        # prose-permeable: a secret scan reads every byte of a file, comments included; this only skips binaries
        if b"\0" in data[:4096]:
            continue
        for shape, value in shaped_literals_in(data.decode("utf-8", errors="replace")):
            hits[(raw.decode(), hashlib.sha256(value.encode()).hexdigest())] = shape
    return hits


def test_no_credential_shaped_literal_is_tracked() -> None:
    stray = sorted(
        f"{path} ({shape}, sha256 {digest})"
        for (path, digest), shape in _tracked_hits().items()
        if (path, digest) not in ALLOWED
    )

    assert stray == [], (
        "credential-shaped literal committed — assemble it at runtime (BACKEND.md §16.3), use an evident "
        "placeholder (kp_live_xxxx…), or allow it in ALLOWED with a reason:\n  " + "\n  ".join(stray)
    )


def test_every_allowed_entry_still_matches() -> None:
    stale = [site for site in ALLOWED if site not in _tracked_hits()]

    assert stale == [], f"ALLOWED entries that no longer match a committed literal: {stale}"


# ── self-tests, spelled by the convention they enforce (assembled at runtime) ──


def _token(n: int) -> str:
    import base64

    return base64.urlsafe_b64encode(bytes(range(7, 7 + n))).decode().rstrip("=")


def test_each_shape_is_seen() -> None:
    key = "kp_" + _token(32)
    jwt = ".".join(("eyJ" + _token(12), "eyJ" + _token(24), _token(32)))
    password = _token(18)
    text = f'api_key: "{key}"\nAuthorization: Bearer {jwt}\nDSN=postgresql://app:{password}@db:5432/x\n'

    assert sorted(shape for shape, _ in shaped_literals_in(text)) == ["jwt", "kp_api_key", "url_password"]


def test_evident_placeholders_pass() -> None:
    for text in (
        "kp_live_" + "x" * 28,
        "kp_demo" + "0" * 46,
        "redis://user:" + "pass" + "@host:6379",
        "postgresql://app:${PG_PW}@db/x",
        "https://probe:{USERINFO_PASSWORD}@example.org",
        "scheme://user:[password]@host",
    ):
        assert shaped_literals_in(text) == [], text


def test_the_boundaries_hold() -> None:
    key = "kp_" + _token(32)
    assert shaped_literals_in("x" + key) == []  # embedded in a longer token
    assert shaped_literals_in("kp_" + _token(20)) == []  # too short to be a minted key
