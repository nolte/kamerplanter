"""E2E test configuration — browser fixtures, screenshots, CLI options (NFR-008 §3.1, §3.4)."""

from __future__ import annotations

import os
import re
import shutil
from collections.abc import Callable, Generator
from datetime import datetime, timezone
from pathlib import Path

import pytest

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService

try:
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.firefox import GeckoDriverManager
except ImportError:
    ChromeDriverManager = None  # type: ignore[assignment,misc]
    GeckoDriverManager = None  # type: ignore[assignment,misc]


# ── Test identifiability: machine-selectable markers (NFR-008a) ────────────
# Two selection axes are derived automatically at collection time so that a
# code/feature change can be mapped to the affected tests without hand-marking
# 700+ test functions:
#
#   1. REQ axis   — a ``req<NNN>`` marker derived from the ``test_req<NNN>_*.py``
#                   file name (e.g. ``pytest -m req004``).
#   2. Feature axis — one or more semantic ``FEATURES`` markers a test module
#                   opts into via a module-level ``FEATURES`` tuple. This axis is
#                   cross-cutting to REQ IDs (e.g. ``nutrient`` spans several
#                   ``test_req004_*.py`` files; a core-lifecycle journey spans
#                   several REQs), enabling ``pytest -m watering``.
#
# In addition, the TC-ID declared in each test's docstring is lifted into the
# machine-readable ``user_properties`` channel (junit ``tc_id`` property) so
# downstream tooling (e.g. release-regression-scope) can consume it.

# Registered semantic feature markers. A test module opts in with, e.g.:
#   FEATURES = ("nutrient",)            # single feature
#   FEATURES = ("watering", "nutrient", "journey")  # cross-cutting journey
# Declaring a feature outside this set is a hard collection error (typo guard).
KNOWN_FEATURE_MARKERS: dict[str, str] = {
    "plant": "plant instance capture & lifecycle (Pflanzenerfassung)",
    "watering": "watering log / irrigation events (Gießen/Bewässerung)",
    "nutrient": "fertilizer, nutrient plans, feeding events, EC (Düngen/Dünger)",
    "harvest": "harvest & post-harvest management (Ernte)",
    "calendar": "calendar, sowing calendar, season overview (Aussaat/Kalender)",
    "journey": "core-lifecycle happy-path journey spanning multiple features/REQs",
}

# ``test_req004_watering_log.py`` -> ``004``
_REQ_FILE_PATTERN = re.compile(r"test_req(\d{3})_")
# File names that are core-lifecycle journeys get an implicit ``journey`` marker.
_JOURNEY_FILE_MARKER = "core_lifecycle_journey"
# Broad TC-ID scan for the machine-readable ``tc_id`` property. Deliberately
# wider than protocol_plugin's strict pattern so it also captures the test-local
# ID shapes in use (e.g. ``TC-REQ-004-W001``, ``TC-REQ-001-PI-005``, ``TC-001-080``).
_TC_ID_SCAN = re.compile(r"\bTC-(?:REQ-)?\d{3}-[A-Za-z0-9-]*\d[a-z]?\b")


def _req_marker_for(path_name: str) -> str | None:
    """Return the ``req<NNN>`` marker name for a ``test_req<NNN>_*.py`` file."""
    m = _REQ_FILE_PATTERN.search(path_name)
    return f"req{m.group(1)}" if m else None


