"""E2E test configuration — browser fixtures, screenshots, CLI options (NFR-008 §3.1, §3.4)."""

from __future__ import annotations

import os
import re
import shutil
import time
from collections.abc import Callable, Generator
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService

try:
    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.firefox import GeckoDriverManager
except ImportError:
    ChromeDriverManager = None  # type: ignore[assignment,misc]
    GeckoDriverManager = None  # type: ignore[assignment,misc]

from ._gherkin import iter_tags as _iter_gherkin_tags
from .pages.plant_instance_detail_page import PlantInstanceDetailPage
from .pages.plant_instance_list_page import PlantInstanceListPage
from .pages.watering_log_list_page import WateringLogListPage


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
#
# Both axes and the TC-ID channel work for pytest-bdd scenarios too, but only
# because of the three adaptations further down: Gherkin tags are registered as
# markers in pytest_configure, the file-name lookups use ``item.path`` (not
# ``item.location[0]``, which points into site-packages for a BDD scenario), and
# the TC-ID falls back to the ``@TC-…`` tag because pytest-bdd overwrites the
# scenario function's docstring. A ``.feature`` therefore only needs its
# ``@TC-…`` tag — the REQ axis still comes from the step module's file name and
# the feature axis from its module-level ``FEATURES`` tuple.

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
# Strict TC-ID shape (``TC-004-092`` / ``TC-REQ-001-006``), owned by
# protocol_plugin so the protocol and this file cannot drift apart.
_TC_ID_STRICT = _pp_mod.TC_ID_PATTERN


# ── Gherkin tags → registered markers (pytest-bdd) ────────────────────────
# pytest-bdd turns every scenario/feature/rule tag into a pytest marker at
# *decoration* time (``pytest_bdd.scenario`` → ``pytest_bdd_apply_tag`` →
# ``getattr(pytest.mark, tag)``) and never registers it. Decoration happens on
# module import, i.e. during collection — so under ``--strict-markers`` an
# unregistered tag is not a failing test but a collection ERROR that aborts the
# whole run (exit 2) and takes all ~720 classic tests with it. Registering the
# tags in pytest_configure (which runs before collection) is therefore
# mandatory, and it is also the only approach that covers tags on an
# ``Examples:`` table — those bypass the ``pytest_bdd_apply_tag`` hook entirely
# and call ``getattr(pytest.mark, tag)`` directly, so a hook-based workaround
# would not see them.
#
# Registration is deliberately NOT a blanket "register whatever the .feature
# says": that would throw away exactly the typo protection ``--strict-markers``
# exists for. Only the four known tag shapes below are accepted; anything else
# is a hard UsageError naming the tag and its file, mirroring the FEATURES typo
# guard in pytest_collection_modifyitems.
_LEGACY_MARKERS = ("smoke", "core_crud", "requires_auth", "requires_desktop", "platform_admin")
_REQ_TAG_PATTERN = re.compile(r"req\d{3}")


def _is_known_tag(tag: str) -> bool:
    """Return whether *tag* matches one of the four accepted tag shapes."""
    return bool(
        _TC_ID_STRICT.fullmatch(tag)
        or _REQ_TAG_PATTERN.fullmatch(tag)
        or tag in KNOWN_FEATURE_MARKERS
        or tag in _LEGACY_MARKERS
    )


def _collect_feature_tags(features_dir: Path) -> dict[str, list[str]]:
    """Map every tag found in ``features/**/*.feature`` to the files declaring it.

    Line classification is delegated to ``_gherkin`` — the single source of truth
    shared with ``scripts/check_bdd_traceability.py`` — rather than re-matching a
    local tag regex here. That matters beyond DRY: the naive "does this line look
    like ``@tag @tag``?" test also fires on a line *inside* a Gherkin docstring,
    where ``@example`` is prose. The phantom tag then fails ``_is_known_tag``
    below and turns ``pytest_configure`` into a collection abort (exit 2) that
    takes all ~720 E2E tests with it — a suite-wide outage caused by a comment.
    ``iter_tags`` carries the docstring state that keeps that from happening.
    """
    tags: dict[str, list[str]] = {}
    if not features_dir.is_dir():
        return tags
    for feature_file in sorted(features_dir.glob("**/*.feature")):
        for _lineno, name in _iter_gherkin_tags(feature_file.read_text(encoding="utf-8")):
            tags.setdefault(name, []).append(feature_file.name)
    return tags


def _tc_id_from_docstring(doc: str | None) -> str | None:
    """Read the TC-ID off the first line of a test docstring (classic channel)."""
    text = (doc or "").strip()
    if not text:
        return None
    match = _TC_ID_SCAN.search(text.splitlines()[0])
    return match.group(0) if match else None


def _tc_id_from_markers(node: pytest.Item) -> str | None:
    """Read the TC-ID off a marker — the pytest-bdd fallback channel.

    ``pytest_bdd.scenario`` overwrites the wrapper's ``__doc__`` unconditionally
    (and without ``functools.wraps``) with ``"<feature>: <scenario>"``, so the
    docstring channel is structurally dead for BDD scenarios; the ID lives in the
    ``@TC-…`` Gherkin tag instead.

    Markers are preferred over ``item.obj.__scenario__.tags`` because markers are
    stable public pytest API (``__scenario__`` is pytest-bdd internals that
    already changed shape between 7.x and 8.x) and because they also carry tags
    declared on an ``Examples:`` table, which never reach the ScenarioTemplate's
    ``tags`` set.
    """
    for mark in node.iter_markers():
        if _TC_ID_STRICT.fullmatch(mark.name):
            return mark.name
    return None


def _tc_id_for_item(item: pytest.Item) -> str | None:
    """Resolve a test's TC-ID: docstring first, Gherkin tag as fallback."""
    obj = getattr(item, "obj", None)
    return _tc_id_from_docstring(getattr(obj, "__doc__", None)) or _tc_id_from_markers(item)


