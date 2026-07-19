from __future__ import annotations

from playwright.sync_api import Browser, expect

from config import settings
from pages.admin.login_page import AdminLoginPage
from pages.admin.users_page import AdminUsersPage
from pages.mobile.event_editing_page import MobileEventEditingPage
from pages.mobile.events_list_page import MobileEventsListPage
from pages.mobile.login_page import MobileLoginPage
from pages.mobile.registration_page import MobileRegistrationPage
from utils.data_factory import TestEvent, TestUser, new_test_user
from utils.flutter import MOBILE_VIEWPORT, enable_semantics


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


def register_alumnus_via_mobile(browser: Browser) -> TestUser:
    """Registers a fresh, unverified alumnus through the real mobile UI.

    Same flow as TC1's registration (fill sign-in fields, go to register,
    fill the form, submit) — reused here since TC7 just needs *an*
    unverified account to act on, not a login.
    """
    user = new_test_user()
    context = browser.new_context(viewport=MOBILE_VIEWPORT, ignore_https_errors=True)
    try:
        page = context.new_page()
        page.goto(settings.mobile_base_url)
        enable_semantics(page)

        login_page = MobileLoginPage(page)
        login_page.is_loaded()
        login_page.fill_credentials(user.email, user.password)
        login_page.go_to_register()

        registration_page = MobileRegistrationPage(page)
        registration_page.is_loaded()
        registration_page.register(user)
        login_page.is_loaded()
        return user
    finally:
        context.close()


def create_event_via_mobile(browser: Browser) -> TestEvent:
    event = TestEvent()
    context = browser.new_context(viewport=MOBILE_VIEWPORT, ignore_https_errors=True)
    try:
        page = context.new_page()
        page.goto(settings.mobile_base_url)
        enable_semantics(page)

        login_page = MobileLoginPage(page)
        login_page.is_loaded()
        login_page.login(settings.test_account_email, settings.test_account_password)

        events_list = MobileEventsListPage(page)
        events_list.is_loaded()
        events_list.open_create_event()
        MobileEventEditingPage(page).create(event)
        events_list.is_loaded()
        return event
    finally:
        context.close()
