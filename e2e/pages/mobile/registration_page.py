from __future__ import annotations

from playwright.sync_api import Page, expect

from pages.base_page import BasePage
from utils.data_factory import TestUser
from utils.flutter import tap_by_text, type_into


class MobileRegistrationPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.first_name_input = page.get_by_label("First name")
        self.last_name_input = page.get_by_label("Last name")
        self.telegram_input = page.get_by_label("Telegram alias")

    def is_loaded(self) -> None:
        expect(self.page.get_by_text("Registration", exact=True)).to_be_visible()

    def pick_graduation_year(self, year: int) -> None:
        tap_by_text(self.page, "Graduation year").click()
        tap_by_text(self.page, str(year)).click()

    def fill(self, user: TestUser) -> None:
        type_into(self.first_name_input, user.first_name)
        type_into(self.last_name_input, user.last_name)
        self.pick_graduation_year(user.graduation_year)
        type_into(self.telegram_input, user.telegram_alias)

    def submit(self) -> None:
        tap_by_text(self.page, "Register").click()

    def register(self, user: TestUser) -> None:
        self.fill(user)
        self.submit()

    def expect_message(self, text: str) -> None:
        expect(self.page.get_by_text(text, exact=False)).to_be_visible()