# ── Protocol plugin state ─────────────────────────────────────────────────
_protocol_generator: ProtocolGenerator | None = None  # type: ignore[assignment]
_protocol_output_dir: Path | None = None
_is_xdist_worker: bool = False
_junit_report_path: Path | None = None


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers (incl. the Gherkin tags of ``features/``)."""
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
    config.addinivalue_line(
        "markers",
        "platform_admin: run this test as the seeded platform-admin account instead of the "
        "demo user (full mode only; no-op in light mode, where the sole operator already is "
        "platform admin per REQ-027) (#1155)",
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

    # Register the Gherkin tags of every ``features/**/*.feature`` (see the
    # _collect_feature_tags block above for why this must happen here). Tags that
    # coincide with an axis registered above (``req004``, ``watering``, ``smoke``)
    # need no second line — they are already valid markers.
    already_registered = (
        set(KNOWN_FEATURE_MARKERS) | set(_LEGACY_MARKERS) | {f"req{n}" for n in req_nums}
    )
    for tag, files in sorted(_collect_feature_tags(conftest_dir / "features").items()):
        if not _is_known_tag(tag):
            raise pytest.UsageError(
                f"features/{files[0]}: unknown Gherkin tag '@{tag}'. Allowed tags are "
                f"a TC-ID (TC-NNN-NNN / TC-REQ-NNN-NNN), a REQ axis tag (reqNNN), a "
                f"feature axis tag ({sorted(KNOWN_FEATURE_MARKERS)}) or one of "
                f"{list(_LEGACY_MARKERS)}."
            )
        if tag in already_registered:
            continue
        config.addinivalue_line(
            "markers",
            f"{tag}: Gherkin tag from {', '.join(sorted(set(files)))} "
            f"(machine-selectable via -m {tag})",
        )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Derive selection markers, then auto-skip by app mode, device and resume state."""
    # ── Selection axes: auto-derive REQ + feature markers (NFR-008a) ───────
    # Both file-name lookups below use ``item.path`` rather than
    # ``item.location[0]``: for a pytest-bdd scenario the latter reports the code
    # object's file, which lives in ``pytest_bdd/scenario.py`` inside
    # site-packages, so the REQ axis (and the journey marker) would silently
    # never be applied — no error, just a test missing from ``-m req004``.
    # ``item.path`` is the collected module's own file for BDD and classic tests
    # alike.
    for item in items:
        req_marker = _req_marker_for(item.path.name)
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
        if _JOURNEY_FILE_MARKER in item.path.name:
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
    """Lift the declared TC-ID into the machine-readable ``tc_id`` property.

    Makes each test's declared TC-ID (e.g. ``TC-REQ-004-W001``) consumable via
    the standard junit ``user_properties`` channel, in addition to the bespoke
    markdown protocol. The docstring is the primary channel and behaves exactly
    as before; a Gherkin ``@TC-…`` tag is the fallback for pytest-bdd scenarios,
    whose docstring pytest-bdd overwrites (see ``_tc_id_from_markers``). No-op
    when neither channel yields an ID.
    """
    tc_id = _tc_id_for_item(request.node)
    if tc_id:
        record_property("tc_id", tc_id)


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

