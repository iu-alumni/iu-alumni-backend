from __future__ import annotations

from playwright.sync_api import Page, expect

from pages.base_page import BasePage
from utils.flutter import tap_by_text, type_into


class MobileLoginPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        # Not `get_by_label` — this screen is revisited after registration
        # with the email/password already carried over and still filled in,
        # and Flutter drops a field's `aria-label` once it's non-empty (a
        # hint doesn't apply to filled fields). Confirmed live: `get_by_label`
        # then times out on the very re-visit a duplicate-email /
        # wrong-password test needs. Position is stable regardless of fill
        # state — this screen only ever has these two fields, in this order.
        fields = page.locator("input, textarea")
        self.email_input = fields.nth(0)
        self.password_input = fields.nth(1)

    def is_loaded(self) -> None:
        expect(self.page.get_by_text("Authorization", exact=True)).to_be_visible()

    def fill_credentials(self, email: str, password: str) -> None:
        type_into(self.email_input, email)
        type_into(self.password_input, password)

    def submit(self) -> None:
        tap_by_text(self.page, "Sign in").click()

    def login(self, email: str, password: str) -> None:
        self.fill_credentials(email, password)
        self.submit()

    def go_to_register(self) -> None:
        """Open the registration form, carrying over whatever was typed above."""
        tap_by_text(self.page, "Register").click()

    def expect_message(self, text: str) -> None:
        expect(self.page.get_by_text(text, exact=False)).to_be_visible()
