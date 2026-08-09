"""Page object for the Dashboard page."""

from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from .base_page import DEFAULT_TIMEOUT, BasePage


class DashboardPage(BasePage):
    """Interact with the Dashboard page (``/dashboard``)."""

    PATH = "/dashboard"

    # Locators
    PAGE = (By.CSS_SELECTOR, "[data-testid='dashboard-page']")
    #: Removed in the REQ-045 widget-dashboard redesign (`DashboardPage.tsx` no
    #: longer renders a static welcome banner) -- kept only as documentation for
    #: `get_welcome_text` below, whose one call site permanently skips before
    #: ever reaching it.
    WELCOME = (By.CSS_SELECTOR, "[data-testid='dashboard-welcome']")
    QUICK_ACTIONS = (By.CSS_SELECTOR, "[data-testid^='quick-action-']")
    #: The `quick_actions` widget's own root. `widgetRegistry.ts` dynamically
    #: imports `QuickActionsWidget` (`lazy(() => import(...))`), and
    #: `WidgetFrame.tsx` renders it behind a bare, un-testid'd `<Skeleton>`
    #: while that chunk is in flight -- `wait_for_loading_complete()` cannot
    #: observe that fallback, it only polls `[data-testid='loading-skeleton']`.
    #: A read of `QUICK_ACTIONS` taken right after `open()` can therefore land
    #: in the window before the chunk resolves and report zero cards, the same
    #: pre-fetch-window defect `wait_for_list_content` guards against on the
    #: DataTable cluster (#946).
    WIDGET_QUICK_ACTIONS = (By.CSS_SELECTOR, "[data-testid='widget-quick_actions']")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def open(self) -> DashboardPage:
        self.navigate(self.PATH)
        self.wait_for_element(self.PAGE)
        self.wait_for_loading_complete()
        return self

    def wait_for_quick_actions_widget(self, timeout: int = DEFAULT_TIMEOUT) -> None:
        """Wait until the quick-actions widget's lazy chunk has rendered.

        See :data:`WIDGET_QUICK_ACTIONS` for why this is needed -- the widget's
        own root is the durable signal, not its `quick-action-*` children,
        which do not exist at all until the same commit that mounts the root.
        """
        self.wait_for_element(self.WIDGET_QUICK_ACTIONS, timeout=timeout)

    def get_welcome_text(self) -> str:
        return self.wait_for_element_visible(self.WELCOME).text

    def get_quick_action_count(self) -> int:
        """Return the number of visible quick-action cards.

        Dead code (no call site) but fixed in passing: ``find_all_by_testid``
        builds an *exact* ``[data-testid='quick-action-']`` selector, which no
        real card testid (``quick-action-/stammdaten/species`` etc.) ever
        equals -- this always answered ``0``, independent of the anchor above.
        Reuses :data:`QUICK_ACTIONS`, the *prefix* locator, like
        :meth:`get_quick_actions` already does.
        """
        self.wait_for_quick_actions_widget()
        return len(self.driver.find_elements(*self.QUICK_ACTIONS))

    def get_quick_actions(self) -> list[str]:
        """Return ``data-testid`` values of all quick-action cards."""
        self.wait_for_quick_actions_widget()
        elements = self.driver.find_elements(*self.QUICK_ACTIONS)
        return [el.get_attribute("data-testid") or "" for el in elements]

    def click_quick_action(self, path: str) -> None:
        """Click the quick-action card whose testid ends with *path*."""
        locator = (By.CSS_SELECTOR, f"[data-testid='quick-action-{path}']")
        self.wait_for_element_clickable(locator).click()
