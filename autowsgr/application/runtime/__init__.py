"""模块功能：运行时上下文的包入口。

上层调用：
- application、business 与 dispatch：通过 RuntimeContext 契约消费运行时服务。

边界：只导出运行时契约；旧 GameContext 链路仍在迁移中，未迁移完成前不在包入口转发。
"""

from __future__ import annotations

from autowsgr.application.runtime.contracts import RuntimeContext


__all__ = ['RuntimeContext']
