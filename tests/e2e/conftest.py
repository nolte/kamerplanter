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
def app_mode(request: pytest.FixtureRequest) -> str:
    """Return the current app mode ('light' or 'full')."""
    return request.config.getoption("--app-mode")


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

        # Skip onboarding wizard so the browser lands on /dashboard
        _post(f"{api}/onboarding/skip", {})
    except Exception as exc:
        result["error"] = str(exc)

    seed_log = Path("test-reports/e2e_seed_data.log")
    seed_log.parent.mkdir(parents=True, exist_ok=True)
    seed_log.write_text(f"api={api}\nmode={app_mode}\nresult={result}\n")

    return result


@pytest.fixture(scope="session")
def browser(request: pytest.FixtureRequest, e2e_seed_data: dict) -> webdriver.Remote:
    """Create a headless browser session per xdist worker (NFR-008 §3.1).

    Depends on ``e2e_seed_data`` to ensure the demo user exists before
    attempting browser login in full mode.

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

    # Check if refresh cookie still exists (= session alive)
    cookies = browser.get_cookies()
    has_refresh = any(c["name"] == "kp_refresh" for c in cookies)
    if has_refresh:
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
