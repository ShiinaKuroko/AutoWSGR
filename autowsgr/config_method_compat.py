"""战斗方法配置和计划的 legacy 兼容迁移。"""

from __future__ import annotations

from typing import Any

from autowsgr.common.system.logger import get_logger


_log = get_logger('infra')


def _is_empty_fleet_slot(value: object) -> bool:
    """是否是计划 fleet 的空槽位。"""
    if value is None:
        return True
    return isinstance(value, str) and not value.strip()


def detect_legacy_plan(data: Any) -> list[str]:
    """返回计划数据中命中的 legacy 项。"""
    if not isinstance(data, dict):
        return []
    fleet = data.get('fleet')
    if isinstance(fleet, list) and fleet and _is_empty_fleet_slot(fleet[0]):
        return ['classic 1-indexed fleet 前导空占位 (首位为空, 请剥离)']
    return []


def migrate_plan_dict(data: Any) -> Any:
    """原地转换 legacy 计划 dict 为当前格式。"""
    if not isinstance(data, dict):
        return data
    _migrate_plan_fleet(data)
    return data


def _migrate_plan_fleet(data: dict[str, Any]) -> None:
    """剥离 classic 1-indexed fleet 的前导空槽位。"""
    fleet = data.get('fleet')
    if not isinstance(fleet, list) or not fleet:
        return

    cleaned = list(fleet)
    while cleaned and _is_empty_fleet_slot(cleaned[0]):
        cleaned.pop(0)

    if cleaned != fleet:
        data['fleet'] = cleaned
        _log.warning(
            '[compat] classic 1-indexed fleet 前导空占位已剥离 ({} → {}), '
            '已迁移为 dev 0-indexed 格式。',
            fleet,
            cleaned,
        )
