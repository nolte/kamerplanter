"""#2248 — every route rate limit is a decision for the DAST scan stack.

The ZAP merge scan and the Nuclei scans run against ``docker-compose.e2e.yml``'s
``backend`` service layered with ``docker-compose.security.override.yml``. That
service carries no ``RATE_LIMIT_*`` of its own, so before #2248 it ran every
budget at its production value — sized for one human per client address — while
the scanner is one address sending hundreds of payloads per route and minute.

The cost was a false "SQL Injection" (rule 40018) on
``POST /api/v1/privacy/email-change/revert`` (run 38123811759). Measured, not
inferred: the alert's evidence line reads ``(429 Too Many Requests)``; the 429
body is constant while every 401 body carries a fresh ``error_id``, so ZAP's
boolean pair "original == AND-true == AND-false, OR-true differs" holds exactly
when the fixed window resets between the AND-false and the OR-true probe. A
local replay of that quartet against the scan stack produced the alert shape
``(429, 429, 429, 401)`` on both email-change routes at ``10/minute`` and none at
the raised budget. The same class was suppressed twice before, row by row, in
``tests/security/zap-api-rules.tsv`` (``/email-change/confirm``,
``/device-pairing/redeem``).

So this file makes the scan stack's answer explicit for every limit a route
applies: **raised** in the scan override (the anonymous merge scan reaches the
limiter, and a refusal there is noise), or **left at production** with the
measured reason. A new rate-limited route fails here until someone decides.

It also pins the two properties the raise depends on: each raised key names a
real ``Settings`` field (a misspelt key is ignored by pydantic-settings and
would leave the production budget silently in force), and the raise exists only
in the scan layer, never in the base compose service or the chart.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml
from limits import parse

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_APP = _REPO_ROOT / "src" / "backend" / "app"
_SCAN_OVERRIDE = _REPO_ROOT / "docker-compose.security.override.yml"
_BASE_COMPOSE = _REPO_ROOT / "docker-compose.e2e.yml"
_CHART = _REPO_ROOT / "helm"

#: Highest per-route request rate measured from the scanner on this stack
#: (local ``zap-api-scan.py`` run, 2026-10-12: ``POST /api/v1/auth/register``).
#: A raised budget must clear it by an order of magnitude, or a longer scan or a
#: busier route brings the flip back.
_MEASURED_SCAN_PEAK_PER_MINUTE = 466
_REQUIRED_HEADROOM = 10

#: Raised in the scan override, with what was measured. Each of these routes is
#: anonymous (or answers before authentication), so the anonymous merge scan
#: reaches the limiter; the histograms are 25-70 anonymous requests in one minute
#: against the scan stack at the production budget.
_RAISED_FOR_THE_SCAN: dict[str, str] = {
    "rate_limit_email_change_confirm": (
        "#2248: /privacy/email-change/confirm and /revert, both unauthenticated. 25 requests "
        "answered {401: 10, 429: 15}; the 40018 finding on /revert and the one suppressed on "
        "/confirm are this flip."
    ),
    "rate_limit_auth": (
        "/auth/login, /auth/register, /auth/password-reset/*: unauthenticated. "
        "/password-reset/request answered {200: 20, 429: 5}; run 38123811759 recorded a 429 "
        "on /auth/login."
    ),
    "rate_limit_token_refresh": (
        "/auth/refresh runs the limiter before it reads the (absent) cookie: 62 of 123 scan "
        "requests in one minute were refused with 429 locally."
    ),
    "rate_limit_resend_verification": (
        "/auth/resend-verification is unauthenticated: 25 requests answered {202: 10, 429: 15}; "
        "the budget is hourly, so the flip lasts the rest of the scan."
    ),
    "rate_limit_calendar_feed": ("feed.ics is token-in-query and anonymous: 40 requests answered {404: 30, 429: 10}."),
    "rate_limit_calendar_feed_per_token": (
        "The per-token bucket of the same feed.ics route; ZAP repeats the original token value "
        "across its rules. With the per-address budget raised, 70 requests with one token "
        "answered {404: 60, 429: 10}."
    ),
    "rate_limit_health": (
        "/api/health is public and in the OpenAPI document: 70 requests answered {200: 60, 429: 10}."
    ),
}

#: Left at the production value in the scan stack, with the reason.
_LEFT_AT_PRODUCTION: dict[str, str] = {
    "rate_limit_device_pairing_redeem": (
        "tests/security/nuclei-templates/kamerplanter-device-pairing-bruteforce.yaml asserts the "
        "429 on this very stack (twelve guesses, the limit is ten). Raising it would leave only "
        "the lockout under test. The lockout answers 423 after five failures whatever the "
        "limit is (25 requests: {401: 5, 423: 5, 429: 15}), so the raise would not remove the "
        "flip either; zap-api-rules.tsv carries the approved row for its 40018 instance."
    ),
    # Authenticated routes: the anonymous merge scan is refused by the auth
    # dependency before slowapi counts (25 anonymous requests: 401 x 25 on each).
    "rate_limit_email_change": "Authenticated (POST /privacy/email-change): 401 x 25 anonymously.",
    "rate_limit_export_download": "Authenticated export downloads: 401 x 25 anonymously.",
    "rate_limit_tenant_import": "Authenticated platform-admin import: 401 x 25 anonymously.",
    "rate_limit_takeover": "Authenticated /system/takeover(-status): 401 x 25 anonymously.",
    "rate_limit_invitation_email": "Authenticated tenant invitation: 401 x 25 anonymously.",
    "rate_limit_notification_test": "Authenticated notification test send: 401 x 25 anonymously.",
    "rate_limit_export": "Authenticated /print routes, per account: 401 x 25 anonymously.",
    "rate_limit_care_events": (
        "Authenticated care-log writes (POST /t/{slug}/care-events and its supersede / void siblings): "
        "401 x 25 anonymously."
    ),
    "rate_limit_task_completion": (
        "Authenticated task completion (POST /t/{slug}/tasks/{key}/complete, …/tasks/batch/status, …/{key}/reopen): "
        "401 x 25 anonymously."
    ),
    "rate_limit_bed_actions": (
        "Authenticated bed actions (POST /t/{slug}/locations/{key}/quick-planting and …/clear): 401 x 25 anonymously."
    ),
    "rate_limit_plan_batch": (
        "Authenticated garden-plan writes (POST /t/{slug}/sites/{key}/plan/batch, PUT …/plan/boundary): "
        "401 x 25 anonymously."
    ),
    "rate_limit_upload": "Authenticated uploads (POST /t/{slug}/attachments): 401 x 40 anonymously.",
    "rate_limit_inference": (
        "Authenticated inference (POST /t/{slug}/diagnosis/analyze, /cv-diagnosis/diagnose): 401 x 40 anonymously."
    ),
}

#: A ``RATE_LIMIT_*`` setting applied by a route decorator, from either limiter.
_DECORATOR = re.compile(r"@(?:limiter|process_memory_limiter)\.limit\(\s*settings\.(rate_limit_[a-z_]+)")


def _limits_gating_a_route() -> set[str]:
    found: set[str] = set()
    for path in _APP.rglob("*.py"):
        found |= set(_DECORATOR.findall(path.read_text(encoding="utf-8")))
    return found


def _service_env(compose: Path, service: str) -> dict[str, str]:
    document = yaml.safe_load(compose.read_text(encoding="utf-8"))
    environment = document["services"][service].get("environment") or {}
    assert isinstance(environment, dict), f"{compose.name}: {service}.environment is not a mapping"
    return {str(key): str(value) for key, value in environment.items()}


def _scan_overrides() -> dict[str, str]:
    """The ``RATE_LIMIT_*`` the scan override sets on ``backend``, keyed by setting name."""
    return {
        key.lower(): value
        for key, value in _service_env(_SCAN_OVERRIDE, "backend").items()
        if key.startswith("RATE_LIMIT_")
    }


def _per_minute(limit: str) -> float:
    item = parse(limit)
    return item.amount * 60 / item.get_expiry()


def test_the_inventory_finds_something() -> None:
    """Loud when the decorator scan goes blind (renamed limiter, moved routers)."""
    found = _limits_gating_a_route()
    assert "rate_limit_email_change_confirm" in found, sorted(found)
    assert "rate_limit_health" in found, "the process-memory limiter in app/main.py was not seen"


@pytest.mark.parametrize("limit", sorted(_limits_gating_a_route()))
def test_every_route_limit_is_decided_for_the_scan_stack(limit: str) -> None:
    raised = limit in _scan_overrides()
    excused = limit in _LEFT_AT_PRODUCTION
    assert raised or excused, (
        f"`settings.{limit}` gates a route, but the DAST scan stack neither raises it nor "
        f"records why it stays at the production value. If the anonymous merge scan reaches "
        f"the limiter, add `{limit.upper()}` to backend.environment in "
        f"docker-compose.security.override.yml and to _RAISED_FOR_THE_SCAN here; otherwise add "
        f"it to _LEFT_AT_PRODUCTION with the measured reason (#2248)."
    )


def test_the_override_and_the_record_agree() -> None:
    """Every raise has its measured reason here, and every recorded raise is in force."""
    assert set(_scan_overrides()) == set(_RAISED_FOR_THE_SCAN)


def test_no_limit_is_both_raised_and_left() -> None:
    assert not set(_RAISED_FOR_THE_SCAN) & set(_LEFT_AT_PRODUCTION)


@pytest.mark.parametrize("limit", sorted(_LEFT_AT_PRODUCTION))
def test_a_left_limit_still_gates_a_route(limit: str) -> None:
    assert limit in _limits_gating_a_route(), f"`{limit}` gates no route any more; drop its entry"


@pytest.mark.parametrize("limit", sorted(_RAISED_FOR_THE_SCAN))
def test_a_raised_key_reaches_its_setting(limit: str) -> None:
    """A key pydantic-settings does not map is ignored, and the production budget stays live."""
    from app.config.settings import Settings

    assert limit in Settings.model_fields, f"{limit.upper()} names no Settings field"
    assert Settings(**{limit: _scan_overrides()[limit]}).model_dump()[limit] == _scan_overrides()[limit]


@pytest.mark.parametrize("limit", sorted(_RAISED_FOR_THE_SCAN))
def test_a_raised_budget_clears_the_measured_scan_peak(limit: str) -> None:
    floor = _MEASURED_SCAN_PEAK_PER_MINUTE * _REQUIRED_HEADROOM
    value = _scan_overrides()[limit]
    assert _per_minute(value) >= floor, f"{limit.upper()}={value} is below {floor}/minute"


def _yaml_names(node: object) -> set[str]:
    """Every mapping key and string scalar in a parsed YAML tree.

    An environment variable reaches a container either as a mapping key
    (``env: {RATE_LIMIT_AUTH: ...}``) or as a ``name:`` value; both are collected.
    Parsed, so a comment that mentions the key is not mistaken for setting it.
    """
    if isinstance(node, dict):
        names = {str(key) for key in node}
        for value in node.values():
            names |= _yaml_names(value)
        return names
    if isinstance(node, list):
        return set().union(*(_yaml_names(item) for item in node)) if node else set()
    return {node} if isinstance(node, str) else set()


def _chart_values_files() -> list[Path]:
    return sorted(path for path in _CHART.rglob("values*.yaml") if path.is_file())


def test_the_chart_values_are_found() -> None:
    """Non-vacuity for the check below: a moved chart would leave it comparing nothing."""
    assert any(path.name == "values.yaml" for path in _chart_values_files()), _CHART


@pytest.mark.parametrize("limit", sorted(_RAISED_FOR_THE_SCAN))
def test_the_raise_lives_in_the_scan_layer_only(limit: str) -> None:
    """Production keeps its budget: neither the base service nor the chart values set the key."""
    key = limit.upper()
    assert key not in _service_env(_BASE_COMPOSE, "backend"), f"{key} is set on the base backend service"
    chart_hits = [
        str(path.relative_to(_REPO_ROOT))
        for path in _chart_values_files()
        if any(key in _yaml_names(document) for document in yaml.safe_load_all(path.read_text(encoding="utf-8")))
    ]
    assert chart_hits == [], f"{key} is set in the chart values: {chart_hits}"


def test_the_production_default_stays_below_the_scan_budget() -> None:
    """The settings default is what production runs; the raise must not have leaked into it."""
    from app.config.settings import Settings

    for limit, value in _scan_overrides().items():
        default = Settings.model_fields[limit].default
        assert _per_minute(default) < _per_minute(value), f"{limit} default {default} is not below {value}"
