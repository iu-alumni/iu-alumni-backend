from __future__ import annotations

from playwright.sync_api import Page, expect

from utils.data_factory import TestEvent
from utils.flutter import tap_by_text, type_into


class MobileEventEditingPage:
    def __init__(self, page: Page) -> None:
        self.page = page
        self.title_input = page.get_by_label("How is the event called?")
        self.description_input = page.get_by_label(
            "Briefly, describe what the event is about, what you are planning to do, etc.",
        )
        self.location_search_input = page.get_by_label("Enter a city")

    def set_location(self, query: str) -> None:
        tap_by_text(self.page, "No location").click()
        type_into(self.location_search_input, query)
        suggestion = self.page.get_by_text(query, exact=False).first
        suggestion.wait_for(state="visible")
        suggestion.click()

    def fill_required_fields(self, event: TestEvent) -> None:
        type_into(self.title_input, event.title)
        type_into(self.description_input, event.description)
        self.set_location(event.location)

    def submit_new_event(self) -> None:
        tap_by_text(self.page, "Post event").click()

    def create(self, event: TestEvent) -> None:
        self.fill_required_fields(event)
        self.submit_new_event()

    def expect_error(self, text: str = "Could not save the event") -> None:
        expect(self.page.get_by_text(text, exact=False)).to_be_visible()

    def expect_rejected(self) -> None:
        """Confirms an invalid submission didn't go through.

        Not a specific error message — confirmed live that submitting with
        every field empty shows no error text at all within a generous
        timeout (unclear whether that's a slow request or a silent no-op).
        What's reliably true either way: a rejected/blocked submission never
        navigates away from this screen. Anchored on "Choose cover" rather
        than the submit button's own label — confirmed live that label
        turns into a bare loading spinner (no text) while a save is still
        in flight, so it isn't a stable "we're still here" signal by itself.
        """
        expect(self.page.get_by_text("Choose cover", exact=True)).to_be_visible()
