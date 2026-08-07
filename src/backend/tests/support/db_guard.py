"""Fail-fast guard against real datastore connections from a test tier (#978).

``app/common/dependencies.py`` is a fan-out of provider functions. Constructing a
service through one of them can transitively reach ``get_db()``, which opens a
**real** ArangoDB connection. On a developer machine with the dev stack up,
``localhost:8529`` answers — so such a test passes locally, silently reads and
writes the dev database, and fails in CI where nothing is listening. It fails
slowly there too: python-arango retries, so the diagnosis costs ~18 s per
connecting call before reporting ``ConnectionAbortedError``.

This module turns that into an immediate, local, self-explaining failure. Install
it from a tier's ``conftest.py`` (see ``tests/unit/conftest.py``).

The exception deliberately derives from :class:`BaseException`: production code
swallows ``Exception`` around optional lookups — ``CropRotationValidator``
wraps its ``get_family_repo()`` call in ``except Exception: pass`` — and a guard
that a stray ``except Exception`` can hide would report green in exactly the
place where the problem lives.
"""

from __future__ import annotations

import traceback
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

#: ``src/backend`` — frames outside it (pytest, stdlib, site-packages) are noise
#: in the caller chain and get dropped from the message.
_BACKEND_ROOT = Path(__file__).resolve().parents[2]

#: Own path, so the guard's own frames never appear in the chain it prints.
_SELF = Path(__file__).resolve()

#: How many of the innermost project frames to show. The interesting part is
#: always the tail: test → engine/service → provider → ``get_db``.
_MAX_FRAMES = 12

#: Path of the provider fan-out, relative to ``src/backend`` — the module whose
#: frames name *what* asked for a repository.
_DEPENDENCIES_MODULE = "app/common/dependencies.py"

#: Opt-out marker, registered in ``pyproject.toml``. Greppable on purpose —
#: ``grep -rn "allow_db_connection" tests/`` counts every exception in the tier,
#: which the per-test patches it replaces never allowed.
ALLOW_MARKER = "allow_db_connection"


class TierDatabaseAccessError(BaseException):
    """A test in a datastore-free tier tried to open a real connection."""


def _project_frames() -> list[traceback.FrameSummary]:
    """Return the innermost ``app/`` and ``tests/`` frames of the current stack."""
    frames: list[traceback.FrameSummary] = []
    for frame in traceback.extract_stack():
        path = Path(frame.filename)
        if path == _SELF:
            continue
        try:
            relative = path.resolve().relative_to(_BACKEND_ROOT)
        except ValueError:
            continue
        if relative.parts[0] not in ("app", "tests"):
            continue
        frame.filename = str(relative)
        frames.append(frame)
    return frames[-_MAX_FRAMES:]


def _provider_name(frames: list[traceback.FrameSummary]) -> str | None:
    """Name the innermost ``app/common/dependencies.py`` provider on the stack."""
    for frame in reversed(frames):
        if frame.filename == _DEPENDENCIES_MODULE and frame.name not in ("get_db", "get_connection"):
            return frame.name
    return None


def _message(tier: str, store: str, target: str, hint: Callable[[list[traceback.FrameSummary]], str]) -> str:
    frames = _project_frames()
    chain = "\n".join(f"  {f.filename}:{f.lineno}  {f.name}" for f in frames) or "  (no project frames on the stack)"
    return (
        f"\n"
        f"{tier} tier: this test tried to open a REAL {store} connection ({target}).\n"
        f"\n"
        f"Tests in tests/{tier}/ must not touch a datastore. With the dev stack up this\n"
        f"connection succeeds: the test then reads or writes the dev database (or\n"
        f"publishes a real Celery message) and reports green. In CI, where nothing\n"
        f"listens, the same test fails — or merely crawls, if the code swallows the\n"
        f"error — through a connection timeout (~18 s per connecting ArangoDB call)\n"
        f"with an unrelated-looking ConnectionAbortedError. See issue #978.\n"
        f"\n"
        f"What asked for the connection (outermost first, the trigger is last):\n"
        f"{chain}\n"
        f"\n"
        f"{hint(frames)}\n"
        f"\n"
        f"If the test genuinely needs a live datastore it belongs in tests/integration/.\n"
        f'As a documented last resort: @pytest.mark.{ALLOW_MARKER}("<reason>")'
    )


