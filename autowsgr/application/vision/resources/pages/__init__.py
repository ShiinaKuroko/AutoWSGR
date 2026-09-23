"""Page-scoped image templates owned by the application layer."""

from autowsgr.application.vision.resources.pages.bath import Bath
from autowsgr.application.vision.resources.pages.common import CommonPage
from autowsgr.application.vision.resources.pages.decisive import Decisive
from autowsgr.application.vision.resources.pages.event import (
    event_difficulty_easy_templates,
    event_difficulty_hard_templates,
    event_fight_button_templates,
    event_icon_templates,
    event_map_title_templates,
)


__all__ = [
    'Bath',
    'CommonPage',
    'Decisive',
    'event_difficulty_easy_templates',
    'event_difficulty_hard_templates',
    'event_fight_button_templates',
    'event_icon_templates',
    'event_map_title_templates',
]
