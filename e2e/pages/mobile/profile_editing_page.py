from __future__ import annotations

from playwright.sync_api import Page, expect

from utils.flutter import tap_by_text, type_into


class MobileProfileEditingPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        # Pre-filled with the current profile's data, so — same as the
        # registration screen's email/password — Flutter never exposes an
        # `aria-label` here (no empty field, no hint to show). Positional
        # lookup instead, in `profile_editing_content.dart`'s field order
        # (First Name, Last Name, Biography, Telegram).
        textboxes = page.get_by_role("textbox")
        self.first_name_input = textboxes.nth(0)
        self.last_name_input = textboxes.nth(1)

    def is_loaded(self) -> None:
        expect(self.page.get_by_text("Editing profile", exact=True)).to_be_visible()

    def set_first_name(self, first_name: str) -> None:
        type_into(self.first_name_input, first_name)

    def set_last_name(self, last_name: str) -> None:
        type_into(self.last_name_input, last_name)

    def save(self) -> None:
        tap_by_text(self.page, "Save").click()