# ── Platform-admin account (full mode only, #1155) ────────────────────────────
# A *second* account, seeded by `app/migrations/seed_e2e_platform_admin.py` and
# configured in `docker-compose.e2e.yml`. It exists because #1120 made the global
# catalogue mutations platform-admin-only, and the demo user must stay an
# ordinary member: a large part of this suite asserts what an ordinary member is
# refused, and promoting the one shared account would leave all of those green
# while checking nothing.
#
# Reach it with `@pytest.mark.platform_admin` on the test. In light mode the
# marker is a no-op — the sole anonymous operator is already treated as platform
# admin (REQ-027), so there is nothing to switch to.
PLATFORM_ADMIN_EMAIL = "e2e-admin@kamerplanter.example"
PLATFORM_ADMIN_PASSWORD = "e2e-admin-passwort-2026"


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
    "care",
    "calendar",
    "watering",
    "tasks",
    "nutrition",
    "tanks",
    "aquaponics",
    "substrates",
    "calculators",
    "ipm",
    "harvest",
    "post_harvest",
    "runs",
    "propagation",
    "master_data",
    "companion",
    "sensors",
    "automation",
    "smart_home",
    "ai",
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
    _post(
        f"{api_base}/api/v1/auth/register",
        {
            "email": DEMO_EMAIL_FULL,
            "password": DEMO_PASSWORD,
            "display_name": DEMO_DISPLAY_NAME,
        },
    )

    # Login to get JWT
    status, resp = _post(
        f"{api_base}/api/v1/auth/login",
        {
            "email": DEMO_EMAIL_FULL,
            "password": DEMO_PASSWORD,
        },
    )
    if status != 200 or "access_token" not in resp:
        raise RuntimeError(f"E2E seed login failed: status={status}, resp={resp}")

    token = resp["access_token"]

    # Discover tenant slug from user's tenants
    _, _get_auth = _api_helpers(token)
    # No trailing slash: #852 removed the trailing-slash route, and FastAPI's
    # 307 for the old path carries a Location built from the *server's* own
    # address. Inside the compose network that is not the address the test
    # client dialled, so urllib follows the redirect straight into
    # "Connection refused" — and because this runs in session setup, every
    # test in the profile errors out before it starts.
    _, tenants = _get_auth(f"{api_base}/api/v1/tenants")
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
    RUN_NAME = "E2E-Durchlauf"
    TANK_NAME = "E2E-Naehrstofftank"

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

        # The same map for the platform-admin account (#1155) — full mode only,
        # since light mode has no second account (its sole operator already is
        # the platform admin, REQ-027).
        #
        # The PATCH above carries the demo user's token and leaves the admin's own
        # preferences untouched, and `master_data` needs experience level
        # `intermediate` — so without this the admin sees the module-hidden
        # placeholder on every `/stammdaten/*` route, and the page object times
        # out on a page that rendered perfectly well.
        #
        # The localStorage fallback does not cover it, for a reason that is easy
        # to miss: `migrateLocalModuleVisibility` PATCHes the seeded localStorage
        # map to the server **and then clears the key**. The demo user's first
        # bootstrap consumes it, so by the time the browser switches accounts
        # there is nothing left to migrate.
        if app_mode == "full":
            admin_status, admin_login = _post(
                f"{api_base}/api/v1/auth/login",
                {"email": PLATFORM_ADMIN_EMAIL, "password": PLATFORM_ADMIN_PASSWORD},
            )
            if admin_status != 200 or "access_token" not in admin_login:
                raise RuntimeError(
                    f"E2E seed: could not log in as the platform-admin account "
                    f"{PLATFORM_ADMIN_EMAIL!r} (status={admin_status}). It is seeded by "
                    f"app/migrations/seed_e2e_platform_admin.py from the "
                    f"E2E_PLATFORM_ADMIN_* variables in docker-compose.e2e.yml — check "
                    f"the backend log for `e2e_platform_admin_created` or `seed_failed`. "
                    f"Raising rather than skipping, because every "
                    f"@pytest.mark.platform_admin case would otherwise fail far from "
                    f"here, on a login timeout that reads as a harness problem."
                )
            admin_token = admin_login["access_token"]
            # Under the admin's *own* tenant slug: `user-preferences` is a
            # tenant-scoped route, so the demo tenant's path would be a 403.
            _, _admin_get = _api_helpers(admin_token)
            _, admin_tenants = _admin_get(f"{api_base}/api/v1/tenants")
            if not isinstance(admin_tenants, list) or not admin_tenants:
                raise RuntimeError(
                    f"E2E seed: the platform-admin account has no tenant, so its "
                    f"preferences cannot be set: {admin_tenants}"
                )
            admin_slug = admin_tenants[0]["slug"]
            admin_mv_status, _ = _api_patch(
                f"{api_base}/api/v1/t/{admin_slug}/user-preferences",
                {"module_visibility": {k: "enabled" for k in _E2E_TOGGLEABLE_MODULES}},
                admin_token,
            )
            result["admin_module_visibility_status"] = admin_mv_status
            result["admin_tenant_slug"] = admin_slug

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
            status, site = _post(
                f"{api}/sites",
                {
                    "name": SITE_NAME,
                    "description": "Automatisch angelegt fuer E2E-Tests — Balkon und Wohnzimmer",
                    "climate_zone": "8a",
                    "total_area_m2": 45,
                    "timezone": "Europe/Berlin",
                },
            )
            if status == 201:
                result["site_key"] = site["key"]
                loc_status, loc = _post(
                    f"{api}/locations",
                    {
                        "name": LOCATION_NAME,
                        "site_key": site["key"],
                        "location_type_key": "room",
                        "area_m2": 18,
                    },
                )
                if loc_status == 201:
                    result["location_key"] = loc["key"]
                _post(
                    f"{api}/locations",
                    {
                        "name": SLOT_LOCATION_NAME,
                        "site_key": site["key"],
                        "location_type_key": "greenhouse",
                        "area_m2": 12,
                    },
                )

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

        # ── One planting run and one tank (#853) ─────────────────────────
        # Both list pages rendered their empty state on every profile, so the
        # REQ-013 and REQ-014 sorting tests had no table to click and failed on
        # `assert headers` instead of on anything they meant to verify. A global
        # seed cannot fix this: runs and tanks are tenant-scoped, so they can
        # only exist once a tenant does — which is here.
        #
        # Idempotent by name, like the site above: this fixture is
        # session-scoped, but the same containers are reused across profiles,
        # and a second POST must not add a second row.
        run_status, runs = _get(f"{api}/planting-runs")
        if run_status == 200 and isinstance(runs, list):
            existing_run = next((r for r in runs if r.get("name") == RUN_NAME), None)
            if existing_run:
                result["planting_run_key"] = existing_run.get("key")
            else:
                _, run = _post(
                    f"{api}/planting-runs",
                    {
                        "name": RUN_NAME,
                        "run_type": "monoculture",
                        "location_key": result.get("location_key"),
                    },
                )
                if isinstance(run, dict):
                    result["planting_run_key"] = run.get("key")

        tank_status, tanks = _get(f"{api}/tanks")
        if tank_status == 200 and isinstance(tanks, list):
            existing_tank = next((t for t in tanks if t.get("name") == TANK_NAME), None)
            if existing_tank:
                result["tank_key"] = existing_tank.get("key")
            else:
                _, tank = _post(
                    f"{api}/tanks",
                    {
                        "name": TANK_NAME,
                        "tank_type": "nutrient",
                        "volume_liters": 100.0,
                        "location_key": result.get("location_key"),
                    },
                )
                if isinstance(tank, dict):
                    result["tank_key"] = tank.get("key")

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


