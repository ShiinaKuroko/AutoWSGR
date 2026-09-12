"""模块功能：负责任务按钮扫描、任务数据读取和任务名称/进度 OCR 识别。

上层调用：
- application.ui.controller.operations.mission_page.page：请求可见任务和任务结果模型。
- testing.ui：通过任务页面控制器验证按钮扫描和任务识别。

下层依赖：
- application.ui.controller.operations.mission_page.constants：提供按钮颜色和 OCR 裁剪参数。
- common.vision：提供像素读取、ROI 裁剪和 OCR 引擎。
- common.vision.ocr：提供任务名称编辑距离匹配。
- common.data.missions.yaml：提供任务名称候选数据。

本模块不执行设备点击、页面导航或运行时上下文创建；OCR 引擎由页面控制器传入。
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

import autowsgr.common.vision.ocr as _ocr
from autowsgr.application.ui.controller.operations.mission_page.constants import (
    BUTTON_SCAN_ROI as BUTTON_SCAN_ROI_COORDS,
)
from autowsgr.application.ui.controller.operations.mission_page.constants import (
    CLAIM_B_MAX,
    CLAIM_G_MIN,
    CLAIM_R_MIN,
    CLUSTER_GAP,
    GOTO_TOLERANCE,
    MIN_CLUSTER_SIZE,
    NAME_CROP_MIN_Y,
    NAME_ROI_X1,
    NAME_ROI_X2,
    NAME_ROI_Y_PAD,
    NAME_Y_OFFSET,
    OCR_CONFIDENCE_MIN,
    PROGRESS_ROI_X1,
    PROGRESS_ROI_X2,
    PROGRESS_ROI_Y_PAD,
    PROGRESS_Y_OFFSET,
    SCAN_X,
    SCAN_Y_STEP,
    WIDE_BTN_CHECK_X,
)
from autowsgr.application.ui.controller.operations.mission_page.constants import (
    GOTO_COLOR as GOTO_COLOR_RGB,
)
from autowsgr.common.vision import Color, PixelChecker
from autowsgr.common.vision.roi import ROI


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.common.vision import OCREngine


_BUTTON_SCAN_ROI = ROI.from_tuple(BUTTON_SCAN_ROI_COORDS)
_GOTO_COLOR = Color.from_rgb_tuple(GOTO_COLOR_RGB)


# ── 识别结果与任务数据库 ────────────────────────────────────────────────────


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


_MISSIONS_YAML = Path(__file__).resolve().parents[5] / 'common' / 'data' / 'missions.yaml'
"""任务名称数据库路径，用于将 OCR 文本匹配为标准任务名。"""


@lru_cache(maxsize=1)
def _load_mission_db() -> dict:
    """加载并缓存任务名称数据库。"""
    with open(_MISSIONS_YAML, encoding='utf-8') as file:
        return yaml.safe_load(file)


def read_all_mission_names() -> list[str]:
    """读取日常和周常任务名称，供 OCR 模糊匹配使用。"""
    db = _load_mission_db()
    names: list[str] = []
    for category in ('daily', 'weekly'):
        for mission in db.get(category, []):
            name = mission['name']
            if name not in names:
                names.append(name)
    return names


PROGRESS_RE = re.compile(r'(\d{1,3})\s*%')
"""任务进度 OCR 正则，用于提取完成百分比。"""


# ═══════════════════════════════════════════════════════════════════════════════
# 像素扫描
# ═══════════════════════════════════════════════════════════════════════════════


def _is_goto_color(c: Color) -> bool:
    return c.near(_GOTO_COLOR, GOTO_TOLERANCE)


def _is_claim_color(c: Color) -> bool:
    return c.r >= CLAIM_R_MIN and c.g >= CLAIM_G_MIN and c.b <= CLAIM_B_MAX


def find_button_rows(screen: np.ndarray) -> list[tuple[float, ButtonType]]:
    """扫描截图右侧, 定位所有 "前往"/"领取" 按钮行。

    Returns:
    list[tuple[float, ButtonType]]
        每个元素为 (y_center_relative, button_type), 按 y 从上到下排列。
    """
    y_start = _BUTTON_SCAN_ROI.y1
    y_end = _BUTTON_SCAN_ROI.y2

    # 收集所有匹配像素的 (y, type)
    hits: list[tuple[float, ButtonType]] = []
    y = y_start
    while y <= y_end:
        c = PixelChecker.get_pixel(screen, SCAN_X, y)
        if _is_goto_color(c):
            hits.append((y, ButtonType.GOTO))
        elif _is_claim_color(c):
            hits.append((y, ButtonType.CLAIM))
        y += SCAN_Y_STEP

    if not hits:
        return []

    # 聚类: 连续同类型像素归为一组
    clusters: list[list[tuple[float, ButtonType]]] = [[hits[0]]]
    for h in hits[1:]:
        prev = clusters[-1][-1]
        if h[0] - prev[0] < CLUSTER_GAP and h[1] == prev[1]:
            clusters[-1].append(h)
        else:
            clusters.append([h])

    # 取每个簇的中心 y 和类型, 过滤过小的簇 (噪点)
    result: list[tuple[float, ButtonType]] = []
    for cluster in clusters:
        if len(cluster) < MIN_CLUSTER_SIZE:
            continue
        ys = [p[0] for p in cluster]
        y_center = (min(ys) + max(ys)) / 2
        btn_type = cluster[0][1]
        result.append((y_center, btn_type))

    # 过滤底部 "一键领取" 按钮: 它的金色区域横向延伸到 x=0.80,
    # 而任务行按钮仅在 x=0.86-0.96 范围内
    filtered: list[tuple[float, ButtonType]] = []
    for y_center, btn_type in result:
        c_wide = PixelChecker.get_pixel(screen, WIDE_BTN_CHECK_X, y_center)
        if _is_goto_color(c_wide) or _is_claim_color(c_wide):
            continue  # 宽按钮 (UI 元素), 跳过
        # 过滤部分可见行: 名称裁切区域被页面标题栏遮挡
        name_top = y_center + NAME_Y_OFFSET - NAME_ROI_Y_PAD
        if name_top < NAME_CROP_MIN_Y:
            continue
        filtered.append((y_center, btn_type))

    return filtered


# ═══════════════════════════════════════════════════════════════════════════════
# OCR + 匹配
# ═══════════════════════════════════════════════════════════════════════════════


def recognize_row(
    screen: np.ndarray,
    anchor_y: float,
    btn_type: ButtonType,
    ocr: OCREngine,
    candidates: list[str],
) -> MissionInfo | None:
    """识别单行任务。返回 None 表示无效行 (部分可见/垃圾 OCR)。"""
    name_y = anchor_y + NAME_Y_OFFSET
    prog_y = anchor_y + PROGRESS_Y_OFFSET

    # -- 裁切名称区域并 OCR --
    name_roi = ROI(
        NAME_ROI_X1,
        max(0.0, name_y - NAME_ROI_Y_PAD),
        NAME_ROI_X2,
        min(1.0, name_y + NAME_ROI_Y_PAD),
    )
    name_img = name_roi.crop(screen)
    name_result = ocr.recognize_single(name_img)
    raw_text = name_result.text.strip()
    confidence = name_result.confidence

    # -- OCR 置信度过滤: 拒绝垃圾识别 (部分可见任务行) --
    if confidence < OCR_CONFIDENCE_MIN:
        return None

    # -- 模糊匹配数据库 --
    matched_name = match_mission_name(raw_text, candidates)
    final_name = matched_name or raw_text

    # -- 裁切进度区域并 OCR --
    prog_roi = ROI(
        PROGRESS_ROI_X1,
        max(0.0, prog_y - PROGRESS_ROI_Y_PAD),
        PROGRESS_ROI_X2,
        min(1.0, prog_y + PROGRESS_ROI_Y_PAD),
    )
    prog_img = prog_roi.crop(screen)
    prog_result = ocr.recognize_single(prog_img, allowlist='0123456789%:')
    prog_text = prog_result.text.strip()
    m = PROGRESS_RE.search(prog_text)
    progress = int(m.group(1)) if m else -1

    claimable = btn_type == ButtonType.CLAIM

    return MissionInfo(
        name=final_name,
        raw_text=raw_text,
        progress=progress,
        claimable=claimable,
        confidence=confidence,
    )


def match_mission_name(
    ocr_text: str,
    candidates: list[str],
    threshold: int = 5,
) -> str | None:
    """在任务数据库中模糊匹配任务名。

    策略:
    1. 精确匹配
    2. 子串包含
    3. Levenshtein 距离 <= threshold
    """
    if not ocr_text:
        return None

    # 精确匹配
    for name in candidates:
        if ocr_text == name:
            return name

    # 子串包含: 仅当长度比 >= 70% 时视为有效匹配, 优先最长候选
    substring_hits = [
        name
        for name in candidates
        if (name in ocr_text or ocr_text in name)
        and min(len(name), len(ocr_text)) >= 0.7 * max(len(name), len(ocr_text))
    ]
    if substring_hits:
        return max(substring_hits, key=len)

    # Levenshtein 模糊匹配
    best_name: str | None = None
    best_dist = threshold + 1
    for name in candidates:
        dist = _ocr._edit_distance(ocr_text, name)
        if dist < best_dist:
            best_dist = dist
            best_name = name
    return best_name if best_dist <= threshold else None


__all__ = [
    'ButtonType',
    'MissionInfo',
    'find_button_rows',
    'match_mission_name',
    'read_all_mission_names',
    'recognize_row',
]
