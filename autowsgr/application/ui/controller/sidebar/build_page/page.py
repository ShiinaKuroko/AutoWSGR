"""模块功能：在建造页执行标签切换与返回。

上层调用：
- application.ui.navigation：执行建造页的标签切换与返回主页的页面边动作。

下层依赖：
- application.ui.controller.sidebar.build_page.constants：提供标签与返回落点。

边界：只点击标签与返回按钮，不识别画面、不确认终态、不编排建造业务。
建造与解装的业务流程尚未迁移到新链路，等第二阶段移植后再补回本模块。
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.sidebar.build_page import constants
from autowsgr.common.system.logger import get_logger


if TYPE_CHECKING:
    from autowsgr.dispatch.context import ContextHandle


_log = get_logger('ui.sidebar.build_page')


# ── 页面标签 ─────────────────────────────────────────────────────────────────


class BuildTab(enum.Enum):
    """建造页面标签组。"""

    BUILD = '建造'
    DESTROY = '解体'
    DEVELOP = '开发'
    DISCARD = '废弃'


# ── 页面控制器 ──────────────────────────────────────────────────────────────


class BuildPage:
    """建造页面的单击控制器。"""

    def __init__(self, ctx: ContextHandle) -> None:
        """绑定任务上下文。

        Args:
            ctx: 提供设备服务的 dispatch 上下文句柄。
        """
        self._ctx = ctx

    # ── 标签切换 ──────────────────────────────────────────────────────────────

    def go_to_tab(self, tab: BuildTab) -> None:
        """点击顶部标签，切到对应内容。

        只负责点击；是否真的切过去了由导航器用标签的 checker 确认。

        Args:
            tab: 目标标签。

        Raises:
            ValueError: 标签没有配置落点。
        """
        position = constants.TAB_POSITIONS.get(tab.name.lower())
        if position is None:
            raise ValueError(f'建造页没有该标签的落点: {tab!r}')
        _log.info('[UI] 建造页面 → 切换标签：tab={!r}，position={!r}', tab.value, position)
        self._ctx.runtime.ctrl.click(*position)

    # ── 页面返回 ──────────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """点击左上角返回按钮，离开建造页。"""
        _log.info('[UI] 建造页 → 返回：position={!r}', constants.CLICK_BACK)
        self._ctx.runtime.ctrl.click(*constants.CLICK_BACK)


__all__ = ['BuildPage', 'BuildTab']
