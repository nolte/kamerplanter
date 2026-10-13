"""``create_care_task`` must confirm its own create before navigating (#1728).

``e2e-nightly`` failed intermittently with "care task ... did not appear in
the queue within 15s". The root cause was in the *arrange* step, not the
lookup: the helper submitted the create form, then called
``wait_for_loading_complete()`` -- which waits for a ``loading-skeleton`` the
create dialog never renders and so returns at once -- and immediately
navigated (``task_queue.open()``) to start scanning the queue. That navigation
aborts a still in-flight ``POST /tasks`` (nginx 499), so whether the backend
ever persisted the task became a race the test could lose.

``TaskCreateDialog`` (``TaskCreateDialog.tsx``) keeps itself mounted and open
while ``taskApi.createTask`` is in flight, and closes only via ``onCreated``
after a 2xx; a rejected create runs ``handleError`` instead and leaves it
open. So "the dialog is gone" is the one signal that can actually fail on an
unconfirmed create, and the fix makes the helper wait for it -- once, without
retrying the click -- before it does anything that could race the request.

Browser-free: ``create_care_task`` is driven through an autospec
``TaskQueuePage`` double (matching ``test_care_provisioning_diagnostics.py``),
so nothing here needs a Selenium Grid or the composed application stack.
"""

from __future__ import annotations

from unittest.mock import create_autospec

import pytest
from selenium.common.exceptions import TimeoutException

from tests.e2e import _journey_helpers
from tests.e2e.pages.task_queue_page import TaskQueuePage

PLANT = "522789"

#: Methods whose invocation order this file asserts on. Everything else on the
#: double is a plain autospec mock (present so a call the real page object
#: would reject fails here too), but its *order* relative to these is not
#: interesting enough to log.
_LOGGED_METHODS = (
    "open",
    "click_create_task",
    "submit_task_form",
    "wait_for_loading_complete",
    "wait_for_create_dialog_closed",
)


def _task_queue_double(*, dialog_closes: bool, diagnostic_text: str = ""):
    """An autospec ``TaskQueuePage`` double that records the order of key calls.

    ``dialog_closes=False`` makes ``wait_for_create_dialog_closed`` raise
    ``TimeoutException`` on every call -- the double's stand-in for "the
    create dialog never went away", i.e. an unconfirmed create. When it is
    ``True`` the call succeeds, standing in for the dialog closing once the
    create POST resolved 2xx.

    ``create_autospec`` (not a hand-written stub) so a call this file could
    not make against the real ``TaskQueuePage`` -- a renamed or removed
    method -- raises here too, matching
    ``test_care_provisioning_diagnostics.py``'s ``_task_queue_double``.
    """
    double = create_autospec(TaskQueuePage, instance=True)
    call_log: list[str] = []

    def _logged(name: str):
        def _fn(*_args, **_kwargs):
            call_log.append(name)
            if name == "wait_for_create_dialog_closed" and not dialog_closes:
                raise TimeoutException("task-create-dialog still visible")
            return None

        return _fn

    for method in _LOGGED_METHODS:
        getattr(double, method).side_effect = _logged(method)

    double.select_task_plant_by_text.return_value = True
    double.get_create_dialog_diagnostic_text.return_value = diagnostic_text
    double.filter_by_plant.return_value = True
    double.find_task_key_by_name.return_value = "task-key-123"
    double.get_task_keys.return_value = ["task-key-123"]
    double.call_log = call_log
    return double


class TestSubmitIsConfirmedBeforeTheLookupNavigates:
    """The dialog-closed wait must sit between the submit click and the re-navigate.

    This is the test that fails against the pre-#1728 helper: that version
    never calls ``wait_for_create_dialog_closed`` at all -- it calls
    ``wait_for_loading_complete`` and then immediately re-navigates -- so
    ``call_log.index("wait_for_create_dialog_closed")`` raises ``ValueError``
    on it, and the "old helper proceeds immediately" assertion below fails
    outright because there is nothing to compare positions with.
    """

    def test_the_dialog_close_wait_gates_the_lookups_navigation(self) -> None:
        queue = _task_queue_double(dialog_closes=True)

        result = _journey_helpers.create_care_task(queue, PLANT, "watering task")

        assert result == "task-key-123"
        log = queue.call_log
        assert "wait_for_loading_complete" not in log, (
            "the post-submit wait must be the dialog-closed signal -- "
            "`wait_for_loading_complete` is satisfied by a skeleton the create "
            "dialog never renders and so proves nothing about the create (#1728)"
        )
        submit_at = log.index("submit_task_form")
        confirm_at = log.index("wait_for_create_dialog_closed")
        # The arrange step's own `open()` (dismissing any stale dialog) is the
        # first entry; the lookup loop's re-navigate is the second.
        open_calls = [i for i, name in enumerate(log) if name == "open"]
        assert len(open_calls) >= 2, (
            f"expected an arrange-phase and a lookup-phase open(), got {log}"
        )
        lookup_navigate_at = open_calls[1]
        assert submit_at < confirm_at < lookup_navigate_at, (
            f"expected submit -> confirm-dialog-closed -> lookup navigate, got {log}. "
            "A navigate before the dialog is confirmed closed can cancel a "
            "still in-flight create POST (#1728)."
        )


class TestAnUnconfirmedSubmitFailsLoudlyWithoutRetrying:
    """A dialog that never closes must fail once, not retry the click.

    Retrying ``submit_task_form`` after an unconfirmed click would resubmit
    the form and risk a duplicate task -- the failure has to surface as a
    diagnostic ``AssertionError`` instead.
    """

    def test_the_failure_message_carries_the_dialogs_own_error_text(self) -> None:
        queue = _task_queue_double(
            dialog_closes=False,
            diagnostic_text="Für dieses Feld ist eine Eingabe erforderlich.",
        )

        with pytest.raises(AssertionError) as exc:
            _journey_helpers.create_care_task(queue, PLANT, "watering task")

        message = str(exc.value)
        assert "Für dieses Feld ist eine Eingabe erforderlich." in message, (
            "the dialog/snackbar text read back from the live page must reach "
            "the failure message, not just 'did not close' (#1728, "
            "e2e-failure-diagnosis §C/§D)"
        )
        assert "not confirmed" in message

    def test_a_timeout_after_the_click_never_resubmits(self) -> None:
        queue = _task_queue_double(dialog_closes=False)

        with pytest.raises(AssertionError):
            _journey_helpers.create_care_task(queue, PLANT, "watering task")

        assert queue.submit_task_form.call_count == 1, (
            "a timeout after an unconfirmed submit must fail outright, not retry "
            "the whole dialog -- a second submit_task_form() call would resubmit "
            "and risk a duplicate task (#1728)"
        )
        assert queue.click_create_task.call_count == 1, (
            "the arrange-loop's own retry must not re-fire once submit was clicked"
        )

    def test_no_error_text_is_reported_as_such_not_as_a_false_success(self) -> None:
        """An empty diagnostic must not be silently treated as 'nothing wrong'."""
        queue = _task_queue_double(dialog_closes=False, diagnostic_text="")

        with pytest.raises(AssertionError) as exc:
            _journey_helpers.create_care_task(queue, PLANT, "watering task")

        message = str(exc.value)
        assert "not confirmed" in message
        assert "No error text was visible" in message