def _e2e_api_post(
    e2e_seed_data: dict, base_url: str, path: str, data: dict | None = None
) -> tuple[int, dict]:
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
def browser(
    request: pytest.FixtureRequest, e2e_seed_data: dict, device_profile: dict
) -> webdriver.Remote:
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
        chromedriver_path = shutil.which("chromedriver") or shutil.which("chromium.chromedriver")
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
            driver.execute_cdp_cmd(
                "Emulation.setDeviceMetricsOverride",
                {
                    "width": dev["width"],
                    "height": dev["height"],
                    "deviceScaleFactor": dev["deviceScaleFactor"],
                    "mobile": dev["mobile"],
                },
            )
            if dev["userAgent"]:
                driver.execute_cdp_cmd(
                    "Emulation.setUserAgentOverride",
                    {
                        "userAgent": dev["userAgent"],
                    },
                )
            driver.execute_cdp_cmd(
                "Emulation.setTouchEmulationEnabled",
                {
                    "enabled": True,
                },
            )
        except Exception:
            # CDP not available (Firefox, older grids) — viewport size is
            # already set via window-size argument, so tests still run at
            # the correct dimensions, just without touch/UA emulation.
            pass

    # Export browser + device name for the protocol plugin metadata
    os.environ["E2E_BROWSER"] = browser_name
    os.environ["E2E_DEVICE"] = dev["name"]

    # ── No implicit wait is configured here. What stands in its place ──────
    # A driver-level implicit wait of 3 s used to sit on this line; #835 removed
    # it. Nothing replaces it *as a driver setting* — the driver now runs at
    # Selenium's default of 0 — so this comment records what the suite grew
    # instead, because the line was load-bearing and its absence is not obvious
    # from anything nearby.
    #
    # The setter's own name is spelled nowhere in this block on purpose:
    # grepping `tests/` for it and getting nothing back is the acceptance
    # criterion of #835, and it stays a clean signal that the anti-pattern has
    # not come back only for as long as no prose answers that grep.
    #
    # Why it had to go. Mixing implicit and explicit waits is a genuine
    # anti-pattern rather than a stylistic one: the implicit wait also applied to
    # the `find_element` calls *inside* a `WebDriverWait`, so the two budgets
    # multiplied instead of bounding each other, and a poll documenting a 15 s
    # ceiling could spend far longer without saying so.
    #
    # Why it could not simply be deleted. Measured on the base commit
    # `1d98bf3ca` (#835): the suite resolves an element and then uses it on a
    # later line — capture-then-use — at 459 sites, 389 of which go on to
    # interact with what they captured. The implicit wait was not padding those
    # lookups; it was delaying each one enough that a re-rendering React table
    # had usually settled *before* the reference was taken. Delete the line on
    # its own and any of those 389 can lose its element between the capture and
    # the use. Five smoke runs confirmed it, and the telling detail was that the
    # failure set *moved* between runs instead of shrinking.
    #
    # What actually replaced it — a change of interaction model, in four steps:
    #
    #   * `pages/_element_proxy.py` — `ReResolvingElement`, a real `WebElement`
    #     subclass that re-acquires itself from its own locator and capture
    #     condition when the node it points at dies. Bounded on every path, and
    #     it raises rather than healing forever.
    #   * `BasePage.wait_for_element`, `.wait_for_element_visible` and
    #     `.wait_for_element_clickable` hand that back instead of a raw element,
    #     so all 459 capture sites inherit it through the call chain — including
    #     the 48 that go through `find_present`, and `find_by_testid`, which
    #     builds on them but currently has no callers at all.
    #     `wait_for_element_hidden` is unchanged; it returns `None`.
    #   * The plural path (`find_elements`, 804 calls) is deliberately *not*
    #     wrapped — a list element has no re-resolution key but its index, and
    #     re-selecting by index after a re-render is the #871 defect. Its lever
    #     is `BasePage.retry_on_stale`, which re-runs a whole acquisition, and it
    #     now sits on all six helpers that own their row lookup and read through
    #     the rows. See the two block comments at the top of `pages/base_page.py`.
    #   * The reads that treat staleness as an *answer* rather than as a
    #     transient are opted out of healing via `BasePage.raw_reference`, so the
    #     change cannot turn "this element is gone" into "something matching its
    #     locator is here". They are enumerated in the second of those blocks.
    #
    # What is left uncovered, deliberately: the 31 singular `find_element(` call
    # sites still hand back raw elements. They were counted, not converted.
    #
    # None of this is proven by the E2E suite alone — a green run cannot
    # distinguish "the healing worked" from "the timing never provoked it". The
    # mechanism is pinned by `tests/e2e_selftest/`, which drives a real
    # `WebDriver` over a stub executor and is in the required `static` gate.

    # Set German locale in localStorage so i18next picks it up (detection
    # order: localStorage → navigator).  We need to navigate to the origin
    # first so that localStorage is bound to the correct domain.
    url = os.environ.get("E2E_BASE_URL") or request.config.getoption("--base-url")
    driver.get(url)
    driver.execute_script("window.localStorage.setItem('kamerplanter-lang', 'de');")

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


def _browser_login(
    driver: webdriver.Remote,
    base_url: str,
    email: str = DEMO_EMAIL_FULL,
    password: str = DEMO_PASSWORD,
) -> None:
    """Log into the app via the browser UI (full mode only).

    Navigates to /login, fills credentials, submits, and waits for
    redirect to /dashboard or /onboarding.

    The credentials default to the demo user, so every existing caller keeps its
    behaviour; `@pytest.mark.platform_admin` supplies the admin pair instead
    (#1155).
    """
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    driver.get(f"{base_url}/login")
    wait = WebDriverWait(driver, 15)

    email_input = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))
    )
    email_input.clear()
    email_input.send_keys(email)

    password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
    password_input.clear()
    password_input.send_keys(password)

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

    # #1155 — which account this test needs. The marker is only meaningful in
    # full mode; light mode never reaches this line.
    wants_admin = "platform_admin" in request.node.keywords
    wanted = "admin" if wants_admin else "demo"

    # The browser is session-scoped, so the account it holds is carried from the
    # previous test on this worker. Tracked on the driver rather than inferred,
    # because there is no way to read "who am I" from the page cheaply, and
    # guessing would silently run an admin case as the demo user — which is the
    # failure mode this whole change exists to prevent (it looks like a passing
    # test of the gated path).
    current_account = getattr(browser, "_kp_account", "demo")

    if current_account != wanted:
        _switch_account(browser, base_url, wanted)
        return

    # Check if the browser ended up on the login page (= session lost).
    # We cannot reliably check the kp_refresh cookie because it is scoped
    # to path=/api/v1/auth and Selenium only returns cookies for the
    # current page's path.
    current = browser.current_url
    if "/login" not in current:
        return

    # Session lost — re-login as whoever this test needs
    _switch_account(browser, base_url, wanted)


