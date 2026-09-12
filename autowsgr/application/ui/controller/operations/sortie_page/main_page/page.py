"""模块功能：管理 sortie_page 页面壳、顶部标签识别和标签切换。

上层调用：
- application.ui.controller.operations.sortie_page.*_page：进入对应出征模式前选择顶部标签。
- application.ui.controller.home.main_page、application.ui.navigation：判断是否已进入 sortie_page，或从 sortie_page 返回主页。
- application.ui.controller.sidebar、application.ui.controller.operations.mission_page：复用顶部标签页面识别器。
- common.vision.page_match：复用标签页状态判断。

下层依赖：
- application.ui.controller.operations.sortie_page.main_page.constants：提供 sortie_page 返回和通知校准。
- application.ui.controller.operations.sortie_page.main_page.data：提供出征顶部标签类型和顺序。
- common.calibration.tabbed：提供标签栏坐标、颜色和模板校准。
- common.vision：提供像素检查和页面匹配结果。

sortie_page 的五个顶部标签共享同一种页面壳；建造、强化、任务和好友页面也复用同一套
视觉匹配算法，但各自的页面控制器直接消费本模块的稳定识别入口，不参与 sortie 页面聚合::

    ┌──────────────────────────────────────────────────────────────┐
    │ ◁   [标签1]  标签2   标签3   ...                            │
    ├──────────────────────────────────────────────────────────────┤
    │                      内容区域                                │
    └──────────────────────────────────────────────────────────────┘

检测体系
--------

1. **标签栏探测** — 5 个固定位置，恰好 1 个蓝色 + 其余暗色
   → 确认为标签页，蓝色索引 = 激活标签 (0-4)

2. **模板匹配** — 对标签栏区域 (顶部 7.5%、左侧 63%) 进行自适应
   二值化，缩放到标准尺寸 (600x40) 后与 5 个参考模板逐一比较，
   取覆盖度 (coverage) 最高者为页面类型。

模板匹配原理
------------

**二值化**: ``cv2.adaptiveThreshold`` (高斯, blockSize=21, C=-5)
在局部邻域做亮度对比，能同时提取高亮激活标签文字与灰色非激活标签文字，
同时抑制暗色背景。

**覆盖度 (coverage)**: 测试图像白色像素中有多少在参考模板中也是白色::

    coverage = |test ∩ template| / |test|

覆盖度越高，说明测试图像的亮区域越接近该模板。
参考模板由多张截图 OR 合成，覆盖了各标签激活状态。

标签与页面对应::

    索引  地图(5标签)  建造(4标签)  强化(3标签)  任务(5标签)  好友(4标签)
      0    出征         建造         强化         任务         好友
      1    演习         解体         改修          —           访问
      2    远征         开发         技能          —           搜索
      3    战役         废弃          —            —           申请
      4    决战          —            —            —            —

使用方式::

    from autowsgr.application.ui.controller.operations.sortie_page.main_page import (
        SortiePage,
        SortieTab,
        TabbedPageType,
        check_tab_bar,
        read_active_tab_index,
        read_page_type,
        create_tab_checker,
    )

    screen = ctrl.screenshot()

    if check_tab_bar(screen):
        idx = read_active_tab_index(screen)       # 0-4
        page = read_page_type(screen)             # MAP / BUILD / FRIEND / ...

    # 用于 click_and_wait_for_page 的 checker
    checker = create_tab_checker(TabbedPageType.MAP, tab_index=2)
"""

from __future__ import annotations

import enum
import time
from functools import lru_cache
from typing import TYPE_CHECKING

import cv2
import numpy as np

from autowsgr.application.ui.controller.operations.sortie_page.main_page import constants
from autowsgr.application.ui.controller.operations.sortie_page.main_page.data import (
    SORTIE_TAB_INDEX,
    SORTIE_TAB_LIST,
    SortieTab,
)
from autowsgr.common.calibration.tabbed import (
    ADAPTIVE_BLOCK as _ADAPTIVE_BLOCK,
)
from autowsgr.common.calibration.tabbed import (
    ADAPTIVE_C as _ADAPTIVE_C,
)
from autowsgr.common.calibration.tabbed import (
    CROP_X as _CROP_X,
)
from autowsgr.common.calibration.tabbed import (
    CROP_Y as _CROP_Y,
)
from autowsgr.common.calibration.tabbed import (
    REFERENCE_HEIGHT as _REF_H,
)
from autowsgr.common.calibration.tabbed import (
    REFERENCE_WIDTH as _REF_W,
)
from autowsgr.common.calibration.tabbed import (
    TAB_BLUE,
    TAB_BLUE_TOLERANCE,
    TAB_DARK_MAX,
    TAB_PROBES,
)
from autowsgr.common.calibration.tabbed import (
    TEMPLATE_DIR as _TEMPLATE_DIR,
)
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.ui.interaction import NavigationError, click_and_wait_for_page
from autowsgr.common.vision import PageMatch, PixelChecker


