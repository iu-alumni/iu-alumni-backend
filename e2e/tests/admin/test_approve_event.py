from __future__ import annotations

import pytest

from pages.admin.event_details_page import AdminEventDetailsPage
from pages.admin.events_page import AdminEventsPage
from utils.admin_flows import create_event_via_mobile


pytestmark = pytest.mark.admin


@pytest.mark.smoke
def test_admin_approves_pending_event(authenticated_admin_page, browser, created_events) -> None:
    events_page = AdminEventsPage(authenticated_admin_page)
    events_page.goto()
    events_page.set_auto_approve(enabled=False)

    try:
        event = create_event_via_mobile(browser)
        created_events.append(event.title)

        events_page.refresh()
        events_page.search_input.fill(event.title)
        events_page.status_of(event.title).wait_for(state="visible")
        events_page.open_details(event.title)

        details_page = AdminEventDetailsPage(authenticated_admin_page)
        details_page.approve()
        details_page.expect_approved()
    finally:
        events_page.goto()
        events_page.set_auto_approve(enabled=True)
