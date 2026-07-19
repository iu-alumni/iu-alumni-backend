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

    def refresh(self) -> None:
        """Reload the current /events page and wait for the real
        approval-settings response — not just for *a* button to render.

        Unlike navigating to a *different* section, `page.reload()` here
        is safe — the admin token lives in localStorage, not just memory,
        so a reload keeps the session. Critical detail: `isVerificationEnabled`
        in `events/index.vue` defaults to `false` (showing "Auto-approve
        (Off)") until the settings fetch resolves — so a "some button is
        visible" check reads that default as truth and can be wrong in
        either direction. Waiting for the actual network response is what
        makes `set_auto_approve()` below reliable instead of a coin flip.
        """
        with self.page.expect_response(lambda r: "settings/events" in r.url):
            self.page.reload()
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

        Always refreshes first — `refresh()` guarantees the button reflects
        the real, server-confirmed state by the time we read it, so a
        single read-then-click-if-needed is enough; no retry loop blindly
        re-clicking, which risks flipping it back and forth.
        """
        self.refresh()
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
        with self.page.expect_response(lambda r: "toggle-auto-approve" in r.url):
            other.click()
        expect(desired).to_be_visible()
