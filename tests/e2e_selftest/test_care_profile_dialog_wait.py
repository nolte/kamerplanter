"""`PflegeDashboardPage.wait_for_profile_dialog` waits for the form, not the frame.

Since #3077 the care-profile dialog opens at once with a loading skeleton and
renders the form only once the requested plant's profile has arrived. A wait
that returned on the visible dialog let TC-REQ-022-036 read the watering slider
from the skeleton (nightly 44931220064, `full`): the failure screenshot, taken a
moment later, shows the loaded form.

Browser-free: the real page object over `FakeDriver`, whose DOM advances one
snapshot per missed lookup, so "returned before the form existed" is observable.
"""

from __future__ import annotations

import pytest

from tests.e2e.pages.pflege_dashboard_page import PflegeDashboardPage

from .fake_driver import FakeDriver

DIALOG = PflegeDashboardPage.PROFILE_DIALOG[1]
FORM = f"{DIALOG} {PflegeDashboardPage.CARE_STYLE_SELECT[1]}"
ERROR = f"{DIALOG} {PflegeDashboardPage.ERROR_DISPLAY[1]}"


def page_for(driver: FakeDriver) -> PflegeDashboardPage:
    return PflegeDashboardPage(driver, "http://app.invalid")  # type: ignore[arg-type]


def test_does_not_return_while_the_dialog_shows_only_its_skeleton() -> None:
    driver = FakeDriver({DIALOG}, {DIALOG}, {DIALOG, FORM})

    page_for(driver).wait_for_profile_dialog(timeout=5)

    assert FORM in driver.present


def test_a_loaded_form_passes_even_though_no_error_display_exists() -> None:
    driver = FakeDriver({DIALOG, FORM})

    page_for(driver).wait_for_profile_dialog(timeout=5)

    assert ERROR not in driver.present


def test_a_load_error_fails_naming_that_state() -> None:
    driver = FakeDriver({DIALOG}, {DIALOG, ERROR})

    with pytest.raises(AssertionError, match="load error"):
        page_for(driver).wait_for_profile_dialog(timeout=5)
