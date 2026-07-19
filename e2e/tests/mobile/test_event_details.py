from __future__ import annotations

import pytest

from config import settings
from pages.mobile.event_editing_page import MobileEventEditingPage
from pages.mobile.event_page import MobileEventPage
from pages.mobile.events_list_page import MobileEventsListPage
from pages.mobile.login_page import MobileLoginPage
from utils.admin_flows import register_alumnus_via_mobile, verify_user
from utils.data_factory import TestEvent
from utils.flutter import MOBILE_VIEWPORT, enable_semantics


pytestmark = pytest.mark.mobile


@pytest.mark.smoke
def test_own_event_details_show_edit_action(logged_in_page, created_events) -> None:
    events_list = MobileEventsListPage(logged_in_page)
    event = TestEvent()
    created_events.append(event.title)

    events_list.open_create_event()
    MobileEventEditingPage(logged_in_page).create(event)
    events_list.is_loaded()
    events_list.refresh()
    events_list.open_event(event.title)

    event_page = MobileEventPage(logged_in_page)
    event_page.expect_details(title=event.title, description=event.description)
    event_page.expect_date_visible()
    event_page.expect_location(event.location)
    event_page.expect_action_button("Edit")


@pytest.mark.smoke
def test_other_users_event_details_show_participate_action(
    logged_in_page, browser, created_events, created_users,
) -> None:
    organizer = register_alumnus_via_mobile(browser)
    created_users.append(organizer.email)
    verify_user(browser, organizer.email)
    event = TestEvent()
    created_events.append(event.title)

    context = browser.new_context(viewport=MOBILE_VIEWPORT, ignore_https_errors=True)
    try:
        page = context.new_page()
        page.goto(settings.mobile_base_url)
        enable_semantics(page)
        MobileLoginPage(page).login(organizer.email, organizer.password)

        organizer_events = MobileEventsListPage(page)
        organizer_events.is_loaded()
        organizer_events.open_create_event()
        MobileEventEditingPage(page).create(event)
        organizer_events.is_loaded()
    finally:
        context.close()

    events_list = MobileEventsListPage(logged_in_page)
    events_list.refresh()
    events_list.open_event(event.title)

    MobileEventPage(logged_in_page).expect_action_button("Participate")
