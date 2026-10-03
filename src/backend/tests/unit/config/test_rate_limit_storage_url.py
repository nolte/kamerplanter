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


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(_VARIABLE, raising=False)


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
