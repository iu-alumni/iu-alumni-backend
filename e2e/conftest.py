from __future__ import annotations

from playwright.sync_api import Page, expect
import pytest

from config import settings
from utils.api_cleanup import delete_alumnus_by_email, delete_event_by_title


# expect() has its own default timeout (5s), separate from
# page.set_default_timeout() below.
expect.set_options(timeout=settings.default_timeout_ms)

FAILURE_PAUSE_SECONDS = 2


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> None:
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    return {
        **browser_context_args,
        "viewport": {"width": 1440, "height": 900},
        "ignore_https_errors": True,
    }


@pytest.fixture(autouse=True)
def _default_timeouts(page: Page) -> None:
    page.set_default_timeout(settings.default_timeout_ms)
    page.set_default_navigation_timeout(settings.navigation_timeout_ms)


@pytest.fixture(autouse=True)
def _pause_on_failure_when_headed(request: pytest.FixtureRequest, page: Page) -> None:
    yield
    if not request.config.getoption("--headed"):
        return
    report = getattr(request.node, "rep_call", None)
    if report is not None and report.failed:
        page.wait_for_timeout(FAILURE_PAUSE_SECONDS * 1000)


@pytest.fixture
def created_events() -> list[str]:
    """Titles of events a test creates, deleted via the API once it ends.

    A test appends to this list right after creating an event; cleanup
    then runs regardless of pass/fail, so events don't pile up on tst.
    """
    titles: list[str] = []
    yield titles
    for title in titles:
        delete_event_by_title(title)


@pytest.fixture
def created_users() -> list[str]:
    """Emails of throwaway accounts a test registers, deleted (cascading
    their owned events/auth rows) via the API once it ends. The fixed
    `TEST_ACCOUNT_EMAIL` is never touched even if appended here — see
    `delete_alumnus_by_email`.
    """
    emails: list[str] = []
    yield emails
    for email in emails:
        delete_alumnus_by_email(email)
