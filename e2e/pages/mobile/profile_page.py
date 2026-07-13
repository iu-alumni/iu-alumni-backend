from __future__ import annotations

from playwright.sync_api import Page, expect

from utils.flutter import tap_by_text


class MobileProfilePage:
    def __init__(self, page: Page) -> None:
        self.page = page

    def is_loaded(self) -> None:
        expect(self.page.get_by_text("Profile", exact=True)).to_be_visible()

    def open_edit(self) -> None:
        tap_by_text(self.page, "Edit").click()

    def logout(self) -> None:
        tap_by_text(self.page, "Logout").click()

    def expect_name(self, full_name: str) -> None:
        expect(self.page.get_by_text(full_name, exact=False)).to_be_visible()
