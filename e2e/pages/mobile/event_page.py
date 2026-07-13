from __future__ import annotations

from playwright.sync_api import Page, expect


class MobileEventPage:
    def __init__(self, page: Page) -> None:
        self.page = page

    def expect_details(self, *, title: str, description: str) -> None:
        expect(self.page.get_by_text(title, exact=False)).to_be_visible()
        expect(self.page.get_by_text(description, exact=False)).to_be_visible()

    def expect_location(self, location: str) -> None:
        expect(self.page.get_by_text(location, exact=False)).to_be_visible()

    def open_participants(self) -> None:
        self.page.get_by_text("Participants", exact=True).click()

    def expect_action_button(self, label: str) -> None:
        """Label is one of: 'Edit', 'Participate', "I won't come"."""
        expect(self.page.get_by_text(label, exact=True)).to_be_visible()
