"""``provision_watering_care_task`` must not discard the answers it checks (#1292).

Two nights of the 2026-09 ``e2e-nightly`` failed inside this helper with a
message that named a status and nothing else::

    Self-provisioning failed: could not create a care profile for '522789' (status=500)
    Self-provisioning failed: generate-care-reminders returned status=500 for tenant 'mein-garten'

``_api_request`` had already parsed the error body — which carries the backend's
``error_id`` — and the helper threw it away. Recovering the cause therefore meant
downloading a 600 MB run artifact and grepping its ``logs/backend.log``. These
guards keep the body in the message, so the next occurrence explains itself.

The third guard covers a silent gap the same investigation turned up. The helper
documented step 1 (``GET …/profile``) as the get-or-*create* that persists the
profile. #1422 removed that write — a read that writes was the defect it fixed —
so the step that actually persists is now the ``PATCH``, whose status the helper
did not look at. An unchecked failure there leaves ``generate-care-reminders``
with no profile, and the test fails two steps later with "the card never
appeared": the #1292 symptom, from an entirely unrelated cause.

Browser-free: the helper's HTTP layer is injected, so nothing here needs a
Selenium Grid or the composed stack.
"""

from __future__ import annotations

import pytest

from tests.e2e import _journey_helpers

BASE_URL = "http://backend:8000"
SEED = {"tenant_slug": "mein-garten"}
PLANT = "522789"

#: The shape FastAPI's error handler really returns, abridged. ``error_id`` is
#: the field that indexes into the backend log, which is why it must survive
#: into the assertion message.
ERROR_BODY = {"error": {"code": "INTERNAL_ERROR", "error_id": "err_0e4afc13"}}


def _fail_on(monkeypatch, *, failing_method: str, failing_marker: str, status: int = 500):
    """Answer every request 200 except one ``(method, url-marker)`` pair."""
    calls: list[tuple[str, str]] = []

    def fake_request(url, method, token=None, data=None):
        calls.append((method, url))
        if method == failing_method and failing_marker in url:
            return status, ERROR_BODY
        return 200, {}

    monkeypatch.setattr(_journey_helpers, "_api_request", fake_request)
    monkeypatch.setattr(
        "tests.e2e.conftest._fresh_access_token",
        lambda seed, base_url: "token",
        raising=True,
    )
    return calls


class TestFailureMessagesCarryTheResponseBody:
    """Every checked step names *why*, not only *that*, it failed."""

    @pytest.mark.parametrize(
        ("method", "marker"),
        [
            ("GET", "/care-reminders/plants/"),
            ("PATCH", "/care-reminders/plants/"),
            ("POST", "/tasks/generate-care-reminders"),
        ],
    )
    def test_the_error_id_reaches_the_assertion_message(self, monkeypatch, method, marker):
        _fail_on(monkeypatch, failing_method=method, failing_marker=marker)

        with pytest.raises(AssertionError) as exc:
            _journey_helpers.provision_watering_care_task(BASE_URL, SEED, PLANT)

        assert "err_0e4afc13" in str(exc.value), (
            "the response body was parsed and then dropped — this is exactly what made "
            "the 2026-09-12 and 2026-09-14 nightly failures unreadable"
        )
        assert "500" in str(exc.value)


class TestTheWritingStepIsChecked:
    """Since #1422 the ``PATCH`` is the step that persists the profile."""

    def test_a_failing_patch_raises_here_rather_than_two_steps_later(self, monkeypatch):
        calls = _fail_on(
            monkeypatch, failing_method="PATCH", failing_marker="/care-reminders/plants/"
        )

        with pytest.raises(AssertionError, match="persist the care profile"):
            _journey_helpers.provision_watering_care_task(BASE_URL, SEED, PLANT)

        assert (
            "POST",
            f"{BASE_URL}/api/v1/t/mein-garten/tasks/generate-care-reminders",
        ) not in calls, (
            "the generator ran anyway, so the failure would have surfaced as a missing card"
        )

    def test_the_happy_path_still_runs_all_three_steps_in_order(self, monkeypatch):
        calls = _fail_on(monkeypatch, failing_method="NONE", failing_marker="never")

        _journey_helpers.provision_watering_care_task(BASE_URL, SEED, PLANT)

        assert [method for method, _ in calls] == ["GET", "PATCH", "POST"]