def _switch_account(driver: webdriver.Remote, base_url: str, account: str) -> None:
    """Put the browser into a session for ``account`` ("demo" or "admin").

    The refresh cookie has to go first, and getting *there* is the subtle part.
    `kp_refresh` is scoped to ``path=/api/v1/auth``, and WebDriver's delete-all
    only touches cookies matching the current document's address — the same
    property `ensure_authenticated` documents for *reading* them. Called from
    ``/login`` it therefore deletes nothing, the previous session survives, the
    app redirects away from the login route, and the form never appears.

    So the browser is parked on the cookie's own path before clearing. Then the
    login form is confirmed to be reachable, because the failure mode this
    guards against is silent: without it an admin-only case would run as the
    demo user and pass by never reaching the thing it tests.
    """
    # Any address under the cookie's path will do; the response is irrelevant.
    driver.get(f"{base_url}/api/v1/auth/csrf")
    driver.delete_all_cookies()

    if account == "admin":
        email, password = PLATFORM_ADMIN_EMAIL, PLATFORM_ADMIN_PASSWORD
    else:
        email, password = DEMO_EMAIL_FULL, DEMO_PASSWORD

    try:
        _browser_login(driver, base_url, email, password)
    except TimeoutException as exc:
        raise AssertionError(
            f"Could not log in as {email!r}. Two things go wrong here and they look "
            f"identical from the outside: the account was never seeded (check the backend "
            f"log for `e2e_platform_admin_created` / `seed_failed`), or the previous "
            f"session survived and the app redirected away from /login before the form "
            f"rendered. Both leave this test running as the wrong user, which is why this "
            f"raises instead of carrying on."
        ) from exc

    driver._kp_account = account  # type: ignore[attr-defined]


@pytest.fixture(scope="session")
def screenshot_dir(request: pytest.FixtureRequest) -> Path:
    """Return the screenshot directory, shared with protocol_plugin (NFR-008 §4.2).

    When ``--generate-protocol`` is active the directory is provided by the
    protocol plugin so that screenshots and the Markdown report live in the
    same timestamped folder.  Otherwise a standalone directory is created.
    """
    protocol_dir: Path | None = getattr(request.config, "_protocol_output_dir", None)
    if protocol_dir is not None:
        path = protocol_dir / "screenshots"
    else:
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        path = Path("test-reports") / "e2e" / timestamp / "screenshots"
    path.mkdir(parents=True, exist_ok=True)
    return path


# ── A checkpoint has to be a passive observation ──────────────────────────────
# ``captureBeyondViewport`` is not passive: Chrome resizes the **layout
# viewport** to capture past the fold and then puts it back. Measured on
# Chromium 150.0.7871.128 (the major the Grid runs, see
# ``docker-compose.e2e.yml``: ``selenium/node-chrome:150.0``) by driving CDP
# directly against a synthetic page, 20 captures per configuration:
#
#   * two ``resize`` events fire per capture -- the payloads show the viewport
#     collapsing to 1x1 (desktop) / 4x4 (emulated mobile) and coming back;
#   * a ``matchMedia('(min-width: 600px)')`` listener flips **false and back to
#     true** every single time, ~5-8 ms apart. So every `useMediaQuery` in the
#     page re-evaluates, and a subtree gated on one unmounts and remounts;
#   * Chrome restores the metrics itself, and does so *before* the CDP command
#     returns: on 26/26 captures the first read after the response already
#     matched the pre-capture ``innerWidth``/``innerHeight`` and the measured
#     height of both a ``height: 100vh`` and a ``height: 60vh`` element.
#
# That measurement was taken against a *synthetic* page, and what it could not
# show is that the numbers it compared are not the capture's to keep still: on a
# live route the application changes them itself, in both directions, several
# times per test. Thirteen nightly/local failures later the equality check is
# gone and the *stretch signature* is checked instead -- see
# `_STRETCH_PROBE_JS` for the measurements and `_settle_after_capture` for what
# it now asserts.
#
# So the metrics do come back -- but nothing ever *checked* that they had, and
# the media-query flips leave React work scheduled that lands after the response
# (React re-renders asynchronously; the synthetic listener used for the
# measurement above mutated the DOM synchronously and therefore cannot time it).
# That is the window `test_create_dialog_add_fertilizer_button` fell into when
# `has_remove_fertilizer_button()` answered `False` one line after a helper had
# waited for that very button (#959). While the driver-level implicit wait was
# in place every raw lookup got a 3 s grace period that outlasted it; #835
# removed the wait and the window became reachable.
#
# The two things below close it without touching a single call site: verify the
# restore instead of assuming it, and hold the checkpoint for a frame so the
# scheduled re-render commits before the test reads again.
#
# Cost, measured the same way over 15 captures: the restore poll is satisfied by
# its first sample every time (0.6 ms median) and the frame barrier resolves
# through the two rAF callbacks every time (20.4 ms median, 37.5 ms worst), never
# through its 250 ms fallback -- so ~21 ms per checkpoint against a capture that
# already costs ~113 ms on desktop and ~900 ms under device emulation.
#
# The alternative the issue lists -- drop the flag and stitch scrolled captures
# -- was not taken, and not only for the capture cost: stitching has to *scroll*
# the page under test, which moves sticky chrome, fires IntersectionObservers and
# can trigger lazy loads. It trades a resize the browser undoes for a scroll
# position nobody restores, which is a larger observation effect, not a smaller
# one.

