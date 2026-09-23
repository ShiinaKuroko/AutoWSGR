"""Read-only event page templates used by event Controllers.

Template paths and source resolutions belong here so page controllers only
request semantic template groups.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.dispatch.image_context import load_cached_template


if TYPE_CHECKING:
    from autowsgr.common.vision.template import Template


def event_map_title_templates() -> list[Template]:
    """Return event map title templates."""
    return [
        load_cached_template(
            'home/event_page/event_title_20260730_540p.png',
            name='event_title_20260730',
        ),
    ]


def event_icon_templates() -> list[Template]:
    """Return event entrance icon templates."""
    return [
        load_cached_template(
            'home/event_page/event_icon_20260212_720p.png',
            name='event_icon_20260212',
            source_resolution=(1280, 720),
        ),
        load_cached_template(
            'home/event_page/event_icon_20260730_540p.png',
            name='event_icon_20260730',
        ),
    ]


def event_fight_button_templates() -> list[Template]:
    """Return event node fight-button templates."""
    return [
        load_cached_template(
            'home/event_page/fight_button_20260730_540p.png',
            name='fight_button',
        ),
    ]


def event_difficulty_hard_templates() -> list[Template]:
    """Return templates shown when the current difficulty is easy."""
    return [
        load_cached_template('home/event_page/difficulty_hard_540p_1.png', name='diff_hard1'),
        load_cached_template('home/event_page/difficulty_hard_540p_2.png', name='diff_hard2'),
    ]


def event_difficulty_easy_templates() -> list[Template]:
    """Return templates shown when the current difficulty is hard."""
    return [
        load_cached_template('home/event_page/difficulty_easy_540p_1.png', name='diff_easy1'),
        load_cached_template('home/event_page/difficulty_easy_540p_2.png', name='diff_easy2'),
    ]
