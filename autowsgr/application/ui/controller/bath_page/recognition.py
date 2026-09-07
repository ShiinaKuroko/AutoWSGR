"""模块功能：从选择修理浮层截图中识别可操作的舰船卡片。

上层调用：
- application.ui.controller.bath_page.page：请求当前浮层的卡片识别结果。
- application.ui.controller.bath_page：导出修理卡片数据模型和识别入口。

下层依赖：
- application.ui.controller.bath_page.constants：提供卡片几何和 OCR 参数。
- common.constants：提供舰船名称表，用于 OCR 模糊匹配。
- common.system.logger：记录卡片检测、OCR 失败和识别结果。
- common.vision.ocr：提供 OCR 引擎和文本匹配能力。
- cv2：定位卡片边界并裁剪 OCR 区域。

识别流程：
1、提取明亮卡片边框并定位卡片矩形。
2、排除被截图边缘截断的卡片。
3、从卡片下半部分分别读取舰船名称和修理时长。
4、按卡片从左到右的顺序返回可用于页面操作的结果。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

import cv2

from autowsgr.application.ui.controller.bath_page import constants
from autowsgr.common.constants import SHIPNAMES
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision.ocr import _fuzzy_match


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.common.vision.ocr import OCREngine

_log = get_logger('ui.bath_page.recognition')

# ── 卡片识别与 OCR 规则 ──────────────────────────────────────────────────────

_TIME_PATTERN = re.compile(r'\d{2}:\d{2}:\d{2}')
"""修理时间格式: HH:MM:SS。"""


@dataclass(frozen=True, slots=True)
class RepairShipInfo:
    """选择修理浮层中识别到的舰船信息。

    Attributes:
        name: 舰船中文名称。
        position: 舰船卡片中心的相对点击坐标。
        repair_time: OCR 得到的修理时长文本，例如 ``"01:23:45"``；未识别时为空。
    """

    name: str
    position: tuple[float, float]
    repair_time: str = ''


def convert_repair_time_to_seconds(time_str: str) -> int:
    """将 OCR 得到的 ``HH:MM:SS`` 修理时长转换为秒数。

    Args:
        time_str: 修理时长文本；空值、字段数量不正确或非数字字段均视为解析失败。

    Returns:
        修理总秒数；解析失败返回 ``0``。
    """
    if not time_str:
        return 0
    parts = time_str.split(':')
    if len(parts) != 3:
        return 0
    try:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except ValueError:
        return 0


def is_fully_visible(
    x: int,
    w: int,
    img_width: int,
    *,
    min_width: int = constants.FULL_CARD_WIDTH,
    width_ratio: float = constants.FULL_CARD_WIDTH_RATIO,
    edge_margin: int = constants.EDGE_MARGIN,
) -> bool:
    """判断卡片是否完整可见，避免页面点击或 OCR 使用截断卡片。

    Args:
        x: 卡片左边缘 x 坐标。
        w: 卡片宽度。
        img_width: 图片总宽度。
        min_width: 标准完整卡片宽度参考值。
        width_ratio: 宽度低于 ``min_width * width_ratio`` 时视为截断。
        edge_margin: 卡片距离图片左右边缘的最小像素距离。

    Returns:
        卡片未被边缘截断且宽度达到阈值时为 ``True``，否则为 ``False``。
    """
    if x < edge_margin:
        return False
    if x + w > img_width - edge_margin:
        return False
    return w >= min_width * width_ratio


def _detect_card_rects(image: np.ndarray) -> list[tuple[int, int, int, int]]:
    """从截图中检测满足几何阈值的卡片矩形。

    Args:
        image: 用于轮廓检测的截图。

    Returns:
        按 x 坐标排序的 ``(x, y, w, h)`` 列表；未检测到卡片时返回空列表。
    """
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, constants.BORDER_THRESHOLD, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    cards: list[tuple[int, int, int, int]] = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if (
            constants.CARD_WIDTH_RANGE[0] < w < constants.CARD_WIDTH_RANGE[1]
            and constants.CARD_HEIGHT_RANGE[0] < h < constants.CARD_HEIGHT_RANGE[1]
        ):
            cards.append((x, y, w, h))

    cards.sort(key=lambda r: r[0])
    return cards


def _normalize_time(raw: str) -> str:
    """把 OCR 原始时间文本统一为可解析的 ``HH:MM:SS`` 形式。

    OCR 引擎常将 ``:`` 识别为 ``;`` 、 ``,`` 或 ``.``，需统一替换。

    Args:
        raw: OCR 原始文本，可能包含“耗时”前缀、空格或错误分隔符。

    Returns:
        规范化后的时间文本；无法恢复完整格式时返回过滤后的文本。
    """
    t = raw.replace('耗时', '').replace(' ', '')
    t = t.replace(';', ':').replace(',', ':').replace('.', ':')
    t = t.strip(':')
    # 只保留时间字段允许的字符。
    t = ''.join(c for c in t if c.isdigit() or c == ':')
    # 连续分隔符不代表有效时间，先压缩为一个。
    while '::' in t:
        t = t.replace('::', ':')
    m = _TIME_PATTERN.search(t)
    if m:
        return m.group(0)
    # OCR 丢失分隔符时，按六位数字恢复 HH:MM:SS。
    digits = ''.join(c for c in t if c.isdigit())
    if len(digits) == 6:
        return f'{digits[0:2]}:{digits[2:4]}:{digits[4:6]}'
    return t


def _ocr_card(
    card_img: np.ndarray,
    ocr: OCREngine,
    card_x: float,
    card_w: float,
    img_width: int,
) -> RepairShipInfo | None:
    """识别单张完整卡片的舰船名称、修理时长和点击位置。

    Args:
        card_img: 卡片区域图像（RGB）。
        ocr: OCR 引擎实例。
        card_x: 卡片在原图中的 x 坐标，用于计算点击位置。
        card_w: 卡片宽度。
        img_width: 原图宽度。

    Returns:
        识别到的舰船信息；名称和修理时长均未识别时返回 ``None``。
    """
    ch = card_img.shape[0]
    half_y = ch // 2
    bottom = card_img[half_y:, :]

    # ── 舰船名称 ─────────────────────────────────────────────────────────────
    results = ocr.recognize(bottom)

    name: str | None = None

    for r in results:
        if r.bbox is None:
            continue
        mid_y = (r.bbox[1] + r.bbox[3]) / 2

        # 只有落在名称区域且达到置信度的文本才能映射为舰船名。
        if constants.NAME_Y_RANGE[0] < mid_y < constants.NAME_Y_RANGE[1]:
            text = r.text.strip()
            if text and name is None and r.confidence >= constants.NAME_CONFIDENCE_MIN:
                matched = _fuzzy_match(text, SHIPNAMES, threshold=3)
                if matched:
                    name = matched

    # ── 修理时长 ─────────────────────────────────────────────────────────────
    time_roi = bottom[constants.TIME_CROP_Y :, :]
    trh, trw = time_roi.shape[:2]
    scaled = cv2.resize(
        time_roi,
        (trw * constants.TIME_SCALE, trh * constants.TIME_SCALE),
        interpolation=cv2.INTER_CUBIC,
    )
    time_results = ocr.recognize(scaled)

    time_text: str = ''
    for r in time_results:
        if r.bbox is None:
            continue
        txt = r.text
        if '耗时' in txt or ':' in txt or ';' in txt or '.' in txt:
            normalized = _normalize_time(txt)
            if _TIME_PATTERN.match(normalized):
                time_text = normalized
                break

    if name is None and time_text == '':
        return None

    # 返回卡片中心的相对坐标，供页面控制器点击整张卡片。
    rel_x = (card_x + card_w / 2) / img_width
    rel_y = 0.5  # 点击卡片中心

    return RepairShipInfo(
        name=name or '',
        position=(rel_x, rel_y),
        repair_time=time_text,
    )


def recognize_repair_cards(
    screen: np.ndarray,
    ocr: OCREngine,
) -> list[RepairShipInfo]:
    """从选择修理浮层截图中识别所有完整可见的舰船卡片。

    Args:
        screen: RGB 截图，形状为 ``(H, W, 3)``。
        ocr: OCR 引擎实例。

    Returns:
        按从左到右排列的舰船信息列表，仅包含完整可见且至少识别出名称或
        修理时长的卡片。
    """
    _h, w = screen.shape[:2]
    # 轮廓检测使用转换后的 BGR 图像，卡片 OCR 仍读取原始 RGB 截图。
    bgr = cv2.cvtColor(screen, cv2.COLOR_RGB2BGR)
    cards = _detect_card_rects(bgr)

    _log.debug('[修理识别] 检测到 {} 张卡片矩形', len(cards))

    result: list[RepairShipInfo] = []
    for x, y, cw, ch in cards:
        if not is_fully_visible(x, cw, w):
            _log.debug('[修理识别] 跳过截断卡片: x={} w={}', x, cw)
            continue

        card_img = screen[y : y + ch, x : x + cw]
        try:
            info = _ocr_card(card_img, ocr, x, cw, w)
        except Exception:
            _log.opt(exception=True).warning('[修理识别] OCR 失败: 卡片 x={} w={}', x, cw)
            continue

        if info is not None:
            result.append(info)
            _log.debug(
                '[修理识别] 识别成功: name={} time={}',
                info.name,
                info.repair_time,
            )

    _log.info('[修理识别] 共识别 {}/{} 张有效卡片', len(result), len(cards))
    return result
