"""链路自检 case — 最小可用示例: ADB 连接 + 截图 + 页面识别。

不动游戏状态 (建议配 ``--no-launch``), 30 秒验证 "设备 → 截图 → 识别" 全链路。
也是新 case 的最小模板: 复制本文件, 改 DESC 和 run() 即可。
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from autowsgr.application.ui.navigation.page_checker.recognition import check_home_page
from autowsgr.dispatch.context import ContextTemplate, context


# 一句话描述 (--list 时显示)
DESC = '链路自检: 连接 + 截图 + 页面识别 (建议 --no-launch)'


def run(rt: Any) -> bool:
    """执行链路自检步骤。"""
    scope_id = f'e2e:{rt.case_name}:{uuid4().hex}'
    with context.bind(scope_id, template=ContextTemplate.for_task('navigation_checker')):
        task_context = context.request()

        screen = rt.action('截图', rt.ctx.ctrl.screenshot)
        if screen is rt.FAILED:
            return False
        task_context.record_screenshot(screen)

        page = rt.action('检查首页 checker', check_home_page, screen)
        if page is rt.FAILED:
            return False
        if page.matched:
            task_context.set_current_page(page.name)
        task_context.record_result(page)
        rt.check('首页模板命中', lambda: page.matched)
        rt.note(f'当前页面: {page.name}, score={page.score:.3f}')
        context.close()
        return page.matched