#: Budget for the layout to be back at its pre-capture metrics. Generous by two
#: orders of magnitude against the measurement (restored before the response on
#: every run), because its purpose is to fail loudly on a browser that does not
#: restore at all, not to trade against a timing.
_CAPTURE_RESTORE_TIMEOUT = 5.0

#: The visual viewport's height next to the document's own height -- the two
#: numbers the *stretch* signature is read from, and deliberately not a
#: before/after equality of "the viewport".
#:
#: **What was measured, 2026-08-13, against the running stack.** No viewport
#: quantity is stable across a capture on a live page, because the page moves
#: them itself:
#:
#:   * ``innerWidth`` is the *layout* viewport, which Chrome widens to the
#:     document's minimum width whenever the page overflows horizontally. The
#:     login route needs 524 CSS px on the 393 px `mobile` profile, so
#:     ``innerWidth`` read 524 while ``visualViewport.width`` read 393 with
#:     ``scale == 1`` at the same instant. It flips whenever an error alert
#:     mounts or a spinner unmounts.
#:   * ``visualViewport.width`` excludes the classic scrollbar, so on `desktop`
#:     it reads 1905 with one and 1920 without -- and the scrollbar comes and
#:     goes with the content height.
#:
#: Both were observed as nightly failures: 393<->524 on `full-mobile` (two login
#: tests, 2026-08-13) and 1905<->1920 on `full` (eleven tests, reproduced
#: locally while fixing the first). Both were the *application* re-rendering
#: between the two reads, reported as a browser that had failed to restore.
#:
#: Against a settled page the capture is passive on both profiles -- six
#: captures each, every quantity identical before and after -- which is what
#: makes "any difference is a defect" the wrong test. What the defect this guard
#: exists for actually looks like is unmistakable and content-independent:
#: ``captureBeyondViewport`` stretches the layout viewport **to the document
#: height**, so a capture that failed to put it back leaves a viewport as tall
#: as the whole document (#778 H1 measured a dialog paper at 1991px against an
#: 852px viewport). That is the signature this probes, and nothing else.
#:
#: Probed on the **layout** viewport, because that is the one the flag stretches
#: and therefore the only one a stretch is guaranteed to show up in. (Whether it
#: also shows up in the visual viewport could not be measured: Chromium 150
#: restores on every capture, so the defect state is not reachable to observe.
#: Probing only the visual one would be a bet that, if wrong, leaves this guard
#: permanently unable to fire while still looking like a check.)
#:
#: **Third number: the scale regime, and it is load-bearing.** Under mobile
#: emulation the layout viewport and ``scrollHeight`` are both expressed in
#: *layout* pixels, and Chrome rescales that space by widening the ICB when the
#: page overflows horizontally -- so both numbers jump together by the same
#: factor and their comparison degenerates. Measured on the login route: 852px
#: tall before, ``(viewport, document) = (1136, 1136)`` after, i.e. 852 x 4/3
#: against a document that now exactly fits, which reads as "stretched to the
#: document height" and is nothing of the kind. The ratio of the layout width to
#: the visual width names that regime (100 unscaled, 133 in the sample above);
#: when it changes between the two reads the heights are in different spaces and
#: no verdict can be drawn from them.
_STRETCH_PROBE_JS = (
    "const visualWidth = Math.max(1, Math.round(window.visualViewport.width));"
    " return [window.innerHeight, document.documentElement.scrollHeight,"
    " Math.round((window.innerWidth / visualWidth) * 100)];"
)

#: One full frame, bounded. Two nested ``requestAnimationFrame`` callbacks span
#: a whole frame, which is enough for work React's scheduler posted from the
#: capture's resize listeners to run and commit. The ``setTimeout`` race is not
#: belt-and-braces: a page whose rAF never fires (a throttled or hidden document)
#: would otherwise hang the checkpoint until the script timeout, so the barrier
#: degrades to a bounded pause rather than to a stall.
_SETTLE_FRAMES_JS = """
const done = arguments[arguments.length - 1];
let finished = false;
const finish = (how) => { if (!finished) { finished = true; done(how); } };
window.setTimeout(() => finish('timeout'), 250);
window.requestAnimationFrame(() => window.requestAnimationFrame(() => finish('frames')));
"""


def _viewport_metrics(driver: webdriver.Remote) -> tuple[int, int, int] | None:
    """Return ``(viewport height, document height, scale regime)``, or ``None``.

    See :data:`_STRETCH_PROBE_JS` for why these three numbers and not a viewport
    size: no viewport size is comparable across a capture on a live page, and
    the two heights are only comparable *within* one scale regime.

    ``None`` means "could not look" and is kept distinct from any triple of
    numbers on purpose: a dead session, a page mid-navigation or an open JS
    alert must not be reported as a viewport that stayed stretched. The only
    thing that follows from ``None`` is that this capture cannot be checked --
    never that it was fine.
    """
    try:
        metrics = driver.execute_script(_STRETCH_PROBE_JS)
    except WebDriverException:
        return None
    if not isinstance(metrics, list) or len(metrics) != 3:
        return None
    try:
        return int(metrics[0]), int(metrics[1]), int(metrics[2])
    except TypeError, ValueError:
        return None


def _viewport_is_stretched(driver: webdriver.Remote, before: tuple[int, int, int]) -> bool:
    """Whether the viewport is *still* as tall as the whole document.

    The `captureBeyondViewport` signature, and the only shape of "the capture
    was not passive" this can tell apart from the page's own re-rendering:

    * the page is in the same **scale regime** it was in before the capture --
      otherwise the layout viewport and the document height have both been
      rescaled and neither is comparable to what was read before (measured:
      852px becomes 1136px against a 1136px document, purely because the page
      started overflowing horizontally) -- **and**
    * the viewport is at least the document's own height -- the state the flag
      puts the page into -- **and**
    * it is taller than it was before the capture, so a page that simply fits
      in its viewport (where the two are equal all the time, e.g. a short login
      form) is never flagged, and neither is a page that got *shorter*.

    ``None`` from the probe answers ``False``: "could not look" is not evidence
    of a defect, and the caller's own next read will fail on its own if the
    session is really gone.
    """
    probe = _viewport_metrics(driver)
    if probe is None:
        return False
    before_height, _before_document, before_scale = before
    height, document_height, scale = probe
    if scale != before_scale:
        return False
    return height >= document_height and height > before_height