def _declared_features(module: object) -> tuple[str, ...]:
    """Read the module-level ``FEATURES`` (tuple) or ``FEATURE`` (str) opt-in."""
    features = getattr(module, "FEATURES", None)
    if features is None:
        single = getattr(module, "FEATURE", None)
        features = (single,) if single else ()
    if isinstance(features, str):
        features = (features,)
    return tuple(features)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register custom CLI options for E2E tests (NFR-008 §3.1)."""
    parser.addoption(
        "--browser",
        default="chrome",
        choices=["chrome", "firefox"],
        help="Browser to run E2E tests (default: chrome)",
    )
    parser.addoption(
        "--base-url",
        default="http://localhost:5173",
        help="Base URL of the running application (default: http://localhost:5173)",
    )
    parser.addoption(
        "--generate-protocol",
        action="store_true",
        default=False,
        help="Generate a test protocol report (NFR-008 §4.4)",
    )
    parser.addoption(
        "--app-mode",
        default=os.environ.get("KAMERPLANTER_MODE", "full"),
        choices=["light", "full"],
        help="Application mode — 'light' skips auth-dependent tests (default: full)",
    )
    parser.addoption(
        "--resume",
        default=None,
        help="Resume a previous interrupted test run from checkpoint. "
             "Pass the test-reports/e2e/<timestamp>/ directory path.",
    )
    parser.addoption(
        "--device",
        default=os.environ.get("E2E_DEVICE", "desktop"),
        choices=["desktop", "mobile", "tablet"],
        help="Device profile for viewport/user-agent emulation (default: desktop)",
    )


# Import protocol_plugin — works both in-repo (as package) and in Docker (flat).
# pytest's conftest loader prevents normal import mechanisms from working
# reliably, so we use importlib with an explicit path as fallback.
import importlib.util as _ilu
import sys as _sys

_pp_path = Path(__file__).parent / "protocol_plugin.py"
_pp_spec = _ilu.spec_from_file_location("protocol_plugin", _pp_path)
_pp_mod = _ilu.module_from_spec(_pp_spec)  # type: ignore[arg-type]
_sys.modules["protocol_plugin"] = _pp_mod
_pp_spec.loader.exec_module(_pp_mod)  # type: ignore[union-attr]
ProtocolGenerator = _pp_mod.ProtocolGenerator
ScreenshotEntry = _pp_mod.ScreenshotEntry
TestResult = _pp_mod.TestResult

# ── Protocol plugin state ─────────────────────────────────────────────────
_protocol_generator: ProtocolGenerator | None = None  # type: ignore[assignment]
_protocol_output_dir: Path | None = None
_is_xdist_worker: bool = False
_junit_report_path: Path | None = None


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "requires_auth: mark test as requiring full auth mode (skipped in light mode)",
    )
    config.addinivalue_line(
        "markers",
        "smoke: mark test as part of the smoke test suite (core functionality)",
    )
    config.addinivalue_line(
        "markers",
        "core_crud: mark test as part of the core CRUD suite (species, cultivar, site CRUD for average users)",
    )
    config.addinivalue_line(
        "markers",
        "requires_desktop: mark test as requiring desktop viewport (skipped on mobile/tablet)",
    )

    # Register the feature-axis markers (semantic, cross-cutting to REQ IDs).
    for name, description in KNOWN_FEATURE_MARKERS.items():
        config.addinivalue_line("markers", f"{name}: {description}")

    # Register a ``req<NNN>`` marker for every REQ discovered from the test file
    # names. Registration must happen here (before collection) because under
    # ``--strict-markers`` even constructing ``pytest.mark.req004`` validates it.
    conftest_dir = Path(__file__).parent
    req_nums = sorted(
        {
            m.group(1)
            for f in conftest_dir.glob("test_req*.py")
            if (m := _REQ_FILE_PATTERN.search(f.name))
        }
    )
    for num in req_nums:
        config.addinivalue_line(
            "markers",
            f"req{num}: auto-derived REQ axis marker for test_req{num}_*.py "
            f"(machine-selectable via -m req{num})",
        )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Derive selection markers, then auto-skip by app mode, device and resume state."""
    # ── Selection axes: auto-derive REQ + feature markers (NFR-008a) ───────
    for item in items:
        req_marker = _req_marker_for(Path(item.location[0]).name)
        if req_marker:
            item.add_marker(getattr(pytest.mark, req_marker))

        module = getattr(item, "module", None)
        for feature in _declared_features(module):
            if feature not in KNOWN_FEATURE_MARKERS:
                raise pytest.UsageError(
                    f"{item.nodeid}: module declares unknown FEATURES entry "
                    f"{feature!r}; allowed values are "
                    f"{sorted(KNOWN_FEATURE_MARKERS)}"
                )
            item.add_marker(getattr(pytest.mark, feature))

        # Core-lifecycle journeys span multiple features/REQs — mark implicitly.
        if _JOURNEY_FILE_MARKER in Path(item.location[0]).name:
            item.add_marker(pytest.mark.journey)

    if config.getoption("--app-mode") == "light":
        skip_light = pytest.mark.skip(reason="requires full auth mode (running in light mode)")
        for item in items:
            if "requires_auth" in item.keywords:
                item.add_marker(skip_light)

    if config.getoption("--device") != "desktop":
        device = config.getoption("--device")
        skip_mobile = pytest.mark.skip(reason=f"requires desktop viewport (running on {device})")
        for item in items:
            if "requires_desktop" in item.keywords:
                item.add_marker(skip_mobile)

    # Resume mode: skip tests that already passed in a previous run
    resume_dir = config.getoption("--resume", default=None)
    if resume_dir:
        checkpoint = Path(resume_dir) / "checkpoint.jsonl"
        if checkpoint.exists():
            passed_nodeids = set()
            for r in _load_checkpoint(checkpoint):
                if r.outcome == "passed":
                    passed_nodeids.add(r.nodeid)
            if passed_nodeids:
                skip_resume = pytest.mark.skip(reason="already passed in previous run (--resume)")
                for item in items:
                    if item.nodeid in passed_nodeids:
                        item.add_marker(skip_resume)


@pytest.fixture(autouse=True)
def _record_tc_id(request: pytest.FixtureRequest, record_property: Callable) -> None:
    """Lift the docstring TC-ID into the machine-readable ``tc_id`` property.

    Makes each test's declared TC-ID (e.g. ``TC-REQ-004-W001``) consumable via
    the standard junit ``user_properties`` channel, in addition to the bespoke
    markdown protocol. No-op when the docstring carries no TC-ID.
    """
    doc = (getattr(request.function, "__doc__", None) or "").strip()
    if doc:
        match = _TC_ID_SCAN.search(doc.splitlines()[0])
        if match:
            record_property("tc_id", match.group(0))


# ── Global-preference serialization across xdist workers ──────────────────
# In light mode the experience level is stored server-side on the singleton
# system user (REQ-021 "serverseitig", REQ-027 "User-Preference am System-User")
# and is therefore global, mutable state shared by every xdist worker. Tests
# that mutate it (onboarding wizard step 1, the account-settings toggle) or
# assert UI gating derived from it (nav tiering, dialog field visibility) must
# not overlap across workers, or the level flips mid-assertion (finding F-8,
# .resume/e2e-selenium/robustness-audit.md). ``--dist=loadfile`` already
# serializes within a file; this advisory file lock serializes the affected
# files against each other. All workers run in the same container, so an
# fcntl lock on a shared path is a correct inter-process mutex.
_GLOBAL_PREFERENCE_MODULES = {
    "test_req020_onboarding_steps",
    "test_req020_onboarding_wizard",
    "test_req021_experience_level",
}

_GLOBAL_PREFERENCE_LOCK_PATH = "/tmp/kamerplanter-e2e-global-preference.lock"


