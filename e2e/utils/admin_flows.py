from __future__ import annotations

from playwright.sync_api import Browser, expect

from config import settings
from pages.admin.login_page import AdminLoginPage
from pages.admin.users_page import AdminUsersPage


_DESKTOP_VIEWPORT = {"width": 1440, "height": 900}


def verify_user(browser: Browser, email: str) -> None:
    context = browser.new_context(viewport=_DESKTOP_VIEWPORT, ignore_https_errors=True)
    try:
        page = context.new_page()
        page.goto(settings.admin_base_url)
        AdminLoginPage(page).login(settings.admin_email, settings.admin_password)
        expect(page.get_by_role("button", name="Logout")).to_be_visible()

        users_page = AdminUsersPage(page)
        users_page.goto()
        users_page.search_input.fill(email)
        users_page.verify_user(email)
        users_page.expect_verified(email)
    finally:
        context.close()
