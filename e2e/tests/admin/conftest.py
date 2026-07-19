from __future__ import annotations

from playwright.sync_api import Page, expect
import pytest

from config import settings
from pages.admin.login_page import AdminLoginPage


@pytest.fixture
def admin_page(page: Page) -> Page:
    page.goto(settings.admin_base_url)
    return page


@pytest.fixture
def authenticated_admin_page(admin_page: Page) -> Page:
    AdminLoginPage(admin_page).login(settings.admin_email, settings.admin_password)
    expect(admin_page.get_by_role("button", name="Logout")).to_be_visible()
    return admin_page
