from __future__ import annotations

import pytest

from config import settings
from pages.admin.users_page import AdminUsersPage
from pages.mobile.login_page import MobileLoginPage
from utils.admin_flows import register_alumnus_via_mobile
from utils.flutter import MOBILE_VIEWPORT, enable_semantics


pytestmark = pytest.mark.admin


@pytest.mark.negative
def test_login_before_verification_is_rejected(browser, created_users) -> None:
    """A freshly registered, not-yet-verified account can't log in yet —
    confirmed live this is checked *before* ban status, so it's the
    message shown regardless of ban state until verified.
    """
    user = register_alumnus_via_mobile(browser)
    created_users.append(user.email)

    context = browser.new_context(viewport=MOBILE_VIEWPORT, ignore_https_errors=True)
    try:
        page = context.new_page()
        page.goto(settings.mobile_base_url)
        enable_semantics(page)
        login_page = MobileLoginPage(page)
        login_page.login(user.email, user.password)
        login_page.expect_message("Account not verified")
    finally:
        context.close()


@pytest.mark.smoke
def test_admin_verifies_unverified_user(authenticated_admin_page, browser, created_users) -> None:
    user = register_alumnus_via_mobile(browser)
    created_users.append(user.email)

    users_page = AdminUsersPage(authenticated_admin_page)
    users_page.goto()
    users_page.search_input.fill(user.email)
    users_page.verify_user(user.email)

    users_page.expect_verified(user.email)


@pytest.mark.smoke
def test_admin_bans_verified_user_and_login_is_rejected(
    authenticated_admin_page, browser, created_users,
) -> None:
    # Verified first — the backend checks verification before ban status,
    # so an unverified-and-banned user would show "Account not verified"
    # instead of the message this test is actually after.
    user = register_alumnus_via_mobile(browser)
    created_users.append(user.email)

    users_page = AdminUsersPage(authenticated_admin_page)
    users_page.goto()
    users_page.search_input.fill(user.email)
    users_page.verify_user(user.email)
    users_page.ban_user(user.email)
    users_page.expect_banned(user.email)

    # Re-use the same tab to attempt a mobile login now that it's banned.
    authenticated_admin_page.goto(settings.mobile_base_url)
    enable_semantics(authenticated_admin_page)
    login_page = MobileLoginPage(authenticated_admin_page)
    login_page.login(user.email, user.password)

    login_page.expect_message("Account is banned")