def _settle_after_capture(
    driver: webdriver.Remote,
    before: tuple[int, int, int] | None,
    timeout: float = _CAPTURE_RESTORE_TIMEOUT,
) -> None:
    """Wait out any leftover stretch from the capture, then out one frame.

    Called with the probe read *before* the capture. Raises when the viewport is
    still stretched to the document height after *timeout*: the capture would
    then have silently re-laid-out everything the test is about to read, and
    there is no honest way to continue from that.

    **It does not compare viewport sizes**, which is what it used to do. Every
    viewport quantity moves with the page's own content -- see
    :data:`_STRETCH_PROBE_JS` for the two measured shapes that produced thirteen
    false failures between them -- so an equality check on one of them reports
    the application re-rendering between two reads as a browser defect. The
    stretch signature is content-independent, and it is the actual failure this
    guard was built for.

    A ``before`` of ``None`` means the baseline could not be established (see
    :func:`_viewport_metrics`), so there is nothing to compare against and the
    check is skipped rather than guessed.
    """
    if before is None:
        return

    deadline = time.monotonic() + timeout
    while _viewport_is_stretched(driver, before) and time.monotonic() < deadline:
        time.sleep(0.02)

    if _viewport_is_stretched(driver, before):
        seen = _viewport_metrics(driver)
        raise AssertionError(
            f"The screenshot checkpoint left the viewport stretched to the "
            f"document height: it read (viewport, document, scale) = {before} "
            f"before the capture and reads {seen} {timeout}s after it. "
            f"`captureBeyondViewport` stretches the layout viewport to the "
            f"document height and is expected to put it back before "
            f"`Page.captureScreenshot` returns; it did not. Every read after "
            f"this checkpoint would be against a re-laid-out page, so the "
            f"capture must stop using that flag in this browser."
        )

    # The metrics are back; the re-render the two media-query flips scheduled
    # may not have committed yet. One frame, bounded, is what makes the
    # checkpoint passive for the caller that reads on the next line.
    try:
        driver.execute_async_script(_SETTLE_FRAMES_JS)
    except WebDriverException:
        # Only reachable if the session died between the poll above and here;
        # the restore has already been verified, so there is nothing left to
        # assert and the real failure belongs to whatever the test does next.
        pass


def _cdp_full_page_screenshot(driver: webdriver.Remote, filepath: Path) -> None:
    """Capture a full-page screenshot via Chrome DevTools Protocol.

    Falls back to the standard Selenium screenshot if CDP is not available
    (e.g. Firefox or older drivers).

    What this image can and cannot answer (#778 H1): it returns the whole scroll
    document, and while doing so Chrome rescales ``position: fixed`` and
    ``height: 100%`` elements to the document height. The same dialog paper
    measured 931px in one shot and 1991px in another, neither equal to the
    852px viewport — so **height in this image means nothing** and it cannot
    answer "is this below the fold". Its *width* stays a sound horizontal-overflow
    measurement. Use :func:`_cdp_viewport_screenshot` for anything vertical.

    Returns only once the page is back at the viewport it had before, and one
    frame after that — see the block comment above for what was measured and
    why. The fallback path needs neither: ``save_screenshot`` captures the
    viewport as it stands and resizes nothing.
    """
    import base64

    before = _viewport_metrics(driver)
    try:
        result = driver.execute_cdp_cmd(
            "Page.captureScreenshot",
            {"captureBeyondViewport": True},
        )
        filepath.write_bytes(base64.b64decode(result["data"]))
    except Exception:
        # Fallback for non-Chrome browsers or remote grids without CDP
        driver.save_screenshot(str(filepath))
        return
    _settle_after_capture(driver, before)


def _cdp_viewport_screenshot(driver: webdriver.Remote, filepath: Path) -> None:
    """Capture exactly what the viewport shows, at the viewport's own size.

    The companion to :func:`_cdp_full_page_screenshot`, and the only one of the
    two that can answer a *vertical* question. Omitting ``captureBeyondViewport``
    leaves the layout viewport untouched, so an element's position in this image
    is its position on the user's screen — which is what "the primary action sits
    below the fold" or "the sticky bar covers the field" actually mean.

    Two agents burned effort on the full-page image before this was pinned down
    (#778 H1), so both are now written per checkpoint rather than leaving the
    reader to guess which question their single image can answer.
    """
    import base64

    try:
        result = driver.execute_cdp_cmd("Page.captureScreenshot", {})
        filepath.write_bytes(base64.b64decode(result["data"]))
    except Exception:
        # Non-Chrome or a grid without CDP: Selenium's own screenshot is already
        # viewport-only, so the fallback is exact rather than approximate here.
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

        # A second, viewport-only image per checkpoint (#778 H1). The full-page
        # one above cannot answer any vertical question, and a reviewer looking
        # at a single image has no way to know that. Written next to it as
        # `<name>.viewport.png` so the pair is obvious in the folder listing.
        viewport_name = f"{name}.viewport.png"
        _cdp_viewport_screenshot(browser, screenshot_dir / viewport_name)

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