@pytest.fixture(autouse=True)
def _serialize_global_preference_mutators(
    request: pytest.FixtureRequest,
) -> Generator[None, None, None]:
    """Hold an inter-worker lock for tests touching the global experience level."""
    module = getattr(request, "module", None)
    module_name = getattr(module, "__name__", "").rpartition(".")[-1]
    if module_name not in _GLOBAL_PREFERENCE_MODULES:
        yield
        return

    import fcntl

    with open(_GLOBAL_PREFERENCE_LOCK_PATH, "w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock_file, fcntl.LOCK_UN)


# ── Device profiles for responsive testing ────────────────────────────────
# Each profile defines viewport dimensions, device scale factor, touch support,
# and a user-agent string.  Used by the ``browser`` fixture to configure
# Chrome DevTools Protocol mobile emulation.
DEVICE_PROFILES: dict[str, dict] = {
    "desktop": {
        "width": 1920,
        "height": 1080,
        "deviceScaleFactor": 1,
        "mobile": False,
        "userAgent": "",  # empty = keep default Chrome UA
    },
    "mobile": {
        # iPhone 14 Pro equivalent
        "width": 393,
        "height": 852,
        "deviceScaleFactor": 3,
        "mobile": True,
        "userAgent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.0 Mobile/15E148 Safari/604.1"
        ),
    },
    "tablet": {
        # iPad Air equivalent
        "width": 820,
        "height": 1180,
        "deviceScaleFactor": 2,
        "mobile": True,
        "userAgent": (
            "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.0 Mobile/15E148 Safari/604.1"
        ),
    },
}


@pytest.fixture(scope="session")
def app_mode(request: pytest.FixtureRequest) -> str:
    """Return the current app mode ('light' or 'full')."""
    return request.config.getoption("--app-mode")


@pytest.fixture(scope="session")
def device_profile(request: pytest.FixtureRequest) -> dict:
    """Return the active device profile dict (viewport, UA, scale, touch)."""
    name = request.config.getoption("--device")
    return {**DEVICE_PROFILES[name], "name": name}


@pytest.fixture(scope="session")
def base_url(request: pytest.FixtureRequest) -> str:
    """Return the base URL for the application under test.

    ``E2E_BASE_URL`` env var takes precedence (set by docker-compose.e2e.yml).
    """
    return os.environ.get("E2E_BASE_URL") or request.config.getoption("--base-url")


# ── Demo user credentials (shared between seed fixture and auth tests) ────
# Light mode uses demo@kamerplanter.local (inserted directly into DB, no validation).
# Full mode registers via API with Pydantic EmailStr which rejects .local domains.
DEMO_EMAIL_LIGHT = "demo@kamerplanter.local"
DEMO_EMAIL_FULL = "demo@kamerplanter.example"
DEMO_PASSWORD = "demo-passwort-2024"
DEMO_DISPLAY_NAME = "Mein Garten"


def _api_helpers(auth_token: str | None = None):
    """Return (post, get) helper functions with optional Bearer auth."""
    import json
    import urllib.request
    import urllib.error

    def _headers() -> dict[str, str]:
        h: dict[str, str] = {"Content-Type": "application/json"}
        if auth_token:
            h["Authorization"] = f"Bearer {auth_token}"
        return h

    def _post(url: str, data: dict) -> tuple[int, dict]:
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, headers=_headers())
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read())
            except Exception:
                err_body = {}
            return e.code, err_body

    def _get(url: str) -> tuple[int, list | dict]:
        req = urllib.request.Request(url, headers=_headers())
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read())
            except Exception:
                err_body = []
            return e.code, err_body

    return _post, _get


# All toggleable (non-core) module keys from the frontend module catalog
# (src/frontend/src/config/moduleCatalog.ts). REQ-042 introduced the ModuleGuard,
# which hides modules whose defaultLevel exceeds the tenant's experience_level
# (a fresh light-mode tenant defaults to BEGINNER). Advanced pages (master_data,
# nutrition, harvest, ipm, tanks, substrates, runs, companion, ...) therefore
# render a "Dieses Modul ist ausgeblendet" placeholder (data-testid
# 'module-guard-hint') instead of the page, and every E2E page-object times out
# waiting for the page marker. Writing an explicit 'enabled' override per module
# short-circuits the experience-level check (useModuleVisibility.ts) and restores
# the pre-REQ-042 assumption that all pages are reachable. Core keys
# (dashboard/plants/locations/settings/onboarding) are validated-away by the
# backend, so listing them is harmless — we only send the toggleable set.
_E2E_TOGGLEABLE_MODULES = (
    "care", "calendar", "watering", "tasks", "nutrition", "tanks", "aquaponics",
    "substrates", "calculators", "ipm", "harvest", "post_harvest", "runs",
    "propagation", "master_data", "companion", "sensors", "automation",
    "smart_home", "ai",
)


def _api_patch(url: str, data: dict, auth_token: str | None = None) -> tuple[int, dict]:
    """Send a PATCH with optional Bearer auth (light mode needs none)."""
    import json
    import urllib.error
    import urllib.request

    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    req = urllib.request.Request(
        url, data=json.dumps(data).encode(), headers=headers, method="PATCH"
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}


def _api_delete(url: str, auth_token: str | None = None) -> int:
    """Send a DELETE with optional Bearer auth; return the status code."""
    import urllib.error
    import urllib.request

    headers = {"Content-Type": "application/json"}
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    req = urllib.request.Request(url, headers=headers, method="DELETE")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code


def _register_and_login(api_base: str) -> tuple[str, str]:
    """Register the demo user (idempotent) and login to get a JWT token.

    Returns (access_token, tenant_slug).
    """
    _post, _get = _api_helpers()

    # Register — idempotent: returns 201 for new, 201 for existing (SEC-H-009)
    _post(f"{api_base}/api/v1/auth/register", {
        "email": DEMO_EMAIL_FULL,
        "password": DEMO_PASSWORD,
        "display_name": DEMO_DISPLAY_NAME,
    })

    # Login to get JWT
    status, resp = _post(f"{api_base}/api/v1/auth/login", {
        "email": DEMO_EMAIL_FULL,
        "password": DEMO_PASSWORD,
    })
    if status != 200 or "access_token" not in resp:
        raise RuntimeError(f"E2E seed login failed: status={status}, resp={resp}")

    token = resp["access_token"]

    # Discover tenant slug from user's tenants
    _, _get_auth = _api_helpers(token)
    _, tenants = _get_auth(f"{api_base}/api/v1/tenants/")
    if not isinstance(tenants, list) or not tenants:
        raise RuntimeError(f"E2E seed: no tenants found after registration: {tenants}")

    tenant_slug = tenants[0]["slug"]
    return token, tenant_slug


