from __future__ import annotations

from playwright.sync_api import Page

from config import settings


class MobileMapPage:
    def __init__(self, page: Page) -> None:
        self.page = page

    def expect_tile_load(self):
        # "networkidle" never fires here — tile servers keep the network
        # busy with background chatter well past 5s even though the map is
        # already visibly rendered. Waiting for the first actual tile
        # response is what "loaded" means for a tiled map.
        return self.page.expect_response(
            lambda response: "tile.openstreetmap.org" in response.url,
            timeout=settings.map_load_timeout_ms,
        )
