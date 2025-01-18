import logging
import sys

from pathlib import Path

from rio import App, Theme, Color, Font, ComponentPage, Session

from pydb import pyrosetup
from .pages import *
logger = logging.getLogger("WebUi")

BASE_WINDOW_TITLE = "Montag"

def start_webserver() -> None:
    theme = Theme.from_colors(
        primary_color=Color.from_hex("67F8BA"),
        secondary_color=Color.from_hex("7A9786"),
        neutral_color=Color.from_hex("8F918E"),
        mode="dark",
        corner_radius_small=0,
        corner_radius_medium=0,
        corner_radius_large=0
    )

    async def on_session_start(session: Session) -> None:
        await session.set_title(BASE_WINDOW_TITLE)

    async def on_app_start(a: App) -> None:
        pass  # @todo: Do check if required services run

    app = App(
        name="Montag",
        build=BasePage,
        pages=[
            ComponentPage(
                name="Landing",
                url_segment="",
                build=Landing,
            )
        ],
        theme=theme,
        assets_dir=Path(__file__).parent / "assets",
        default_attachments=[pyrosetup.pydbserver()],
        on_session_start=on_session_start,
        on_app_start=on_app_start,
        icon=Path(__file__).parent / "assets" / "favicon.png",
        meta_tags={
            "robots": "INDEX,FOLLOW",
            "description": "Browser based ebook library",
            "og:description": "Browser based ebook library",
            "keywords": "ebook",
            "author": "Montag Group",
            "publisher": "Montag Group",
            "copyright": "Montag Group",
            "audience": "Everyone",
            "page-type": "Management Application",
            "page-topic": "E-Books",
            "expires": "",
            "revisit-after": "2 days"
        }
    )

    sys.exit(app.run_as_web_server())

if __name__ == "__main__":
    start_webserver()
