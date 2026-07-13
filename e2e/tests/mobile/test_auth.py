from __future__ import annotations

import uuid

import pytest

from config import settings
from pages.mobile.events_list_page import MobileEventsListPage
from pages.mobile.login_page import MobileLoginPage
from pages.mobile.registration_page import MobileRegistrationPage
from utils.admin_flows import verify_user
from utils.data_factory import TestUser, new_test_user, unique_email


pytestmark = pytest.mark.mobile


@pytest.mark.smoke
def test_register_then_login(mobile_page, test_user: TestUser, browser) -> None:
    login_page = MobileLoginPage(mobile_page)
    login_page.is_loaded()
    login_page.fill_credentials(test_user.email, test_user.password)
    login_page.go_to_register()

    registration_page = MobileRegistrationPage(mobile_page)
    registration_page.is_loaded()
    registration_page.register(test_user)
    login_page.is_loaded()

    verify_user(browser, test_user.email)

    login_page.is_loaded()
    login_page.submit()

    MobileEventsListPage(mobile_page).is_loaded()


@pytest.mark.negative
def test_register_with_existing_email_is_rejected(mobile_page) -> None:
    duplicate = new_test_user(email=settings.test_account_email)

    login_page = MobileLoginPage(mobile_page)
    login_page.fill_credentials(duplicate.email, duplicate.password)
    login_page.go_to_register()

    registration_page = MobileRegistrationPage(mobile_page)
    registration_page.is_loaded()
    registration_page.register(duplicate)

    registration_page.expect_message("Email already registered")


@pytest.mark.negative
def test_login_with_wrong_password_is_rejected(mobile_page) -> None:
    login_page = MobileLoginPage(mobile_page)
    login_page.login(settings.test_account_email, f"wrong-{uuid.uuid4().hex[:8]}")

    login_page.expect_message("Incorrect email or password")


@pytest.mark.negative
def test_login_with_unregistered_email_is_rejected(mobile_page) -> None:
    login_page = MobileLoginPage(mobile_page)
    login_page.login(unique_email(), "SomePassword123!")

    login_page.expect_message("Incorrect email or password")


@pytest.mark.negative
def test_registration_with_empty_fields_shows_validation_error(mobile_page) -> None:
    login_page = MobileLoginPage(mobile_page)
    login_page.is_loaded()
    login_page.go_to_register()

    registration_page = MobileRegistrationPage(mobile_page)
    registration_page.is_loaded()
    registration_page.submit()

    registration_page.expect_message(
        "Please enter your first name, last name, university email, "
        "graduation year, and password",
    )
