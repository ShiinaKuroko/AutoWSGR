"""选船页面 UI 控制器。

使用 :meth:`ChooseShipPage.change_single_ship` 根据舰名、等级和舰种查找并选择舰船。
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

from autowsgr.application.ui.ship_list import extract_ship_type_from_text
from autowsgr.common.calibration.choose_ship import (
    CLICK_DISMISS_KEYBOARD,
    CLICK_REMOVE_SHIP,
    CLICK_SEARCH_BOX,
    INPUT_SIGNATURE,
    PAGE_SIGNATURE,
    SCROLL_FROM_Y,
    SCROLL_TO_Y,
)
from autowsgr.common.constants import SHIPNAMES, normalize_ship_name
from autowsgr.common.system.logger import get_logger
from autowsgr.common.types import PageName
from autowsgr.common.ui.interaction import wait_for_page, wait_leave_page
from autowsgr.common.vision import PageMatch, PixelChecker
from autowsgr.common.vision.ocr import _fuzzy_match
from autowsgr.common.vision.ship_list import (
    LevelOCRRetryNeededError,
    locate_ship_rows,
    read_ship_level_at_card,
    recognize_card_type_texts,
)


if TYPE_CHECKING:
    import numpy as np

    from autowsgr.application.ui.context import UIContext as GameContext
    from autowsgr.application.ui.fleet import ShipSelector
    from autowsgr.common.types import ShipType
    from autowsgr.common.vision import OCREngine


_log = get_logger('ui')

# 选船列表操作重试次数
_OCR_MAX_ATTEMPTS: int = 3

# ═══════════════════════════════════════════════════════════════════════════════
# 页面控制器
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True, slots=True)
class _CardConstraintResult:
    """单张船卡的约束校验结果。"""

    accepted: bool
    type_unknown: bool = False
    level_unknown: bool = False
    retry_level_ocr: bool = False

    @property
    def is_fallback(self) -> bool:
        """是否只能作为宽泛校验的后备候选。"""
        return self.type_unknown or self.level_unknown

    @property
    def fallback_priority(self) -> tuple[int, bool]:
        """后备优先级：未知项更少、舰种已确认的候选优先。"""
        return (
            int(self.type_unknown) + int(self.level_unknown),
            self.type_unknown,
        )


class ChooseShipPage:
    """选船页面控制器。

    从出征准备页面点击舰船槽位后进入此页面。
    提供搜索、选择、移除舰船等原子操作。

    Parameters
    ----------
    ctrl:
        Android 设备控制器实例。
    """

    def __init__(self, ctx: GameContext) -> None:
        self._ctx = ctx
        self._ctrl = ctx.ctrl
        self._ship_ocr = getattr(ctx, 'ship_ocr', None)

    @property
    def _preferred_ocr(self) -> OCREngine | None:
        """返回选船识别优先使用的 OCR 引擎 (增强识别开启时用 FastOCR)。"""
        return self._ship_ocr or self._ctx.ocr

    def _detect_hit_ship_type(
        self,
        screen: np.ndarray,
        cx: float,
        cy: float,
        row_key: float,
    ) -> ShipType | None:
        """以舰名位置为锚点，只识别命中卡片内的舰种区域。"""
        return self._detect_ship_type_in_single_card(screen, cx, cy, row_key)

    # ── 页面识别 ──────────────────────────────────────────────────────────

    @staticmethod
    def is_current_page(screen: np.ndarray) -> PageMatch:
        """判断截图是否为选船页面。

        返回带匹配比例的 :class:`PageMatch` 供候选集排序
        (``PageMatch.__bool__`` 保证旧式真值调用不变)。

        Parameters
        ----------
        screen:
            截图 (HxWx3, RGB)。
        """
        result = PixelChecker.check_signature(screen, PAGE_SIGNATURE)
        return PageMatch(
            name=PageName.CHOOSE_SHIP.value,
            matched=result.matched,
            score=result.ratio,
        )

    def _wait_leave_current_page(self, timeout: float = 5.0):
        wait_leave_page(
            self._ctrl, self.is_current_page, timeout=timeout, source='编队选船', target='编队'
        )

    # ── 操作 ──────────────────────────────────────────────────────────────
    def ensure_search_box(self) -> None:
        """点击搜索框，准备输入舰船名。"""
        _log.debug('[UI] 选船 → 打开搜索框')
        self._ctrl.click(*CLICK_SEARCH_BOX)
        wait_for_page(
            self._ctrl,
            lambda screen: PixelChecker.check_signature(screen, INPUT_SIGNATURE).matched,
            timeout=5.0,
        )

    def input_ship_name(self, name: str) -> None:
        """在搜索框中输入舰船名。

        调用前应先 :meth:`click_search_box`。

        Parameters
        ----------
        name:
            舰船名 (中文)。
        """
        _log.debug("[UI] 选船 → 输入舰船名 '{}'", name)
        self._ctrl.text(name)
        # 等待输入同步
        time.sleep(0.1)

    def ensure_dismiss_keyboard(self) -> None:
        """点击空白区域关闭软键盘。"""
        _log.debug('[UI] 选船 → 关闭键盘')
        self._ctrl.click(*CLICK_DISMISS_KEYBOARD)
        wait_leave_page(
            self._ctrl,
            lambda screen: PixelChecker.check_signature(screen, INPUT_SIGNATURE).matched,
            timeout=5.0,
        )
        # 等待键盘关闭
        time.sleep(0.2)

    def click_remove(self) -> None:
        """点击「移除」按钮，移除当前槽位的舰船。"""
        _log.debug('[UI] 选船 → 移除舰船')
        self._ctrl.click(*CLICK_REMOVE_SHIP)

    def change_single_ship(
        self,
        selector: ShipSelector | None,
        *,
        use_search: bool = True,
    ) -> str | None:
        """按一条明确规则更换舰船，或移除当前槽位舰船。

        使用 DLL 行定位 + OCR 在选船列表中查找目标舰船并点击。
        最多重试 ``_OCR_MAX_ATTEMPTS`` 次, 每次失败后向上滚动列表。

        Parameters
        ----------
        selector:
            FleetChange 已决定好的单条舰船选择规则；``None`` 表示移除。
        use_search:
            是否使用搜索框输入舰船名来过滤列表。
            常规出征为 ``True`` (默认), 决战为 ``False``
            (决战选船界面没有搜索框)。

        Returns
        -------
        str | None
            实际选中的舰船名；移除操作返回 ``None``。
        """
        if selector is None:
            self.click_remove()
            self._wait_leave_current_page()
            return None

        if self._ctx.ocr is None:
            _log.warning('[UI] 未提供 OCR 引擎, 无法识别选船列表')
            return None

        search_name = self._normalize_search_keyword(
            selector.search_name or selector.name,
        )
        if use_search:
            self.ensure_search_box()
            self.input_ship_name(search_name)
            self.ensure_dismiss_keyboard()
        matched = self._click_ship_in_list(
            selector.name,
            ship_type=selector.ship_types or None,
            min_level=selector.min_level,
            max_level=selector.max_level,
            relaxed_constraints=selector.relaxed_constraints,
        )
        if matched is not None:
            self._wait_leave_current_page()
        return matched

    @staticmethod
    def _normalize_hit_entry(hit: object) -> tuple[str, float, float, float]:
        """归一化 locate_ship_rows 的返回为 (name, cx, cy, row_key)。"""
        if not isinstance(hit, (tuple, list)):
            raise TypeError(f'unsupported hit entry: {hit!r}')

        if len(hit) < 3:
            raise ValueError(f'unsupported hit entry length: {hit!r}')

        matched = str(hit[0]).strip()
        cx = float(hit[1])
        cy = float(hit[2])

        if len(hit) >= 4 and isinstance(hit[3], (int, float)):
            row_key = round(float(hit[3]), 4)
        else:
            row_key = round(cy, 4)
        return matched, cx, cy, row_key

    @staticmethod
    def _is_level_in_range(level: int | None, min_level: int | None, max_level: int | None) -> bool:
        if min_level is None and max_level is None:
            return True
        if level is None:
            return False
        if min_level is not None and level < min_level:
            return False
        return not (max_level is not None and level > max_level)

    def _check_hit_constraints(
        self,
        ocr: OCREngine,
        screen: np.ndarray,
        matched: str,
        cx: float,
        cy: float,
        row_key: float,
        *,
        ship_type: tuple[ShipType, ...] | None,
        min_level: int | None,
        max_level: int | None,
        relaxed_constraints: bool,
    ) -> _CardConstraintResult:
        """按舰种、等级顺序校验一张已定位的船卡。"""
        type_unknown = False
        if ship_type is not None:
            detected_ship_type = self._detect_hit_ship_type(
                screen,
                cx,
                cy,
                row_key,
            )
            if detected_ship_type is None:
                _log.debug("[UI] 命中 '{}', 但舰种未识别", matched)
                if not relaxed_constraints:
                    return _CardConstraintResult(accepted=False)
                type_unknown = True
            elif not self._is_ship_type_in_rule(detected_ship_type, ship_type):
                _log.debug(
                    "[UI] 命中 '{}' 舰种 '{}' 不满足要求 '{}'",
                    matched,
                    detected_ship_type,
                    ship_type,
                )
                return _CardConstraintResult(accepted=False)

        level_unknown = False
        retry_level_ocr = False
        if min_level is not None or max_level is not None:
            try:
                level = read_ship_level_at_card(
                    ocr,
                    screen,
                    card_x=cx,
                    row_key=row_key,
                )
            except LevelOCRRetryNeededError:
                retry_level_ocr = True
                level = None
                _log.debug("[UI] 命中 '{}', 但等级 OCR 噪声过高", matched)

            if level is None:
                if not retry_level_ocr:
                    _log.debug("[UI] 命中 '{}', 但等级未识别", matched)
                if not relaxed_constraints:
                    return _CardConstraintResult(
                        accepted=False,
                        retry_level_ocr=retry_level_ocr,
                    )
                level_unknown = True
            elif not self._is_level_in_range(level, min_level, max_level):
                _log.debug(
                    "[UI] 命中 '{}', 但等级 {} 不满足范围 [{}, {}]",
                    matched,
                    level,
                    min_level if min_level is not None else '-',
                    max_level if max_level is not None else '-',
                )
                return _CardConstraintResult(accepted=False)

        result = _CardConstraintResult(
            accepted=True,
            type_unknown=type_unknown,
            level_unknown=level_unknown,
            retry_level_ocr=retry_level_ocr,
        )
        _log.debug(
            "[选船列表] 船卡校验通过: name='{}' row={} type_unknown={} level_unknown={} relaxed={}",
            matched,
            row_key,
            type_unknown,
            level_unknown,
            relaxed_constraints,
        )
        return result

    def _click_ship_in_list(
        self,
        name: str,
        *,
        ship_type: tuple[ShipType, ...] | None = None,
        min_level: int | None = None,
        max_level: int | None = None,
        relaxed_constraints: bool = False,
    ) -> str | None:
        """在选船列表页使用 DLL 定位 + OCR 识别舰船名并点击目标。

        最多重试 ``_OCR_MAX_ATTEMPTS`` 次, 每次失败后向上滚动列表。

        Parameters
        ----------
        name:
            目标舰船名。
            匹配时会先做舰名归一化（如去除“·改”与尾部括号别名）后再比较。
        relaxed_constraints:
            备选舰船使用。舰名必须命中；等级或舰种无法识别时允许作为
            后备候选，明确识别为不符合约束时仍会淘汰。

        Returns
        -------
        str | None
            匹配并点击成功时返回舰船名；失败返回 ``None``。
        """
        assert self._ctx.ocr is not None
        ocr = self._preferred_ocr
        use_level_filter = min_level is not None or max_level is not None
        use_card_constraints = ship_type is not None or use_level_filter

        for attempt in range(_OCR_MAX_ATTEMPTS):
            screen = self._ctrl.screenshot()
            extra_names = {'expected_names': (name,)} if name not in SHIPNAMES else {}
            if use_card_constraints:
                raw_hits = locate_ship_rows(
                    ocr,
                    screen,
                    deduplicate_by_name=False,
                    include_row_key=True,
                    **extra_names,
                )
            else:
                raw_hits = locate_ship_rows(ocr, screen, **extra_names)

            hits = [self._normalize_hit_entry(hit) for hit in raw_hits]
            _log.debug(
                "[选船列表] OCR轮次 {}/{}: target='{}' hits={} required_types={} "
                'level_range=[{}, {}] relaxed={}',
                attempt + 1,
                _OCR_MAX_ATTEMPTS,
                name,
                hits,
                [item.value for item in ship_type] if ship_type is not None else [],
                min_level,
                max_level,
                relaxed_constraints,
            )
            selected_hit: tuple[str, float, float] | None = None
            relaxed_hits: list[tuple[int, bool, int, tuple[str, float, float]]] = []
            retry_level_ocr = False

            for hit_index, (matched, cx, cy, row_key) in enumerate(hits):
                if not self._matches_ship_name(name, matched):
                    continue

                constraint = self._check_hit_constraints(
                    ocr,
                    screen,
                    matched,
                    cx,
                    cy,
                    row_key,
                    ship_type=ship_type,
                    min_level=min_level,
                    max_level=max_level,
                    relaxed_constraints=relaxed_constraints,
                )
                retry_level_ocr = retry_level_ocr or constraint.retry_level_ocr
                if not constraint.accepted:
                    continue

                hit = (matched, cx, cy)
                if constraint.is_fallback:
                    relaxed_hits.append(
                        (
                            *constraint.fallback_priority,
                            hit_index,
                            hit,
                        ),
                    )
                    continue

                selected_hit = hit
                break

            if selected_hit is None and relaxed_hits:
                selected_hit = min(relaxed_hits, key=lambda candidate: candidate[:3])[3]

            if selected_hit is not None:
                matched, cx, cy = selected_hit
                # 当前不判断“远征中”“维修中”等不可选状态；如需支持，应在点击前增加卡片状态识别。
                _log.debug(
                    "[UI] 选船 DLL+OCR -> '{}' (第 {}/{} 次), 点击 ({:.3f}, {:.3f})",
                    name,
                    attempt + 1,
                    _OCR_MAX_ATTEMPTS,
                    cx,
                    cy,
                )
                time.sleep(1.0)
                self._ctrl.click(cx, cy)
                return matched

            if retry_level_ocr and not relaxed_constraints:
                _log.debug(
                    '[UI] 等级 OCR 噪声过高，触发重新识别 (第 {}/{} 次)',
                    attempt + 1,
                    _OCR_MAX_ATTEMPTS,
                )
                if attempt >= _OCR_MAX_ATTEMPTS - 1:
                    _log.debug('[UI] 等级 OCR 噪声过高，本规则校验失败')
                    return None
                time.sleep(0.3)
                continue

            _log.debug(
                "[UI] 选船列表未匹配到 '{}' (第 {}/{} 次), 向上滚动",
                name,
                attempt + 1,
                _OCR_MAX_ATTEMPTS,
            )
            if attempt < _OCR_MAX_ATTEMPTS - 1:
                self._ctrl.swipe(0.4, SCROLL_FROM_Y, 0.4, SCROLL_TO_Y, duration=0.4)
                time.sleep(0.5)

        return None

    def _detect_ship_type_in_single_card(
        self,
        screen: np.ndarray,
        cx: float,
        cy: float,
        row_key: float,
    ) -> ShipType | None:
        """根据舰名中心和所在横带，裁剪单张卡片的舰种区域。"""
        ocr = self._preferred_ocr
        assert ocr is not None

        for scale, results in recognize_card_type_texts(
            ocr,
            screen,
            card_x=cx,
            card_y=cy,
            row_key=row_key,
        ):
            detected_types: set[ShipType] = set()
            for result in results:
                text = str(getattr(result, 'text', '')).strip()
                ship_type = self._extract_ship_type_from_text(text)
                if ship_type is not None:
                    detected_types.add(ship_type)
            _log.debug(
                '[选船列表] 舰种OCR原始及后处理: row={} card_x={} scale={} raw={} parsed={}',
                row_key,
                cx,
                scale,
                results,
                sorted(ship_type.value for ship_type in detected_types),
            )
            if len(detected_types) == 1:
                return next(iter(detected_types))
            if len(detected_types) > 1:
                _log.debug(
                    '[UI] 单卡舰种 OCR 得到多个结果: {}',
                    sorted(ship_type.value for ship_type in detected_types),
                )
                return None
        return None

    @staticmethod
    def _extract_ship_type_from_text(text: str) -> ShipType | None:
        """从 OCR 文本中提取舰种 (共享实现见 :func:`extract_ship_type_from_text`)。"""
        return extract_ship_type_from_text(text)

    @staticmethod
    def _is_ship_type_in_rule(
        detected: ShipType | None,
        expected: tuple[ShipType, ...],
    ) -> bool:
        return detected is not None and detected in expected

    @staticmethod
    def _normalize_search_keyword(name: str) -> str:
        """保留用户在游戏内使用的自定义舰名作为搜索条件。"""
        name = name.strip()
        from autowsgr.common.vision.ocr_rules import get_user_ship_name_alias

        return get_user_ship_name_alias(name) or name

    @classmethod
    def _matches_ship_name(cls, target: str, matched: str) -> bool:
        """比较目标名与 OCR 船池结果，不修改任一原始文本。"""
        normalized_target = normalize_ship_name(target)
        normalized_matched = normalize_ship_name(matched)
        if normalized_target == normalized_matched:
            return True

        pool_target = _fuzzy_match(target, SHIPNAMES, threshold=0)
        return pool_target is not None and normalize_ship_name(pool_target) == normalized_matched
