"""模块功能：提供决战出征准备页的无搜索框编队入口。

上层调用：
- business.combat.decisive：传入决战目标舰队并执行出征准备。
- testing.ui：验证决战编队分支。

下层依赖：
- application.ui.controller.battle_preparation.preparation：提供共享准备页能力。
- application.ui.controller.operations.sortie_page.decisive_page.legacy_fleet_change：保留旧算法入口。
- application.ui.fleet：构造精确舰队规则。

决战页面不使用搜索框，选船实现仍由准备页 `fleet_change` 子包负责。

旧实现说明:

继承自 :class:`~autowsgr.application.ui.controller.battle_preparation.preparation.BattlePreparationPage`，
仅通过 ``_use_search = False`` 切换为 "不使用搜索框" 的换船模式。

与普通换船的差异
---------------
- 普通换船: 点击搜索框 -> 输入舰船名 -> 等待筛选结果 -> 点击第一项
- 决战换船: 统一编队入口识别 ``task_type='decisive'`` 后，直接 OCR 选船列表

这是因为决战选船流程没有搜索框（界面为直接列表展示），
且候选集合相对固定（由配置 level1/level2 决定）。

换船算法 (扫描 -> 定点更换 -> 调整次序) 由父类
:class:`~autowsgr.application.ui.controller.battle_preparation.fleet_change.FleetChangeMixin` 统一提供。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.application.ui.controller.battle_preparation.preparation import BattlePreparationPage
from autowsgr.application.ui.controller.operations.sortie_page.decisive_page.legacy_fleet_change import (
    change_fleet_legacy,
)
from autowsgr.application.ui.fleet import exact_fleet_rules


if TYPE_CHECKING:
    from collections.abc import Sequence

    from autowsgr.application.ui.context import UIContext as GameContext
    from autowsgr.common.system import DecisiveConfig
    from autowsgr.common.vision import OCREngine


class DecisiveBattlePreparationPage(BattlePreparationPage):
    """决战出征准备页控制器，使用无搜索框换船流程。

    Args:
        ctx: 当前运行时 UI 上下文。
        config: 决战配置。
        ocr: 可选的 OCR 引擎；未传入时使用上下文中的引擎。
    """

    _use_search: bool = False

    def __init__(
        self,
        ctx: GameContext,
        config: DecisiveConfig,
        ocr: OCREngine | None = None,
    ) -> None:
        """保存准备页上下文、决战配置和 OCR 引擎。"""
        super().__init__(ctx, ocr)
        self._ocr: OCREngine = ocr or ctx.ocr  # type: ignore[assignment]
        self._config = config

    def change_fleet(
        self,
        fleet_id: int | None,
        ship_names: Sequence[str | None],
    ) -> bool:
        """按决战任务类型进入统一编队分支。

        Args:
            fleet_id: 要操作的舰队编号；没有指定时保持当前舰队。
            ship_names: 按槽位排列的目标舰船名称。

        Returns:
            编队成功时返回 ``True``，旧流程或新流程失败时返回 ``False``。
        """
        if not self._config.use_new_fleet_change_algorithm:
            return change_fleet_legacy(self, fleet_id, ship_names)
        rules = exact_fleet_rules([name for name in ship_names if name])
        return super().change_fleet(fleet_id, rules)


__all__ = ['DecisiveBattlePreparationPage']