if TYPE_CHECKING:
    from collections.abc import Callable

    from autowsgr.application.ui.context import UIContext as GameContext


_log = get_logger('ui')


# ═══════════════════════════════════════════════════════════════════════════════
# 枚举
# ═══════════════════════════════════════════════════════════════════════════════


class TabbedPageType(enum.Enum):
    """标签页面类型。"""

    MAP = PageName.MAP
    BUILD = PageName.BUILD
    INTENSIFY = PageName.INTENSIFY
    MISSION = PageName.MISSION
    FRIEND = PageName.FRIEND


# ═══════════════════════════════════════════════════════════════════════════════
# 标签栏探测常量
# ═══════════════════════════════════════════════════════════════════════════════


# ── 非激活标签参考暗色 ──


# ═══════════════════════════════════════════════════════════════════════════════
# 模板匹配常量与加载
# ═══════════════════════════════════════════════════════════════════════════════


def _load_templates() -> dict[TabbedPageType, np.ndarray]:
    """从 ``autowsgr/common/data/images/ui/`` 加载 5 个参考模板。

    模板为二值 PNG (0/255)，尺寸 600x40。

    Returns:
    dict[TabbedPageType, np.ndarray]
        布尔数组 (True = 白色像素)。
    """
    mapping = {
        TabbedPageType.MAP: 'map.png',
        TabbedPageType.BUILD: 'build.png',
        TabbedPageType.INTENSIFY: 'intensify.png',
        TabbedPageType.MISSION: 'mission.png',
        TabbedPageType.FRIEND: 'friend.png',
    }
    result: dict[TabbedPageType, np.ndarray] = {}
    for page_type, filename in mapping.items():
        path = _TEMPLATE_DIR / filename
        buf = np.frombuffer(path.read_bytes(), np.uint8)
        img = cv2.imdecode(buf, cv2.IMREAD_UNCHANGED)
        result[page_type] = img > 0
    return result


# 模块级缓存 — 首次调用时加载
@lru_cache(maxsize=1)
def _get_templates() -> dict[TabbedPageType, np.ndarray]:
    """获取参考模板 (懒加载 + 缓存)。"""
    return _load_templates()


def _binarize_tabbar(screen: np.ndarray) -> np.ndarray:
    """将截图标签栏区域二值化并缩放到标准尺寸。

    步骤:

    1. 裁剪顶部 7.5%、左侧 63% (标签栏区域)
    2. 转灰度
    3. 自适应阈值二值化 (高斯, blockSize=21, C=-5)
    4. 缩放到 600x40 (最近邻插值)

    Args:
    screen:
        截图 (HxWx3, RGB 或 BGR 均可用于灰度转换)。

    Returns:
    np.ndarray
        布尔数组 (600x40)，True = 白色像素。
    """
    h, w = screen.shape[:2]
    crop = screen[0 : int(h * _CROP_Y), 0 : int(w * _CROP_X)]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        _ADAPTIVE_BLOCK,
        _ADAPTIVE_C,
    )
    resized = cv2.resize(binary, (_REF_W, _REF_H), interpolation=cv2.INTER_NEAREST)
    return resized > 0


def _coverage(test: np.ndarray, template: np.ndarray) -> float:
    """计算覆盖度: 测试图像白色像素中有多少在模板中也是白色。

    ``coverage = |test ∩ template| / |test|``

    Args:
    test:
        测试图像布尔数组。
    template:
        参考模板布尔数组。

    Returns:
    float
        覆盖度 [0.0, 1.0]。
    """
    test_sum = int(test.sum())
    if test_sum == 0:
        return 0.0
    return float((test & template).sum()) / test_sum


def _match_page_type(screen: np.ndarray) -> tuple[TabbedPageType, float] | None:
    """通过模板匹配识别标签页面类型。

    对标签栏区域二值化后，与 5 个参考模板逐一比较覆盖度，
    取最高者。

    Args:
    screen:
        截图 (HxWx3)。

    Returns:
    tuple[TabbedPageType, float] | None
        ``(页面类型, 覆盖度)``;覆盖度需 > 0.6 才视为命中。
        无模板或无命中时返回 ``None``。
    """
    templates = _get_templates()
    if not templates:
        return None

    test_bin = _binarize_tabbar(screen)
    best_type: TabbedPageType | None = None
    best_score = -1.0
    for page_type, tmpl in templates.items():
        score = _coverage(test_bin, tmpl)
        if score > 0.6 and score > best_score:
            best_score = score
            best_type = page_type
    if best_type is None:
        return None
    return best_type, best_score


