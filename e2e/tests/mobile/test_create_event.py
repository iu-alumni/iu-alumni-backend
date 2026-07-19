from __future__ import annotations

import pytest

from pages.mobile.event_editing_page import MobileEventEditingPage
from pages.mobile.events_list_page import MobileEventsListPage
from utils.data_factory import TestEvent


pytestmark = pytest.mark.mobile


@pytest.mark.smoke
def test_create_event_appears_in_list_after_refresh(logged_in_page, created_events) -> None:
    events_list = MobileEventsListPage(logged_in_page)
    event = TestEvent()
    created_events.append(event.title)

    events_list.open_create_event()
    MobileEventEditingPage(logged_in_page).create(event)

    events_list.is_loaded()
    events_list.refresh()
    events_list.expect_event_visible(event.title)


@pytest.mark.negative
def test_create_event_with_empty_required_fields_is_rejected(logged_in_page) -> None:
    events_list = MobileEventsListPage(logged_in_page)
    events_list.open_create_event()

    editing_page = MobileEventEditingPage(logged_in_page)
    editing_page.submit_new_event()

    editing_page.expect_rejected()
