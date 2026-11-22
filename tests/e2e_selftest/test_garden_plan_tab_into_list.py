"""`GardenPlanPage.tab_into_list` starts its Tab walk at the "Liste" tab, not wherever focus was left.

`open_tab` activates the tab with `HTMLElement.click()`, which neither focuses it nor moves
Chrome's sequential focus navigation starting point. TC-053-009 then tabbed from the
document start (nightly 44931220064, `light`, desktop): through the header and the whole
sidebar, and its 25 presses ended on the sidebar entry "Import" without reaching the list.

Browser-free: the real page object over a driver that models only the focus and the
document's Tab order, so "where the first Tab lands" is observable.
"""

from __future__ import annotations

from tests.e2e.pages.garden_plan_page import GardenPlanPage

from .fake_driver import FakeElement

LIST_TAB = "[data-testid='garden-plan-tab-list']"
#: Header and sidebar stops before the editor: more than the walk's 25 presses.
CHROME = [f"chrome-{i}" for i in range(30)]
EDITOR = [LIST_TAB, "feldmodus", "seitenpanel", "overflow"]
ROW = "row:bed_1"


class TabOrderDriver:
    """The focus and the Tab order of a page, nothing else."""

    def __init__(self, *, tab_inline: bool = True) -> None:
        self.order = [*CHROME, *EDITOR, ROW]
        self.focused: str | None = None  # the body: the first Tab goes to the first stop
        self.tab_inline = tab_inline

    def press_tab(self) -> None:
        start = -1 if self.focused is None else self.order.index(self.focused)
        self.focused = self.order[(start + 1) % len(self.order)]

    def find_elements(self, _by: str, value: str) -> list[FakeElement]:
        return [FakeElement(value, displayed=self.tab_inline)] if value == LIST_TAB else []

    def find_element(self, by: str, value: str) -> FakeElement:
        return self.find_elements(by, value)[0]

    def execute_script(self, script: str, *args: object) -> object:
        if "focus()" in script and args and isinstance(args[0], FakeElement):
            self.focused = args[0].selector
            return None
        if "activeElement" in script and "data-list-key" in script:
            return (
                self.focused.split(":", 1)[1]
                if self.focused and self.focused.startswith("row:")
                else None
            )
        raise AssertionError(f"TabOrderDriver got an unexpected script: {script[:60]!r}")


def page_for(driver: TabOrderDriver) -> GardenPlanPage:
    page = GardenPlanPage(driver, "http://app.invalid")  # type: ignore[arg-type]
    page.press = lambda *_keys: driver.press_tab()  # type: ignore[method-assign]
    return page


def test_the_walk_starts_at_the_list_tab_even_when_the_focus_was_on_the_body() -> None:
    driver = TabOrderDriver()

    assert page_for(driver).tab_into_list() == "bed_1"


def test_below_md_the_walk_keeps_the_focus_the_overflow_menu_handed_back() -> None:
    driver = TabOrderDriver(tab_inline=False)
    driver.focused = "overflow"

    assert page_for(driver).tab_into_list() == "bed_1"
