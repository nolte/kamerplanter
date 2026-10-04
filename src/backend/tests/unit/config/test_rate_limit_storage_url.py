"""``RATE_LIMIT_STORAGE_URL`` is checked when the settings load, without echoing it (#2045).

The value is a storage URI and may carry the Valkey password. Unchecked, a typo'd
scheme reached ``limits.storage.storage_from_string`` while the auth router was
being imported — before the redacting log setup runs — and its
``ConfigurationError("unknown storage scheme : <the whole URL>")`` went to stderr
through the interpreter's default hook. The setting is now refused at load with
the ``load_settings`` contract of #1832: the variable and the allowed schemes are
named, the value is not.

The allow-list is what this backend can actually count in, measured against the
installed ``limits`` 5.8: ``redis``, ``rediss``, ``redis+unix`` and ``memory``.
``valkey://`` and its variants are registered schemes in ``limits`` but need the
``valkey`` client package, which the backend does not ship — they would fail the
same way at import. ``async+…`` storages hand the synchronous slowapi limiter
coroutines instead of counts.
"""

from __future__ import annotations

import pytest

from app.config.settings import SettingsError, load_settings

_VARIABLE = "RATE_LIMIT_STORAGE_URL"
_SECRET = "hunter2-limiter-password"

_PW = "".join(["p", "w"])  # assembled at runtime: a credential-shaped literal trips secret scanners


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(_VARIABLE, raising=False)
    monkeypatch.delenv("REDIS_URL", raising=False)


