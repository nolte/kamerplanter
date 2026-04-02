"""E2E test configuration — browser fixtures, screenshots, CLI options (NFR-008 §3.1, §3.4)."""

from __future__ import annotations

import os
import shutil
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


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Auto-skip tests based on app mode and resume state."""
    if config.getoption("--app-mode") == "light":
        skip_light = pytest.mark.skip(reason="requires full auth mode (running in light mode)")
        for item in items:
            if "requires_auth" in item.keywords:
                item.add_marker(skip_light)

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


@pytest.fixture(scope="session")
def base_url(request: pytest.FixtureRequest) -> str:
    """Return the base URL for the application under test.

    ``E2E_BASE_URL`` env var takes precedence (set by docker-compose.e2e.yml).
    """
    return os.environ.get("E2E_BASE_URL") or request.config.getoption("--base-url")


@pytest.fixture(scope="session", autouse=True)
def e2e_seed_data(base_url: str) -> dict:
    """Create seed data (Site + Location) via backend API for E2E tests.

    Runs once per session. Returns dict with created keys.
    In light mode, uses the system tenant slug 'mein-garten'.
    """
    import json
    import urllib.request
    import urllib.error

    api_base = base_url.rstrip("/")
    tenant_slug = "mein-garten"
    api = f"{api_base}/api/v1/t/{tenant_slug}"
    result: dict = {}

    def _post(url: str, data: dict) -> tuple[int, dict]:
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, {}

    def _get(url: str) -> tuple[int, list | dict]:
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as e:
            return e.code, []

    # Idempotent seed: check whether our named site already exists before
    # creating a new one.  This avoids accumulating duplicate "E2E-Teststandort"
    # entries across repeated test runs.
    SITE_NAME = "E2E-Sonnengarten"
    LOCATION_NAME = "E2E-Wohnzimmer"
    SLOT_LOCATION_NAME = "E2E-Gewaechshaus"

    try:
        # Check for existing site by name
        list_status, sites = _get(f"{api}/sites")
        existing_site = None
        if list_status == 200 and isinstance(sites, list):
            existing_site = next((s for s in sites if s.get("name") == SITE_NAME), None)

        if existing_site:
            result["site_key"] = existing_site["key"]
            # Ensure location exists within this site
            tree_status, tree = _get(f"{api}/locations/tree?site_key={existing_site['key']}")
            if tree_status == 200 and isinstance(tree, list) and tree:
                result["location_key"] = tree[0]["key"]
        else:
            # Create a recognizable Site with realistic data
            status, site = _post(f"{api}/sites", {
                "name": SITE_NAME,
                "description": "Automatisch angelegt fuer E2E-Tests — Balkon und Wohnzimmer",
                "climate_zone": "8a",
                "total_area_m2": 45,
                "timezone": "Europe/Berlin",
            })
            if status == 201:
                result["site_key"] = site["key"]
                # Create two Locations with distinct types for tree/detail tests
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
    except (urllib.error.URLError, OSError) as exc:
        result["error"] = str(exc)

    # Write debug log to test-reports for diagnosis
    seed_log = Path("test-reports/e2e_seed_data.log")
    seed_log.parent.mkdir(parents=True, exist_ok=True)
    seed_log.write_text(f"api={api}\nresult={result}\n")

    return result


@pytest.fixture(scope="session")
def browser(request: pytest.FixtureRequest) -> webdriver.Remote:
    """Create a headless browser session per xdist worker (NFR-008 §3.1).

    With pytest-xdist, ``scope="session"`` means one session per worker
    process — each of the N workers gets exactly one browser.  Without
    xdist, all tests share a single browser as before.

    When ``SELENIUM_REMOTE_URL`` is set (e.g. in docker-compose.e2e.yml),
    a Remote WebDriver connecting to Selenium Grid is used.  Otherwise a
    local browser is started as before.
    """
    browser_name = request.config.getoption("--browser")
    remote_url = os.environ.get("SELENIUM_REMOTE_URL")

    if remote_url:
        # ── Remote WebDriver (Selenium Grid / Docker) ──────────
        if browser_name == "firefox":
            options = webdriver.FirefoxOptions()
            options.add_argument("--headless")
            options.add_argument("--width=1920")
            options.add_argument("--height=1080")
            options.set_preference("intl.accept_languages", "de-DE,de")
        else:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
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
        options.add_argument("--width=1920")
        options.add_argument("--height=1080")
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
        options.add_argument("--window-size=1920,1080")
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

    # Export browser name for the protocol plugin metadata
    os.environ["E2E_BROWSER"] = browser_name

    driver.implicitly_wait(10)

    # Set German locale in localStorage so i18next picks it up (detection
    # order: localStorage → navigator).  We need to navigate to the origin
    # first so that localStorage is bound to the correct domain.
    url = os.environ.get("E2E_BASE_URL") or request.config.getoption("--base-url")
    driver.get(url)
    driver.execute_script(
        "window.localStorage.setItem('kamerplanter-lang', 'de');"
    )

    yield driver
    driver.quit()


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
        browser.save_screenshot(str(filepath))

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

    # After test — capture on failure
    report = getattr(request.node, "_report", None)
    if report and report.failed:
        test_name = request.node.name.replace("[", "_").replace("]", "_")
        _capture(
            f"FAILURE_{test_name}",
            f"Automatischer Screenshot nach Fehler in {test_name}",
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
            message = str(report.longrepr) if report.failed else ""
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
    if _protocol_generator is not None and _protocol_output_dir is not None:
        try:
            path = _protocol_generator.generate(_protocol_output_dir)
            print(f"\nTestprotokoll geschrieben: {path}")
        except Exception as exc:
            print(f"\nWarnung: Protokoll-Generierung fehlgeschlagen: {exc}")


def pytest_sessionstart(session: pytest.Session) -> None:
    """Initialize protocol generator if --generate-protocol is active."""
    import atexit
    global _protocol_generator, _protocol_output_dir

    if session.config.getoption("--generate-protocol", default=False):
        resume_dir = session.config.getoption("--resume", default=None)
        if resume_dir:
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


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Write the test protocol at the end of the session."""
    _generate_protocol_safe()
