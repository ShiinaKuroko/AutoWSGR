"""出征准备 — 舰船状态检测与舰队信息识别。

提供血量检测、等级 OCR 识别等静态 / 实例方法。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from autowsgr.application.ui.pages.battle_preparation.base import BaseBattlePreparation
from autowsgr.application.ui.ship_list import extract_ship_type_from_text
from autowsgr.common.calibration.battle_preparation import (
    BLOOD_BAR_PROBE,
    SHIP_LEVEL_CROP,
    SHIP_TYPE_CROP,
)
from autowsgr.common.system.logger import get_logger
from autowsgr.common.vision import PixelChecker
from autowsgr.common.vision.ocr_rules import (
    EasyOCRProfile,
)
from autowsgr.common.vision.ship_list import (
    best_fleet_level,
    parse_fleet_level,
    prepare_level_crop,
    upscale_text_crop,
)
from autowsgr.types import ShipDamageState, ShipType

from .blood import classify_blood


if TYPE_CHECKING:
    from collections.abc import Collection

    import numpy as np


_log = get_logger('ui.preparation')


# ═══════════════════════════════════════════════════════════════════════════════
# 数据类
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class FleetInfo:
    """舰队详细信息。"""

    fleet_id: int | None = None
    """舰队编号 (1-4)，``None`` 表示未指定。"""
    ship_levels: dict[int, int | None] = field(default_factory=dict)
    """槽位号 (0-5) → 等级，无法识别或无舰船则为 ``None``。"""
    ship_damage: dict[int, ShipDamageState] = field(default_factory=dict)
    """槽位号 (0-5) → 血量状态。"""

    def to_ships(self, names: list[str | None] | list[str] | None = None) -> list[object]:
        """将舰队信息转换为 Ship 列表。

        Parameters
        ----------
        names:
            可选的舰船名称列表 (0-indexed, 与槽位对应)。
            ``None`` 元素或缺少的索引将使用空字符串。

        Returns
        -------
        list[object]
            按槽位顺序排列，跳过无舰船的槽位。
        """
        from types import SimpleNamespace

        ships: list[object] = []
        for i in range(6):
            damage = self.ship_damage.get(i, ShipDamageState.NORMAL)
            if damage == ShipDamageState.NO_SHIP:
                continue
            name = ''
            if names and i < len(names) and names[i] is not None:
                name = names[i] or ''
            ships.append(
                SimpleNamespace(name=name, level=self.ship_levels.get(i) or 0, damage_state=damage)
            )
        return ships


# ═══════════════════════════════════════════════════════════════════════════════
# Mixin
# ═══════════════════════════════════════════════════════════════════════════════


class DetectionMixin(BaseBattlePreparation):
    """舰船状态检测 Mixin。

    依赖 :class:`~autowsgr.application.ui.pages.battle_preparation.base.BaseBattlePreparation` 提供的
    ``_ctrl``, ``_ocr``, ``get_selected_fleet``, ``select_fleet``。
    """

    # ── 血量检测 ──────────────────────────────────────────────────────────

    @staticmethod
    def detect_ship_damage(screen: np.ndarray) -> dict[int, ShipDamageState]:
        """检测 6 个舰船槽位的血量状态。

        Returns
        -------
        dict[int, ShipDamageState]
            槽位号 (0-5) → 血量状态。
        """
        result: dict[int, ShipDamageState] = {}
        for slot, (x, y) in BLOOD_BAR_PROBE.items():
            pixel = PixelChecker.get_pixel(screen, x, y)
            result[slot] = classify_blood(pixel)
        _log.debug(
            '[准备页] 血量检测: {}',
            ' | '.join(f'槽{i}={result[i].name}' for i in range(len(result))),
        )
        return result

    # ── 等级 OCR ──────────────────────────────────────────────────────────

    def _recognize_fleet_levels(
        self,
        screen: np.ndarray,
        slots: Collection[int] | None = None,
    ) -> dict[int, int | None]:
        """从准备页截图中 OCR 识别每艘舰船的等级。

        读取各舰船卡片上的 ``Lv.XX`` / ``Lv XX`` 文本，提取数字部分。

        Parameters
        ----------
        screen:
            出征准备页的截图。
        slots:
            仅识别指定槽位。未指定时按原逻辑先检测血条，再识别全部有船槽位。

        Returns
        -------
        dict[int, int | None]
            槽位号 (0-5) → 等级。无法识别或无舰船则为 ``None``。
        """
        requested_slots = list(range(6)) if slots is None else sorted(set(slots))
        levels: dict[int, int | None] = dict.fromkeys(requested_slots)
        ocr = self._preferred_ocr
        if ocr is None:
            _log.warning('[UI] 未提供 OCR 引擎，无法识别舰船等级')
            return levels

        if slots is None:
            damage = self.detect_ship_damage(screen)
            target_slots = [
                slot for slot in requested_slots if damage.get(slot) != ShipDamageState.NO_SHIP
            ]
        else:
            target_slots = requested_slots

        for slot in target_slots:
            crop_region = SHIP_LEVEL_CROP.get(slot)
            if crop_region is None:
                continue

            prepared = PixelChecker.crop(screen, *crop_region)
            if self._ship_ocr is None:
                prepared = prepare_level_crop(prepared)

            # 两种引擎统一使用等级字符集和同一套结果解析规则。
            ocr_results = ocr.recognize_line(
                prepared,
                easyocr_profile=EasyOCRProfile.FLEET_SHIP_LEVEL,
            )
            level = self._best_level_from_results(ocr_results)
            levels[slot] = level

            _log.debug(
                '[准备页] 等级OCR原始及后处理: 物理槽位={} raw={} parsed={}',
                slot + 1,
                ocr_results,
                level,
            )
        return levels

    # ── 舰种 OCR ─────────────────────────────────────────────────────────

    def _recognize_fleet_ship_types(
        self,
        screen: np.ndarray,
        slots: Collection[int] | None = None,
    ) -> dict[int, ShipType | None]:
        """从准备页截图中 OCR 识别每艘舰船的舰种。

        读取各舰船卡片上的舰种文本 (如 ``轻巡(J国)``)，用于首次换船快照，
        使已就位的目标舰船可以跳过船池二次确认。
        """
        requested_slots = list(range(6)) if slots is None else sorted(set(slots))
        ship_types: dict[int, ShipType | None] = dict.fromkeys(requested_slots)
        ocr = self._preferred_ocr
        if ocr is None:
            _log.warning('[UI] 未提供 OCR 引擎，无法识别舰种')
            return ship_types

        if slots is None:
            damage = self.detect_ship_damage(screen)
            target_slots = [
                slot for slot in requested_slots if damage.get(slot) != ShipDamageState.NO_SHIP
            ]
        else:
            target_slots = requested_slots

        for slot in target_slots:
            crop_region = SHIP_TYPE_CROP.get(slot)
            if crop_region is None:
                continue

            cropped = PixelChecker.crop(screen, *crop_region)
            # 4x 上采样提升小字 OCR 准确率 (对齐等级识别)
            upscaled = upscale_text_crop(cropped, 4)
            ocr_results = ocr.recognize(upscaled)
            ship_type = self._best_ship_type_from_results(ocr_results)
            ship_types[slot] = ship_type

            _log.debug(
                '[准备页] 舰种OCR原始及后处理: 物理槽位={} raw={} parsed={}',
                slot + 1,
                ocr_results,
                ship_type.value if ship_type is not None else None,
            )
        return ship_types

    @staticmethod
    def _best_ship_type_from_results(results: list) -> ShipType | None:
        """从多个 OCR 结果中提取唯一舰种；歧义或无法识别返回 None。"""
        detected: ShipType | None = None
        for r in results:
            text = str(getattr(r, 'text', '')).strip()
            if not text:
                continue
            ship_type = extract_ship_type_from_text(text)
            if ship_type is None:
                continue
            if detected is not None and detected != ship_type:
                return None
            detected = ship_type
        return detected

    # ── 舰队信息聚合 ─────────────────────────────────────────────────────

    def detect_fleet_info(
        self,
        fleet_id: int | None = None,
    ) -> FleetInfo:
        """识别指定舰队的详细信息（等级、血量）。

        若 ``fleet_id`` 不为 ``None`` 且与当前选中的舰队不同，
        将先切换到目标舰队。

        Parameters
        ----------
        fleet_id:
            目标舰队编号 (1-4)。为 ``None`` 则不切换舰队。

        Returns
        -------
        FleetInfo
            包含舰队编号、各舰船等级和血量信息。
        """
        if fleet_id is not None:
            screen = self._ctrl.screenshot()
            current_fleet = self.get_selected_fleet(screen)
            if current_fleet != fleet_id:
                self.select_fleet(fleet_id)
                time.sleep(0.5)

        screen = self._ctrl.screenshot()
        actual_fleet = self.get_selected_fleet(screen)
        damage = self.detect_ship_damage(screen)
        levels = self._recognize_fleet_levels(screen)

        info = FleetInfo(
            fleet_id=actual_fleet,
            ship_levels=levels,
            ship_damage=damage,
        )

        _log.info(
            '[UI] 舰队 {} 信息: {}',
            actual_fleet or '?',
            ' | '.join(
                f'槽{i}=Lv.{levels.get(i, "?")} {damage[i].name if i in damage else "?"}'
                for i in range(6)
            ),
        )
        return info

    # ── 工具 ──────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_level(text: str) -> int | None:
        """解析准备页等级文本。"""
        return parse_fleet_level(text)

    @classmethod
    def _best_level_from_results(cls, results: list) -> int | None:
        """从多个 OCR 结果中选取最佳等级值。"""
        return best_fleet_level(results)
