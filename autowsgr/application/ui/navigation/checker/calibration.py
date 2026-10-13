"""模块功能：加载页码检查器共用的模板。

上层调用：
- application.ui.navigation.checker 下各模块检查器：读取本期活动的模板。

下层依赖：
- common.vision：加载模板并返回模板模型。

本模块只做加载，不解释识别规则、不持有页面状态，也不执行视觉识别。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from autowsgr.common.vision.adapters.template_matching import load_template


if TYPE_CHECKING:
    from autowsgr.common.vision import Template


# 模板根目录，位于 common.vision 的模板根下，按模块命名空间分目录。
# 活动模板的命名空间是 <活动>_<期号>，一期一个目录，换期换目录。
_TEMPLATE_ROOT = 'application/ui/navigation/checker'


def require_activity(event_type: str, activity: str) -> None:
    """校验调用方选择的活动玩法与当前 checker 一致。

    Args:
        event_type: 调用方给出的活动玩法标识。
        activity: 当前 checker 归属的活动标识。

    Raises:
        ValueError: 活动玩法标识与当前 checker 不一致。
    """
    if event_type != activity:
        raise ValueError(f'当前 checker 不支持的活动玩法: {event_type!r}')


def load_module_template(namespace: str, filename: str, *, name: str) -> Template:
    """加载某个模块命名空间下的模板。

    Args:
        namespace: 模板根下的相对目录，例如 `event/stage_push_20260930` 或 `home`。
        filename: 命名空间内的模板文件名。
        name: 模板业务名称，用于识别日志和匹配结果。

    Returns:
        已加载的模板。
    """
    return load_template(f'{_TEMPLATE_ROOT}/{namespace}/{filename}', name=name)
