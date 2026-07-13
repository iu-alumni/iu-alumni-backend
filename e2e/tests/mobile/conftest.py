from __future__ import annotations

from playwright.sync_api import Page
import pytest

from config import settings
from pages.mobile.events_list_page import MobileEventsListPage
from pages.mobile.login_page import MobileLoginPage
from utils.data_factory import TestUser, new_test_user
from utils.flutter import MOBILE_VIEWPORT, enable_semantics


@pytest.fixture
def browser_context_args(browser_context_args: dict) -> dict:
    return {**browser_context_args, "viewport": MOBILE_VIEWPORT}


@pytest.fixture
def mobile_page(page: Page) -> Page:
    page.goto(settings.mobile_base_url)
    enable_semantics(page)
    return page


@pytest.fixture
def test_user() -> TestUser:
    return new_test_user()


@pytest.fixture
def logged_in_page(mobile_page: Page) -> Page:
    login_page = MobileLoginPage(mobile_page)
    login_page.is_loaded()
    login_page.login(settings.test_account_email, settings.test_account_password)
    MobileEventsListPage(mobile_page).is_loaded()
    return mobile_page