# ═══════════════════════════════════════════════════════════════════════════════
# 检测函数
# ═══════════════════════════════════════════════════════════════════════════════


def check_tab_bar(screen: np.ndarray) -> bool:
    """判断截图是否为标签页面 (地图/建造/强化/任务 之一)。

    检测逻辑: 5 个标签栏探测点中恰好 1 个蓝色 + 其余全部暗色。

    Args:
    screen:
        截图 (HxWx3, RGB)。
    """
    blue_count = 0
    dark_count = 0
    for _i, (x, y) in enumerate(TAB_PROBES):
        pixel = PixelChecker.get_pixel(screen, x, y)
        is_blue = pixel.near(TAB_BLUE, TAB_BLUE_TOLERANCE)
        is_dark = max(pixel.r, pixel.g, pixel.b) < TAB_DARK_MAX
        # _log.debug(
        #     '[TabCheck] probe[{}] ({:.4f},{:.4f}) → ({},{},{}) blue={} dark={}',
        #     i, x, y, pixel.r, pixel.g, pixel.b, is_blue, is_dark,
        # )
        if is_blue:
            blue_count += 1
        elif is_dark:
            dark_count += 1
    result = blue_count == 1 and dark_count == len(TAB_PROBES) - 1
    # _log.debug('[TabCheck] blue={} dark={} → is_tabbed={}', blue_count, dark_count, result)
    return result


def check_tabbed_page(screen: np.ndarray, page_type: TabbedPageType) -> PageMatch:
    """识别截图是否为指定标签页面类型,返回带覆盖度分数的 :class:`PageMatch`。

    供 5 个标签页面 (地图/建造/强化/任务/好友) 的 ``check_current_page`` 注册到
    :func:`~autowsgr.application.ui.navigation.registry.register_page` 使用:把两层检测
    (标签栏验证 + 模板覆盖度) 的结果统一为 ``score``,让页面注册中心
    能在候选集内按分数排序、消歧。

    Args:
    screen:
        截图 (HxWx3, RGB)。
    page_type:
        期望的页面类型。

    Returns:
    PageMatch
        ``matched=True`` 时 ``score`` 为该页面的模板覆盖度 (0.6, 1.0]。
    """
    page_name = str(page_type.value)
    if not check_tab_bar(screen):
        return PageMatch(name=page_name, matched=False, score=0.0)
    matched = _match_page_type(screen)
    if matched is None or matched[0] != page_type:
        return PageMatch(name=page_name, matched=False, score=0.0)
    return PageMatch(name=page_name, matched=True, score=matched[1])


def read_active_tab_index(screen: np.ndarray) -> int | None:
    """获取当前激活标签的索引 (0-4)。

    Args:
    screen:
        截图 (HxWx3, RGB)。

    Returns:
    int | None
        蓝色探测点的索引 (0-4)，未找到返回 ``None``。
    """
    for i, (x, y) in enumerate(TAB_PROBES):
        if PixelChecker.get_pixel(screen, x, y).near(TAB_BLUE, TAB_BLUE_TOLERANCE):
            return i
    return None


def read_page_type(screen: np.ndarray) -> TabbedPageType | None:
    """识别截图对应的标签页面类型。

    两层检测:

    1. 标签栏验证 — 确认为标签页 (1 蓝 + 4 暗)
    2. 模板匹配 — 对标签栏区域二值化，与 5 个参考模板比较覆盖度

    Args:
    screen:
        截图 (HxWx3, RGB)。

    Returns:
    TabbedPageType | None
        页面类型，非标签页返回 ``None``。
    """
    if not check_tab_bar(screen):
        return None

    matched = _match_page_type(screen)
    return matched[0] if matched else None


def create_tab_checker(
    page_type: TabbedPageType,
    tab_index: int,
) -> Callable[[np.ndarray], bool]:
    """创建用于 :func:`click_and_wait_for_page` 的标签页验证函数。

    返回的函数检查:
    1. 页面类型匹配
    2. 激活标签索引匹配

    Args:
    page_type:
        期望的页面类型。
    tab_index:
        期望的激活标签索引 (0-4)。
    """

    def _check(screen: np.ndarray) -> bool:
        return read_page_type(screen) == page_type and read_active_tab_index(screen) == tab_index

    return _check


def create_page_checker(
    page_type: TabbedPageType,
) -> Callable[[np.ndarray], bool]:
    """创建仅检查页面类型的验证函数 (不限定具体标签)。

    Args:
    page_type:
        期望的页面类型。
    """

    def _check(screen: np.ndarray) -> bool:
        return read_page_type(screen) == page_type

    return _check


