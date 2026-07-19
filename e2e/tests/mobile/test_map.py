from __future__ import annotations

import time

import pytest

from config import settings
from pages.mobile.map_page import MobileMapPage
from pages.mobile.root_navigation import RootNavigation


pytestmark = pytest.mark.mobile


@pytest.mark.smoke
def test_map_loads_within_budget(logged_in_page) -> None:
    map_page = MobileMapPage(logged_in_page)
    nav = RootNavigation(logged_in_page)

    started_at = time.perf_counter()
    with map_page.expect_tile_load():
        nav.go_to_map()
    elapsed_ms = (time.perf_counter() - started_at) * 1000

    assert elapsed_ms <= settings.map_load_timeout_ms, (
        f"Map took {elapsed_ms:.0f}ms, budget is {settings.map_load_timeout_ms}ms"
    )
