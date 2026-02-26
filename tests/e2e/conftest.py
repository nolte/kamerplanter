"""E2E test configuration — browser fixtures, screenshots, CLI options."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

import shutil

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
    """Register custom CLI options for E2E tests."""
    parser.addoption(
        "--browser",
        default="chrome",
        choices=["chrome", "firefox"],
        help="Browser to run E2E tests (default: chrome)",
    )
    parser.addoption(
        "--base-url",
        default="http://localhost:8080",
        help="Base URL of the running application (default: http://localhost:8080)",
    )
    parser.addoption(
        "--generate-protocol",
        action="store_true",
        default=False,
        help="Generate a test protocol report (NFR-008 §4.4)",
    )


@pytest.fixture(scope="session")
def base_url(request: pytest.FixtureRequest) -> str:
    """Return the base URL for the application under test."""
    return request.config.getoption("--base-url")


@pytest.fixture(scope="session")
def browser(request: pytest.FixtureRequest) -> webdriver.Remote:
    """Create a headless browser session for the entire test run."""
    browser_name = request.config.getoption("--browser")

    if browser_name == "firefox":
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
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        chrome_path = shutil.which("chromedriver")
        if chrome_path:
            service = ChromeService(chrome_path)
        elif ChromeDriverManager is not None:
            service = ChromeService(ChromeDriverManager().install())
        else:
            service = ChromeService()
        driver = webdriver.Chrome(service=service, options=options)

    driver.implicitly_wait(10)
    yield driver
    driver.quit()


@pytest.fixture(scope="session")
def screenshot_dir() -> Path:
    """Create and return the screenshot output directory for this run."""
    timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = Path("test-reports") / timestamp / "screenshots"
    path.mkdir(parents=True, exist_ok=True)
    return path


@pytest.fixture(autouse=True)
def screenshot(
    request: pytest.FixtureRequest,
    browser: webdriver.Remote,
    screenshot_dir: Path,
) -> None:  # noqa: PT004 — yield fixture without value is intentional
    """Auto-capture a screenshot on test failure."""

    def _capture(name: str) -> Path:
        filename = f"{name}.png"
        filepath = screenshot_dir / filename
        browser.save_screenshot(str(filepath))
        return filepath

    request.node._screenshot_capture = _capture  # type: ignore[attr-defined]
    yield
    # After test — capture on failure
    report = getattr(request.node, "_report", None)
    if report and report.failed:
        test_name = request.node.name.replace("[", "_").replace("]", "_")
        _capture(f"FAILURE_{test_name}")


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item) -> None:
    """Attach the test report to the item node for the screenshot fixture."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        item._report = report  # type: ignore[attr-defined]
