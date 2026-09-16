"""Temporary concrete errors awaiting their owning modules.

The shared roots come from ``common.system.errors``. Device-owned game errors
live in ``common.device.errors`` and are not duplicated here.
"""

from __future__ import annotations

from autowsgr.common.system.errors import (
    ApplicationError,
    BusinessError,
    CommonError,
    SystemError,
)


# ── 视觉层异常 ──


class OCRError(CommonError):
    """OCR 识别失败。"""


class ImageNotFoundError(CommonError):
    """模板图像在屏幕上未找到。"""

    def __init__(self, template_name: str = '', timeout: float = 0) -> None:
        self.template_name = template_name
        self.timeout = timeout
        msg = f'未找到图像: {template_name}'
        if timeout:
            msg += f' (超时 {timeout:.1f}s)'
        super().__init__(msg)


# ── UI 层异常 ──


class PageNotFoundError(ApplicationError):
    """无法识别当前页面。"""


class NavigationError(ApplicationError):
    """页面导航失败（从 A 到 B 的转移失败）。"""

    def __init__(self, source: str, target: str, reason: str = '') -> None:
        self.source = source
        self.target = target
        msg = f'导航失败: {source} -> {target}'
        if reason:
            msg += f' ({reason})'
        super().__init__(msg)


# ── 业务动作异常 ──


class ManualRepairRequiredError(BusinessError):
    """Manual repair was dispatched and the active task must terminate."""


# ── 战斗系统异常 ──


class DockFullError(BusinessError):
    """决战模块具体的船坞已满错误。"""


class CombatRecognitionTimeoutError(BusinessError):
    """战斗状态识别超时。"""

    def __init__(self, candidates: list[str] | None = None, timeout: float = 0) -> None:
        self.candidates = candidates or []
        self.timeout = timeout
        names = ', '.join(self.candidates)
        super().__init__(f'战斗状态识别超时 ({timeout:.1f}s): [{names}]')


class CombatDecisionError(BusinessError):
    """战斗决策错误（规则配置问题等）。"""


# ── 不可恢复错误 ──


class CriticalError(SystemError):
    """不可恢复的严重错误，需要终止。"""
