"""What the screenshot checkpoint may hold the capture to, and what it may not.

## The failures this comes from

Two `full-mobile` login tests failed in the 2026-08-13 nightly inside
`screenshot(...)`, in `conftest._settle_after_capture`:

    the viewport was 524x1136 before the capture and reads (393, 852) 5.0s after

and, in the other test, the same pair reversed. Reproduced locally in 45 s by
running `test_req023_login.py` alone against the `full-mobile` stack, then
measured from inside the failing page:

    inner: [524, 1136]   visualViewport: [393, scale 1]   screen: [393, 852]
    dpr: 3   UA: iPhone   meta: width=device-width, initial-scale=1.0

Nothing about the emulation was lost. ``innerWidth`` is the **layout** viewport,
which Chrome widens to the document's minimum width when the page overflows
horizontally -- the login route needs 524 CSS px on a 393 px device -- so it
reports the *page's* width, and moves whenever the page's content does.

Switching the check to ``visualViewport`` made those two tests pass and eleven
`full`-profile tests fail: the visual viewport excludes the classic scrollbar,
so it reads 1905 with one and 1920 without, and the scrollbar comes and goes
with the content height.

Both readings were the application re-rendering between the two reads, reported
as a browser that had failed to restore. Against a *settled* page the capture is
passive on both profiles -- six captures each, every quantity identical before
and after -- which is what makes "any difference is a defect" the wrong test.

## What replaced it

`captureBeyondViewport` stretches the layout viewport **to the document height**.
A capture that failed to put it back therefore leaves a viewport as tall as the
whole document, which is content-independent and unmistakable. That signature is
what `_settle_after_capture` now waits out and, if it persists, raises on.

This module pins both directions, because the cheap way to stop a check firing
is to stop it checking:

* a page that re-renders around the capture is **not** a failure, and
* a viewport left stretched to the document height still **is** one.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from selenium.common.exceptions import WebDriverException

from tests.e2e.conftest import _cdp_full_page_screenshot, _settle_after_capture

#: A 1x1 transparent PNG, base64 — the capture writes bytes and nothing reads them.
PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
    "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)

#: The `mobile` profile's viewport height, and a document several screens long.
VIEWPORT_H = 852
DOCUMENT_H = 3400


class FakePage:
    """A page whose viewport height and document height move independently.

    *stretches* models the defect: the capture leaves the viewport as tall as
    the document. *reflow_to* models the application: a React commit changes the
    page's own size while the capture is in flight, which is what produced every
    false failure this guard has ever reported.
    """

    def __init__(
        self,
        *,
        viewport: int = VIEWPORT_H,
        document: int = DOCUMENT_H,
        scale: int = 100,
        stretches: bool = False,
        reflow_to: tuple[int, int] | None = None,
        rescale_to: tuple[int, int, int] | None = None,
    ) -> None:
        self.viewport = viewport
        self.document = document
        self.scale = scale
        self.stretches = stretches
        self.reflow_to = reflow_to
        self.rescale_to = rescale_to
        self.probes = 0

    def execute_cdp_cmd(self, cmd: str, _params: dict[str, Any]) -> dict[str, Any]:
        if cmd != "Page.captureScreenshot":
            raise WebDriverException(f"unmodelled CDP command: {cmd}")
        if self.stretches:
            self.viewport = self.document
        if self.reflow_to is not None:
            self.viewport, self.document = self.reflow_to
        if self.rescale_to is not None:
            self.viewport, self.document, self.scale = self.rescale_to
        return {"data": PNG_B64}

    def execute_script(self, script: str, *_args: Any) -> Any:
        if "visualViewport" in script:
            self.probes += 1
            return [self.viewport, self.document, self.scale]
        raise WebDriverException(f"unmodelled script: {script[:40]!r}")

    def execute_async_script(self, _script: str, *_args: Any) -> Any:
        return "frames"

    def save_screenshot(self, _path: str) -> None:  # pragma: no cover - fallback path
        raise AssertionError("the CDP path must not fall back in these tests")


@pytest.fixture
def png(tmp_path: Path) -> Path:
    return tmp_path / "checkpoint.png"


class TestThePageIsAllowedToMove:
    """The thirteen false failures, in the two shapes they were measured in."""

    def test_a_page_that_grows_around_the_capture_is_not_a_failure(self, png: Path) -> None:
        """An error alert mounts: the document gets taller, the viewport does not."""
        page = FakePage(reflow_to=(VIEWPORT_H, DOCUMENT_H + 900))

        _cdp_full_page_screenshot(page, png)  # must not raise

        assert png.read_bytes(), "the image must still have been written"

    def test_a_page_that_shrinks_around_the_capture_is_not_a_failure(self, png: Path) -> None:
        """A spinner unmounts and the document now fits the viewport.

        The viewport then *equals* the document height, which is the stretched
        state's first condition -- and must not be read as one, because the
        viewport did not grow.
        """
        page = FakePage(reflow_to=(VIEWPORT_H, VIEWPORT_H))

        _cdp_full_page_screenshot(page, png)  # must not raise

    def test_a_short_page_is_never_flagged(self, png: Path) -> None:
        """A login form that fits: viewport == document before *and* after."""
        page = FakePage(viewport=VIEWPORT_H, document=VIEWPORT_H)

        _cdp_full_page_screenshot(page, png)  # must not raise

    def test_a_page_that_starts_overflowing_horizontally_is_not_a_failure(self, png: Path) -> None:
        """The measured regress, reduced (login route, `full-mobile`, 2026-08-13).

        Chrome rescales the whole layout space when a page begins to overflow
        horizontally, so the viewport *and* the document jump by the same factor:
        852px tall becomes 1136 against a 1136px document. Read without the scale
        regime that is indistinguishable from "stretched to the document height"
        -- it satisfies both height conditions exactly -- and it fired on a real
        run while this module's other cases stayed green.
        """
        page = FakePage(
            viewport=VIEWPORT_H,
            document=DOCUMENT_H,
            rescale_to=(1136, 1136, 133),
        )

        _cdp_full_page_screenshot(page, png)  # must not raise


class TestTheCaptureIsNotAllowedToStretch:
    """The defect the guard exists for, which must survive the fix."""

    def test_a_viewport_left_at_the_document_height_fails(self, png: Path) -> None:
        page = FakePage(stretches=True)

        with pytest.raises(AssertionError, match="stretched to the document height"):
            _cdp_full_page_screenshot(page, png)

    def test_the_wait_gives_a_late_restore_its_budget(self, png: Path) -> None:
        """A capture that restores a few polls late must pass, not fail.

        The wait is the reason this is a settling helper and not a bare
        assertion -- Chrome restores before the response today, and this keeps
        being true if it ever restores just after one.
        """
        page = FakePage(stretches=True)
        original_probe = page.execute_script

        def restore_on_third_probe(script: str, *args: Any) -> Any:
            result = original_probe(script, *args)
            if page.probes == 3:
                page.viewport = VIEWPORT_H
            return result

        page.execute_script = restore_on_third_probe  # type: ignore[method-assign]

        _cdp_full_page_screenshot(page, png)  # must not raise

    def test_an_unaskable_page_is_not_reported_as_a_defect(self) -> None:
        """`None` means "could not look", never "it broke"."""

        class Dead(FakePage):
            def execute_script(self, script: str, *_args: Any) -> Any:
                raise WebDriverException("session is gone")

        _settle_after_capture(Dead(), (VIEWPORT_H, DOCUMENT_H, 100))  # must not raise
        _settle_after_capture(Dead(), None)  # must not raise