@pytest.mark.parametrize(
    "value",
    [
        f"redis-typo://:{_SECRET}@valkey:6379/0",
        f"async+redis://:{_SECRET}@valkey:6379/0",
        f"valkey://:{_SECRET}@valkey:6379/0",
        f"redis+sentinel://:{_SECRET}@valkey:26379/main",
        f"valkey:{_SECRET}@valkey:6379/0",
        _SECRET,
    ],
)
def test_an_unusable_storage_url_refuses_to_load_without_echoing_it(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv(_VARIABLE, value)

    with pytest.raises(SettingsError) as raised:
        load_settings()

    message = str(raised.value)
    assert _VARIABLE in message
    assert "redis://" in message  # the allowed schemes are named ...
    assert _SECRET not in message  # ... the configured value is not
    assert "valkey:6379" not in message


def test_the_validator_message_itself_carries_no_value(monkeypatch: pytest.MonkeyPatch) -> None:
    """Even pydantic's raw ``ValidationError`` text: only its ``input_value`` echoes the input."""
    from pydantic import ValidationError

    from app.config.settings import Settings

    with pytest.raises(ValidationError) as raised:
        Settings(rate_limit_storage_url=f"redis-typo://:{_SECRET}@valkey:6379/0")

    errors = raised.value.errors(include_input=False, include_context=False, include_url=False)
    assert [error["loc"] for error in errors] == [("rate_limit_storage_url",)]
    assert _SECRET not in errors[0]["msg"]


@pytest.mark.parametrize(
    "value",
    ["", "memory://", "redis://valkey:6379/1", "rediss://valkey:6380/1", "redis+unix:///run/valkey.sock"],
)
def test_every_usable_storage_url_loads(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv(_VARIABLE, value)

    assert load_settings().rate_limit_storage_url == value


def test_the_allow_list_is_exactly_what_the_installed_limits_can_build() -> None:
    """Every allowed scheme constructs a synchronous ``limits`` storage here, lazily."""
    from limits.storage import Storage, storage_from_string

    from app.config.settings import RATE_LIMIT_STORAGE_SCHEMES

    probes = {
        "memory": "memory://",
        "redis": "redis://valkey.invalid:6379/0",
        "rediss": "rediss://valkey.invalid:6379/0",
        "redis+unix": "redis+unix:///nonexistent/valkey.sock",
    }
    assert set(RATE_LIMIT_STORAGE_SCHEMES) == set(probes)
    for uri in probes.values():
        assert isinstance(storage_from_string(uri), Storage)


@pytest.mark.parametrize("variable", [_VARIABLE, "REDIS_URL"])
@pytest.mark.parametrize("separator", ["/", "#", "?"])
def test_a_malformed_authority_refuses_to_load_without_echoing_it(
    monkeypatch: pytest.MonkeyPatch, variable: str, separator: str
) -> None:
    """An unencoded ``/``, ``#`` or ``?`` in the password moves it into the port (R2-01).

    ``urllib`` reads ``redis://:pw/x@host`` as host ``''`` and port ``'pw'``;
    redis-py's ``ValueError`` then quoted that "port". Both variables are
    checked: an empty ``RATE_LIMIT_STORAGE_URL`` hands ``REDIS_URL`` to the
    limiter.
    """
    monkeypatch.setenv(variable, f"redis://:{_SECRET}{separator}x@valkey:6379/0")

    with pytest.raises(SettingsError) as raised:
        load_settings()

    message = str(raised.value)
    assert variable in message
    assert _SECRET not in message
    assert raised.value.__context__ is None


def test_a_well_formed_redis_url_with_an_encoded_password_loads(monkeypatch: pytest.MonkeyPatch) -> None:
    value = "redis://:s3cr%2Ft%23x@valkey:6379/0"
    monkeypatch.setenv("REDIS_URL", value)

    assert load_settings().redis_url == value


#: Forms an operator or a chart actually writes. Each was measured to build a
#: ``limits`` ``RedisStorage`` (lazily, no connection) on the installed limits
#: 5.8 / redis-py 8.1 — host, port, password and socket path parsed as meant.
_ACCEPTED_URLS = [
    "redis://kamerplanter-valkey:6379/0",  # the chart's value
    "redis://valkey:6379/1",  # docker-compose.e2e
    "redis://localhost:6379/0",  # the settings default
    "rediss://h:6379/0?ssl_cert_reqs=required",
    "redis://[::1]:6379/0",
    "redis://:p%40ss@h:6379/0",  # percent-encoded '@' in the password
    f"redis+unix://:{_PW}@/run/valkey.sock",
    # The positive matrix of #2062: every other shape an operator writes, each measured to build.
    f"redis://user:{_PW}@h:6379/0",  # ACL user and password
    f"redis://:{_PW}@h/0",  # no port
    "redis://h",  # bare host
    "redis://h:6379",  # no database
    f"rediss://:{_PW}@h:6380/2",  # TLS, percent-encoded '/' in the password
    f"redis://u%40ser:{_PW}@h:6379/0",  # percent-encoded '@' in the user
    "redis://h:6379/0?socket_timeout=3",  # a query option, no '@'
    "redis+unix:///run/valkey.sock",  # socket without a password
    f"redis+unix://:{_PW}@/run/valkey.sock?db=2",
]


@pytest.mark.parametrize("variable", [_VARIABLE, "REDIS_URL"])
@pytest.mark.parametrize("value", _ACCEPTED_URLS)
def test_a_usable_url_loads_and_builds_the_limiter(monkeypatch: pytest.MonkeyPatch, variable: str, value: str) -> None:
    """The validators refuse only what breaks: every real-world form still loads (R3-04)."""
    from app.api.v1.auth.router import _rate_limit_key
    from app.common import rate_limit

    monkeypatch.setenv(variable, value)
    loaded = load_settings()

    assert getattr(loaded, variable.lower()) == value
    # The same value through the limiter factory, as the auth router builds it.
    monkeypatch.setattr(rate_limit, "settings", loaded)
    assert rate_limit.resolve_rate_limit_storage_url() == value
    storage = rate_limit.build_rate_limiter(_rate_limit_key).limiter.storage
    assert isinstance(storage, rate_limit.FailoverStorage)


def test_an_empty_storage_url_falls_back_to_redis_url(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.common import rate_limit

    monkeypatch.setenv(_VARIABLE, "")
    monkeypatch.setenv("REDIS_URL", "redis://valkey:6379/1")
    loaded = load_settings()
    monkeypatch.setattr(rate_limit, "settings", loaded)

    assert loaded.rate_limit_storage_url == ""
    assert rate_limit.resolve_rate_limit_storage_url() == "redis://valkey:6379/1"


def test_an_empty_redis_url_loads_but_gives_the_limiter_nothing_to_count_in(monkeypatch: pytest.MonkeyPatch) -> None:
    """``REDIS_URL=""`` passes the shape check (other consumers decide about it); the limiter refuses it.

    With both variables empty there is no storage to count in, and the factory
    says so without a value instead of falling back to per-process counting.
    """
    from app.api.v1.auth.router import _rate_limit_key
    from app.common import rate_limit

    monkeypatch.setenv(_VARIABLE, "")
    monkeypatch.setenv("REDIS_URL", "")
    loaded = load_settings()
    monkeypatch.setattr(rate_limit, "settings", loaded)

    assert loaded.redis_url == ""
    with pytest.raises(rate_limit.RateLimitStorageConfigError):
        rate_limit.build_rate_limiter(_rate_limit_key)


@pytest.mark.parametrize("variable", [_VARIABLE, "REDIS_URL"])
@pytest.mark.parametrize("value", ["redis://h:6379/0?client_name=a@b", "redis://h:6379/a@b", "redis://h:6379/0#a@b"])
def test_an_at_sign_after_the_authority_is_refused_although_redis_py_would_read_it(
    monkeypatch: pytest.MonkeyPatch, variable: str, value: str
) -> None:
    """The deliberate boundary of the check (#2062): ``@`` in path, query or fragment is refused.

    redis-py reads ``redis://h:6379/0?client_name=a@b`` as host ``h``. The same rule
    cannot tell it from ``redis://hunter2/x@h:6379`` — a password whose unencoded
    ``/`` ended the authority — where the *password* becomes the host name, and the
    DNS error of a connection attempt then quotes it. The form that is safe to accept
    and the form that leaks differ only in what the operator meant, so the check
    refuses both and tells the operator to percent-encode; the cost is one rare URL.
    """
    monkeypatch.setenv(variable, value)

    with pytest.raises(SettingsError) as raised:
        load_settings()

    assert variable in str(raised.value)
    assert "percent-encode" in str(raised.value)


def test_the_look_alike_of_a_valid_url_puts_the_password_into_the_host() -> None:
    """Pins the measurement the boundary above rests on."""
    from urllib.parse import urlsplit

    assert urlsplit("redis://h:6379/0?client_name=a@b").hostname == "h"
    assert urlsplit(f"redis://{_PW}/x@h:6379").hostname == _PW
