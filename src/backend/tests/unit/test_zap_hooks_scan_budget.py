"""The nightly ZAP hook bounds the active scan (NFR-015 §4.3, §5.3).

``zap-full-scan.py`` has no flag for the active-scan duration: ``-m`` bounds only
the spiders and ``-T`` bounds only ZAP start-up and the passive-scan wait. Left
unbounded, the nightly ran until the hosted runner died (four of eight nights in
2026-08/09, run 33593622257 the last). The hook is the only place the bound can
live, so this test asserts the hook sets it — and reads it back, so a ZAP that
silently ignores the option fails loud instead of scanning without a budget
(NFR-018 §1).

The third test ties the hook to the workflow: the spider budget (``-m``) plus the
active-scan budget must fit under the job timeout, or the timeout kills the run
before the verdict step can read the report — the exact outcome the budget exists
to prevent.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType

import pytest

from tests.support.repo_scripts import find_repo_root

_REPO_ROOT = find_repo_root(Path(__file__).resolve())
if _REPO_ROOT is None:  # pragma: no cover — only outside a full checkout
    pytest.skip("checkout root not found", allow_module_level=True)

_HOOK = _REPO_ROOT / "tests" / "security" / "zap-setup" / "zap_hooks.py"
_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "security-zap-nightly.yml"


def _load_hook() -> ModuleType:
    spec = importlib.util.spec_from_file_location("_zap_hooks_under_test", _HOOK)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["_zap_hooks_under_test"] = module
    spec.loader.exec_module(module)
    return module


class _FakeScript:
    """The subset of ``zap.script`` the hook touches; every action answers OK."""

    def __init__(self) -> None:
        self.loaded: list[str] = []

    def load(self, scriptname: str, **_: object) -> str:
        self.loaded.append(scriptname)
        return "OK"

    def enable(self, scriptname: str) -> str:
        return "OK"

    def set_global_var(self, varkey: str, varvalue: str) -> str:
        return "OK"

    @property
    def list_scripts(self) -> list[dict[str, str]]:
        return [{"name": name} for name in self.loaded]


class _FakeAscan:
    """``zap.ascan`` as the real client exposes it: a setter that answers OK and a
    read-back property. ``honours`` decides whether the setter takes effect — the
    real ZAP does, but a ZAP that answers OK and keeps the default is exactly the
    failure the read-back exists to catch."""

    def __init__(self, *, honours: bool = True) -> None:
        self._max = "0"
        self._honours = honours
        self.requested: list[int] = []

    def set_option_max_scan_duration_in_mins(self, integer: int) -> str:
        self.requested.append(integer)
        if self._honours:
            self._max = str(integer)
        return "OK"

    @property
    def option_max_scan_duration_in_mins(self) -> str:
        return self._max


class _FakeZap:
    def __init__(self, *, honours_bound: bool = True) -> None:
        self.script = _FakeScript()
        self.ascan = _FakeAscan(honours=honours_bound)


@pytest.fixture
def hook(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    module = _load_hook()
    scripts = []
    for name, kind, path in module.SCRIPTS:
        stub = tmp_path / Path(path).name
        stub.write_text("// stub\n")
        scripts.append((name, kind, str(stub)))
    monkeypatch.setattr(module, "SCRIPTS", scripts)
    monkeypatch.setenv("KP_ZAP_TOKEN", "test-token")
    return module


def test_the_hook_bounds_the_active_scan(hook: ModuleType) -> None:
    zap = _FakeZap()

    hook.zap_started(zap, "http://frontend:8080")

    assert hook.ACTIVE_SCAN_MAX_MINUTES > 0
    assert zap.ascan.requested == [hook.ACTIVE_SCAN_MAX_MINUTES]
    assert zap.ascan.option_max_scan_duration_in_mins == str(hook.ACTIVE_SCAN_MAX_MINUTES)


def test_a_zap_that_ignores_the_bound_fails_the_scan(hook: ModuleType) -> None:
    zap = _FakeZap(honours_bound=False)

    with pytest.raises(RuntimeError, match="active scan"):
        hook.zap_started(zap, "http://frontend:8080")


def test_the_budgets_fit_under_the_job_timeout(hook: ModuleType) -> None:
    text = _WORKFLOW.read_text()
    timeout = int(re.search(r"^\s+timeout-minutes:\s*(\d+)", text, re.MULTILINE).group(1))
    spider = re.search(r"zap-full-scan\.py(?:.|\n)*?-m\s+(\d+)", text)
    assert spider is not None, "the nightly passes no -m, so the spiders run unbounded"
    spider_minutes = int(spider.group(1))

    # Stack build (~4 min), ZAP pull, spiders, active scan, passive-scan wait and
    # report writing all share the timeout; 30 minutes of headroom covers the
    # non-scan phases with margin.
    assert spider_minutes + hook.ACTIVE_SCAN_MAX_MINUTES + 30 <= timeout