@pytest.fixture(scope="session", autouse=True)
def e2e_seed_data(base_url: str, app_mode: str) -> dict:
    """Create seed data (Site + Location) via backend API for E2E tests.

    Runs once per session.
    - Light mode: uses the system tenant slug 'mein-garten' (no auth needed).
    - Full mode: registers demo user, logs in to get JWT, discovers tenant slug.
    """
    api_base = base_url.rstrip("/")
    result: dict = {}

    # In full mode, register + login to get auth token and tenant slug
    if app_mode == "full":
        token, tenant_slug = _register_and_login(api_base)
        result["access_token"] = token
        result["tenant_slug"] = tenant_slug
        _post, _get = _api_helpers(token)
    else:
        tenant_slug = "mein-garten"
        result["tenant_slug"] = tenant_slug
        _post, _get = _api_helpers()

    api = f"{api_base}/api/v1/t/{tenant_slug}"

    SITE_NAME = "E2E-Sonnengarten"
    LOCATION_NAME = "E2E-Wohnzimmer"
    SLOT_LOCATION_NAME = "E2E-Gewaechshaus"

    try:
        # ── Enable all toggleable modules server-side (REQ-042, FULL mode) ──
        # Full mode reads module_visibility from the server user_preferences.
        # (Light mode ignores the server value and uses the localStorage key
        # 'kp-module-visibility' seeded in the browser fixture instead.)
        # Idempotent: PATCH replaces the whole map.
        mv_status, _ = _api_patch(
            f"{api}/user-preferences",
            {"module_visibility": {k: "enabled" for k in _E2E_TOGGLEABLE_MODULES}},
            result.get("access_token"),
        )
        result["module_visibility_status"] = mv_status

        list_status, sites = _get(f"{api}/sites")
        existing_site = None
        if list_status == 200 and isinstance(sites, list):
            existing_site = next((s for s in sites if s.get("name") == SITE_NAME), None)

        if existing_site:
            result["site_key"] = existing_site["key"]
            tree_status, tree = _get(f"{api}/locations/tree?site_key={existing_site['key']}")
            if tree_status == 200 and isinstance(tree, list) and tree:
                result["location_key"] = tree[0]["key"]
        else:
            status, site = _post(f"{api}/sites", {
                "name": SITE_NAME,
                "description": "Automatisch angelegt fuer E2E-Tests — Balkon und Wohnzimmer",
                "climate_zone": "8a",
                "total_area_m2": 45,
                "timezone": "Europe/Berlin",
            })
            if status == 201:
                result["site_key"] = site["key"]
                loc_status, loc = _post(f"{api}/locations", {
                    "name": LOCATION_NAME,
                    "site_key": site["key"],
                    "location_type_key": "room",
                    "area_m2": 18,
                })
                if loc_status == 201:
                    result["location_key"] = loc["key"]
                _post(f"{api}/locations", {
                    "name": SLOT_LOCATION_NAME,
                    "site_key": site["key"],
                    "location_type_key": "greenhouse",
                    "area_m2": 12,
                })

        # ── Seed tasks for task-queue tests (REQ-006) ────────────────────
        # Find-or-create: this session fixture runs once per xdist worker
        # (4x by default). An unconditional POST here would race those workers
        # into recreating the same three named tasks four times, leaving
        # duplicate "E2E: ..." rows in the queue and making any
        # ``keys[0]``-based lookup non-deterministic (the original failure
        # mode behind the REQ-030 source→notification feedback tests).
        # Checking for an existing pending/in_progress task of the same name
        # first converges every worker onto a single seeded set instead.
        from datetime import datetime as _dt, timedelta as _td, timezone as _tz

        _now = _dt.now(_tz.utc)
        _seed_tasks = [
            {
                "name": "E2E: Water indoor plants",
                "name_de": "E2E: Zimmerpflanzen gießen",
                "category": "care_reminder",
                "priority": "high",
                "due_date": (_now - _td(hours=2)).isoformat(),
                "instruction_de": "Alle Zimmerpflanzen im Wohnzimmer gießen",
            },
            {
                "name": "E2E: Check pH levels",
                "name_de": "E2E: pH-Werte prüfen",
                "category": "observation",
                "priority": "medium",
                "due_date": _now.isoformat(),
                "instruction_de": "pH-Werte im Nährstofftank messen und dokumentieren",
            },
            {
                "name": "E2E: Prune tomato suckers",
                "name_de": "E2E: Tomatentriebe ausgeizen",
                "category": "maintenance",
                "priority": "low",
                "due_date": (_now + _td(days=1)).isoformat(),
                "instruction_de": "Seitentriebe der Tomatenpflanzen entfernen",
            },
        ]
        _tasks_list_status, _existing_tasks = _get(f"{api}/tasks?limit=500")
        _existing_task_names: set = set()
        if _tasks_list_status == 200 and isinstance(_existing_tasks, list):
            _existing_task_names = {
                t.get("name")
                for t in _existing_tasks
                if t.get("status") in ("pending", "in_progress")
            }
        for task_data in _seed_tasks:
            if task_data["name"] in _existing_task_names:
                continue
            status, resp = _post(f"{api}/tasks", task_data)
            if status == 201:
                result.setdefault("task_keys", []).append(resp.get("key"))

        # ── Trigger care reminder generation (REQ-022) ───────────────
        # This creates care tasks for any plant instances that have care
        # profiles, so the pflege dashboard tests have data to work with.
        _post(f"{api}/tasks/generate-care-reminders", {})

        # Skip onboarding wizard so the browser lands on /dashboard
        _post(f"{api}/onboarding/skip", {})
    except Exception as exc:
        result["error"] = str(exc)

    # The result dict carries the demo account's live JWT in full mode — never
    # write it to a report file that a broadened artifact upload could publish
    # (SEC-006).
    from ._seed_log import format_seed_log

    seed_log = Path("test-reports/e2e_seed_data.log")
    seed_log.parent.mkdir(parents=True, exist_ok=True)
    seed_log.write_text(format_seed_log(api, app_mode, result))

    return result


