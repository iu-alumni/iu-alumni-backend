from __future__ import annotations

from playwright.sync_api import Page

from config import settings


class MobileMapPage:
    def __init__(self, page: Page) -> None:
        self.page = page

    def wait_until_loaded(self) -> None:
        self.page.wait_for_load_state(
            "networkidle",
            timeout=settings.map_load_timeout_ms,
        )
