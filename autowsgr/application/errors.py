"""模块功能：定义 application 层实际拥有的具体错误类型。

上层调用：
- application.ui.controller：页面与修理工作流抛出具体操作错误。
- business.combat：业务用例识别并向上传递手动修理终止信号。
- dispatch 与 server：捕获手动修理终止信号并结束当前任务。

下层依赖：
- common.system.errors：提供 ApplicationError 捕获基类。

本模块只定义 application 层错误的所有权、构造参数和稳定文本，不实现恢复策略、
任务状态或页面流程。
"""

from __future__ import annotations

from autowsgr.common.system.errors import ApplicationError


class ActionFailedError(ApplicationError):
    """页面或工作流中的一次操作未能在限定条件下完成。"""

    def __init__(self, action_name: str, reason: str = '') -> None:
        self.action_name = action_name
        msg = f'操作失败: {action_name}'
        if reason:
            msg += f' ({reason})'
        super().__init__(msg)


class ManualRepairRequiredError(ActionFailedError):
    """手动修理已派出，当前任务必须终止。"""


__all__ = ['ActionFailedError', 'ManualRepairRequiredError']
