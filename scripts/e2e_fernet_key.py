#!/usr/bin/env python3
"""Print the Fernet key the E2E compose stack runs with — generated, never committed (#1838).

``docker-compose.e2e.yml`` reads ``FERNET_KEY`` from ``E2E_FERNET_KEY``. This
script is the one place that value comes from, so every caller that brings the
stack up (``scripts/run-e2e.sh``, the ``ephemeral-stack`` action, the reach and
MCP tasks) gets the same key:

1. ``E2E_FERNET_KEY`` from the environment, when set (validated);
2. otherwise the key stored in ``.e2e-secrets/fernet.key`` of this working copy
   (git-ignored, mode 0600);
3. otherwise a freshly generated key, stored there for the next call.

The stored key keeps one stack consistent across separate ``docker compose up``
calls — a backend recreated with a different key than its Celery workers could
no longer decrypt what they stored. A CI job starts from a fresh checkout, so
there every run gets its own key; locally it is one key per working copy.
``rm -r .e2e-secrets`` (with the stack down) rotates it.

Standard library only: the callers run it on bare CI runners.
"""

from __future__ import annotations

import base64
import binascii
import contextlib
import os
import stat
import sys
from collections.abc import Mapping
from pathlib import Path

ENV_VARIABLE = "E2E_FERNET_KEY"
KEY_FILE = Path(__file__).resolve().parents[1] / ".e2e-secrets" / "fernet.key"


def is_fernet_key(value: str) -> bool:
    """Whether *value* is a usable Fernet key (URL-safe base64 of 32 bytes)."""
    # ``as exc`` keeps the tuple parenthesised: ``ruff format`` rewrites a bare
    # ``except (A, B):`` into PEP 758 form, a SyntaxError before Python 3.14 —
    # and the callers run this with the runner's system ``python3``.
    try:
        decoded = base64.urlsafe_b64decode(value.encode())
    except (binascii.Error, ValueError) as exc:
        del exc
        return False
    return len(decoded) == 32 and len(value) == 44


def generate() -> str:
    """A new random key in the format ``cryptography.fernet.Fernet.generate_key`` produces."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode()


def _private_dir(directory: Path) -> None:
    """Create *directory* 0700, refusing one that is a symlink or not ours."""
    with contextlib.suppress(FileExistsError):
        directory.mkdir(mode=0o700)
    info = directory.lstat()
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
        raise SystemExit(f"{directory} must be a directory owned by you, not a symlink.")
    os.chmod(directory, 0o700)


def _read_stored(key_file: Path) -> str | None:
    """The stored key, ``None`` when there is none; refuse anything else loudly."""
    try:
        info = key_file.lstat()
    except FileNotFoundError:
        return None
    if not stat.S_ISREG(info.st_mode):
        raise SystemExit(f"{key_file} must be a regular file, not a symlink.")
    stored = key_file.read_text(encoding="utf-8").strip()
    if not is_fernet_key(stored):
        # Never replaced silently: a running stack encrypted with the old key.
        raise SystemExit(f"{key_file} does not hold a Fernet key; remove it (with the stack down) to rotate.")
    return stored


def _store_new(key_file: Path) -> str:
    """Store a fresh key atomically; the first of two racing callers wins, both return it."""
    key = generate()
    temporary = key_file.with_name(f".{key_file.name}.{os.getpid()}.tmp")
    fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(key + "\n")
        with contextlib.suppress(FileExistsError):  # another caller stored one first: theirs wins
            os.link(temporary, key_file)  # atomic, never a half-written key file
    finally:
        temporary.unlink(missing_ok=True)
    stored = _read_stored(key_file)
    assert stored is not None
    return stored


def resolve(environ: Mapping[str, str] | None = None, key_file: Path = KEY_FILE) -> str:
    """The key to run the stack with, following the order in the module docstring."""
    environ = os.environ if environ is None else environ
    given = environ.get(ENV_VARIABLE, "").strip()
    if given:
        if not is_fernet_key(given):
            raise SystemExit(f"{ENV_VARIABLE} is set but is not a Fernet key (URL-safe base64 of 32 bytes).")
        stored = _read_stored(key_file) if key_file.parent.is_dir() else None
        if stored is not None and stored != given:
            print(
                f"warning: {ENV_VARIABLE} differs from {key_file}; a stack started from another shell of "
                "this working copy uses the stored key, and the two cannot decrypt each other's data.",
                file=sys.stderr,
            )
        return given
    _private_dir(key_file.parent)
    return _read_stored(key_file) or _store_new(key_file)


def main() -> int:
    sys.stdout.write(resolve() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
