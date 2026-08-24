"""任务页面数据 - 枚举、数据结构、常量、坐标。

坐标/颜色/OCR 参数的数据源统一为 infra/base/constants 分类 YAML:
    - coordinates/mission.yaml — 点击坐标 (1280x720 绝对像素, point() 归一化)
    - colors/mission.yaml     — 按钮颜色与检测阈值
    - ocr/mission.yaml        — 按钮扫描 / 名称与进度裁切参数
时序参数 (面板切换延迟等) 由页面模块自行管理。
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from autowsgr.infra.base.constants.colors import color as _color
from autowsgr.infra.base.constants.colors import param as _color_param
from autowsgr.infra.base.constants.colors import tolerance as _color_tolerance
from autowsgr.infra.base.constants.coordinates import point
from autowsgr.infra.base.constants.ocr import param as _ocr_param
from autowsgr.vision.roi import ROI


# ═══════════════════════════════════════════════════════════════════════════════
# 面板枚举
# ═══════════════════════════════════════════════════════════════════════════════


class MissionPanel(enum.Enum):
    """任务页面内部子标签。"""

    ALL = '全部'
    MAIN = '主线'
    DAILY = '日常'
    WEEKLY = '周常'
    TIMED = '限时'


PANEL_LIST: list[MissionPanel] = list(MissionPanel)
"""面板枚举值列表。"""

CLICK_PANEL: dict[MissionPanel, tuple[float, float]] = {
    panel: point('mission', f'panel.{panel.name.lower()}') for panel in MissionPanel
}
"""面板子标签点击位置 — 数据源: coordinates/mission.yaml。"""

PANEL_SWITCH_DELAY: float = 0.5
"""面板切换后等待 (秒) — 时序参数, 由页面模块管理。"""


# ═══════════════════════════════════════════════════════════════════════════════
# 按钮类型 & 任务数据
# ═══════════════════════════════════════════════════════════════════════════════


class ButtonType(enum.Enum):
    """任务行右侧按钮类型。"""

    GOTO = 'goto'
    """蓝色 "前往" 按钮 - 任务未完成。"""

    CLAIM = 'claim'
    """橙色/金色 "领取" 按钮 - 任务已完成可领取。"""


@dataclass(frozen=True, slots=True)
class MissionInfo:
    """单条任务识别结果。"""

    name: str
    """数据库匹配后的标准任务名 (若未匹配则为 OCR 原始文本)。"""
    raw_text: str
    """OCR 原始识别文本。"""
    progress: int
    """完成百分比 0-100 (-1 表示未能识别)。"""
    claimable: bool
    """是否可领取 (按钮为 "领取")。"""
    confidence: float
    """OCR 置信度 (名称识别)。"""


# ═══════════════════════════════════════════════════════════════════════════════
# 按钮扫描颜色常量 — 数据源: colors/mission.yaml
# ═══════════════════════════════════════════════════════════════════════════════

# "前往" 按钮蓝色
GOTO_COLOR = _color('mission', 'goto_blue')
GOTO_TOLERANCE = _color_tolerance('mission', 'goto_blue')

# "领取" 按钮检测: 高红+中绿+低蓝 (橙/金色)
CLAIM_R_MIN = _color_param('mission', 'claim.r_min')
CLAIM_G_MIN = _color_param('mission', 'claim.g_min')
CLAIM_B_MAX = _color_param('mission', 'claim.b_max')


# ═══════════════════════════════════════════════════════════════════════════════
# 按钮扫描 / OCR 裁切常量 — 数据源: ocr/mission.yaml
# ═══════════════════════════════════════════════════════════════════════════════

# 按钮扫描区域 (右侧按钮列)
BUTTON_SCAN_ROI = ROI.from_tuple(tuple(_ocr_param('mission', 'button_scan_roi')))

# 扫描步长 (相对坐标)
SCAN_X: float = _ocr_param('mission', 'scan_x')  # 按钮中心 x
SCAN_Y_STEP: float = _ocr_param('mission', 'scan_y_step')  # y 步进

# 聚类阈值: 相对 y 距离小于此值视为同一按钮
# "领取" 按钮中央文字区域会产生 ~0.04 的颜色间断, 需 >= 0.05 才能合并
CLUSTER_GAP: float = _ocr_param('mission', 'cluster_gap')

# 最小聚类大小: 低于此值的簇视为噪点而非真实按钮
MIN_CLUSTER_SIZE: int = _ocr_param('mission', 'min_cluster_size')

# 宽按钮 (一键领取) 过滤: 检测 x 坐标
WIDE_BTN_CHECK_X: float = _ocr_param('mission', 'wide_btn_check_x')

# 名称裁切区域上边界: name_top < 此值表示名称被页面标题栏遮挡, 不可读
NAME_CROP_MIN_Y: float = _ocr_param('mission', 'name_crop_min_y')

# OCR 置信度下限: 低于此值视为无效识别
OCR_CONFIDENCE_MIN: float = _ocr_param('mission', 'ocr_confidence_min')

# 名称裁切
NAME_ROI_X1: float = _ocr_param('mission', 'name_roi.x1')
NAME_ROI_X2: float = _ocr_param('mission', 'name_roi.x2')
NAME_Y_OFFSET: float = _ocr_param('mission', 'name_roi.y_offset')  # 名称中心在按钮中心上方 (负值)
NAME_ROI_Y_PAD: float = _ocr_param('mission', 'name_roi.y_pad')  # 名称区域上下半高

# 进度裁切
PROGRESS_ROI_X1: float = _ocr_param('mission', 'progress_roi.x1')
PROGRESS_ROI_X2: float = _ocr_param('mission', 'progress_roi.x2')
PROGRESS_Y_OFFSET: float = _ocr_param('mission', 'progress_roi.y_offset')
PROGRESS_ROI_Y_PAD: float = _ocr_param('mission', 'progress_roi.y_pad')

# 进度正则: 匹配 "XX%"
PROGRESS_RE = re.compile(r'(\d{1,3})\s*%')


# ═══════════════════════════════════════════════════════════════════════════════
# 点击坐标 — 数据源: coordinates/mission.yaml
# ═══════════════════════════════════════════════════════════════════════════════

CLICK_BACK: tuple[float, float] = point('mission', 'back')
"""回退按钮。"""


# ═══════════════════════════════════════════════════════════════════════════════
# 任务数据库
# ═══════════════════════════════════════════════════════════════════════════════

_MISSIONS_YAML = Path(__file__).resolve().parent.parent.parent / 'data' / 'missions.yaml'


@lru_cache(maxsize=1)
def _load_mission_db() -> dict:
    """加载并缓存任务数据库。"""
    with open(_MISSIONS_YAML, encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_all_mission_names() -> list[str]:
    """获取数据库中所有任务名称 (用于模糊匹配)。"""
    db = _load_mission_db()
    names: list[str] = []
    for category in ('daily', 'weekly'):
        for mission in db.get(category, []):
            name = mission['name']
            if name not in names:
                names.append(name)
    return names
