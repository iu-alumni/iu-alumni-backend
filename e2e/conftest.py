from __future__ import annotations

from playwright.sync_api import Page, expect
import pytest

from config import settings


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
