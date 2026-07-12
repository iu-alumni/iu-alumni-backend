from __future__ import annotations

from playwright.sync_api import Locator, Page, expect

from pages.base_page import BasePage


class AdminUsersPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)
        self.search_input = page.get_by_placeholder("Search by name or email...")

    def goto(self) -> None:
        """Open the Users section via the sidebar link.

        Not `page.goto()` — confirmed live that a hard navigation drops the
        admin session (it's kept in memory, not a cookie) and bounces back
        to the sign-in screen. `level=2` picks the page's own heading, not
        the sidebar nav link's (which is *also* an accessible "Users"
        heading, just at level 5). Scoped to the `banner` landmark because
        the Dashboard overview page (where login lands) can *also* render
        its own "Users" quick-link in the main content area once its widgets
        finish loading — confirmed live as an intermittent strict-mode
        "2 elements" failure once that second link had time to render.
        """
        self.page.get_by_role("banner").get_by_role("link", name="Users").click()
        expect(self.page.get_by_role("heading", name="Users", level=2)).to_be_visible()

    def row(self, email: str) -> Locator:
        row = self.page.locator("div.border-t:visible", has_text=email)
        row.wait_for(state="visible")
        return row

    def verify_user(self, email: str) -> None:
        self.row(email).get_by_role("button", name="Verify", exact=True).click()

    def ban_user(self, email: str) -> None:
        self.row(email).get_by_role("button", name="Ban", exact=True).click()

    def unban_user(self, email: str) -> None:
        self.row(email).get_by_role("button", name="Unban", exact=True).click()

    def expect_verified(self, email: str) -> None:
        expect(self.row(email).get_by_text("Verified", exact=True)).to_be_visible()

    def expect_banned(self, email: str) -> None:
        expect(
            self.row(email).get_by_role("button", name="Unban", exact=True),
        ).to_be_visible()