def _fresh_access_token(e2e_seed_data: dict, base_url: str) -> str | None:
    """Return a currently-valid access token for API helpers.

    The session-scoped seed token expires after the JWT access TTL (15 min) —
    long before late-scheduled tests run, so helpers that reuse it fail with
    'Token has expired'. Full mode: re-login with the demo credentials and
    cache the token for 10 minutes. Light mode (no seed token): ``None``.
    """
    if not e2e_seed_data.get("access_token"):
        return None
    import time as _time

    cached = e2e_seed_data.get("_fresh_token")
    if cached and _time.time() - cached[1] < 600:
        return cached[0]
    _post, _ = _api_helpers()
    status, resp = _post(
        f"{base_url.rstrip('/')}/api/v1/auth/login",
        {"email": DEMO_EMAIL_FULL, "password": DEMO_PASSWORD},
    )
    token = resp.get("access_token") if status == 200 else None
    if not token:
        return e2e_seed_data.get("access_token")
    e2e_seed_data["_fresh_token"] = (token, _time.time())
    return token


def _e2e_api_post(e2e_seed_data: dict, base_url: str, path: str, data: dict | None = None) -> tuple[int, dict]:
    """Make an authenticated POST to a tenant-scoped API endpoint.

    Helper for test fixtures that need to call the backend API (e.g. resetting
    onboarding state).  Works in both light and full mode.
    """
    token = _fresh_access_token(e2e_seed_data, base_url)
    slug = e2e_seed_data.get("tenant_slug", "mein-garten")
    _post, _ = _api_helpers(token)
    url = f"{base_url.rstrip('/')}/api/v1/t/{slug}/{path.lstrip('/')}"
    return _post(url, data or {})


# NOTE: deliberately no ``--force-prefers-reduced-motion`` here. It was added to
# close the MUI option-mis-click race and did not: that race is driven by
# JavaScript layout effects (``Menu`` scrolling its paper to the selected item,
# ``Popover`` clamping upward), which no animation setting removes -- it is now
# closed coordinate-independently in ``BasePage.click_menu_option``. What the
# flag *did* do was switch the application under test into its reduced-motion
# branch globally (``theme.ts``: every transition collapsed to 0.01 ms), so the
# suite stopped measuring the UI real users get -- and it removed the drawer
# slide that had been masking a latent page-object defect (nav items clipped by
# the sidebar's scroll container), turning two green tests red.