# ── Shared page-object fixtures ───────────────────────────────────────────
# The REQ-004 cross-view watering journey exists in two flavours — the classic
# Selenium test and its pytest-bdd sibling — and both drive the very same page
# objects. The fixtures live here rather than in ``_journey_helpers.py`` because
# a fixture is only discoverable through the fixture graph: pytest collects
# fixtures from conftest files and plugins, never from an imported helper
# module, and a pytest-bdd step binding can request nothing else. Duplicating
# them per module (the state BDR-004 flagged) is the only alternative, and that
# is precisely the drift risk being removed.
#
# Adding them here is additive: a module that declares a fixture of the same
# name still shadows this one (several do, with the richer ``PlantInstanceDetailExt``
# type), and no module currently requests one of these names without declaring it.


@pytest.fixture
def plant_creator(browser: webdriver.Remote, base_url: str) -> PlantInstanceListPage:
    """Plant-instance list page — the entry point for self-provisioning a plant."""
    return PlantInstanceListPage(browser, base_url)


@pytest.fixture
def watering_list(browser: webdriver.Remote, base_url: str) -> WateringLogListPage:
    """Tenant-wide watering-log list page (``/giessprotokoll``)."""
    return WateringLogListPage(browser, base_url)


@pytest.fixture
def plant_detail(browser: webdriver.Remote, base_url: str) -> PlantInstanceDetailPage:
    """Plant-instance detail page, incl. its ``#watering-log`` and ``#tasks`` tabs."""
    return PlantInstanceDetailPage(browser, base_url)


def pytest_bdd_after_step(
    request: pytest.FixtureRequest,
    feature: Any,
    scenario: Any,
    step: Any,
    step_func: Callable[..., Any],
) -> None:
    """Capture a screenshot checkpoint after each executed When/Then BDD step.

    This MUST live here rather than in a step-binding module: pytest-bdd's
    custom ``pytest_bdd_*`` hooks are dispatched through pytest's plugin
    manager, which only collects hook implementations from registered plugins
    (conftest.py, or anything installed via a ``pytest11`` entry point) — a
    bare function of the same name defined inside a ``test_*.py`` module is
    never registered and silently never fires (verified empirically: an
    identical hook body in the test module never printed, the same body here
    fires for every step). Only ``when``/``then`` steps are captured — a
    ``given`` may run before the browser has navigated anywhere meaningful.

    The filter keys on ``step.type``, the *resolved* step type, never on
    ``step.keyword``. ``keyword`` is the literal Gherkin word as written, so a
    conjunction (``And``/``But``) carries ``"And"``/``"But"`` there no matter
    which block it continues; pytest-bdd resolves the block itself and exposes
    it as ``step.type`` ∈ ``{"given", "when", "then"}``
    (``pytest_bdd.parser.Parser.parse_steps`` carries ``current_type`` forward
    across every ``Conjunction`` keyword). Filtering on ``keyword`` therefore
    screenshotted the ``Given``-block continuation line
    ``And the plant has 1 watering task due`` — exactly the pre-navigation state
    this guard exists to skip.

    The TC-ID prefix is derived from the scenario's ``@TC-…`` marker
    (``_tc_id_from_markers``) rather than hard-coded, so this stays correct as
    more BDD scenarios are added.
    """
    if step.type not in {"when", "then"}:
        return
    take = request.getfixturevalue("screenshot")
    tc_id = _tc_id_from_markers(request.node) or "bdd"
    slug = re.sub(r"[^a-z0-9]+", "-", step.name.lower()).strip("-")[:60]
    take(f"{tc_id}_{slug}", step.name)


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
            # xfail and xpass are recorded as their own outcomes rather than
            # folded into skipped/passed (#778 A6/A7). A profile reported
            # "green" with 34 xpasses is a different fact from one green with
            # none: a marker that keeps xpassing is a marker that should be
            # removed, and that is invisible while it counts as an ordinary
            # pass. pytest sets ``wasxfail`` for both directions and downgrades
            # a non-strict expected failure to ``skipped``.
            if getattr(report, "wasxfail", None) is not None:
                outcome_str = "xfailed" if report.skipped else "xpassed"
            # ``longrepr`` survives pytest's xfail downgrade (skipping.py only
            # rewrites ``outcome``), so recording it for an expected failure
            # puts the actual traceback into ``checkpoint.jsonl`` instead of
            # discarding the only machine-readable evidence an xfail produces.
            keep_longrepr = report.failed or getattr(report, "wasxfail", None) is not None
            message = str(report.longrepr) if keep_longrepr and report.longrepr else ""
            docstring = ""
            if item.obj and item.obj.__doc__:
                docstring = item.obj.__doc__.strip().split("\n")[0]
            screenshots: list[ScreenshotEntry] = getattr(item, "_protocol_screenshots", [])
            result = TestResult(
                nodeid=item.nodeid,
                outcome=outcome_str,
                duration=report.duration,
                message=message,
                docstring=docstring,
                screenshots=screenshots,
                # Gherkin-tag channel only. Classic tests carry no TC marker, so
                # this stays empty for them and protocol_plugin keeps deriving
                # their ID from ``docstring`` byte-identically to before.
                tc_id=_tc_id_from_markers(item) or "",
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
        # Carried explicitly: under xdist the controller rebuilds every result
        # from this file, and a BDD scenario's TC-ID is not recoverable from its
        # generated docstring.
        "tc_id": result.tc_id,
        "screenshots": [
            {"filename": s.filename, "description": s.description} for s in result.screenshots
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
        results.append(
            TestResult(
                nodeid=entry["nodeid"],
                outcome=entry["outcome"],
                duration=entry.get("duration", 0.0),
                message=entry.get("message", ""),
                docstring=entry.get("docstring", ""),
                tc_id=entry.get("tc_id", ""),
                screenshots=[
                    ScreenshotEntry(
                        filename=s["filename"],
                        description=s["description"],
                        test_nodeid=entry["nodeid"],
                    )
                    for s in entry.get("screenshots", [])
                ],
            )
        )
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
