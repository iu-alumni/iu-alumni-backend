from __future__ import annotations

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class AdminEventDetailsPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.approve_button = page.get_by_role("button", name="Approve Event")
        self.cancel_button = page.get_by_role("button", name="Cancel Event")

    def approve(self) -> None:
        self.approve_button.click()

    def expect_approved(self) -> None:
        expect(self.page.get_by_text("Event Approved", exact=True)).to_be_visible()