@pytest.fixture(scope="function")
def browser(request: pytest.FixtureRequest, e2e_seed_data: dict, device_profile: dict) -> webdriver.Remote:
    """Create a fresh headless browser session per test (NFR-008 §3.1).

    Depends on ``e2e_seed_data`` to ensure the demo user exists before
    attempting browser login in full mode.

    Function-scope (one Remote-WebDriver session per test) instead of the
    cheaper session-scope (one per xdist worker) is required because the
    REQ-020/REQ-021 wizard tests interact via shared backend tenant state.
    On session-scope a single test that leaves the Wizard in a bad state
    (e.g. ``OnboardingState.skipped=True`` after the seed-fixture's
    ``/onboarding/skip`` call) cascades into every subsequent test on the
    same xdist worker — observed as 14–17 failures all attributed to one
    worker (gw3) while the other workers stayed clean. Per-test browser
    sessions guarantee a clean cookie/localStorage/sessionStorage starting
    point for every test; combined with the per-test
    ``OnboardingWizardPage._reset_wizard_via_api`` this yields
    deterministic state.

    Cost: one extra Remote WebDriver allocation per test (~1–2 s on
    Selenium Grid). At ~450 executed tests this adds ~10–15 min to a full
    suite run, parallelised across 4 xdist workers.

    When ``SELENIUM_REMOTE_URL`` is set (e.g. in docker-compose.e2e.yml),
    a Remote WebDriver connecting to Selenium Grid is used.  Otherwise a
    local browser is started as before.

    The ``--device`` option controls viewport size and mobile emulation
    via Chrome DevTools Protocol.
    """
    browser_name = request.config.getoption("--browser")
    remote_url = os.environ.get("SELENIUM_REMOTE_URL")
    dev = device_profile
    win_size = f"{dev['width']},{dev['height']}"

    if remote_url:
        # ── Remote WebDriver (Selenium Grid / Docker) ──────────
        if browser_name == "firefox":
            options = webdriver.FirefoxOptions()
            options.add_argument("--headless")
            options.add_argument(f"--width={dev['width']}")
            options.add_argument(f"--height={dev['height']}")
            options.set_preference("intl.accept_languages", "de-DE,de")
        else:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument(f"--window-size={win_size}")
            options.add_argument("--lang=de-DE")
        driver = webdriver.Remote(
            command_executor=remote_url,
            options=options,
        )
        # Enable local file uploads to remote Selenium Grid nodes.
        # Without this, send_keys(file_path) on file inputs fails because
        # the file only exists on the test host, not inside the Grid node.
        from selenium.webdriver.remote.file_detector import LocalFileDetector

        driver.file_detector = LocalFileDetector()
    elif browser_name == "firefox":
        # ── Local Firefox ──────────────────────────────────────
        options = webdriver.FirefoxOptions()
        options.add_argument("--headless")
        options.add_argument(f"--width={dev['width']}")
        options.add_argument(f"--height={dev['height']}")
        gecko_path = shutil.which("geckodriver")
        if gecko_path:
            service = FirefoxService(gecko_path)
        elif GeckoDriverManager is not None:
            service = FirefoxService(GeckoDriverManager().install())
        else:
            service = FirefoxService()
        driver = webdriver.Firefox(service=service, options=options)
    else:
        # ── Local Chrome ───────────────────────────────────────
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--remote-debugging-port=0")
        options.add_argument(f"--window-size={win_size}")
        # Support snap-installed Chromium (Ubuntu)
        chromium_snap = shutil.which("chromium-browser") or shutil.which("chromium")
        if chromium_snap and not shutil.which("google-chrome"):
            options.binary_location = chromium_snap
        chromedriver_path = (
            shutil.which("chromedriver")
            or shutil.which("chromium.chromedriver")
        )
        if chromedriver_path:
            service = ChromeService(chromedriver_path)
        elif ChromeDriverManager is not None:
            service = ChromeService(ChromeDriverManager().install())
        else:
            service = ChromeService()
        driver = webdriver.Chrome(service=service, options=options)

    # ── Apply device emulation via CDP (Chrome only) ──────────────────
    if dev["name"] != "desktop":
        try:
            driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
                "width": dev["width"],
                "height": dev["height"],
                "deviceScaleFactor": dev["deviceScaleFactor"],
                "mobile": dev["mobile"],
            })
            if dev["userAgent"]:
                driver.execute_cdp_cmd("Emulation.setUserAgentOverride", {
                    "userAgent": dev["userAgent"],
                })
            driver.execute_cdp_cmd("Emulation.setTouchEmulationEnabled", {
                "enabled": True,
            })
        except Exception:
            # CDP not available (Firefox, older grids) — viewport size is
            # already set via window-size argument, so tests still run at
            # the correct dimensions, just without touch/UA emulation.
            pass

    # Export browser + device name for the protocol plugin metadata
    os.environ["E2E_BROWSER"] = browser_name
    os.environ["E2E_DEVICE"] = dev["name"]

    # Keep the implicit wait small: elements that genuinely need waiting use
    # explicit WebDriverWait (15 s), while every *absence* check
    # (find_elements on a missing element, is_present, locator-fallback misses)
    # otherwise blocks for the full implicit timeout. At 10 s those misses
    # dominated the per-test cost; 3 s still covers real element appearances on
    # a loaded page. (Mixing implicit + explicit waits is a known anti-pattern;
    # a follow-up should move to 0 once all bare find_element calls are on
    # explicit waits.)
    driver.implicitly_wait(3)

    # Set German locale in localStorage so i18next picks it up (detection
    # order: localStorage → navigator).  We need to navigate to the origin
    # first so that localStorage is bound to the correct domain.
    url = os.environ.get("E2E_BASE_URL") or request.config.getoption("--base-url")
    driver.get(url)
    driver.execute_script(
        "window.localStorage.setItem('kamerplanter-lang', 'de');"
    )

    # ── Enable all toggleable modules (REQ-042 ModuleGuard) ──────────────
    # In light mode the frontend treats localStorage key 'kp-module-visibility'
    # as the source of truth for module overrides and OVERWRITES the server value
    # on every fetch (userPreferencesSlice.fetchPreferences.fulfilled). A fresh
    # browser has no overrides, so advanced pages (stammdaten/düngung/harvest/ipm/
    # tanks/substrates/runs/companion ...) render the "module hidden" placeholder
    # and every page-object times out. Seed the localStorage override map here so
    # the next in-test navigation reads it. (Full mode ignores localStorage and
    # uses the server PATCH done in e2e_seed_data instead — setting this is a
    # harmless no-op there.)
    import json as _json

    driver.execute_script(
        "window.localStorage.setItem('kp-module-visibility', arguments[0]);",
        _json.dumps({k: "enabled" for k in _E2E_TOGGLEABLE_MODULES}),
    )

    # In full mode, log the browser in so non-auth tests can access the app.
    # Auth-specific tests manage their own login/logout state.
    if request.config.getoption("--app-mode") == "full":
        _browser_login(driver, url)

    yield driver
    driver.quit()


