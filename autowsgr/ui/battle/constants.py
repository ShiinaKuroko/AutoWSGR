"""出征准备页面常量 — 坐标、颜色、OCR 裁切参数。

数据源统一为 infra/base/constants 分类 YAML:
    - coordinates/battle_prep.yaml — 点击/探测坐标 (1280x720 绝对像素, point() 归一化)
    - colors/battle_prep.yaml      — 选中态/支援颜色与状态检测容差
    - ocr/battle_prep.yaml         — 舰船等级/舰种 OCR 裁切区域
"""

from __future__ import annotations

from autowsgr.infra.base.constants.colors import color as _color
from autowsgr.infra.base.constants.colors import param as _color_param
from autowsgr.infra.base.constants.coordinates import point, points
from autowsgr.infra.base.constants.ocr import param as _ocr_param


# ═══════════════════════════════════════════════════════════════════════════════
# 选中态参考颜色 (RGB) — 数据源: colors/battle_prep.yaml
# ═══════════════════════════════════════════════════════════════════════════════

FLEET_ACTIVE = _color('battle_prep', 'fleet_active')
"""舰队标签选中态颜色 — 明亮蓝色。"""

PANEL_ACTIVE = _color('battle_prep', 'panel_active')
"""面板标签选中态颜色 — 明亮蓝色。"""

AUTO_SUPPLY_ON = _color('battle_prep', 'auto_supply_on')
"""自动补给启用态颜色 — 蓝色勾选框。"""

STATE_TOLERANCE = _color_param('battle_prep', 'state_tolerance')
"""状态检测颜色容差。"""


# ═══════════════════════════════════════════════════════════════════════════════
# 探测坐标 — 采样颜色判断状态 (数据源: coordinates/battle_prep.yaml)
# ═══════════════════════════════════════════════════════════════════════════════

FLEET_PROBE: dict[int, tuple[float, float]] = dict(
    enumerate(points('battle_prep', 'fleet_probe'), 1)
)
"""舰队标签探测点 (1-4)。选中项探测颜色 ≈ (16, 133, 228)。"""

SUPPORT_PROBE: tuple[float, float] = point('battle_prep', 'support_probe')
"""战役支援探测点。"""

AUTO_SUPPLY_PROBE: tuple[float, float] = point('battle_prep', 'auto_supply_probe')
"""自动补给探测点。启用态探测颜色 ≈ (13, 140, 233)。"""


# ═══════════════════════════════════════════════════════════════════════════════
# 点击坐标 — 执行操作 (数据源: coordinates/battle_prep.yaml)
# ═══════════════════════════════════════════════════════════════════════════════

CLICK_BACK: tuple[float, float] = point('battle_prep', 'back')
"""回退按钮 (◁)。"""

CLICK_FLEET: dict[int, tuple[float, float]] = dict(
    enumerate(points('battle_prep', 'fleet'), 1)
)
"""舰队标签点击位置 (1-4)。"""

CLICK_SUPPORT: tuple[float, float] = point('battle_prep', 'support')
"""战役支援点击位置。"""

CLICK_AUTO_SUPPLY: tuple[float, float] = point('battle_prep', 'auto_supply')
"""自动补给复选框点击位置。"""

CLICK_START_BATTLE: tuple[float, float] = point('battle_prep', 'start_battle')
"""「开始出征」按钮点击位置。"""

CLICK_SHIP_SLOT: dict[int, tuple[float, float]] = dict(
    enumerate(points('battle_prep', 'ship_slot'))
)
"""6 个舰船槽位的点击坐标 (0-indexed)。"""


# ═══════════════════════════════════════════════════════════════════════════════
# 血量检测探测坐标 (数据源: coordinates/battle_prep.yaml)
# ═══════════════════════════════════════════════════════════════════════════════

BLOOD_BAR_PROBE: dict[int, tuple[float, float]] = dict(
    enumerate(points('battle_prep', 'blood_bar'))
)
"""出征准备页 6 个舰船血条探测点 (0-indexed)。"""


# ═══════════════════════════════════════════════════════════════════════════════
# 战役支援颜色 (RGB) — 数据源: colors/battle_prep.yaml
# ═══════════════════════════════════════════════════════════════════════════════

SUPPORT_ENABLE = _color('battle_prep', 'support_enable')
"""战役支援启用 — 黄色。"""
SUPPORT_DISABLE = _color('battle_prep', 'support_disable')
"""战役支援禁用 — 蓝色。"""
SUPPORT_EXHAUSTED = _color('battle_prep', 'support_exhausted')
"""战役支援次数用尽 — 灰色。"""


# ═══════════════════════════════════════════════════════════════════════════════
# 舰船等级 OCR 裁切区域 (数据源: ocr/battle_prep.yaml)
# ═══════════════════════════════════════════════════════════════════════════════

SHIP_LEVEL_CROP: dict[int, tuple[float, float, float, float]] = {
    i: tuple(crop) for i, crop in enumerate(_ocr_param('battle_prep', 'ship_level_crop'))
}
"""出征准备页 6 个舰船槽位的等级文本 OCR 裁切区域 (x1, y1, x2, y2)。

每个区域覆盖对应舰船卡片上的 ``Lv.XX`` 文本。
"""


# ═══════════════════════════════════════════════════════════════════════════════
# 舰船舰种 OCR 裁切区域 (数据源: ocr/battle_prep.yaml)
# ═══════════════════════════════════════════════════════════════════════════════

SHIP_TYPE_CROP: dict[int, tuple[float, float, float, float]] = {
    i: tuple(crop) for i, crop in enumerate(_ocr_param('battle_prep', 'ship_type_crop'))
}
"""出征准备页 6 个舰船槽位的舰种文本 OCR 裁切区域 (x1, y1, x2, y2)。

只保留舰种的两个汉字，排除国家括号、锁图标及相邻等级文字。
"""
