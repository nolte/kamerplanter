"""#2062 — every Valkey client the backend builds bounds its socket wait, or says why it need not.

The defect class: ``redis.Redis.from_url(url)`` with no socket options waits
**5 s** per connect and per read (redis-py 8.1). A Valkey that accepts TCP and
never answers then holds every request that touches the client, per Valkey
call — measured for ``_get_redis_client()`` and ``RedisOAuthStateStore`` (the
device-pairing store, the API-key limiter, the MCP session store, the OAuth
state of the anonymous OAuth routes). #2045 bounded the clients of the mail
budgets and of the IP limiter and left these two; a hand list of "the clients"
cannot see the next ``from_url`` somebody adds.

**Predicate** — every call in ``app/`` that builds a Valkey connection
(``from_url``, ``Redis``, ``StrictRedis``, ``ConnectionPool``,
``BlockingConnectionPool``, ``storage_from_string``) must pass
``**bounded_redis_client_options()`` — directly, or through a name the same
function assigns from that call (``options = bounded_redis_client_options()``).

**Spellings this predicate cannot see:** a client built through a third-party
factory it does not name (a Celery broker URL is configured, not built here), a
call reached through ``getattr``, ``socket_timeout`` spelled out by hand instead
of through the shared function (flagged: say it through the function so the
bound stays one number), and code outside ``app/``.
"""

from __future__ import annotations

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[3] / "app"

_CONSTRUCTORS = frozenset(
    {"from_url", "Redis", "StrictRedis", "ConnectionPool", "BlockingConnectionPool", "storage_from_string"}
)
_OPTIONS_FACTORY = "bounded_redis_client_options"

#: ``"<relative path>:<enclosing function>"`` → reason the call needs no bound. Empty today.
_CLASSIFIED: dict[str, str] = {
    "common/rate_limit.py:_build_primary": (
        "Takes its options as a parameter; the one caller that builds them for a Valkey scheme, "
        "``build_rate_limiter``, merges ``bounded_redis_client_options()`` into them "
        "(checked by ``test_the_limiter_factory_merges_the_bounded_options`` below)."
    ),
}

#: Pinned so a predicate that silently loses a member fails instead of shrinking.
_EXPECTED_MEMBERS = {
    "common/dependencies.py:_get_redis_client",
    "common/dependencies.py:_throttle_redis_client_for",
    "common/rate_limit.py:_build_primary",
    "data_access/external/redis_oauth_state.py:__init__",
}


def _callee_name(call: ast.Call) -> str | None:
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    if isinstance(call.func, ast.Name):
        return call.func.id
    return None


def _is_factory_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and _callee_name(node) == _OPTIONS_FACTORY


def _is_bounded(call: ast.Call, function: ast.AST) -> bool:
    """A ``**`` argument that is the factory call, or a name assigned from it in ``function``."""
    for keyword in call.keywords:
        if keyword.arg is not None:
            continue
        value = keyword.value
        if _is_factory_call(value):
            return True
        if isinstance(value, ast.Name):
            for node in ast.walk(function):
                if (
                    isinstance(node, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == value.id for t in node.targets)
                    and _is_factory_call(node.value)
                ):
                    return True
    return False


def _clients(source: str, label: str) -> dict[str, bool]:
    """``{"<label>:<function>": bounded}`` for every client construction in ``source``."""
    out: dict[str, bool] = {}
    tree = ast.parse(source)
    for function in ast.walk(tree):
        if not isinstance(function, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        for node in ast.walk(function):
            if isinstance(node, ast.Call) and _callee_name(node) in _CONSTRUCTORS:
                # The innermost enclosing function owns the call; ast.walk over an outer
                # function revisits it, so keep the most specific (last-visited) owner only
                # when it is bounded or not yet recorded.
                key = f"{label}:{function.name}"
                out[key] = out.get(key, True) and _is_bounded(node, function)
    return out


def _live_clients() -> dict[str, bool]:
    out: dict[str, bool] = {}
    for path in sorted(APP.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        out |= _clients(source, path.relative_to(APP).as_posix())
    return out


def _is_valkey_construction(label: str) -> bool:
    """Drop constructors that are not Valkey clients (a psycopg ``ConnectionPool``)."""
    return "timescale" not in label


def test_the_predicate_finds_the_known_members() -> None:
    live = {k for k in _live_clients() if _is_valkey_construction(k)}

    assert live >= _EXPECTED_MEMBERS, sorted(_EXPECTED_MEMBERS - live)


def test_every_client_bounds_its_socket_wait_or_is_classified() -> None:
    unbounded = sorted(
        key
        for key, bounded in _live_clients().items()
        if _is_valkey_construction(key) and not bounded and key not in _CLASSIFIED
    )

    assert unbounded == [], (
        "Valkey client(s) built without **bounded_redis_client_options() — redis-py waits 5 s per socket "
        f"operation and a hanging Valkey holds every caller (#2062): {unbounded}"
    )


def test_the_limiter_factory_merges_the_bounded_options() -> None:
    """The classification of ``_build_primary`` holds only while its caller keeps merging the bound in."""
    tree = ast.parse((APP / "common" / "rate_limit.py").read_text(encoding="utf-8"))
    factory = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "build_rate_limiter")
    merges = [
        n
        for n in ast.walk(factory)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "update"
        and any(_is_factory_call(arg) for arg in n.args)
    ]

    assert merges, "build_rate_limiter no longer merges bounded_redis_client_options() into the storage options"


def test_no_classification_is_stale() -> None:
    live = _live_clients()
    stale = sorted(key for key in _CLASSIFIED if key not in live or live[key])

    assert stale == [], f"classified entries that no longer name an unbounded client: {stale}"


# ── self-test: the predicate on synthetic code ────────────────────────────


def test_selftest_the_pre_2062_default_client_is_flagged() -> None:
    old = "import redis\n\ndef _get_redis_client():\n    return redis.Redis.from_url(url, decode_responses=True)\n"

    assert _clients(old, "x.py") == {"x.py:_get_redis_client": False}


def test_selftest_the_factory_call_marks_the_client_bounded() -> None:
    new = (
        "import redis\n\ndef build():\n"
        "    return redis.Redis.from_url(url, decode_responses=True, **bounded_redis_client_options())\n"
    )

    assert _clients(new, "x.py") == {"x.py:build": True}


def test_selftest_a_name_assigned_from_the_factory_marks_the_client_bounded() -> None:
    named = (
        "def build(uri):\n"
        "    options = bounded_redis_client_options()\n"
        "    return storage_from_string(uri, **options)\n"
    )

    assert _clients(named, "x.py") == {"x.py:build": True}


def test_selftest_a_hand_written_timeout_is_flagged() -> None:
    """Spelling the bound out by hand forks the number; it must come through the shared function."""
    hand = "def build():\n    return redis.Redis.from_url(url, socket_timeout=0.5)\n"

    assert _clients(hand, "x.py") == {"x.py:build": False}


def test_selftest_a_name_not_assigned_from_the_factory_is_flagged() -> None:
    other = "def build(uri, options):\n    return storage_from_string(uri, **options)\n"

    assert _clients(other, "x.py") == {"x.py:build": False}


def test_selftest_a_function_without_a_client_is_no_member() -> None:
    assert _clients("def f():\n    return 1\n", "x.py") == {}
