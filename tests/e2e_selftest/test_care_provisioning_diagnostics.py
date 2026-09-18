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


class _FakeClock:
    """A monotonic stand-in for the ``time`` module the poll loop reads.

    ``create_care_task`` polls for 15 wall-clock seconds. Only two names are
    needed — ``time`` and ``sleep`` — and letting ``sleep`` advance the same
    clock keeps the loop's iteration count exactly what it is in production
    (15 passes at 1.0 s), rather than collapsing it to a single pass.
    """

    def __init__(self) -> None:
        self.now = 1_000.0

    def time(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def _task_queue_double(*, filter_takes: bool, keys: list[str]):
    """A ``TaskQueuePage`` the create dialog can be driven against, card-free.

    ``create_autospec`` rather than a hand-written stub: the double then rejects
    every call the real page object would reject, so a message asserted here
    cannot be produced by a method signature that does not exist (the failure
    class where the double accepts what the real thing refuses).
    """
    from unittest.mock import create_autospec

    from tests.e2e.pages.task_queue_page import TaskQueuePage

    double = create_autospec(TaskQueuePage, instance=True)
    double.select_task_plant_by_text.return_value = True
    double.filter_by_plant.return_value = filter_takes
    double.find_task_key_by_name.return_value = None  # the card never appears
    double.get_task_keys.return_value = keys
    return double


class TestTheLookupDiagnosisStatesOnlyWhatItMeasured:
    """The message names the scope, the count and the keys — and infers nothing (#1485).

    Its predecessor concluded "look at the create, not the lookup" from the
    filter having taken. That conclusion did not follow: until #1484 the filter
    narrowed a response the queue endpoint caps at 200 rows, so the plant's
    cards could be absent from the payload no matter how well the filter worked
    — and the reader was sent after a create that had succeeded.
    """

    @pytest.fixture(autouse=True)
    def _fast_clock(self, monkeypatch):
        monkeypatch.setattr(_journey_helpers, "time", _FakeClock())

    def test_a_taken_scope_reports_the_cards_it_read_and_draws_no_conclusion(self, monkeypatch):
        queue = _task_queue_double(filter_takes=True, keys=["other-1", "other-2"])

        with pytest.raises(AssertionError) as exc:
            _journey_helpers.create_care_task(queue, PLANT, "watering task")

        message = str(exc.value)
        assert "look at the create" not in message, (
            "that is an inference about a step this loop never observed; the loop "
            "measured a scope, a count and a set of keys"
        )
        assert "scoped to plant '522789' server-side" in message
        assert "a read taken after the deadline saw 2 task card(s)" in message, (
            "the count comes from a fresh read here, not from the pass that failed to "
            "find the card — a message that blurs the two describes the wrong moment"
        )
        assert "other-1" in message

    def test_a_scope_that_never_took_names_the_cap_that_bounds_the_unscoped_read(self, monkeypatch):
        queue = _task_queue_double(filter_takes=False, keys=[])

        with pytest.raises(AssertionError) as exc:
            _journey_helpers.create_care_task(queue, PLANT, "watering task")

        message = str(exc.value)
        assert "the plant filter never took" in message
        assert "at most 200 rows" in message, (
            "an unscoped read is bounded by the endpoint's cap — without that number "
            "the reader cannot tell a missing card from a truncated answer"
        )
        assert "a read taken after the deadline saw 0 task card(s)" in message

    def test_a_long_queue_is_summarised_rather_than_dumped(self, monkeypatch):
        # Up to 200 keys in an assertion message buries the two facts that
        # matter — how many, and whether any of them is the one being looked for.
        queue = _task_queue_double(filter_takes=True, keys=[f"key-{i}" for i in range(60)])

        with pytest.raises(AssertionError) as exc:
            _journey_helpers.create_care_task(queue, PLANT, "watering task")

        message = str(exc.value)
        assert "saw 60 task card(s)" in message
        assert "(first 10 of 60)" in message
        assert "key-9" in message
        assert "key-10" not in message

    def test_an_unreadable_queue_says_so_instead_of_inventing_a_count(self, monkeypatch):
        from selenium.common.exceptions import StaleElementReferenceException

        queue = _task_queue_double(filter_takes=True, keys=[])
        queue.get_task_keys.side_effect = StaleElementReferenceException("gone")

        with pytest.raises(AssertionError) as exc:
            _journey_helpers.create_care_task(queue, PLANT, "watering task")

        assert "could not be read after the deadline (StaleElementReferenceException)" in str(
            exc.value
        )
