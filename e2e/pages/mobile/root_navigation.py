from __future__ import annotations

from playwright.sync_api import Page


_TAB_BAR_BOTTOM_OFFSET_PX = 32  # SafeArea + vertical padding + half of the 48px bar
_TAB_ORDER = ("map", "events", "profile")


class RootNavigation:
    def __init__(self, page: Page) -> None:
        self.page = page

    def _tap_tab(self, name: str) -> None:
        index = _TAB_ORDER.index(name)
        viewport = self.page.viewport_size
        assert viewport is not None, "page has no viewport set"
        column_width = viewport["width"] / len(_TAB_ORDER)
        x = column_width * index + column_width / 2
        y = viewport["height"] - _TAB_BAR_BOTTOM_OFFSET_PX
        self.page.mouse.click(x, y)

    def _tap_until_landed(self, name: str, marker_text: str) -> None:
        # Coordinates occasionally miss (confirmed live) — retry against a
        # screen-specific marker rather than trusting one tap blindly.
        marker = self.page.get_by_text(marker_text, exact=True)
        for attempt in range(3):
            self._tap_tab(name)
            try:
                marker.wait_for(state="visible", timeout=3000)
                return
            except Exception:
                if attempt == 2:
                    raise

    def go_to_map(self) -> None:
        self._tap_tab("map")

    def go_to_events(self) -> None:
        self._tap_until_landed("events", "Events")

    def go_to_profile(self) -> None:
        self._tap_until_landed("profile", "Profile")
