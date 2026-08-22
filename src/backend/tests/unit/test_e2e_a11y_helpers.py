"""The a11y scan fails loudly rather than reporting a clean page (#1095).

`tests/e2e/_a11y_helpers.py` is dependency-free by design — no selenium import —
so its fail-loud contract can be verified here, in the backend suite, without a
browser. That contract is the whole reason the journey means anything: a scan
that quietly did not run would return an empty violation list, which reads
exactly like a clean page (NFR-018 §2).
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


def _load_a11y_module() -> ModuleType:
    for candidate in Path(__file__).resolve().parents:
        module_path = candidate / "tests" / "e2e" / "_a11y_helpers.py"
        if module_path.is_file():
            spec = importlib.util.spec_from_file_location("e2e_a11y_helpers", module_path)
            assert spec is not None and spec.loader is not None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    pytest.skip("tests/e2e/_a11y_helpers.py not found from this checkout")


a11y = _load_a11y_module()


class _Driver:
    """Minimal driver double. Records scripts; answers only what it was told to."""

    def __init__(self, *, axe_defined=True, run_result=None, raises_on_run=False):
        self.scripts: list[str] = []
        self._axe_defined = axe_defined
        self._run_result = run_result
        self._raises = raises_on_run
        self.script_timeout: float | None = None

    def execute_script(self, script, *args):
        self.scripts.append(script)
        if "typeof window.axe" in script:
            return self._axe_defined
        return None

    def set_script_timeout(self, seconds):
        self.script_timeout = seconds

    def execute_async_script(self, script, *args):
        if self._raises:
            raise RuntimeError("browser said no")
        return self._run_result


def _bundle(tmp_path: Path, monkeypatch) -> None:
    """Point the helper at a stub bundle so injection can be exercised offline."""
    stub = tmp_path / "axe.min.js"
    stub.write_text("/* stub */", encoding="utf-8")
    monkeypatch.setattr(a11y, "AXE_BUNDLE", stub)


class TestItRefusesToReportACleanPageItNeverScanned:
    def test_a_missing_bundle_raises(self, tmp_path, monkeypatch):
        monkeypatch.setattr(a11y, "AXE_BUNDLE", tmp_path / "absent.js")
        monkeypatch.setattr(a11y, "_LOCAL_BUNDLE", tmp_path / "also-absent.js")

        with pytest.raises(a11y.AxeUnavailableError, match="bundle not found"):
            a11y.run_axe(_Driver())

    def test_injection_that_defines_nothing_raises(self, tmp_path, monkeypatch):
        """A CSP blocking inline script looks exactly like a no-op."""
        _bundle(tmp_path, monkeypatch)

        with pytest.raises(a11y.AxeUnavailableError, match="window.axe"):
            a11y.run_axe(_Driver(axe_defined=False))

    def test_axe_run_reporting_failure_raises(self, tmp_path, monkeypatch):
        _bundle(tmp_path, monkeypatch)
        driver = _Driver(run_result={"ok": False, "error": "boom"})

        with pytest.raises(a11y.AxeUnavailableError, match="boom"):
            a11y.run_axe(driver)

    def test_no_result_at_all_raises(self, tmp_path, monkeypatch):
        """`execute_async_script` returning None must not read as zero violations."""
        _bundle(tmp_path, monkeypatch)

        with pytest.raises(a11y.AxeUnavailableError):
            a11y.run_axe(_Driver(run_result=None))


class TestTheHappyPath:
    def test_violations_are_returned_unchanged(self, tmp_path, monkeypatch):
        _bundle(tmp_path, monkeypatch)
        found = [{"id": "color-contrast", "impact": "serious", "nodes": []}]
        driver = _Driver(run_result={"ok": True, "violations": found})

        assert a11y.run_axe(driver) == found

    def test_a_genuinely_clean_page_returns_empty(self, tmp_path, monkeypatch):
        """The one case where `[]` is legitimate — reached only after axe ran."""
        _bundle(tmp_path, monkeypatch)
        driver = _Driver(run_result={"ok": True, "violations": []})

        assert a11y.run_axe(driver) == []

    def test_the_script_timeout_is_set_rather_than_inherited(self, tmp_path, monkeypatch):
        _bundle(tmp_path, monkeypatch)
        driver = _Driver(run_result={"ok": True, "violations": []})

        a11y.run_axe(driver)

        assert driver.script_timeout == a11y.AXE_RUN_TIMEOUT_SECONDS

    def test_the_requested_tags_reach_axe(self, tmp_path, monkeypatch):
        """The tag set is stated so an axe release cannot silently widen or
        narrow what the journey asserts."""
        _bundle(tmp_path, monkeypatch)
        assert "wcag22aa" in a11y.DEFAULT_TAGS


class TestReporting:
    def test_a_violation_is_rendered_with_its_selector(self):
        """'color-contrast: 3 nodes' sends the reader hunting; the target does not."""
        rendered = a11y.format_violations(
            [
                {
                    "id": "color-contrast",
                    "impact": "serious",
                    "help": "Elements must have sufficient colour contrast",
                    "nodes": [{"target": ["#a11y-negative-control"], "failureSummary": "Fix any of the following: …"}],
                }
            ]
        )

        assert "#a11y-negative-control" in rendered
        assert "color-contrast" in rendered

    def test_no_violations_says_so_rather_than_rendering_nothing(self):
        assert a11y.format_violations([]) == "no violations"

    def test_the_protocol_payload_drops_axes_full_node_blob(self):
        """The artifact records what was found, not axe's entire DOM snapshot."""
        payload = a11y.violations_json(
            [{"id": "region", "impact": "moderate", "help": "h", "nodes": [{"target": ["main"], "html": "<x/>"}]}]
        )

        assert "region" in payload
        assert "<x/>" not in payload
