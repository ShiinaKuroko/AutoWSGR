"""Read-only event page templates used by event Controllers.

Template paths and source resolutions belong here so page controllers only
request semantic template groups.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from autowsgr.common.vision.resources._lazy import load_template


if TYPE_CHECKING:
    from autowsgr.common.vision import ImageTemplate


def event_map_title_templates() -> list[ImageTemplate]:
    """Return event map title templates."""
    return [
        load_template(
            'event/event_title_20260730_540p.png',
            name='event_title_20260730',
            source_resolution=(960, 540),
        ),
    ]


@lru_cache(maxsize=1)
def event_icon_templates() -> list[ImageTemplate]:
    """Return event entrance icon templates."""
    return [
        load_template(
            'event/event_icon_20260212_720p.png',
            name='event_icon_20260212',
            source_resolution=(1280, 720),
        ),
        load_template(
            'event/event_icon_20260730_540p.png',
            name='event_icon_20260730',
            source_resolution=(960, 540),
        ),
    ]


@lru_cache(maxsize=1)
def event_fight_button_templates() -> list[ImageTemplate]:
    """Return event node fight-button templates."""
    return [load_template('event/fight_button_20260730_540p.png', name='fight_button')]


@lru_cache(maxsize=1)
def event_difficulty_hard_templates() -> list[ImageTemplate]:
    """Return templates shown when the current difficulty is easy."""
    return [
        load_template('event/difficulty_hard_540p_1.png', name='diff_hard1'),
        load_template('event/difficulty_hard_540p_2.png', name='diff_hard2'),
    ]


@lru_cache(maxsize=1)
def event_difficulty_easy_templates() -> list[ImageTemplate]:
    """Return templates shown when the current difficulty is hard."""
    return [
        load_template('event/difficulty_easy_540p_1.png', name='diff_easy1'),
        load_template('event/difficulty_easy_540p_2.png', name='diff_easy2'),
    ]
