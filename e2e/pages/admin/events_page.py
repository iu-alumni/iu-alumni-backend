from __future__ import annotations

import re

from playwright.sync_api import Locator, Page, expect

from pages.base_page import BasePage


_STATUS_PATTERN = re.compile(r"^(Pending|Approved|Rejected)$")


class AdminEventsPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.search_input = page.get_by_placeholder("Search...")

    def goto(self) -> None:
        """Open the Events section via the sidebar link — see
        `AdminUsersPage.goto()` for why not `page.goto()`.
        """
        self.page.get_by_role("link", name="Events").click()
        expect(self.page.get_by_role("heading", name="Events", level=2)).to_be_visible()

    def row(self, event_title: str) -> Locator:
        """The single table row for `event_title` (desktop layout)."""
        return self.page.locator("div.divide-y > div", has_text=event_title)

    def status_of(self, event_title: str) -> Locator:
        return self.row(event_title).get_by_text(_STATUS_PATTERN)

    def open_details(self, event_title: str) -> None:
        """Equivalent of the scenario's "View Details" step.

        The row's only labelled-enough control is its first icon button
        (pencil / edit, see `EventTable.vue`), which navigates to
        `/events/{id}` — the same detail page an "View Details" link would.
        """
        self.row(event_title).locator("button").first.click()

    def set_auto_approve(self, *, enabled: bool) -> None:
        """Ensure the "Auto-approve" toggle is in the given state.

        The button's own label always reflects the *current* state (see
        `pages/events/index.vue`), so we only click it when it doesn't
        already say what we want.
        """
        desired = self.page.get_by_role(
            "button",
            name=f"Auto-approve ({'On' if enabled else 'Off'})",
        )
        if desired.is_visible():
            return
        other = self.page.get_by_role(
            "button",
            name=f"Auto-approve ({'Off' if enabled else 'On'})",
        )
        other.click()
        expect(desired).to_be_visible()
