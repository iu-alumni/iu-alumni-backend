from __future__ import annotations

from playwright.sync_api import Page, expect

from pages.base_page import BasePage
from utils.flutter import enable_semantics, tap_by_text


class MobileEventsListPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def is_loaded(self) -> None:
        expect(self.page.get_by_text("Events", exact=True)).to_be_visible()

    def open_create_event(self) -> None:
        tap_by_text(self.page, "Create").click()

    def open_event(self, title: str) -> None:
        tap_by_text(self.page, title, exact=False).click()

    def refresh(self) -> None:
        # A full reload resets Flutter's accessibility bridge.
        self.page.reload()
        enable_semantics(self.page)
        self.is_loaded()

    def expect_event_visible(self, title: str) -> None:
        expect(self.page.get_by_text(title, exact=False)).to_be_visible()
