"""链路自检 case：连接设备、处理主页浮窗并识别主页。

checker 会处理主页浮窗，不适合要求完全不操作游戏状态的检查。
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from autowsgr.application.ui.navigation.page_checker.home import check_home_page
from autowsgr.application.ui.navigation.types import PageName
from autowsgr.dispatch.context import ContextTemplate, RuntimeBindings, context


# 一句话描述 (--list 时显示)
DESC = '链路自检: 连接 + 主页浮窗处理 + 主页识别'


def run(rt: Any) -> bool:
    """执行链路自检步骤。"""
    scope_id = f'e2e:{rt.case_name}:{uuid4().hex}'
    with context.bind(
        scope_id,
        template=ContextTemplate.for_task('navigation_checker'),
        runtime=RuntimeBindings(
            ctrl=rt.ctx.ctrl,
            config=rt.ctx.config,
            ocr=rt.ctx.ocr,
            ship_ocr=rt.ctx.ship_ocr,
        ),
    ):
        task_context = context.request()

        screen = rt.action('截图', rt.ctx.ctrl.screenshot)
        if screen is rt.FAILED:
            return False
        task_context.record_screenshot(screen)

        page = rt.action('检查首页并处理浮窗', check_home_page, task_context)
        if page is rt.FAILED:
            return False
        if page:
            task_context.set_current_page(PageName.HOME.value)
        task_context.record_result(page)
        rt.check('首页模板命中', lambda: page)
        rt.note(f'首页模板命中: {page}')
        context.close()
        return page
