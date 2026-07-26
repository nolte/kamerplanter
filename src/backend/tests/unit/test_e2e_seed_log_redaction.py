"""The E2E seed log never carries a live token (SEC-006).

``tests/e2e/conftest.py`` dumps its seed result to
``test-reports/e2e_seed_data.log``; in full mode that dict holds the demo
account's JWT. The file is gitignored and today's CI artifact upload does not
include it, but a broadened report-upload turns that into a live token sitting
in a 14-day-retention artifact.

The redaction rule lives in the dependency-free ``tests/e2e/_seed_log`` module so
it can be verified here, in the backend suite, without importing the E2E
conftest (which pulls in selenium) or running a browser.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


def _load_seed_log_module() -> ModuleType:
    """Import ``tests/e2e/_seed_log.py`` by path, from the enclosing repository."""
    for candidate in Path(__file__).resolve().parents:
        module_path = candidate / "tests" / "e2e" / "_seed_log.py"
        if module_path.is_file():
            spec = importlib.util.spec_from_file_location("e2e_seed_log", module_path)
            assert spec is not None and spec.loader is not None
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise AssertionError("tests/e2e/_seed_log.py not found above this test file")


seed_log = _load_seed_log_module()

TOKEN = "eyJhbGciOiJIUzI1NiJ9.payload.signature"


def test_access_token_is_redacted_in_the_log_body() -> None:
    body = seed_log.format_seed_log(
        "http://localhost:8000/api/v1/t/personal",
        "full",
        {"access_token": TOKEN, "tenant_slug": "personal"},
    )

    assert TOKEN not in body
    assert seed_log.REDACTED in body
    # Everything non-secret is still logged — the file stays useful for triage.
    assert "tenant_slug" in body
    assert "personal" in body
    assert "mode=full" in body


@pytest.mark.parametrize("key", ["access_token", "refresh_token", "api_key", "password", "client_secret"])
def test_every_secret_bearing_key_is_redacted(key: str) -> None:
    """A future sibling token key is covered without touching the redaction."""
    redacted = seed_log.redact_secrets({key: "s3cret"})

    assert redacted[key] == seed_log.REDACTED


def test_nested_secrets_are_redacted() -> None:
    redacted = seed_log.redact_secrets(
        {"seeded": [{"access_token": TOKEN, "key": "plant-1"}], "tenant_slug": "personal"}
    )

    assert redacted["seeded"][0]["access_token"] == seed_log.REDACTED
    assert redacted["seeded"][0]["key"] == "plant-1"


def test_light_mode_result_without_a_token_is_unchanged() -> None:
    """Light mode seeds no token; the log must look exactly as before."""
    result = {"tenant_slug": "mein-garten", "site_key": "s1", "task_keys": ["t1", "t2"]}

    assert seed_log.redact_secrets(result) == result


def test_absent_token_value_is_not_masked_into_a_lie() -> None:
    """An empty token stays empty rather than implying a redacted secret."""
    assert seed_log.redact_secrets({"access_token": ""}) == {"access_token": ""}


def test_conftest_writes_through_the_redaction() -> None:
    """Pin the call site: the seed fixture must not format the log by hand."""
    for candidate in Path(__file__).resolve().parents:
        conftest = candidate / "tests" / "e2e" / "conftest.py"
        if conftest.is_file():
            source = conftest.read_text(encoding="utf-8")
            break
    else:  # pragma: no cover - defensive
        raise AssertionError("tests/e2e/conftest.py not found above this test file")

    assert "format_seed_log(api, app_mode, result)" in source
    assert "result={result}" not in source
