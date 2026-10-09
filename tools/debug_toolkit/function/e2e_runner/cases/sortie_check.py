"""静态验证 case：用外挂截图跑出征页检查器。

样本属于临时验证数据，放在仓库之外的 debug 目录，不随仓库提交。
运行方式::

    python tools/debug_toolkit/main.py e2e --static sortie_check
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from autowsgr.application.ui.navigation.page_checker import sortie_checker


DESC = '出征页检查器静态验证: 出征 / 演习 / 远征 / 战役 / 决战标签激活'

# 外挂截图目录；样本是各标签激活时的整页截图。
_SHOT_DIR = Path('C:/ShiinaKuroko/01.Project/debug/nav/静态模板/出征')

_SAMPLES = (
    ('出征页面.png', 'check_sortie_page'),
    ('选择演习tab.png', 'check_exercise_page'),
    ('选择远征tab.png', 'check_expedition_page'),
    ('选择战役tab.png', 'check_campaign_page'),
    ('选择决战tab.png', 'check_decisive_page'),
)


def run(rt: Any) -> bool:
    """按样本切换静态截图并校验五个标签识别入口。"""
    ctx = rt.ctx

    for filename, entry_name in _SAMPLES:
        rt.use_frame(_SHOT_DIR / filename)
        entry = getattr(sortie_checker, entry_name)
        matched = rt.action(f'识别 {entry_name}', entry, ctx)
        if matched is rt.FAILED:
            return False
        if not rt.check(f'{filename} 命中 {entry_name}', lambda: matched):
            return False
    return True
