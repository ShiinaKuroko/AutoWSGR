"""活动地图页面使用的只读模板。"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.common.vision.resources._lazy import load_template


if TYPE_CHECKING:
    from autowsgr.common.vision import ImageTemplate


def event_map_title_templates() -> list[ImageTemplate]:
    """返回活动地图标题模板。"""
    return [
        load_template(
            'event/event_title_20260730_540p.png',
            name='event_title_20260730',
            source_resolution=(960, 540),
        ),
    ]