def _browser_login(driver: webdriver.Remote, base_url: str) -> None:
    """Log into the app via the browser UI (full mode only).

    Navigates to /login, fills credentials, submits, and waits for
    redirect to /dashboard or /onboarding.
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    driver.get(f"{base_url}/login")
    wait = WebDriverWait(driver, 15)

    email_input = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "input[type='email']")
    ))
    email_input.clear()
    email_input.send_keys(DEMO_EMAIL_FULL)

    password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    password_input.clear()
    password_input.send_keys(DEMO_PASSWORD)

    submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_btn.click()

    # Wait for successful redirect (dashboard or onboarding)
    wait.until(lambda d: "/login" not in d.current_url)


@pytest.fixture(autouse=True)
def ensure_authenticated(
    request: pytest.FixtureRequest,
    browser: webdriver.Remote,
    base_url: str,
) -> None:
    """Re-login the browser before each test if auth state was lost (full mode only).

    Auth tests (requires_auth) that deliberately log out and test login flows
    can break the session for subsequent non-auth tests on the same xdist worker.
    This fixture detects a lost session by checking for the ``kp_refresh`` cookie
    and re-logs in if needed.
    """
    if request.config.getoption("--app-mode") != "full":
        return

    # Skip for tests that explicitly manage their own auth state
    if "requires_auth" in request.node.keywords:
        return

    # Check if the browser ended up on the login page (= session lost).
    # We cannot reliably check the kp_refresh cookie because it is scoped
    # to path=/api/v1/auth and Selenium only returns cookies for the
    # current page's path.
    current = browser.current_url
    if "/login" not in current:
        return

    # Session lost — re-login
    _browser_login(browser, base_url)


@pytest.fixture(scope="session")
def screenshot_dir(request: pytest.FixtureRequest) -> Path:
    """Return the screenshot directory, shared with protocol_plugin (NFR-008 §4.2).

    When ``--generate-protocol`` is active the directory is provided by the
    protocol plugin so that screenshots and the Markdown report live in the
    same timestamped folder.  Otherwise a standalone directory is created.
    """
    protocol_dir: Path | None = getattr(
        request.config, "_protocol_output_dir", None
    )
    if protocol_dir is not None:
        path = protocol_dir / "screenshots"
    else:
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = Path("test-reports") / "e2e" / timestamp / "screenshots"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cdp_full_page_screenshot(driver: webdriver.Remote, filepath: Path) -> None:
    """Capture a full-page screenshot via Chrome DevTools Protocol.

    Falls back to the standard Selenium screenshot if CDP is not available
    (e.g. Firefox or older drivers).
    """
    import base64

    try:
        result = driver.execute_cdp_cmd(
            "Page.captureScreenshot",
            {"captureBeyondViewport": True},
        )
        filepath.write_bytes(base64.b64decode(result["data"]))
    except Exception:
        # Fallback for non-Chrome browsers or remote grids without CDP
        driver.save_screenshot(str(filepath))


@pytest.fixture(autouse=True)
def screenshot(
    request: pytest.FixtureRequest,
    browser: webdriver.Remote,
    screenshot_dir: Path,
):
    """Provide a callable ``screenshot(name, description)`` for explicit checkpoints.

    This fixture is autouse — it always runs to ensure:
    1. ``request.node._screenshot_capture`` is available (legacy pattern)
    2. Failure screenshots are captured automatically (NFR-008 §3.4)

    Usage in tests — new style (preferred)::

        def test_dashboard_loads(self, screenshot, dashboard):
            dashboard.open()
            screenshot("001_dashboard-overview", "Dashboard after initial load")

    Usage in tests — legacy style (still supported)::

        def test_tank_list(self, request, tank_list):
            capture = request.node._screenshot_capture
            capture("req014_001_tank_list")
    """
    def _capture(name: str, description: str = "") -> Path:
        filename = f"{name}.png"
        filepath = screenshot_dir / filename
        _cdp_full_page_screenshot(browser, filepath)

        # Register with protocol plugin for report generation
        screenshots_list = getattr(request.node, "_protocol_screenshots", [])
        screenshots_list.append(
            ScreenshotEntry(
                filename=filename,
                description=description or name.replace("_", " "),
                test_nodeid=request.node.nodeid,
            )
        )
        request.node._protocol_screenshots = screenshots_list  # type: ignore[attr-defined]
        return filepath

    # Make capture available via both the fixture return value and the node attribute
    request.node._screenshot_capture = _capture  # type: ignore[attr-defined]

    yield _capture

    # After test — capture on failure, and on an *expected* failure too.
    # An xfail(strict=False) that actually fails is reported as ``skipped``
    # (with ``wasxfail`` set), so the plain ``report.failed`` branch left every
    # xfail-marked test without a single artefact: no failure screenshot, no
    # traceback, nothing to triage the marker against. Reconstructing why
    # TC-REQ-020-032 xfailed took inferring the stop point from which
    # checkpoint screenshots existed.
    report = getattr(request.node, "_report", None)
    if report is not None:
        test_name = request.node.name.replace("[", "_").replace("]", "_")
        if report.failed:
            _capture(
                f"FAILURE_{test_name}",
                f"Automatischer Screenshot nach Fehler in {test_name}",
            )
        elif report.skipped and getattr(report, "wasxfail", None) is not None:
            _capture(
                f"XFAIL_{test_name}",
                f"Automatischer Screenshot nach erwartetem Fehlschlag in {test_name}",
            )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item) -> None:
    """Attach the test report to the item node for the screenshot fixture (NFR-008 §3.4).

    Also record results for the protocol generator.
    """
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        item._report = report  # type: ignore[attr-defined]

        # ── Protocol recording ────────────────────────────────────
        if _protocol_generator is not None:
            outcome_str = "passed" if not report.failed else "failed"
            if report.skipped:
                outcome_str = "skipped"
            # ``longrepr`` survives pytest's xfail downgrade (skipping.py only
            # rewrites ``outcome``), so recording it for an expected failure
            # puts the actual traceback into ``checkpoint.jsonl`` instead of
            # discarding the only machine-readable evidence an xfail produces.
            keep_longrepr = report.failed or getattr(report, "wasxfail", None) is not None
            message = str(report.longrepr) if keep_longrepr and report.longrepr else ""
            docstring = ""
            if item.obj and item.obj.__doc__:
                docstring = item.obj.__doc__.strip().split("\n")[0]
            screenshots: list[ScreenshotEntry] = getattr(
                item, "_protocol_screenshots", []
            )
            result = TestResult(
                nodeid=item.nodeid,
                outcome=outcome_str,
                duration=report.duration,
                message=message,
                docstring=docstring,
                screenshots=screenshots,
            )
            _protocol_generator.add_result(result)
            # Incremental checkpoint — append to JSONL so partial results
            # survive interrupts (Ctrl+C, crash, timeout).
            _write_checkpoint(result)


def _write_checkpoint(result: TestResult) -> None:
    """Append a single test result to the JSONL checkpoint file.

    Each line is a self-contained JSON object.  On interrupt the file
    contains all results completed so far and can be used to:
    1. Generate a partial protocol (``--generate-protocol``)
    2. Resume a test run (``--resume``)
    """
    import json
    if _protocol_output_dir is None:
        return
    checkpoint = _protocol_output_dir / "checkpoint.jsonl"
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "nodeid": result.nodeid,
        "outcome": result.outcome,
        "duration": result.duration,
        "message": result.message[:500] if result.message else "",
        "docstring": result.docstring,
        "screenshots": [
            {"filename": s.filename, "description": s.description}
            for s in result.screenshots
        ],
    }
    with checkpoint.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _load_checkpoint(checkpoint_path: Path) -> list[TestResult]:
    """Load results from a JSONL checkpoint file."""
    import json
    results: list[TestResult] = []
    if not checkpoint_path.exists():
        return results
    for line in checkpoint_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        entry = json.loads(line)
        results.append(TestResult(
            nodeid=entry["nodeid"],
            outcome=entry["outcome"],
            duration=entry.get("duration", 0.0),
            message=entry.get("message", ""),
            docstring=entry.get("docstring", ""),
            screenshots=[
                ScreenshotEntry(
                    filename=s["filename"],
                    description=s["description"],
                    test_nodeid=entry["nodeid"],
                )
                for s in entry.get("screenshots", [])
            ],
        ))
    return results


def _generate_protocol_safe() -> None:
    """Generate the protocol from whatever results exist — safe to call on interrupt."""
    if _is_xdist_worker:
        # Workers only append to the shared checkpoint.jsonl; the controller
        # generates the single protocol after every worker has finished.
        # A per-worker protokoll.md would hold only that worker's subset and
        # overwrite the aggregate.
        return
    if _protocol_generator is not None and _protocol_output_dir is not None:
        try:
            if not _protocol_generator.results:
                # Under xdist the controller executes no tests itself — its
                # results come from the checkpoint the workers appended to.
                checkpoint = _protocol_output_dir / "checkpoint.jsonl"
                if checkpoint.exists():
                    _protocol_generator.results = _load_checkpoint(checkpoint)
            path = _protocol_generator.generate(_protocol_output_dir)
            print(f"\nTestprotokoll geschrieben: {path}")
        except Exception as exc:
            print(f"\nWarnung: Protokoll-Generierung fehlgeschlagen: {exc}")


def _relocate_junit_report() -> None:
    """Move the finished JUnit XML into the run's timestamped report dir.

    ``--junitxml`` needs a static path known at pytest-invocation time (it is set
    in the compose entrypoint), whereas the protocol report directory is created
    dynamically per run in :func:`pytest_sessionstart`. Relocating the merged XML
    into that directory lets ``scripts/run-e2e.sh``'s existing
    ``cp -r <container-report-dir>/*`` move carry it into the run's host report
    dir alongside ``protokoll.md`` — no extra copy logic required.

    Controller-only: xdist workers never register the built-in junit plugin, so
    only the controller writes (and therefore relocates) the single merged file.
    Registered via ``atexit`` so it runs after the junit plugin's
    ``pytest_sessionfinish`` has written the file.
    """
    if _is_xdist_worker:
        return
    if _junit_report_path is None or _protocol_output_dir is None:
        return
    source = _junit_report_path
    if not source.exists():
        return
    dest = _protocol_output_dir / source.name
    try:
        if source.resolve() == dest.resolve():
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(dest))
        print(f"\nJUnit-Report verschoben: {dest}")
    except Exception as exc:
        print(f"\nWarnung: JUnit-Report-Verschiebung fehlgeschlagen: {exc}")


@pytest.hookimpl(optionalhook=True)
def pytest_configure_node(node) -> None:  # type: ignore[no-untyped-def]
    """xdist (controller side): hand the shared protocol dir to each worker.

    Without this every worker creates its own timestamped report dir and
    writes a fragmentary protokoll.md, while the controller (which executes
    no tests) writes an empty one.
    """
    if _protocol_output_dir is not None:
        node.workerinput["protocol_output_dir"] = str(_protocol_output_dir)


def pytest_sessionstart(session: pytest.Session) -> None:
    """Initialize protocol generator if --generate-protocol is active."""
    import atexit
    global _protocol_generator, _protocol_output_dir, _is_xdist_worker
    global _junit_report_path

    workerinput = getattr(session.config, "workerinput", None)
    _is_xdist_worker = workerinput is not None

    if session.config.getoption("--generate-protocol", default=False):
        resume_dir = session.config.getoption("--resume", default=None)
        shared_dir = (workerinput or {}).get("protocol_output_dir")
        if shared_dir:
            # xdist worker — write checkpoint/screenshots into the
            # controller's directory instead of a fresh timestamped one.
            _protocol_output_dir = Path(shared_dir)
            _protocol_generator = ProtocolGenerator()
            _protocol_generator.start_time = datetime.now(tz=timezone.utc)
        elif resume_dir:
            # Resume mode — load checkpoint from a previous interrupted run
            resume_path = Path(resume_dir)
            _protocol_output_dir = resume_path
            _protocol_generator = ProtocolGenerator()
            checkpoint = resume_path / "checkpoint.jsonl"
            if checkpoint.exists():
                loaded = _load_checkpoint(checkpoint)
                _protocol_generator.results = loaded
                _protocol_generator.start_time = datetime.now(tz=timezone.utc)
                print(f"\nFortgesetzt mit {len(loaded)} Ergebnissen aus {checkpoint}")
        else:
            timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
            _protocol_output_dir = Path("test-reports") / "e2e" / timestamp
            _protocol_generator = ProtocolGenerator()
            _protocol_generator.start_time = datetime.now(tz=timezone.utc)

        session.config._protocol_output_dir = _protocol_output_dir  # type: ignore[attr-defined]

        # Safety net: generate protocol even on unclean exit (Ctrl+C, crash)
        atexit.register(_generate_protocol_safe)

        # --junitxml is written to a static path (compose entrypoint); relocate
        # the merged XML into the dynamic report dir so run-e2e.sh's cp move
        # carries it alongside protokoll.md. Controller-only — workers never
        # register the junit plugin.
        xmlpath = getattr(session.config.option, "xmlpath", None)
        if xmlpath and not _is_xdist_worker:
            _junit_report_path = Path(xmlpath)
            atexit.register(_relocate_junit_report)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Write the test protocol at the end of the session."""
    _generate_protocol_safe()
