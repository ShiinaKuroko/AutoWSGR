"""模块功能：读取登录流程各画面的识别事实。

上层调用：
- application.ui.navigation.page_checker.login_checker.checker：提供画面判断与区服定位。

下层依赖：
- login_checker.constants：提供识别区域、模板与期望文本。
- page_checker.calibration：加载本模块模板。
- common.vision：提供模板与 OCR 识别入口。

边界：只读取画面事实，不点击、不导航、不判断业务流程。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.navigation.page_checker import calibration
from autowsgr.application.ui.navigation.page_checker.login_checker import constants
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import Template, expect_ocr, expect_template


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui.login_checker')


def _template(filename: str, name: str) -> Template:
    """加载本模块模板。

    Args:
        filename: 模板文件名。
        name: 模板的业务名称，用于日志与匹配结果。

    Returns:
        可匹配的模板对象。
    """
    return calibration.load_module_template(constants.TEMPLATE_NAMESPACE, filename, name=name)


def is_black_screen_visible(ctx: ContextHandle) -> bool:
    """判断是否停留在健康游戏提示的黑屏画面。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        全屏模板命中时为真。
    """
    result = expect_template(
        ctx,
        template=_template(constants.BLACK_SCREEN_TEMPLATE, '健康游戏提示'),
        attempts=1,
    )
    _log.debug('[UI] 登录识别 → 健康游戏提示：matched={!r}', result.satisfied)
    return result.satisfied


def is_update_prompt_visible(ctx: ContextHandle) -> bool:
    """判断是否出现"有新的内容需要更新"提示。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        提示文字区域识别到期望文本时为真。
    """
    result = expect_ocr(
        ctx,
        expect=constants.UPDATE_PROMPT_TEXT,
        roi=constants.UPDATE_PROMPT_ROI,
        recognition_profile='single_line',
        attempts=1,
    )
    _log.debug('[UI] 登录识别 → 更新提示：matched={!r}', result.satisfied)
    return result.satisfied


def is_loading_visible(ctx: ContextHandle) -> bool:
    """判断是否正在加载（"正在进入港区"）。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        进度文字区域识别到"正在进入港区"时为真。
    """
    result = expect_ocr(
        ctx,
        expect=constants.LOADING_TEXT,
        roi=constants.PROGRESS_TEXT_ROI,
        recognition_profile='single_line',
        attempts=1,
    )
    _log.debug('[UI] 登录识别 → 加载中：matched={!r}', result.satisfied)
    return result.satisfied


def is_login_page_visible(ctx: ContextHandle) -> bool:
    """判断是否在登录页。

    进入游戏按钮与点击换区文字**二选一命中**即视为在登录页。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        任一登录页模板命中时为真。
    """
    result = expect_template(
        ctx,
        template=(
            _template(constants.ENTER_BUTTON_TEMPLATE, '进入游戏按钮'),
            _template(constants.SWITCH_ENTRY_TEMPLATE, '点击换区'),
        ),
        attempts=1,
    )
    _log.debug('[UI] 登录识别 → 登录页：matched={!r}', result.satisfied)
    return result.satisfied


def read_enter_button_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取登录页"进入游戏"按钮的中心。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        按钮模板命中时的归一化中心；未命中时为 None。
    """
    result = expect_template(
        ctx,
        template=_template(constants.ENTER_BUTTON_TEMPLATE, '进入游戏按钮'),
        roi=constants.ENTER_BUTTON_ROI,
        attempts=1,
    )
    center = result.observation[0].center
    _log.debug('[UI] 登录识别 → 读进入游戏中心：center={!r}', center)
    return center


def read_switch_entry_center(ctx: ContextHandle) -> tuple[float, float] | None:
    """读取登录页"点击换区"入口的中心。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        入口模板命中时的归一化中心；未命中时为 None。
    """
    result = expect_template(
        ctx,
        template=_template(constants.SWITCH_ENTRY_TEMPLATE, '点击换区'),
        roi=constants.SWITCH_ENTRY_ROI,
        attempts=1,
    )
    center = result.observation[0].center
    _log.debug('[UI] 登录识别 → 读换区入口中心：center={!r}', center)
    return center


def is_server_select_visible(ctx: ContextHandle) -> bool:
    """判断是否在区服选择页。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。

    Returns:
        切换大区按钮命中时为真。
    """
    result = expect_template(
        ctx,
        template=_template(constants.SWITCH_SERVER_TEMPLATE, '切换大区按钮'),
        roi=constants.SWITCH_SERVER_ROI,
        attempts=1,
    )
    _log.debug('[UI] 登录识别 → 区服选择页：matched={!r}', result.satisfied)
    return result.satisfied


def find_server_position(ctx: ContextHandle, name: str) -> int | None:
    """查找目标区服在列表中的位置。

    区服列表固定不滚动，因此拿目标区服名依次比对四条区域即可。

    Args:
        ctx: 提供设备服务和截图事实的 dispatch 上下文句柄。
        name: 目标区服名，取值见 `constants.SERVER_NAMES`。

    Returns:
        命中的位置序号（0 起），未命中时返回 None。
    """
    for index, roi in enumerate(constants.SERVER_NAME_ROIS):
        result = expect_ocr(
            ctx,
            expect=name,
            roi=roi,
            recognition_profile='single_line',
            attempts=1,
        )
        if result.satisfied:
            _log.info('[UI] 登录识别 → 区服定位：name={!r}，position={}', name, index)
            return index
    _log.warning('[UI] 登录识别 → 区服定位失败：name={!r}', name)
    return None


__all__ = [
    'find_server_position',
    'is_black_screen_visible',
    'is_loading_visible',
    'is_login_page_visible',
    'is_server_select_visible',
    'is_update_prompt_visible',
    'read_enter_button_center',
    'read_switch_entry_center',
]
