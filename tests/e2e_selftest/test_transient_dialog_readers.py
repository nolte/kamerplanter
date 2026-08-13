"""The dialog-open readers that were never migrated onto `is_any_displayed`.

## What this pins, and why it exists

`BasePage.is_any_displayed` already records the decision every "is this dialog
still open?" reader has to make: a reference that dies **while being read** means
the dialog is *gone*, not "look again" — see the "Staleness as a *verdict*" block
in `tests/e2e/pages/base_page.py`. Three page objects were routed through it;
seven more kept their own copy of the loop:

    dialogs = self.driver.find_elements(*self.CREATE_DIALOG)
    return any(d.is_displayed() for d in dialogs)

That copy has no verdict in it. MUI unmounts a `Dialog` only after its exit
transition finishes (~195 ms), so the window between the `find_elements` and the
`is_displayed()` is exactly the window a cancelled dialog dies in — and the read
then raises `StaleElementReferenceException` out of the *test*, where it reads
as a defect in the application rather than in the reader.

It is not hypothetical. `test_cancel_create_dialog_closes_without_saving`
(TC-004-006) failed on this line in **every** nightly run between 2026-08-10 and
2026-08-13, across the `light`, `full`, `full-tablet` and `full-mobile`
profiles — always with the same stack, always through
`FertilizerListPage.is_create_dialog_open`.

Each test below therefore asserts the contract at **both** polarities, because a
reader that answered ``False`` unconditionally would satisfy the staleness half
on its own and certify nothing:

* a dying reference answers ``False`` instead of raising, and
* an attached, displayed dialog still answers ``True``.

## Why the driver is stubbed and nothing else is

Same technique and reason as `test_row_helpers.py`: a **real**
`selenium.webdriver.remote.webdriver.WebDriver` over a fake command executor, so
the real page objects and the real `is_any_displayed` run unmodified — only the
wire is fake. Provoking the unmount at the precise instant between two commands
in a real browser is the flakiest imaginable way to assert a deterministic
contract; it is what the nightly has been doing by accident.

This is a browser-free unit test and belongs in this tier, never under
`tests/e2e/` — see `tests/e2e_selftest/README.md`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import pytest
from selenium.webdriver.common.options import ArgOptions
from selenium.webdriver.remote.webdriver import WebDriver

from tests.e2e.pages.base_page import BasePage
from tests.e2e.pages.disease_list_page import DiseaseListPage
from tests.e2e.pages.fertilizer_detail_page import FertilizerDetailPage
from tests.e2e.pages.fertilizer_list_page import FertilizerListPage
from tests.e2e.pages.nutrient_plan_detail_page import NutrientPlanDetailPage
from tests.e2e.pages.nutrient_plan_list_page import NutrientPlanListPage
from tests.e2e.pages.pest_list_page import PestListPage
from tests.e2e.pages.treatment_list_page import TreatmentListPage

# The stub itself, not the fixture function — see the note in
# `test_list_page_readers.py` for why the fixture is re-declared locally
# instead of imported (Ruff F811 cannot tell a fixture re-export from a shadow).
from .test_row_helpers import Harness, StubConnection, StubNode, TableDom


@pytest.fixture
def harness() -> Harness:
    dom = TableDom()
    connection = StubConnection(dom)
    driver = WebDriver(command_executor=connection, options=ArgOptions())
    return Harness(dom, connection, driver)


def _render_class_dialog(dom: TableDom, css_class: str) -> StubNode:
    """Render a dialog addressed by a bare class (`FertilizerListPage`'s shape).

    `FertilizerListPage.CREATE_DIALOG` is ``.MuiDialog-root`` — the one dialog
    locator in this set that is neither a testid nor the structural
    ``.MuiDialog-root [role='dialog']`` the stub models with `render_mui_dialog`.
    """
    node = StubNode("class-dialog", testid="", css_class=css_class)
    dom.root.children.append(node)
    return node


@dataclass(frozen=True)
class Reader:
    """One reader that owned a private copy of the `is_any_displayed` loop.

    *render* differs per entry because the locators do: a bare class
    (`FertilizerListPage`), the structural MUI selector (the four list pages
    addressing ``.MuiDialog-root [role='dialog']``) and plain testids (the two
    `confirm-dialog` readers and `NutrientPlanListPage`).
    """

    name: str
    page_class: type[BasePage]
    method: str
    locator: tuple[str, str]
    render: Callable[[TableDom], StubNode]


READERS: list[Reader] = [
    Reader(
        "FertilizerListPage.is_create_dialog_open",
        FertilizerListPage,
        "is_create_dialog_open",
        FertilizerListPage.CREATE_DIALOG,
        lambda dom: _render_class_dialog(dom, "MuiDialog-root"),
    ),
    Reader(
        "DiseaseListPage.is_create_dialog_open",
        DiseaseListPage,
        "is_create_dialog_open",
        DiseaseListPage.CREATE_DIALOG,
        lambda dom: dom.render_mui_dialog(),
    ),
    Reader(
        "PestListPage.is_create_dialog_open",
        PestListPage,
        "is_create_dialog_open",
        PestListPage.CREATE_DIALOG,
        lambda dom: dom.render_mui_dialog(),
    ),
    Reader(
        "TreatmentListPage.is_create_dialog_open",
        TreatmentListPage,
        "is_create_dialog_open",
        TreatmentListPage.CREATE_DIALOG,
        lambda dom: dom.render_mui_dialog(),
    ),
    Reader(
        "NutrientPlanListPage.is_create_dialog_open",
        NutrientPlanListPage,
        "is_create_dialog_open",
        NutrientPlanListPage.CREATE_DIALOG,
        lambda dom: dom.render_dialog("nutrient-plan-create-dialog"),
    ),
    Reader(
        "NutrientPlanDetailPage.is_confirm_dialog_open",
        NutrientPlanDetailPage,
        "is_confirm_dialog_open",
        NutrientPlanDetailPage.CONFIRM_DIALOG,
        lambda dom: dom.render_dialog("confirm-dialog"),
    ),
    Reader(
        "FertilizerDetailPage.is_confirm_dialog_open",
        FertilizerDetailPage,
        "is_confirm_dialog_open",
        FertilizerDetailPage.CONFIRM_DIALOG,
        lambda dom: dom.render_dialog("confirm-dialog"),
    ),
]


@pytest.mark.parametrize("reader", READERS, ids=[r.name for r in READERS])
class TestDialogReadersAnswerRatherThanRaise:
    """Each reader is a *verdict* site: it answers with the staleness, or it lies."""

    def test_a_dying_reference_reads_as_closed(self, harness: Harness, reader: Reader) -> None:
        """The node unmounts between the lookup and the read — as on cancel.

        Without the verdict this raises `StaleElementReferenceException` out of
        the reader and the *test* is reported as failed, which is what the
        nightly has been reporting since 2026-08-10.
        """
        node = reader.render(harness.dom)
        elements = harness.driver.find_elements(*reader.locator)
        node.attached = False
        harness.find_elements_always_returns(elements[0])
        page = reader.page_class(harness.driver, "http://stub.invalid")

        assert getattr(page, reader.method)() is False

    def test_an_attached_dialog_still_reads_as_open(self, harness: Harness, reader: Reader) -> None:
        """The other polarity, without which the test above certifies nothing.

        A reader hard-wired to ``False`` would pass every staleness assertion in
        this module. This is the assertion it could not pass.
        """
        reader.render(harness.dom)
        page = reader.page_class(harness.driver, "http://stub.invalid")

        assert getattr(page, reader.method)() is True
