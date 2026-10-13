"""#1996 — the Apprise private-target switch: every cell of mode × switch × target × lane.

``validate_apprise_urls`` is the save lane, ``partition_apprise_urls`` the send
lane. The DNS seam ``url_safety.resolve_host_addresses`` is a zone double.
"""

import itertools

import pytest

from app.common import url_safety
from app.common.exceptions import ValidationError
from app.common.url_safety import _HostCache, partition_apprise_urls, validate_apprise_urls
from app.config.settings import Settings, settings

PUBLIC = "93.184.216.34"
_ZONE = {
    "public.example": [PUBLIC],
    "private10.example": ["10.244.1.7"],
    "ula.example": ["fd12:3456::1"],
    "mapped.example": ["::ffff:10.0.0.1"],
    "cgnat.example": ["100.64.0.10"],
    "nat64-private.example": ["64:ff9b::a00:1"],  # carries 10.0.0.1
    "loop.example": ["127.0.0.1"],
}

#: target kind -> (url, is_private, always_refused)
TARGETS = {
    "public-literal": ("gotify://172.32.0.1/t", False, False),
    "public-name": ("gotify://public.example/t", False, False),
    "private-literal-10": ("gotify://10.96.0.1:443/x/token", True, False),
    "private-literal-172-edge": ("gotify://172.31.255.254/t", True, False),
    "private-literal-192": ("matrix://u:p@192.168.1.5/room", True, False),
    "cgnat-literal": ("gotify://100.127.255.254/t", True, False),
    "private-name": ("gotify://private10.example/t", True, False),
    "ula-name": ("gotify://ula.example/t", True, False),
    "mapped-name": ("gotify://mapped.example/t", True, False),
    "nat64-name": ("gotify://nat64-private.example/t", True, False),
    "cgnat-name": ("ntfy://cgnat.example/topic", True, False),
    "loopback-literal": ("gotify://127.0.0.1/t", False, True),
    "loopback-name": ("gotify://loop.example/t", False, True),
    "metadata-literal": ("gotify://169.254.169.254/t", False, True),
}
MODES = ["full", "light"]
SWITCH = [None, True, False]  # unset (mode decides), explicit on, explicit off
LANES = ["save", "send"]


@pytest.fixture
def zone(monkeypatch):
    calls: list[str] = []

    def _resolve(host: str) -> list[str]:
        calls.append(host)
        try:
            return list(_ZONE[host])
        except KeyError:
            raise OSError("Name or service not known") from None

    monkeypatch.setattr(url_safety, "resolve_host_addresses", _resolve)
    return calls


def _allowed(url: str, lane: str) -> bool:
    if lane == "save":
        try:
            validate_apprise_urls([url], owner_key="u1")
        except ValidationError:
            return False
        return True
    allowed, refused = partition_apprise_urls([url], owner_key="u1")
    return allowed == [url] and refused == 0


@pytest.mark.parametrize(("mode", "switch", "kind", "lane"), list(itertools.product(MODES, SWITCH, TARGETS, LANES)))
def test_every_cell_of_the_matrix(monkeypatch, zone, mode, switch, kind, lane):
    monkeypatch.setattr(settings, "kamerplanter_mode", mode)
    monkeypatch.setattr(settings, "apprise_allow_private_targets", switch)
    url, is_private, always_refused = TARGETS[kind]
    private_ok = switch if switch is not None else mode == "light"
    expected = not always_refused and (not is_private or private_ok)
    assert _allowed(url, lane) is expected, (mode, switch, kind, lane)


def test_the_refusal_names_the_rule_and_not_the_value(monkeypatch, zone):
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    monkeypatch.setattr(settings, "apprise_allow_private_targets", None)
    for url in ("gotify://10.96.0.1:443/x/token", "gotify://private10.example/t"):
        with pytest.raises(ValidationError) as caught:
            validate_apprise_urls([url], owner_key="u1")
        reason = caught.value.details[0]["reason"]
        assert "private network address" in reason
        assert "10." not in reason and "private10" not in reason


def test_a_bot_id_that_spells_a_private_address_is_not_a_host(monkeypatch, zone):
    """``tgram://167772161:TOKEN/x`` parses as host ``167772161`` (= 10.0.0.1); Telegram is not dialled there."""
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    monkeypatch.setattr(settings, "apprise_allow_private_targets", False)
    assert validate_apprise_urls(["tgram://167772161:TOKEN/4711"], owner_key="u1")
    assert zone == []


def test_a_switch_change_applies_to_cached_answers_without_clearing_the_cache(monkeypatch, zone):
    """The cache keeps raw addresses and is judged on read: no cache surgery after a setting change."""
    monkeypatch.setattr(url_safety, "_resolution_cache", _HostCache())
    monkeypatch.setattr(settings, "apprise_allow_private_targets", True)
    url = "gotify://private10.example/t"
    assert validate_apprise_urls([url], owner_key="u1")
    monkeypatch.setattr(settings, "apprise_allow_private_targets", False)
    with pytest.raises(ValidationError):
        validate_apprise_urls([url], owner_key="u1")
    monkeypatch.setattr(settings, "apprise_allow_private_targets", True)
    assert validate_apprise_urls([url], owner_key="u1")
    assert zone == ["private10.example"], "the answer was resolved again instead of judged from the cache"


# ── Settings: default per mode, env overrides both ways ─────────────


@pytest.mark.parametrize(
    ("mode", "env", "expected"),
    [
        ("full", None, False),
        ("light", None, True),
        ("full", "true", True),
        ("light", "false", False),
        ("full", "false", False),
        ("light", "true", True),
    ],
)
def test_the_default_follows_the_mode_and_the_env_overrides_it(monkeypatch, mode, env, expected):
    monkeypatch.setenv("KAMERPLANTER_MODE", mode)
    if env is None:
        monkeypatch.delenv("APPRISE_ALLOW_PRIVATE_TARGETS", raising=False)
    else:
        monkeypatch.setenv("APPRISE_ALLOW_PRIVATE_TARGETS", env)
    loaded = Settings()
    assert loaded.apprise_allow_private_targets == (None if env is None else env == "true")
    assert loaded.apprise_private_targets_allowed() is expected


def test_debug_does_not_loosen_the_switch(monkeypatch, zone):
    monkeypatch.setattr(settings, "kamerplanter_mode", "full")
    monkeypatch.setattr(settings, "apprise_allow_private_targets", None)
    monkeypatch.setattr(settings, "debug", True)
    with pytest.raises(ValidationError):
        validate_apprise_urls(["gotify://10.96.0.1/t"], owner_key="u1")


# ── R5: ``ntfy://name?to=`` / ``?mode=`` dial ``name`` ───────────────


@pytest.mark.parametrize("lane", LANES)
def test_ntfy_with_a_host_query_does_not_tolerate_nxdomain(zone, lane):
    assert _allowed("ntfy://nxname.example?to=x", lane) is False
    assert _allowed("ntfy://nxname.example?Mode=private", lane) is False
    assert _allowed("ntfy://nxname", lane) is True  # still a ntfy.sh topic


@pytest.mark.parametrize("lane", LANES)
def test_ntfy_with_a_host_query_judges_its_literal_as_dialled(zone, lane):
    assert _allowed("ntfy://0.1.2.3?mode=private", lane) is False  # "this network": refused when dialled
    assert _allowed("ntfy://1234", lane) is True  # a numeric topic, not a host