class SortiePage:
    """sortie_page 页面壳控制器，直接管理顶部标签和通用返回。"""

    _TAB_SWITCH_MAX_RETRIES = 3
    """顶部标签切换失败时的最大重试次数。"""

    _TAB_SWITCH_RETRY_DELAY = 1.0
    """顶部标签切换重试前的等待时间。"""

    def __init__(self, ctx: GameContext) -> None:
        """保存调用方注入的运行时 UI 上下文。

        Args:
            ctx: 当前运行时 UI 上下文。
        """
        self._ctx = ctx
        self._ctrl = ctx.ctrl
        self._ocr = ctx.ocr

    # ── 页面检查 ──────────────────────────────────────────────────────────

    @staticmethod
    def check_current_page(screen: np.ndarray) -> PageMatch:
        """判断截图是否已经进入 sortie_page 页面壳。

        Args:
            screen: RGB 截图，形状为 ``(H, W, 3)``。

        Returns:
            sortie_page 顶部标签栏的页面匹配结果。
        """
        return check_tabbed_page(screen, TabbedPageType.MAP)

    @staticmethod
    def check_expedition_notification(screen: np.ndarray) -> bool:
        """检查 sortie_page 顶部是否仍显示远征完成通知。

        Args:
            screen: sortie_page 当前截图。

        Returns:
            顶部远征通知探针命中时返回 ``True``。
        """
        x, y = constants.EXPEDITION_NOTIF_PROBE
        return PixelChecker.get_pixel(screen, x, y).near(
            constants.EXPEDITION_NOTIF_COLOR,
            constants.EXPEDITION_NOTIF_TOLERANCE,
        )

    # ── 顶部标签状态 ──────────────────────────────────────────────────────

    @staticmethod
    def read_active_tab(screen: np.ndarray) -> SortieTab | None:
        """读取 sortie_page 当前选中的业务标签。

        Args:
            screen: sortie_page 当前截图。

        Returns:
            当前选中的出征标签；无法识别时返回 ``None``。
        """
        index = read_active_tab_index(screen)
        if index is None or index >= len(SORTIE_TAB_LIST):
            return None
        return SORTIE_TAB_LIST[index]

    # ── 顶部标签动作 ──────────────────────────────────────────────────────

    def click_tab(self, tab: SortieTab) -> None:
        """点击目标顶部标签并确认 sortie_page 仍处于目标标签。

        Args:
            tab: 要打开的出征业务标签。

        Raises:
            NavigationError: 多次点击后仍未到达目标标签。
        """
        current = self.read_active_tab(self._ctrl.screenshot())
        target_index = SORTIE_TAB_INDEX[tab]
        source = f'sortie_page-{current.value if current else "?"}'
        target = f'sortie_page-{tab.value}'
        last_error: NavigationError | None = None

        for attempt in range(1, self._TAB_SWITCH_MAX_RETRIES + 1):
            if attempt > 1:
                time.sleep(self._TAB_SWITCH_RETRY_DELAY)
            try:
                click_and_wait_for_page(
                    self._ctrl,
                    click_coord=constants.TAB_POSITIONS[tab.name.lower()],
                    checker=create_tab_checker(TabbedPageType.MAP, target_index),
                    source=source,
                    target=target,
                )
            except NavigationError as error:
                last_error = error
            else:
                return

        raise NavigationError(
            f'顶部标签切换失败 (已重试 {self._TAB_SWITCH_MAX_RETRIES} 次): {source} -> {target}',
            screen=self._ctrl.screenshot(),
        ) from last_error

    def select_tab(self, tab: SortieTab) -> None:
        """确保 sortie_page 当前处于目标顶部标签。

        Args:
            tab: 需要处于选中状态的出征业务标签。
        """
        if self.read_active_tab(self._ctrl.screenshot()) != tab:
            self.click_tab(tab)

    # ── 页面回退 ──────────────────────────────────────────────────────────

    def go_back(self) -> None:
        """从 sortie_page 页面壳返回 Home。

        Raises:
            NavigationError: 点击返回后未确认回到 Home。
        """
        from autowsgr.application.ui.controller.home.main_page import HomePage

        click_and_wait_for_page(
            self._ctrl,
            click_coord=constants.CLICK_BACK,
            checker=HomePage.check_current_page,
            source=PageName.MAP,
            target=PageName.HOME,
        )


__all__ = [
    'SortiePage',
    'SortieTab',
    'TabbedPageType',
    'check_tab_bar',
    'check_tabbed_page',
    'create_page_checker',
    'create_tab_checker',
    'read_active_tab_index',
    'read_page_type',
]
