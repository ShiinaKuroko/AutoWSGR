"""模块功能：维护建造页面及解体标签专用的物理校准常量。

上层调用：
- application.ui.controller.sidebar.build_page.page：读取页面和标签切换坐标。
- application.ui.controller.sidebar.build_page.operations：读取原子点击坐标。
- application.ui.controller.sidebar.build_page.workflow：读取建造和解装流程坐标。

下层依赖：
- 无。常量值来自建造页面的 1280x720 校准结果，并以相对坐标保存。

本模块不保存页面状态、设备对象、运行时上下文或建造业务规则。
"""

from __future__ import annotations


# ── 页面与标签坐标 ───────────────────────────────────────────────────────────

# 左上角返回按钮；建造页与出征页、好友页、强化页的返回按钮落在同一位置。
CLICK_BACK: tuple[float, float] = (0.0219, 0.0584)
# 坐标为 1280x720 参考画面的归一化值；建造与解体取自激活标签模板的中心，
# 开发与废弃暂沿用等距估算值（尚未采到激活模板）。
TAB_POSITIONS: dict[str, tuple[float, float]] = {
    'build': (0.1832, 0.0472),  # 顶部建造标签，用于进入舰船建造内容。
    'destroy': (0.3121, 0.0472),  # 顶部解体标签，用于进入舰船解装内容。
    'develop': (0.4375, 0.0458),  # 顶部开发标签，用于进入装备开发内容。
    'discard': (0.5625, 0.0458),  # 顶部废弃标签，用于进入废弃内容。
}

# ── 建造流程 ─────────────────────────────────────────────────────────────────

CLICK_CONFIRM: tuple[float, float] = (
    0.8898,
    0.8903,
)  # 资源选择页面确认按钮，用于提交当前建造配方。
CLICK_DISMISS_ANIMATION: tuple[float, float] = (
    0.9531,
    0.9542,
)  # 建造结果动画跳过区域，用于继续处理结果。

# ── 解体标签操作 ─────────────────────────────────────────────────────────────

CLICK_DESTROY_ADD: tuple[float, float] = (
    0.0938,
    0.3819,
)  # 解体列表添加按钮，用于打开待解装舰船选择。
CLICK_DESTROY_QUICK_SELECT: tuple[float, float] = (
    0.9102,
    0.3000,
)  # 解体快速选择按钮，用于批量选择舰船。
CLICK_DESTROY_CONFIRM_SELECT: tuple[float, float] = (
    0.9148,
    0.9056,
)  # 解体选择确认按钮，用于提交舰船选择。
CLICK_DESTROY_REMOVE_EQUIP: tuple[float, float] = (
    0.8367,
    0.6458,
)  # 卸下装备选项，用于先移除舰船装备。
CLICK_DESTROY_CONFIRM: tuple[float, float] = (0.9000, 0.9000)  # 解体确认按钮，用于提交解装操作。
CLICK_DESTROY_FOUR_STAR_CONFIRM: tuple[float, float] = (
    0.3797,
    0.5667,
)  # 四星确认按钮，用于确认高星舰船解装。
CLICK_DESTROY_TYPE_FILTER: tuple[float, float] = (
    0.9117,
    0.6806,
)  # 舰种过滤入口，用于展开筛选面板。
CLICK_DESTROY_CONFIRM_FILTER: tuple[float, float] = (
    0.9000,
    0.8500,
)  # 舰种过滤确认按钮，用于应用筛选条件。

DESTROY_TYPE_POSITIONS: dict[str, tuple[float, float]] = {
    'CV': (0.5550, 0.1970),  # 航母筛选按钮，用于选择航母舰种。
    'CVL': (0.6460, 0.1970),  # 轻母筛选按钮，用于选择轻型航母舰种。
    'AV': (0.7380, 0.1970),  # 装母筛选按钮，用于选择装甲航母舰种。
    'BB': (0.8300, 0.1970),  # 战列筛选按钮，用于选择战列舰舰种。
    'BBV': (0.9220, 0.1970),  # 航战筛选按钮，用于选择航空战列舰舰种。
    'BC': (0.5560, 0.2880),  # 战巡筛选按钮，用于选择战列巡洋舰舰种。
    'CA': (0.6460, 0.2880),  # 重巡筛选按钮，用于选择重巡洋舰舰种。
    'CAV': (0.7380, 0.2880),  # 航巡筛选按钮，用于选择航空巡洋舰舰种。
    'CLT': (0.8300, 0.2880),  # 雷巡筛选按钮，用于选择重雷装巡洋舰舰种。
    'CL': (0.9220, 0.2880),  # 轻巡筛选按钮，用于选择轻巡洋舰舰种。
    'BM': (0.5560, 0.3790),  # 炮舰筛选按钮，用于选择炮舰舰种。
    'DD': (0.6460, 0.3790),  # 驱逐筛选按钮，用于选择驱逐舰舰种。
    'SSG': (0.7380, 0.3790),  # 炮潜筛选按钮，用于选择炮潜艇舰种。
    'SS': (0.8300, 0.3790),  # 潜艇筛选按钮，用于选择潜艇舰种。
    'SC': (0.9220, 0.3790),  # 其他潜艇筛选按钮，用于选择特殊潜艇舰种。
    'NAP': (0.5550, 0.4700),  # 补给舰筛选按钮，用于选择补给舰舰种。
    'ASDG': (0.6460, 0.4700),  # 导驱筛选按钮，用于选择导弹驱逐舰舰种。
    'AADG': (0.7380, 0.4700),  # 防驱筛选按钮，用于选择防空驱逐舰舰种。
    'KP': (0.8300, 0.4700),  # 导巡筛选按钮，用于选择导弹巡洋舰舰种。
    'CG': (0.9220, 0.4700),  # 防巡筛选按钮，用于选择防空巡洋舰舰种。
    'CBG': (0.5550, 0.5610),  # 大巡筛选按钮，用于选择大型巡洋舰舰种。
    'BG': (0.6460, 0.5610),  # 导战筛选按钮，用于选择导弹战列舰舰种。
    'Other': (0.7380, 0.5610),  # 其他筛选按钮，用于选择未分类舰种。
}


__all__ = [  # noqa: RUF022 - exports follow the page coordinate definition order
    'CLICK_BACK',
    'TAB_POSITIONS',
    'CLICK_CONFIRM',
    'CLICK_DISMISS_ANIMATION',
    'CLICK_DESTROY_ADD',
    'CLICK_DESTROY_QUICK_SELECT',
    'CLICK_DESTROY_CONFIRM_SELECT',
    'CLICK_DESTROY_REMOVE_EQUIP',
    'CLICK_DESTROY_CONFIRM',
    'CLICK_DESTROY_FOUR_STAR_CONFIRM',
    'CLICK_DESTROY_TYPE_FILTER',
    'CLICK_DESTROY_CONFIRM_FILTER',
    'DESTROY_TYPE_POSITIONS',
]
