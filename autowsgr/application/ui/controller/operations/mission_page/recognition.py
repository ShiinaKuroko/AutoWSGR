"""模块功能：负责任务按钮扫描、任务数据读取和任务名称/进度 OCR 识别。

上层调用：
- application.ui.controller.operations.mission_page.page：请求可见任务和任务结果模型。
- testing.ui：通过任务页面控制器验证按钮扫描和任务识别。

下层依赖：
- common.vision：提供像素读取、ROI 裁剪和 OCR 引擎。
- common.vision.ocr：提供任务名称编辑距离匹配。
- common.data.missions.yaml：提供任务名称候选数据。

边界：
只读取任务页面事实并构造任务结果；不执行设备点击、页面导航或运行时上下文创建。
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import yaml

from autowsgr.application.vision.resources import Templates
from autowsgr.common import vision
from autowsgr.common.vision import ocr
from autowsgr.common.vision.adapters.template_matching import ROI


if TYPE_CHECKING:
    import numpy

    from autowsgr.common.vision import OCREngine


# ── 页面识别校准 ────────────────────────────────────────────────────────────────────


class _MissionCoordinates(NamedTuple):
    """任务按钮、名称和进度区域的归一化坐标。"""

    button_scan_roi: ROI
    scan_x: float
    wide_button_check_x: float
    name_region: tuple[float, float, float, float]
    progress_region: tuple[float, float, float, float]


_MISSION_COORDINATES = _MissionCoordinates(
    button_scan_roi=ROI.from_tuple((0.8600, 0.1700, 0.9600, 0.8500)),
    scan_x=0.9100,
    wide_button_check_x=0.8000,
    name_region=(0.2200, 0.6000, -0.1450, 0.0350),
    progress_region=(0.7500, 0.8700, 0.1050, 0.0350),
)
"""任务按钮、名称和进度识别区域，按页面业务对象聚合。"""

_CLAIM_COLOR_BOUNDS: tuple[int, int, int] = (180, 120, 80)
"""领取按钮颜色阈值，依次为 R 最小值、G 最小值和 B 最大值。"""

_GOTO_COLOR = vision.Color.from_rgb_tuple((15, 132, 228))
_GOTO_TOLERANCE: float = 40.0
_MISSION_NAME_DISTANCE_THRESHOLD: int = 5
"""任务名称编辑距离的最大允许阈值。"""

_SCAN_Y_STEP: float = 0.0050
"""按钮扫描纵向步长，用于平衡精度和采样次数。"""

_CLUSTER_GAP: float = 0.0600
"""按钮颜色聚类间隔，用于合并同一任务按钮的采样点。"""

_MIN_CLUSTER_SIZE: int = 3
"""按钮最小聚类大小，用于过滤颜色噪点。"""

_NAME_CROP_MIN_Y: float = 0.1200
"""任务名称裁剪上限，用于过滤被标题栏遮挡的任务行。"""

_OCR_CONFIDENCE_MIN: float = 0.10
"""任务名称最低置信度，用于拒绝无效 OCR 结果。"""


# ── 识别结果与任务数据库 ────────────────────────────────────────────────────────────────


class ButtonType(enum.Enum):
    """任务行右侧按钮类型。"""

    GOTO = 'goto'
    """蓝色“前往”按钮，表示任务未完成。"""

    CLAIM = 'claim'
    """橙色/金色“领取”按钮，表示任务已完成可领取。"""


@dataclass(frozen=True, slots=True)
class MissionInfo:
    """单条任务 OCR 识别结果。"""

    name: str
    """数据库匹配后的标准任务名；未匹配时为 OCR 原始文本。"""
    raw_text: str
    """任务名称的 OCR 原始文本。"""
    progress: int
    """完成百分比 0-100；无法识别时为 -1。"""
    claimable: bool
    """是否检测到可领取按钮。"""
    confidence: float
    """任务名称 OCR 置信度。"""


_MISSIONS_YAML: Path = Path(__file__).resolve().parents[5] / 'common' / 'data' / 'missions.yaml'
"""任务名称数据库路径，用于将 OCR 文本匹配为标准任务名。"""


@lru_cache(maxsize=1)
def _load_mission_db() -> dict:
    """加载并缓存任务名称数据库。"""
    with open(_MISSIONS_YAML, encoding='utf-8') as file:
        return yaml.safe_load(file)


def read_all_mission_names() -> list[str]:
    """读取日常和周常任务名称。

    Returns:
        去重后的任务名称列表，供 OCR 模糊匹配使用。
    """
    db = _load_mission_db()
    names: list[str] = []
    for category in ('daily', 'weekly'):
        for mission in db.get(category, []):
            name = mission['name']
            if name not in names:
                names.append(name)
    return names


_PROGRESS_PATTERN = re.compile(r'(\d{1,3})\s*%')
"""任务进度 OCR 正则，用于提取完成百分比。"""


# ── 任务按钮扫描 ────────────────────────────────────────────────────────────────────


def _is_goto_color(color: vision.Color) -> bool:
    return color.near(_GOTO_COLOR, _GOTO_TOLERANCE)


def _is_claim_color(color: vision.Color) -> bool:
    claim_r_min, claim_g_min, claim_b_max = _CLAIM_COLOR_BOUNDS
    return color.r >= claim_r_min and color.g >= claim_g_min and color.b <= claim_b_max


def find_button_rows(screen: numpy.ndarray) -> list[tuple[float, ButtonType]]:
    """扫描任务页面右侧，定位所有“前往”和“领取”按钮行。

    Args:
        screen: 任务页面 RGB 截图，形状为 ``(H, W, 3)``。

    Returns:
        按页面顺序排列的按钮行中心坐标和按钮类型。
    """
    y_start = _MISSION_COORDINATES.button_scan_roi.y1
    y_end = _MISSION_COORDINATES.button_scan_roi.y2

    # 1. 收集按钮颜色命中的纵向采样点。
    hits: list[tuple[float, ButtonType]] = []
    y = y_start
    while y <= y_end:
        c = vision.PixelChecker.get_pixel(screen, _MISSION_COORDINATES.scan_x, y)
        if _is_goto_color(c):
            hits.append((y, ButtonType.GOTO))
        elif _is_claim_color(c):
            hits.append((y, ButtonType.CLAIM))
        y += _SCAN_Y_STEP

    if not hits:
        return []

    # 2. 将连续且同类型的采样点合并为按钮行。
    clusters: list[list[tuple[float, ButtonType]]] = [[hits[0]]]
    for h in hits[1:]:
        prev = clusters[-1][-1]
        if h[0] - prev[0] < _CLUSTER_GAP and h[1] == prev[1]:
            clusters[-1].append(h)
        else:
            clusters.append([h])

    # 3. 计算按钮行中心并过滤采样噪点。
    result: list[tuple[float, ButtonType]] = []
    for cluster in clusters:
        if len(cluster) < _MIN_CLUSTER_SIZE:
            continue
        ys = [p[0] for p in cluster]
        y_center = (min(ys) + max(ys)) / 2
        btn_type = cluster[0][1]
        result.append((y_center, btn_type))

    # 4. 排除底部宽按钮和被标题栏遮挡的任务行。
    filtered: list[tuple[float, ButtonType]] = []
    for y_center, btn_type in result:
        c_wide = vision.PixelChecker.get_pixel(
            screen,
            _MISSION_COORDINATES.wide_button_check_x,
            y_center,
        )
        if _is_goto_color(c_wide) or _is_claim_color(c_wide):
            continue
        _, _, name_y_offset, name_y_pad = _MISSION_COORDINATES.name_region
        name_top = y_center + name_y_offset - name_y_pad
        if name_top < _NAME_CROP_MIN_Y:
            continue
        filtered.append((y_center, btn_type))

    return filtered


# ── 任务 OCR 识别 ─────────────────────────────────────────────────────────────────


def recognize_row(
    screen: numpy.ndarray,
    anchor_y: float,
    btn_type: ButtonType,
    ocr_engine: OCREngine,
    candidates: list[str],
) -> MissionInfo | None:
    """识别单行任务，无法确认时返回 None。

    Args:
        screen: 任务页面 RGB 截图。
        anchor_y: 任务按钮行中心的相对纵坐标。
        btn_type: 当前任务行右侧按钮类型。
        ocr_engine: 用于识别任务名称和进度的 OCR 引擎。
        candidates: 任务名称标准候选列表。

    Returns:
        识别出的任务信息；名称区域不可确认时返回 None。
    """
    name_x1, name_x2, name_y_offset, name_y_pad = _MISSION_COORDINATES.name_region
    progress_x1, progress_x2, progress_y_offset, progress_y_pad = (
        _MISSION_COORDINATES.progress_region
    )
    name_y = anchor_y + name_y_offset
    prog_y = anchor_y + progress_y_offset

    # 1. 裁剪任务名称区域并执行 OCR。
    name_roi = ROI(
        name_x1,
        max(0.0, name_y - name_y_pad),
        name_x2,
        min(1.0, name_y + name_y_pad),
    )
    name_img = name_roi.crop(screen)
    name_result = ocr_engine.recognize_single(name_img)
    raw_text = name_result.text.strip()
    confidence = name_result.confidence

    # 2. 低置信度结果无法支撑业务匹配，直接忽略该任务行。
    if confidence < _OCR_CONFIDENCE_MIN:
        return None

    # 3. 将 OCR 原文匹配为任务数据库中的标准名称。
    matched_name = match_mission_name(raw_text, candidates)
    final_name = matched_name or raw_text

    # 4. 裁剪进度区域并提取完成百分比。
    prog_roi = ROI(
        progress_x1,
        max(0.0, prog_y - progress_y_pad),
        progress_x2,
        min(1.0, prog_y + progress_y_pad),
    )
    prog_img = prog_roi.crop(screen)
    prog_result = ocr_engine.recognize_single(prog_img, allowlist='0123456789%:')
    prog_text = prog_result.text.strip()
    progress_match = _PROGRESS_PATTERN.search(prog_text)
    progress = int(progress_match.group(1)) if progress_match else -1

    claimable = btn_type == ButtonType.CLAIM

    return MissionInfo(
        name=final_name,
        raw_text=raw_text,
        progress=progress,
        claimable=claimable,
        confidence=confidence,
    )


def recognize_missions(
    screen: numpy.ndarray,
    ocr_engine: OCREngine,
) -> list[MissionInfo]:
    """识别单帧截图中的可见任务。

    Args:
        screen: 任务页面 RGB 截图。
        ocr_engine: 用于识别任务名称和进度的 OCR 引擎。

    Returns:
        按页面从上到下排列的可见任务列表。
    """
    rows = find_button_rows(screen)
    if not rows:
        return []

    candidates = read_all_mission_names()
    missions: list[MissionInfo] = []
    for anchor_y, btn_type in rows:
        mission = recognize_row(screen, anchor_y, btn_type, ocr_engine, candidates)
        if mission is not None:
            missions.append(mission)
    return missions


def match_mission_name(
    ocr_text: str,
    candidates: list[str],
    threshold: int = _MISSION_NAME_DISTANCE_THRESHOLD,
) -> str | None:
    """在任务数据库中模糊匹配任务名。

    Args:
        ocr_text: 任务名称的 OCR 原文。
        candidates: 任务名称标准候选列表。
        threshold: 允许的最大编辑距离。

    Returns:
        匹配到的标准任务名；无法确认时返回 None。
    """
    if not ocr_text:
        return None

    # 1. 精确匹配优先，避免对可靠文本执行模糊推断。
    for name in candidates:
        if ocr_text == name:
            return name

    # 2. 仅当长度比例足够接近时接受子串匹配，并优先最长候选。
    substring_hits = [
        name
        for name in candidates
        if (name in ocr_text or ocr_text in name)
        and min(len(name), len(ocr_text)) >= 0.7 * max(len(name), len(ocr_text))
    ]
    if substring_hits:
        return max(substring_hits, key=len)

    # 3. 最后使用编辑距离处理 OCR 的少量字符误差。
    best_name: str | None = None
    best_dist = threshold + 1
    for name in candidates:
        # common.vision.ocr 未公开编辑距离；通过模块限定名保留实现归属。
        dist = ocr._edit_distance(ocr_text, name)
        if dist < best_dist:
            best_dist = dist
            best_name = name
    return best_name if best_dist <= threshold else None


# ── 奖励按钮识别 ────────────────────────────────────────────────────────────────────


def find_reward_collect_all_button(
    screen: numpy.ndarray,
) -> vision.ImageMatchDetail | None:
    """读取任务页面的一键领取按钮命中结果。

    Args:
        screen: 任务页面 RGB 截图。

    Returns:
        一键领取按钮的模板匹配结果；未命中时返回 None。
    """
    return vision.ImageChecker.find_template(screen, Templates.GameUI.REWARD_COLLECT_ALL)


def find_reward_collect_button(screen: numpy.ndarray) -> vision.ImageMatchDetail | None:
    """读取任务页面的单个领取按钮命中结果。

    Args:
        screen: 任务页面 RGB 截图。

    Returns:
        单个领取按钮的模板匹配结果；未命中时返回 None。
    """
    return vision.ImageChecker.find_template(screen, Templates.GameUI.REWARD_COLLECT)


def find_confirm_button(screen: numpy.ndarray) -> vision.ImageMatchDetail | None:
    """读取奖励确认按钮命中结果。

    Args:
        screen: 奖励确认弹窗 RGB 截图。

    Returns:
        确认按钮的模板匹配结果；未命中时返回 None。
    """
    return vision.ImageChecker.find_any(screen, Templates.Confirm.all())


# 按上方识别流程的定义顺序导出公开对象。
__all__ = [  # noqa: RUF022
    'ButtonType',
    'MissionInfo',
    'read_all_mission_names',
    'find_button_rows',
    'recognize_row',
    'recognize_missions',
    'match_mission_name',
    'find_reward_collect_all_button',
    'find_reward_collect_button',
    'find_confirm_button',
]
