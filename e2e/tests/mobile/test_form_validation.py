from __future__ import annotations

import pytest

from pages.mobile.event_editing_page import MobileEventEditingPage
from pages.mobile.events_list_page import MobileEventsListPage
from pages.mobile.login_page import MobileLoginPage
from pages.mobile.registration_page import MobileRegistrationPage
from utils.data_factory import TestEvent, new_test_user
from utils.flutter import type_into


pytestmark = pytest.mark.mobile


@pytest.mark.negative
def test_registration_with_only_first_name_filled_is_rejected(mobile_page) -> None:
    login_page = MobileLoginPage(mobile_page)
    login_page.is_loaded()
    login_page.go_to_register()

    registration_page = MobileRegistrationPage(mobile_page)
    registration_page.is_loaded()
    type_into(registration_page.first_name_input, new_test_user().first_name)
    registration_page.submit()

    registration_page.expect_message(
        "Please enter your last name, university email, graduation year, and password",
    )


@pytest.mark.negative
def test_create_event_with_only_title_filled_is_rejected(logged_in_page) -> None:
    events_list = MobileEventsListPage(logged_in_page)
    events_list.open_create_event()

    editing_page = MobileEventEditingPage(logged_in_page)
    type_into(editing_page.title_input, TestEvent().title)
    editing_page.submit_new_event()

    editing_page.expect_rejected()
