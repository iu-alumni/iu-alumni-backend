from __future__ import annotations

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


_WRONG_CREDENTIALS_MESSAGE = "Incorrect password or e-mail"


class AdminLoginPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.email_input = page.get_by_placeholder("E-mail")
        self.password_input = page.get_by_placeholder("Password")
        self.continue_button = page.get_by_role("button", name="Continue")

    def login(self, email: str, password: str) -> None:
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.continue_button.click()

    def expect_wrong_credentials_error(self) -> None:
        expect(self.page.get_by_text(_WRONG_CREDENTIALS_MESSAGE)).to_be_visible()