def _arango_hint(frames: list[traceback.FrameSummary]) -> str:
    """Name the provider from the chain, so the suggested patch is copy-pasteable."""
    provider = _provider_name(frames) or "get_species_repo"
    return (
        "Fix it by injecting a fake/mock repository rather than letting the code reach\n"
        "a provider, or by patching the provider the chain above names:\n"
        f'  monkeypatch.setattr("app.common.dependencies.{provider}", lambda: MagicMock())'
    )


def _timescale_hint(frames: list[traceback.FrameSummary]) -> str:
    return (
        "Fix it by injecting a fake observation repository, or patch the provider:\n"
        '  monkeypatch.setattr("app.common.dependencies.get_timescale_connection", lambda: None)'
    )


def _redis_hint(frames: list[traceback.FrameSummary]) -> str:
    return (
        "Most hits here are a Celery dispatch — `<task>.delay(...)` publishes to the\n"
        "broker. Stub the task the way the neighbouring tests do, e.g.\n"
        '  monkeypatch.setattr(storage_tasks.generate_thumbnails, "delay", lambda *a, **k: None)\n'
        "For a directly used client, inject a fake instead:\n"
        '  monkeypatch.setattr("app.common.dependencies._get_redis_client", lambda: MagicMock())'
    )


def _arango_target(connection: Any) -> str:
    settings = getattr(connection, "_settings", None)
    if settings is None:
        return "the configured ArangoDB host"
    return f"{settings.arangodb_host}:{settings.arangodb_port}"


def _timescale_target(connection: Any) -> str:
    settings = getattr(connection, "_settings", None)
    if settings is None:
        return "the configured TimescaleDB host"
    return f"{settings.timescaledb_host}:{settings.timescaledb_port}"


def install(monkeypatch: pytest.MonkeyPatch, *, tier: str) -> None:
    """Make every datastore connection attempt raise immediately.

    Patches the three choke points through which the backend opens a network
    connection to a datastore:

    * :meth:`app.data_access.arango.connection.ArangoConnection.connect` — the only
      place an ``ArangoClient`` is built; ``get_db()``, ``get_connection().db`` and
      the Celery tasks that build their own ``ArangoConnection`` all pass here.
    * :meth:`app.data_access.timescale.connection.TimescaleConnection.connect` —
      the only place a psycopg ``ConnectionPool`` is opened.
    * ``redis.connection.AbstractConnection.connect`` — the socket-level choke
      point of redis-py, and with it the Celery broker, which reaches Valkey
      through kombu's redis transport. Patched one level lower than the others
      because ``redis.Redis.from_url()`` is lazy: constructing a client is
      harmless, and only an actual command opens a socket.

    Object storage (S3/MinIO) is deliberately **not** covered: it is not a
    datastore in the sense of this guard, its boto3 client is lazy, and the tests
    that exercise it drive it against ``moto`` or the local-filesystem adapter.

    Args:
        monkeypatch: Function-scoped monkeypatch fixture; the patches are undone
            after each test.
        tier: Directory name of the tier under ``tests/``, used in the message.
    """
    from redis.connection import AbstractConnection

    from app.data_access.arango.connection import ArangoConnection
    from app.data_access.timescale.connection import TimescaleConnection

    def _blocked_arango(self: Any) -> None:
        raise TierDatabaseAccessError(_message(tier, "ArangoDB", _arango_target(self), _arango_hint))

    def _blocked_timescale(self: Any) -> None:
        raise TierDatabaseAccessError(_message(tier, "TimescaleDB", _timescale_target(self), _timescale_hint))

    def _blocked_redis(self: Any) -> None:
        raise TierDatabaseAccessError(_message(tier, "Redis/Valkey", getattr(self, "host", "?"), _redis_hint))

    monkeypatch.setattr(ArangoConnection, "connect", _blocked_arango)
    monkeypatch.setattr(TimescaleConnection, "connect", _blocked_timescale)
    monkeypatch.setattr(AbstractConnection, "connect", _blocked_redis)


def install_unless_marked(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch, *, tier: str) -> None:
    """Install the guard for the current test unless it opted out.

    The opt-out is ``@pytest.mark.allow_db_connection("<reason>")``. The reason is
    mandatory: an exception nobody had to justify is a silent bypass, and the
    point of a marker over a per-test patch is that the exceptions stay countable.
    """
    marker = request.node.get_closest_marker(ALLOW_MARKER)
    if marker is not None:
        reason = next(iter(marker.args), None)
        if not reason:
            raise pytest.UsageError(
                f"@pytest.mark.{ALLOW_MARKER} requires a reason, "
                f"so the tier's exceptions stay countable: {request.node.nodeid}"
            )
        return
    install(monkeypatch, tier=tier)
