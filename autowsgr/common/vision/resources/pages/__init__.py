"""Page-scoped template resources used by UI Controllers."""

from autowsgr.common.vision.resources.pages.bath import Bath
from autowsgr.common.vision.resources.pages.common import CommonPage
from autowsgr.common.vision.resources.pages.decisive import Decisive
from autowsgr.common.vision.resources.pages.event import (
    event_difficulty_easy_templates,
    event_difficulty_hard_templates,
    event_fight_button_templates,
    event_icon_templates,
    event_map_title_templates,
)
from autowsgr.common.vision.resources.pages.main_page import MainPage


__all__ = [
    'Bath',
    'CommonPage',
    'Decisive',
    'MainPage',
    'event_difficulty_easy_templates',
    'event_difficulty_hard_templates',
    'event_fight_button_templates',
    'event_icon_templates',
    'event_map_title_templates',
]
