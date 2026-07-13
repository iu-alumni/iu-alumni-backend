from __future__ import annotations

from playwright.sync_api import Locator, Page


_GLASS_PANE = "flt-glass-pane"
_SEMANTICS_PLACEHOLDER = "flt-semantics-placeholder"

MOBILE_VIEWPORT = {"width": 414, "height": 896}


def wait_for_app_ready(page: Page) -> None:
    page.locator(_GLASS_PANE).wait_for(state="attached")


def enable_semantics(page: Page) -> None:
    # Flutter Web paints to a <canvas>; locators only see widgets once its
    # accessibility bridge is on. The "Enable accessibility" placeholder is
    # a 1x1px, visually-hidden-but-focusable element, so a coordinate-based
    # .click() fails ("outside of the viewport") — dispatch_event bypasses
    # that.
    wait_for_app_ready(page)
    placeholder = page.locator(_SEMANTICS_PLACEHOLDER)
    placeholder.wait_for(state="attached")
    placeholder.dispatch_event("click")
    placeholder.wait_for(state="detached")


def tap_by_text(page: Page, text: str, *, exact: bool = True) -> Locator:
    locator = page.get_by_text(text, exact=exact)
    locator.wait_for(state="visible")
    return locator


def type_into(locator: Locator, text: str) -> None:
    # .fill() silently fails to update Flutter's TextEditingController on
    # some fields; real keystrokes via press_sequentially don't.
    locator.click()
    locator.press("Control+A")
    locator.press("Delete")
    locator.press_sequentially(text, delay=15)
