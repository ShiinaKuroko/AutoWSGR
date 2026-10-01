"""模块功能：处理主页浮窗并重试确认主页模板。

上层调用：
- application.runtime.initialize.initialize：确认启动后是否进入主页。
- application.ui.navigation.route_manage.registry：确认导航到达主页。

下层依赖：
- application.ui.controller.home.main_page.HomePage：处理主页浮窗。
- application.ui.recognition_flow：记录初始截图并重试模板识别。
- common.vision：加载主页模板并执行 ROI 匹配。

本模块编排截图、主页浮窗处理和模板确认，不复制浮窗业务逻辑。
设备能力来自运行时上下文，截图事实写入 dispatch Context。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui import recognition_flow
from autowsgr.application.ui.controller.home.main_page import HomePage
from autowsgr.common import vision
from autowsgr.common.vision.adapters.template_matching import ROI, Template


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_HOME_PAGE_ROI = ROI(0.9109, 0.8681, 0.9758, 0.9139)
_HOME_PAGE_CONFIDENCE = 0.85
_HOME_TEMPLATE_PATH = 'application/ui/navigation/page_checker/HOME/HOME_MAIN_720P.png'


def check_home_page(ctx: ContextHandle) -> bool:
    """处理主页浮窗后，通过重试识别确认主页模板。

    Args:
        ctx: 提供任务事实和已绑定运行时服务的统一 ContextHandle。

    Returns:
        命中主页模板时返回 ``True``。

    Raises:
        ContextNotBoundError: 当前执行作用域未绑定 dispatch Context。
    """
    runtime = ctx.runtime
    recognition_flow.capture_frame(runtime.ctrl, record_screenshot=ctx.record_screenshot)
    HomePage(runtime).dismiss_current_overlay(navigation_context=ctx)

    template = Template(
        name='home_main',
        relative_path=_HOME_TEMPLATE_PATH,
        image=vision.opencv.load_image(_HOME_TEMPLATE_PATH),
        source_resolution=(1280, 720),
    )
    result = recognition_flow.recognize_with_retry(
        runtime.ctrl,
        mode=recognition_flow.RecognitionMode.OPENCV,
        template=template,
        roi=_HOME_PAGE_ROI,
        confidence=_HOME_PAGE_CONFIDENCE,
        record_screenshot=ctx.record_screenshot,
    )
    return result.satisfied


__all__ = ['check_home_page']
