"""读取 sortie_page 页面壳和顶部标签的视觉事实。

上层调用：
- application.ui.controller.operations.sortie_page.main_page.page：提供页面检查和标签状态。
- application.ui.controller.operations.sortie_page.*_page：确认顶部标签和页面类型。

下层依赖：
- application.ui.controller.operations.sortie_page.main_page.constants：提供通知校准。
- common.types：提供页面类型契约。
- common.calibration.tabbed：提供标签栏和模板校准。
- common.vision：提供像素检查和页面匹配结果。

边界：
只从截图读取页面事实，不执行设备操作、页面导航或业务调度。
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

import cv2
import numpy as np

from autowsgr.application.ui.controller.operations.sortie_page.main_page import constants
from autowsgr.common.calibration import tabbed
from autowsgr.application.ui.navigation.types import PageName
from autowsgr.application.ui.navigation.types import PageMatch
from autowsgr.common.vision import PixelChecker


if TYPE_CHECKING:
    from collections.abc import Callable


# ── 识别参数 ────────────────────────────────────────────────────────────────────────

_HOME_PAGE_COVERAGE_MIN = 0.6  # 标签模板覆盖度达到此值才确认页面类型。


# ── 标签模板 ────────────────────────────────────────────────────────────────────────

_TEMPLATE_FILES: dict[PageName, str] = {
    PageName.SORTIE_MAP: 'map.png',
    PageName.BUILD: 'build.png',
    PageName.INTENSIFY: 'intensify.png',
    PageName.MISSION: 'mission.png',
    PageName.FRIEND: 'friend.png',
}


def _load_templates() -> dict[PageName, np.ndarray]:
    """加载 sortie_page 顶部标签参考模板。"""
    result: dict[PageName, np.ndarray] = {}
    for page_type, filename in _TEMPLATE_FILES.items():
        path = tabbed.TEMPLATE_DIR / filename
        buffer = np.frombuffer(path.read_bytes(), np.uint8)
        image = cv2.imdecode(buffer, cv2.IMREAD_UNCHANGED)
        result[page_type] = image > 0
    return result


@lru_cache(maxsize=1)
def _get_templates() -> dict[PageName, np.ndarray]:
    """懒加载并缓存标签参考模板。"""
    return _load_templates()


# ── 标签栏识别 ──────────────────────────────────────────────────────────────────────


def _binarize_tab_bar(screen: np.ndarray) -> np.ndarray:
    """将截图顶部标签栏裁剪、二值化并缩放到模板尺寸。

    Args:
        screen: RGB 截图。

    Returns:
        标签栏二值图像。
    """
    height, width = screen.shape[:2]
    crop = screen[0 : int(height * tabbed.CROP_Y), 0 : int(width * tabbed.CROP_X)]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        tabbed.ADAPTIVE_BLOCK,
        tabbed.ADAPTIVE_C,
    )
    resized = cv2.resize(
        binary,
        (tabbed.REFERENCE_WIDTH, tabbed.REFERENCE_HEIGHT),
        interpolation=cv2.INTER_NEAREST,
    )
    return resized > 0


def _coverage(test: np.ndarray, template: np.ndarray) -> float:
    """计算测试标签图像在参考模板中的覆盖度。"""
    test_pixels = int(test.sum())
    if test_pixels == 0:
        return 0.0
    return float((test & template).sum()) / test_pixels


def _match_page_type(screen: np.ndarray) -> tuple[PageName, float] | None:
    """从标签栏图像中选择覆盖度最高的页面类型。"""
    templates = _get_templates()
    test = _binarize_tab_bar(screen)
    best_type: PageName | None = None
    best_score = _HOME_PAGE_COVERAGE_MIN
    for page_type, template in templates.items():
        score = _coverage(test, template)
        if score > best_score:
            best_type = page_type
            best_score = score
    if best_type is None:
        return None
    return best_type, best_score


def check_tab_bar(screen: np.ndarray) -> bool:
    """判断截图是否包含一个激活且其余未激活的顶部标签栏。"""
    blue_count = 0
    dark_count = 0
    for x, y in tabbed.TAB_PROBES:
        pixel = PixelChecker.get_pixel(screen, x, y)
        if pixel.near(tabbed.TAB_BLUE, tabbed.TAB_BLUE_TOLERANCE):
            blue_count += 1
        elif max(pixel.r, pixel.g, pixel.b) < tabbed.TAB_DARK_MAX:
            dark_count += 1
    return blue_count == 1 and dark_count == len(tabbed.TAB_PROBES) - 1


def check_tabbed_page(screen: np.ndarray, page_type: PageName) -> PageMatch:
    """判断截图是否属于指定标签页面并返回匹配分数。"""
    page_name = str(page_type.value)
    if not check_tab_bar(screen):
        return PageMatch(name=page_name, matched=False, score=0.0)
    matched = _match_page_type(screen)
    if matched is None or matched[0] is not page_type:
        return PageMatch(name=page_name, matched=False, score=0.0)
    return PageMatch(name=page_name, matched=True, score=matched[1])


def read_active_tab_index(screen: np.ndarray) -> int | None:
    """读取当前激活标签的视觉索引。"""
    for index, (x, y) in enumerate(tabbed.TAB_PROBES):
        if PixelChecker.get_pixel(screen, x, y).near(
            tabbed.TAB_BLUE,
            tabbed.TAB_BLUE_TOLERANCE,
        ):
            return index
    return None


def read_page_type(screen: np.ndarray) -> PageName | None:
    """读取截图对应的标签页面类型。"""
    if not check_tab_bar(screen):
        return None
    matched = _match_page_type(screen)
    return matched[0] if matched else None


def create_tab_checker(
    page_type: PageName,
    tab_index: int,
) -> Callable[[np.ndarray], bool]:
    """创建同时检查页面类型和激活标签的导航检查器。"""

    def _check(screen: np.ndarray) -> bool:
        return read_page_type(screen) is page_type and read_active_tab_index(screen) == tab_index

    return _check


def create_page_checker(page_type: PageName) -> Callable[[np.ndarray], bool]:
    """创建只检查标签页面类型的导航检查器。"""

    def _check(screen: np.ndarray) -> bool:
        return read_page_type(screen) is page_type

    return _check


def check_expedition_notification(screen: np.ndarray) -> bool:
    """检查 sortie_page 顶部是否显示远征完成通知。"""
    x, y = constants.EXPEDITION_NOTIF_PROBE
    return PixelChecker.get_pixel(screen, x, y).near(
        constants.EXPEDITION_NOTIF_COLOR,
        constants.EXPEDITION_NOTIF_TOLERANCE,
    )
